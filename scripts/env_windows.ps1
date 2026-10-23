# Dot-source at the start of each PowerShell session:   . D:\dev\knack\scripts\env_windows.ps1
# Portable git/uv on PATH, caches on D:, clean Python env vars, venv active, cwd = repo.
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Root = Split-Path -Parent $Repo
$Tools = Join-Path $Root "dev-tools"
foreach ($p in @("$Tools\git\cmd", "$Tools\uv")) { if (Test-Path $p) { $env:PATH = "$p;$env:PATH" } }
New-Item -ItemType Directory -Force "$Root\cache", "$Root\tmp" | Out-Null
$env:UV_CACHE_DIR = "$Root\cache\uv"; $env:PIP_CACHE_DIR = "$Root\cache\pip"; $env:MPLCONFIGDIR = "$Root\cache\matplotlib"
$env:TEMP = "$Root\tmp"; $env:TMP = "$Root\tmp"
foreach ($v in "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PIP_REQUIRE_VIRTUALENV", "PIP_TARGET", "PIP_PREFIX") { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
Set-Location $Repo
. "$Repo\.venv\Scripts\Activate.ps1"
Write-Host "knack ready in $Repo ($(python --version))" -ForegroundColor Green
