<#
  FOX3 local demo installer (Windows). Needs Python 3.12+ on PATH; Node.js only if web\dist is not already built.
  Usage:  powershell -ExecutionPolicy Bypass -File scripts\install-demo.ps1
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Need($cmd, $hint) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd not found. $hint" }
}

Need python 'Install Python 3.12 or newer from https://www.python.org/downloads/ (tick "Add to PATH").'
$ver = [version](python -c "import sys;print('.'.join(map(str,sys.version_info[:3])))")
if ($ver -lt [version]'3.12') { throw "Python $ver found, 3.12+ required." }

Write-Host '1/3 Creating virtual environment...'
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -e .

if (-not (Test-Path web\dist\index.html)) {
    Write-Host '2/3 Building the web interface...'
    Need npm 'Install Node.js LTS from https://nodejs.org/ (only needed to build the web interface).'
    Push-Location web
    npm ci --silent
    npm run build --silent
    Pop-Location
} else {
    Write-Host '2/3 Web interface already built.'
}

Write-Host '3/3 Done. Start the demo with:  scripts\run-demo.ps1'
