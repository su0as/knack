# Knack: one-time setup on Windows (PowerShell 7 or Windows PowerShell 5.1).
#
#   powershell -ExecutionPolicy Bypass -File D:\dev\knack\scripts\setup_windows.ps1
#
# Or before the repo exists (folder may already hold your .env):
#   powershell -ExecutionPolicy Bypass -File D:\dev\knack\bootstrap.ps1
#
# What it does (nothing here spends money; no model is called except the free /models list):
#   1. puts portable git + uv on PATH if they live in -Tools (default D:\dev\dev-tools)
#   2. keeps caches and temp files on the same drive as the repo (not C:)
#   3. links the folder to github.com/su0as/knack (keeps an existing .env untouched)
#   4. creates .venv with Python 3.12 and installs knack[dev]
#   5. runs the free checks: knack check, knack oracle --n 5, knack models --remote
param(
    [string]$Repo = "D:\dev\knack",
    [string]$Tools = "D:\dev\dev-tools",
    [string]$Remote = "https://github.com/su0as/knack.git",
    [switch]$SkipChecks
)
$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. tools
foreach ($p in @("$Tools\git\cmd", "$Tools\uv")) { if (Test-Path $p) { $env:PATH = "$p;$env:PATH" } }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git not found. Install Git for Windows or put MinGit in $Tools\git" }
$haveUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)

# 2. caches next to the repo
$Drive = Split-Path -Qualifier $Repo
$Root = Join-Path $Drive "dev"
New-Item -ItemType Directory -Force "$Root\cache", "$Root\tmp", $Repo | Out-Null
$env:UV_CACHE_DIR = "$Root\cache\uv"; $env:PIP_CACHE_DIR = "$Root\cache\pip"; $env:MPLCONFIGDIR = "$Root\cache\matplotlib"
$env:TEMP = "$Root\tmp"; $env:TMP = "$Root\tmp"
foreach ($v in "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PIP_REQUIRE_VIRTUALENV", "PIP_TARGET", "PIP_PREFIX") { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }

# 3. repo
Set-Location $Repo
if (-not (Test-Path "$Repo\.git")) {
    Step "Linking $Repo to $Remote (an existing .env is kept: it is gitignored)"
    git init -b main | Out-Null
    git remote add origin $Remote
    git fetch origin
    if ($LASTEXITCODE -ne 0) {
        Write-Host "git fetch failed. The repo is private: sign in when Git asks, or download the ZIP from GitHub, unzip it here and re-run." -ForegroundColor Yellow
        exit 1
    }
    git reset --hard origin/main | Out-Null
    git branch --set-upstream-to=origin/main main | Out-Null
} else {
    Step "Repo already linked; pulling"
    git pull --ff-only
}
Remove-Item "$Repo\.probe" -ErrorAction SilentlyContinue
if (-not (Test-Path "$Repo\.env")) {
    Copy-Item "$Repo\.env.example" "$Repo\.env"
    Write-Host "Created .env from .env.example: put your Token Factory key in NEBIUS_API_KEY" -ForegroundColor Yellow
}
git check-ignore -q .env
if ($LASTEXITCODE -ne 0) { throw ".env is NOT gitignored. Stop and fix .gitignore before doing anything else." }

# 4. venv
if (-not (Test-Path "$Repo\.venv\Scripts\python.exe")) {
    Step "Creating .venv (Python 3.12)"
    if ($haveUv) { uv venv --python 3.12 .venv } else { py -3.12 -m venv .venv }
}
Step "Installing knack[dev]"
if ($haveUv) { uv pip install --python .venv\Scripts\python.exe -e ".[dev]" } else { .venv\Scripts\python.exe -m pip install -e ".[dev]" }
. "$Repo\.venv\Scripts\Activate.ps1"

# 5. free checks
if (-not $SkipChecks) {
    Step "knack check (MuJoCo, rendering, key present; no calls)"
    knack check
    Step "knack oracle --n 5 (simulator sanity check; free)"
    knack oracle --n 5 --min 0.6
    Step "knack models --remote (lists models your key can see; free)"
    knack models --remote
}
Write-Host ""
Write-Host "Ready. Next session: . $Repo\scripts\env_windows.ps1" -ForegroundColor Green
Write-Host "Free:  knack learn lift --mock ; knack ui" -ForegroundColor Green
Write-Host "Costs tokens (capped): knack learn lift --coder super --budget 0.30" -ForegroundColor Yellow
