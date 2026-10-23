<#
  FOX3 central installer for Windows (production). Run as Administrator in the project folder.

  Prerequisites you provide (the script checks them and says what is missing):
    - Python 3.12+ and (only to build the web interface) Node.js LTS
    - a PostgreSQL database for FOX3 (create an empty database and a user) -> pass its URL when asked
    - caddy.exe on PATH (https://caddyserver.com/download) : gets and renews the Let's Encrypt certificate
    - nssm.exe on PATH (https://nssm.cc) : runs FOX3 and Caddy as Windows services
    - the DNS name pointing to this PC's public IP, and the router forwarding TCP 80 and 443 to this PC

  Usage:
    powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Hostname fox3.example.org `
        -AdminDiscordIds 123456789012345678 -DiscordClientId 111222333444555666
    Add -DryRun to see every step without changing anything.
    Re-running is safe: existing services are updated in place (nssm set). Leave the secret prompts empty on a re-run to keep them.
    Remove: scripts\install-central.ps1 -Uninstall   (keeps data; add -PurgeData to delete %ProgramData%\FOX3)

  SECURITY: FOX3Central and FOX3Caddy run as the virtual accounts NT SERVICE\FOX3Central / NT SERVICE\FOX3Caddy (not LocalSystem);
  %ProgramData%\FOX3 and the services' registry keys are restricted with ACLs. Local administrators can still read the secrets.

  STATUS: the individual pieces are tested (migrations on PostgreSQL, configuration, CLI); this installer as a whole has not
  been run on a clean Windows PC yet, and the certificate issuance needs your real DNS name and open ports.
#>
[CmdletBinding(DefaultParameterSetName = 'Install')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Install')][ValidatePattern('^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}$')][string]$Hostname,
    [Parameter(ParameterSetName = 'Install')][string[]]$AdminDiscordIds = @(),
    [Parameter(ParameterSetName = 'Install')][string]$DiscordClientId = '',
    [Parameter(ParameterSetName = 'Install')][int]$Port = 8000,
    [Parameter(ParameterSetName = 'Install')][switch]$SkipAgentBuild,
    [Parameter(Mandatory, ParameterSetName = 'Uninstall')][switch]$Uninstall,
    [Parameter(ParameterSetName = 'Uninstall')][switch]$PurgeData,
    [string]$ConfigDir = (Join-Path $env:ProgramData 'FOX3'),
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$exe = Join-Path $root '.venv\Scripts\fox3-central.exe'

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Run($text, [scriptblock]$action) {
    if ($DryRun) { Write-Host "    [dry run] $text" -ForegroundColor DarkGray } else { & $action }
}
function Need($cmd, $hint) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd not found. $hint" }
}
function Plain([securestring]$s) { [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)) }
foreach ($lib in 'fox3-service', 'fox3-acl', 'fox3-uninstall') { . (Join-Path $PSScriptRoot "lib\$lib.ps1") }

if ($Uninstall) {
    Step 'Uninstalling FOX3 central'
    if (-not $DryRun -and -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrator')) { throw 'Run this script as Administrator.' }
    Invoke-Uninstall $ConfigDir $root -PurgeData:$PurgeData
    return
}

Step 'Checking prerequisites'
if (-not $DryRun -and -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrator')) {
    throw 'Run this script as Administrator.'
}
Need python 'Install Python 3.12 or newer (tick "Add to PATH").'
$ver = [version](python -c "import sys;print('.'.join(map(str,sys.version_info[:3])))")
if ($ver -lt [version]'3.12') { throw "Python $ver found, 3.12+ required." }
if (-not $DryRun) {
    Need caddy 'Download caddy.exe from https://caddyserver.com/download and put it on PATH.'
    Need nssm 'Download nssm.exe from https://nssm.cc and put it on PATH.'
}

Step 'Python environment'
Run 'python -m venv .venv ; pip install ".[postgres]"' {
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install --quiet ".[postgres]"
}

Step 'Web interface'
if (-not (Test-Path web\dist\index.html)) {
    Run 'npm ci ; npm run build (in web\)' {
        Need npm 'Install Node.js LTS (needed once, to build the web interface).'
        Push-Location web; npm ci --silent; npm run build --silent; Pop-Location
    }
} else { Write-Host '    already built' }

Step 'Agent package (the executable that administrators download for their DCS server PC)'
if ($SkipAgentBuild) { Write-Host '    skipped (-SkipAgentBuild): the download button will say the agent is not built' } else {
    Run 'pip install ".[build]" ; python tools\build_agent.py --out "$ConfigDir\agent"  (takes about a minute)' {
        & .\.venv\Scripts\python.exe -m pip install --quiet ".[build]"
        & .\.venv\Scripts\python.exe tools\build_agent.py --out "$ConfigDir\agent"
        if ($LASTEXITCODE -ne 0) { throw 'The agent build failed (re-run with -SkipAgentBuild to install without the agent download).' }
    }
}


Step 'Folders (logs and Caddy data live inside the restricted configuration folder)'
foreach ($d in 'agent', 'logs\central', 'logs\caddy', 'caddy\data', 'caddy\config') {
    Run "create $ConfigDir\$d" { New-Item -ItemType Directory -Force -Path (Join-Path $ConfigDir $d) | Out-Null }
}
if (-not $DryRun) {
    $home_ = (Get-Content .venv\pyvenv.cfg | Where-Object { $_ -match '^home\s*=' }) -replace '^home\s*=\s*', ''
    if ($home_ -like "$env:SystemDrive\Users\*") { Write-Warning "Python lives in $home_ (a user profile): the service account cannot read it. Install Python for all users (C:\Program Files) and recreate .venv." }
}

Step 'Secrets (kept in the Windows service configuration, never in a file)'
$dbUrl = ''; $discordSecret = ''
$centralExists = (-not $DryRun) -and (Test-Service 'FOX3Central')
if (-not $DryRun) {
    $hint = if ($centralExists) { ' (empty = keep the current one)' } else { '' }
    $dbUrl = Plain (Read-Host "PostgreSQL URL, e.g. postgresql+psycopg://fox3:PASSWORD@localhost:5432/fox3$hint" -AsSecureString)
    if ($DiscordClientId -and $dbUrl) { $discordSecret = Plain (Read-Host 'Discord application client secret' -AsSecureString) }
    if (-not $dbUrl -and -not $centralExists) { throw 'The PostgreSQL URL is required.' }
}

Step "Configuration in $ConfigDir"
$initArgs = @('init', '--hostname', $Hostname, '--port', $Port, '--out', $ConfigDir)
foreach ($id in $AdminDiscordIds) { $initArgs += @('--admin-id', $id) }
if ($DiscordClientId) { $initArgs += @('--discord-client-id', $DiscordClientId) }
if (-not $SkipAgentBuild) { $initArgs += @('--agent-dir', "$ConfigDir\agent") }
Run 'fox3-central init ... (writes central.toml and the Caddyfile; existing files are kept)' {
    & $exe @initArgs
    if ($LASTEXITCODE -ne 0) { throw 'Could not write the configuration (check the host name and the Discord ids).' }
}

Step 'Database schema'
if ($dbUrl -or $DryRun) {
    Run 'fox3-central migrate' {
        $env:FOX3_DATABASE_URL = $dbUrl
        try { & $exe migrate --config "$ConfigDir\central.toml" } finally { Remove-Item Env:FOX3_DATABASE_URL -ErrorAction SilentlyContinue }
        if ($LASTEXITCODE -ne 0) { throw 'Migration failed: check the database URL and that the database is empty or already migrated.' }
    }
} else { Write-Host '    skipped (kept the current database URL: run fox3-central migrate yourself if the schema changed)' }

Step 'Windows services (nssm; created or updated in place)'
$caddyExe = if ($DryRun) { 'caddy.exe' } else { (Get-Command caddy).Source }
$central = @{ AppStdout = "$ConfigDir\logs\central\central.log"; AppStderr = "$ConfigDir\logs\central\central.log"; AppRotateFiles = 1; Start = 'SERVICE_AUTO_START' }
if ($dbUrl -or $DryRun) {
    $central.AppEnvironmentExtra = @("FOX3_DATABASE_URL=$dbUrl", "FOX3_DISCORD_CLIENT_SECRET=$discordSecret", 'PYTHONDONTWRITEBYTECODE=1')
}
Set-FoxService 'FOX3Central' $exe @('serve', '--config', "$ConfigDir\central.toml") $central
# Caddy keeps its certificates in $XDG_DATA_HOME\caddy and its autosave in $XDG_CONFIG_HOME\caddy: point both into the ACL'd folder.
Set-FoxService 'FOX3Caddy' $caddyExe @('run', '--config', "$ConfigDir\Caddyfile", '--adapter', 'caddyfile') @{
    AppDirectory = $ConfigDir; Start = 'SERVICE_AUTO_START'; AppRotateFiles = 1
    AppStdout = "$ConfigDir\logs\caddy\caddy.log"; AppStderr = "$ConfigDir\logs\caddy\caddy.log"
    AppEnvironmentExtra = @("XDG_DATA_HOME=$ConfigDir\caddy\data", "XDG_CONFIG_HOME=$ConfigDir\caddy\config")
}

Step 'Service accounts (virtual accounts instead of LocalSystem)'
foreach ($n in $script:FoxServices) { Set-ServiceAccount $n }

Step 'Permissions (NTFS and service registry keys)'
Set-FoxAcls $ConfigDir $root $caddyExe
foreach ($n in $script:FoxServices) { Lock-ServiceKey $n }

Step 'Firewall and start'
Set-FirewallRules $caddyExe
Start-FoxServices

Write-Host ''
Write-Host "Done. Open https://$Hostname (the first visit may take a few seconds while the certificate is issued)." -ForegroundColor Green
Write-Host "If it does not load: DNS must point to this PC, and the router must forward TCP 80 and 443 here. Logs: $ConfigDir\logs"
Write-Host "Discord: add this redirect URL in the Discord developer portal: https://$Hostname/api/v1/auth/discord/callback"
