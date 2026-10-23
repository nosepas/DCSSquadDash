<#
  RETIRED. The agent service is now installed by the guided installer:

      powershell -ExecutionPolicy Bypass -File scripts\install-agent.ps1 -CentralUrl https://YOUR-CENTRAL [-ServiceUser "PC\you"] [-DryRun]

  (it also creates the environment, writes agent.toml, pairs and checks the connection).
#>
Write-Host 'scripts\install-agent-service.ps1 was replaced by scripts\install-agent.ps1 (run it with -DryRun first).' -ForegroundColor Yellow
exit 1
