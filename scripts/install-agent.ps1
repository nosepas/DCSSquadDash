<#
  FOX3 agent installer for the Windows PC that runs the DCS server. Run as Administrator in the project folder.

  What it does (add -DryRun to only PRINT every step without changing anything):
    1. checks Python 3.12+, creates/uses .venv and installs the agent
    2. asks (without echo) for the one-time pairing code from the web admin, and optionally the DCSServerBot API key
    3. writes agent.toml (fox3-agent init), shows what it finds on this PC (discover), pairs, and checks the connection
    4. installs the Windows service with NSSM (restarts on failure, rotated log); the DCSServerBot key is stored ONLY in the
       service environment, never in a file; the pairing code is never written anywhere

  Usage:
    powershell -ExecutionPolicy Bypass -File scripts\install-agent.ps1 -CentralUrl https://fox3.example.org
    Run the service as your own Windows user (REQUIRED when Tacview recordings are in a Google Drive for desktop folder):
    powershell -ExecutionPolicy Bypass -File scripts\install-agent.ps1 -CentralUrl https://fox3.example.org -ServiceUser "PCNAME\yourname"

  Prerequisites you provide: Python 3.12+ on PATH, and nssm.exe on PATH (download from https://nssm.cc/download, unzip, copy
  win64\nssm.exe somewhere on PATH).

  STATUS: the Python commands used here are covered by tests; this script as a whole has NOT been run on a real server PC.
  Whether the service account can read the DPAPI-protected credentials and Google Drive folders is unverified.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^https?://[A-Za-z0-9._:\[\]-]+(/.*)?$')][string]$CentralUrl,
    [string]$ConfigDir = (Join-Path $env:ProgramData 'FOX3Agent'),
    [ValidatePattern('^[^\\\s]+\\[^\\\s]+$')][string]$ServiceUser = '',
    [string]$ServiceName = 'FOX3Agent',
    [switch]$UseDcsBot,
    [switch]$NoDcsBot,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$exe = Join-Path $root '.venv\Scripts\fox3-agent.exe'
$toml = Join-Path $ConfigDir 'agent.toml'
$keyVar = 'FOX3_DCSBOT_API_KEY'

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Run($text, [scriptblock]$action) {
    if ($DryRun) { Write-Host "    [dry run] $text" -ForegroundColor DarkGray } else { & $action }
}
function Need($cmd, $hint) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd not found. $hint" }
}
function Plain([securestring]$s) {
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "$what failed (exit code $LASTEXITCODE)." } }
$nssmHint = 'Download it from https://nssm.cc/download, unzip it and copy win64\nssm.exe to a folder on PATH, then run this script again.'

Step 'Checking prerequisites'
if (-not $DryRun -and -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrator')) {
    throw 'Run this script as Administrator.'
}
Need python 'Install Python 3.12 or newer from https://www.python.org (tick "Add to PATH").'
$ver = [version](python -c "import sys;print('.'.join(map(str,sys.version_info[:3])))")
if ($ver -lt [version]'3.12') { throw "Python $ver found, 3.12+ required." }
Write-Host "    Python $ver OK"
if ($DryRun) {
    if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) { Write-Host "    [dry run] nssm.exe is NOT on PATH: a real run would stop here. $nssmHint" -ForegroundColor Yellow }
} else {
    Need nssm $nssmHint
}
if ($ServiceUser) { Write-Host "    The service will run as $ServiceUser (a password will be asked)." }
else { Write-Host '    The service will run as LocalSystem (it will NOT see Google Drive for desktop folders; use -ServiceUser for that).' }

Step 'Python environment (.venv, pip install .)'
Run 'python -m venv .venv ; .venv\Scripts\python.exe -m pip install --upgrade pip ; pip install .' {
    python -m venv .venv; Check 'Creating the virtual environment'
    & .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip; Check 'Upgrading pip'
    & .\.venv\Scripts\python.exe -m pip install --quiet .; Check 'Installing the agent'
}

Step 'Secrets (typed here, never echoed, never written to a file)'
$pairCode = ''; $botKey = ''
if ($DryRun) {
    Write-Host '    [dry run] would ask for the one-time pairing code (create the server in the web admin first; the code expires in 15 minutes)'
    Write-Host '    [dry run] would ask whether to use DCSServerBot and, if yes, for its REST API key'
} else {
    $pairCode = Plain (Read-Host 'Pairing code from the web admin (empty = this PC is already paired)' -AsSecureString)
    $wantBot = $UseDcsBot -or (-not $NoDcsBot -and (Read-Host 'Use DCSServerBot (REST API key)? [y/N]') -match '^[yYsS]')
    if ($wantBot) { $botKey = Plain (Read-Host 'DCSServerBot REST API key' -AsSecureString) }
}
$useBot = $UseDcsBot -or [bool]$botKey

