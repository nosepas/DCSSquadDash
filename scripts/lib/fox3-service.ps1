# Helpers for install-central.ps1 (dot-sourced): Windows services through nssm, running under virtual service accounts.
# Uses Run / $DryRun from the caller's scope. Never prints secret values.

$script:FoxServices = @('FOX3Central', 'FOX3Caddy')
$script:FirewallRules = @('FOX3 HTTP (certificate validation)', 'FOX3 HTTPS')

function Invoke-Native([string]$Exe, [string[]]$Arguments, [switch]$Tolerate) {
    & $Exe @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0 -and -not $Tolerate) { throw "$Exe $($Arguments[0]) failed (exit code $LASTEXITCODE)." }
}
function Test-Service([string]$Name) { & sc.exe query $Name *> $null; return ($LASTEXITCODE -eq 0) }
function Get-ServiceAccount([string]$Name) { "NT SERVICE\$Name" }
function Get-AccountSid([string]$Account) { (New-Object Security.Principal.NTAccount($Account)).Translate([Security.Principal.SecurityIdentifier]).Value }

# Create the service with nssm, or update it in place (nssm set) when it already exists. Settings = @{ Name = value-or-array }.
function Set-FoxService([string]$Name, [string]$Program, [string[]]$ProgramArgs, [hashtable]$Settings) {
    $exists = (-not $DryRun) -and (Test-Service $Name)
    Run "nssm install-or-update $Name : $Program $($ProgramArgs -join ' ')  (nssm set when it already exists)" {
        if ($exists) {
            Invoke-Native nssm @('stop', $Name) -Tolerate
            $quoted = @($ProgramArgs | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } })
            Invoke-Native nssm @('set', $Name, 'Application', $Program)
            Invoke-Native nssm @('set', $Name, 'AppParameters', ($quoted -join ' '))
        } else { Invoke-Native nssm (@('install', $Name, $Program) + $ProgramArgs) }
    }
    foreach ($key in $Settings.Keys) {
        $shown = if ($key -eq 'AppEnvironmentExtra') { '(values hidden)' } else { $Settings[$key] -join ' ' }
        Run "nssm set $Name $key $shown" { Invoke-Native nssm (@('set', $Name, $key) + @($Settings[$key])) }
    }
}

# Run the service as its own virtual account (no password, no profile, only the rights we grant it).
function Set-ServiceAccount([string]$Name) {
    $acct = Get-ServiceAccount $Name
    Run "sc.exe config $Name obj= `"$acct`"  (virtual service account, empty password)" {
        Invoke-Native sc.exe @('config', $Name, 'obj=', $acct)
        if (-not ((& sc.exe qc $Name) -match [regex]::Escape($acct))) { throw "$Name is not running as $acct after sc config." }
    }
}

function Remove-FirewallRules {
    foreach ($r in $script:FirewallRules) { Get-NetFirewallRule -DisplayName $r -ErrorAction SilentlyContinue | Remove-NetFirewallRule }
}
function Set-FirewallRules([string]$CaddyExe) {
    Run "firewall: (re)create inbound TCP 80 and 443 rules limited to $CaddyExe" {
        Remove-FirewallRules
        New-NetFirewallRule -DisplayName $script:FirewallRules[0] -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -Program $CaddyExe | Out-Null
        New-NetFirewallRule -DisplayName $script:FirewallRules[1] -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow -Program $CaddyExe | Out-Null
    }
}

function Start-FoxServices {
    Run 'nssm start FOX3Central, FOX3Caddy and check both report RUNNING' {
        foreach ($n in $script:FoxServices) { Invoke-Native nssm @('start', $n) -Tolerate }
        Start-Sleep -Seconds 5
        foreach ($n in $script:FoxServices) {
            if (-not ((& sc.exe query $n) -match 'RUNNING')) { Write-Warning "$n is not running: read the log in the logs folder and the Windows Event Viewer (Application)." }
        }
    }
}
