<#
  Starts the FOX3 demo (central + simulated agent) at http://localhost:8000 and opens the browser.
  Usage:  powershell -ExecutionPolicy Bypass -File scripts\run-demo.ps1 [-Port 8000] [-Reset]
#>
param([int]$Port = 8000, [switch]$Reset)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$exe = Join-Path $root '.venv\Scripts\fox3-demo.exe'
if (-not (Test-Path $exe)) { throw 'Not installed yet. Run scripts\install-demo.ps1 first.' }
$env:FOX3_WEB_DIR = Join-Path $root 'web\dist'
$argsList = @('--port', $Port)
if ($Reset) { $argsList += '--reset' }
Start-Job { Start-Sleep 4; Start-Process "http://localhost:$using:Port" } | Out-Null
& $exe @argsList