Step "Configuration in $ConfigDir"
$initArgs = @('init', '--central-url', $CentralUrl, '--out', $ConfigDir)
if ($useBot -or $DryRun) { $initArgs += @('--dcsbot-api-key-env', $keyVar) }
if (Test-Path $toml) {
    Write-Host "    $toml already exists: kept untouched (fox3-agent init never overwrites)."
} else {
    Run "fox3-agent $($initArgs -join ' ')" {
        & $exe @initArgs; Check 'Writing agent.toml'
    }
}
if ($botKey) { Set-Item -Path "Env:$keyVar" -Value $botKey }  # only for this script's child processes (check)

Step 'What this PC offers (discover)'
$discoverArgs = @('discover')
if ($ServiceUser) {
    $profileDir = Join-Path (Split-Path $env:USERPROFILE) ($ServiceUser.Split('\')[-1])
    if ($DryRun -or (Test-Path $profileDir)) { $discoverArgs += @('--home', $profileDir) }
}
Run "fox3-agent $($discoverArgs -join ' ')" { & $exe @discoverArgs }

Step 'Pairing with central'
Run 'fox3-agent pair --config agent.toml --code-stdin   (the code is piped through stdin, not on the command line)' {
    if ($pairCode) {
        $pairCode | & $exe pair --config $toml --code-stdin; Check 'Pairing (is the code correct, unused and younger than 15 minutes?)'
    } else { Write-Host '    no code given: pairing skipped' }
}
$pairCode = $null

Step 'Connection check'
Run 'fox3-agent check --config agent.toml' { & $exe check --config $toml; Check 'Connection check' }
if ($botKey) { Remove-Item "Env:$keyVar" }

Step "Windows service $ServiceName (NSSM)"
$svcPassword = ''
if ($ServiceUser -and -not $DryRun) { $svcPassword = Plain (Read-Host "Windows password of $ServiceUser" -AsSecureString) }
if ($ServiceUser) {
    Run "icacls ConfigDir /grant ${ServiceUser}:(OI)(CI)M   (the service user must write the queue and logs there)" {
        icacls $ConfigDir /grant "${ServiceUser}:(OI)(CI)M" | Out-Null; Check 'Granting access to the configuration folder'
    }
}
Run "if the service exists: nssm stop + remove; then nssm install $ServiceName fox3-agent run --config agent.toml" {
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        nssm stop $ServiceName | Out-Null
        nssm remove $ServiceName confirm | Out-Null
    }
    nssm install $ServiceName $exe run --config $toml; Check 'nssm install'
}
Run 'nssm set: description, auto start, AppDirectory, restart on failure (5 s), log file rotated at 5 MB' {
    nssm set $ServiceName DisplayName 'FOX3 Agent' | Out-Null
    nssm set $ServiceName Description 'Sends DCS server data to FOX3 (outbound HTTPS only)' | Out-Null
    nssm set $ServiceName Start SERVICE_AUTO_START | Out-Null
    nssm set $ServiceName AppDirectory $ConfigDir | Out-Null
    nssm set $ServiceName AppExit Default Restart | Out-Null
    nssm set $ServiceName AppRestartDelay 5000 | Out-Null
    nssm set $ServiceName AppStdout (Join-Path $ConfigDir 'agent.log') | Out-Null
    nssm set $ServiceName AppStderr (Join-Path $ConfigDir 'agent.log') | Out-Null
    nssm set $ServiceName AppRotateFiles 1 | Out-Null
    nssm set $ServiceName AppRotateOnline 1 | Out-Null
    nssm set $ServiceName AppRotateBytes 5000000 | Out-Null
}
if ($useBot) {
    Run "nssm set AppEnvironmentExtra $keyVar=<key>   (service environment only; not in agent.toml)" {
        nssm set $ServiceName AppEnvironmentExtra "$keyVar=$botKey" | Out-Null
    }
}
if ($ServiceUser) {
    Run "nssm set ObjectName $ServiceUser <password>" { nssm set $ServiceName ObjectName $ServiceUser $svcPassword | Out-Null }
}
$svcPassword = $null; $botKey = $null
Run "nssm start $ServiceName" {
    nssm start $ServiceName; Check 'Starting the service'
    Start-Sleep -Seconds 3
    nssm status $ServiceName
}

Write-Host ''
if ($DryRun) { Write-Host 'Dry run finished: nothing was changed.' -ForegroundColor Green }
else { Write-Host "Service $ServiceName installed and started. Log: $(Join-Path $ConfigDir 'agent.log')" -ForegroundColor Green }
Write-Host 'Next, in the web admin:'
Write-Host '  1. Open the server -> Agent: it should show ONLINE with the folders this PC detected.'
Write-Host '  2. In "Detected folders" click the Foothold saves folder (and the Tacview one) to fill the field, then press Save.'
Write-Host '  3. The agent applies the settings live (no restart). Run "fox3-agent check --config <agent.toml>" again if something is red.'
if ($useBot -or $DryRun) { Write-Host '  4. DCSServerBot: enable it in the admin (REST address); the API key is already in the service environment.' }
Write-Host "Support report for us:  $exe diagnose --config $toml --out report.txt"
