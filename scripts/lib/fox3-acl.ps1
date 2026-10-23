# NTFS and registry permissions for install-central.ps1 (dot-sourced). Uses Run / $DryRun from the caller's scope.
# Well-known SIDs instead of names so it works on any Windows language: S-1-5-18 = SYSTEM, S-1-5-32-544 = Administrators.

function Grant([string]$Path, [string]$Account, [string]$Perm) {
    Run "icacls `"$Path`" /grant `"${Account}:$Perm`"" {
        Invoke-Native icacls.exe @($Path, '/grant', "${Account}:$Perm")
    }
}

# $ConfigDir: only Administrators + SYSTEM by default; each service account gets the minimum it needs.
#  - Central only READS config/agent/repo; its only write is its log folder (nssm opens the log as the service account).
#  - Caddy reads the Caddyfile and WRITES its own data (certificates, ACME account key) and config folder.
function Set-FoxAcls([string]$ConfigDir, [string]$RepoRoot, [string]$CaddyExe) {
    $central = Get-ServiceAccount 'FOX3Central'; $caddy = Get-ServiceAccount 'FOX3Caddy'
    Run "icacls `"$ConfigDir`" /inheritance:r  (cut inheritance: ordinary users no longer read it)" {
        Invoke-Native icacls.exe @($ConfigDir, '/inheritance:r')
    }
    Grant $ConfigDir '*S-1-5-32-544' '(OI)(CI)F'
    Grant $ConfigDir '*S-1-5-18' '(OI)(CI)F'
    Grant $ConfigDir $central '(RX)'                     # this folder only, to open the files in it
    Grant $ConfigDir $caddy '(RX)'
    Grant "$ConfigDir\central.toml" $central '(R)'
    Grant "$ConfigDir\Caddyfile" $caddy '(R)'
    Grant "$ConfigDir\agent" $central '(OI)(CI)RX'
    Grant "$ConfigDir\logs\central" $central '(OI)(CI)M'
    Grant "$ConfigDir\logs\caddy" $caddy '(OI)(CI)M'
    Grant "$ConfigDir\caddy" $caddy '(OI)(CI)M'          # data (certificates) and config
    Grant $RepoRoot $central '(OI)(CI)RX'                # program files: .venv, web\dist, contracts
    Grant $CaddyExe $caddy '(RX)'                         # the one file, not its folder
    foreach ($p in @($RepoRoot, $CaddyExe)) {
        if ($p -like "$env:SystemDrive\Users\*") { Write-Warning "$p is inside a user profile: check that the service accounts can read it (a per-user Python or caddy install usually cannot be used by a service)." }
    }
}

# The nssm settings (database URL, Discord secret) live in HKLM\SYSTEM\...\Services\<name>\Parameters. By default that key
# can be read by ordinary users; make it readable only by SYSTEM, Administrators and the service account itself.
function Lock-ServiceKey([string]$Name) {
    Run "registry ACL on HKLM:\SYSTEM\CurrentControlSet\Services\$Name\Parameters: SYSTEM + Administrators full, $(Get-ServiceAccount $Name) read-only, no inheritance" {
        $path = "HKLM:\SYSTEM\CurrentControlSet\Services\$Name\Parameters"
        $rights = [Security.AccessControl.RegistryRights]
        $inherit = [Security.AccessControl.InheritanceFlags]::ContainerInherit
        $none = [Security.AccessControl.PropagationFlags]::None
        $allow = [Security.AccessControl.AccessControlType]::Allow
        $acl = Get-Acl $path
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($r in @($acl.Access)) { [void]$acl.RemoveAccessRule($r) }
        $grants = @{ 'S-1-5-18' = $rights::FullControl; 'S-1-5-32-544' = $rights::FullControl; (Get-AccountSid (Get-ServiceAccount $Name)) = $rights::ReadKey }
        foreach ($sid in $grants.Keys) {
            $who = New-Object Security.Principal.SecurityIdentifier($sid)
            $acl.AddAccessRule((New-Object Security.AccessControl.RegistryAccessRule($who, $grants[$sid], $inherit, $none, $allow)))
        }
        Set-Acl -Path $path -AclObject $acl
    }
}
