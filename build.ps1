# Build script for TOPS 2.0 Measurement System
# Sets up Python venv + dependencies, builds the Next.js frontend,
# and copies the output into backend/static/.
# Run this once after cloning, or whenever the frontend changes.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend\tops-2.0-measurement-system"
$backendStaticDir = Join-Path $root "backend\static"
$venvDir = Join-Path $backendDir "myenv"

# --- Python setup ---
if (-Not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv $venvDir
}
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& (Join-Path $venvDir "Scripts\pip.exe") install -e $backendDir

# --- Frontend build ---
Write-Host "Building frontend..." -ForegroundColor Cyan
Push-Location $frontendDir
try {
    npm ci
    npm run build
} finally {
    Pop-Location
}

$outDir = Join-Path $frontendDir "out"
if (-Not (Test-Path $outDir)) {
    Write-Host "ERROR: Frontend build output not found at $outDir" -ForegroundColor Red
    exit 1
}

Write-Host "Copying build output to backend/static..." -ForegroundColor Cyan
if (Test-Path $backendStaticDir) {
    Remove-Item -Recurse -Force $backendStaticDir
}
Copy-Item -Recurse -Force $outDir $backendStaticDir

Write-Host "Build complete. Run start.bat to launch the application." -ForegroundColor Green
