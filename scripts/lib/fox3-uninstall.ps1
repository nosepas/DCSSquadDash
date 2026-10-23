# -Uninstall for install-central.ps1 (dot-sourced). Removes services and firewall rules; keeps data unless -PurgeData.
function Invoke-Uninstall([string]$ConfigDir, [string]$RepoRoot, [switch]$PurgeData) {
    foreach ($n in $script:FoxServices) {
        $sid = $null
        if (-not $DryRun -and (Test-Service $n)) { $sid = Get-AccountSid (Get-ServiceAccount $n) }   # before the service (and its SID) disappears
        Run "nssm stop $n ; nssm remove $n confirm (skipped if it does not exist)" {
            if (Test-Service $n) { Invoke-Native nssm @('stop', $n) -Tolerate; Invoke-Native nssm @('remove', $n, 'confirm') }
        }
        if ($sid) { Run "icacls `"$RepoRoot`" /remove *$sid  (read access granted to $n)" { Invoke-Native icacls.exe @($RepoRoot, '/remove', "*$sid") -Tolerate } }
    }
    Run 'remove firewall rules "FOX3 HTTP (certificate validation)" and "FOX3 HTTPS"' { Remove-FirewallRules }
    if ($PurgeData) {
        Run "DELETE $ConfigDir (configuration, logs, agent package, Caddy certificates)" { if (Test-Path $ConfigDir) { Remove-Item -Recurse -Force $ConfigDir } }
    } else { Write-Host "    data kept in $ConfigDir (add -PurgeData to delete it; the PostgreSQL database is never touched)" }
}
