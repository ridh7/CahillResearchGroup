# Build script for TOPS 2.0 Measurement System
# Sets up Python venv + dependencies, builds the Next.js frontend,
# and copies the output into backend/static/.
# Run this once after cloning, or whenever the frontend changes.

$ErrorActionPreference = "Stop"

function Exit-WithPause($code) {
    Write-Host ""
    Write-Host "Press any key to close..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit $code
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend\tops-2.0-measurement-system"
$backendStaticDir = Join-Path $root "backend\static"
$venvDir = Join-Path $backendDir "myenv"

# --- Python setup ---
if (-Not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create Python virtual environment." -ForegroundColor Red
        Exit-WithPause 1
    }
}

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& (Join-Path $venvDir "Scripts\pip.exe") install -e $backendDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Python dependencies." -ForegroundColor Red
    Exit-WithPause 1
}
Write-Host "Python setup complete." -ForegroundColor Green

# --- Frontend build ---
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location $frontendDir
try {
    npm ci
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: 'npm ci' failed. Check package-lock.json or node version." -ForegroundColor Red
        Exit-WithPause 1
    }
    Write-Host "Frontend dependencies installed." -ForegroundColor Green

    Write-Host "Building frontend..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed. Check for TypeScript/ESLint errors above." -ForegroundColor Red
        Exit-WithPause 1
    }
    Write-Host "Frontend build complete." -ForegroundColor Green
} finally {
    Pop-Location
}

$outDir = Join-Path $frontendDir "out"
if (-Not (Test-Path $outDir)) {
    Write-Host "ERROR: Frontend build output not found at $outDir" -ForegroundColor Red
    Exit-WithPause 1
}

Write-Host "Copying build output to backend/static..." -ForegroundColor Cyan
if (Test-Path $backendStaticDir) {
    Remove-Item -Recurse -Force $backendStaticDir
}
Copy-Item -Recurse -Force $outDir $backendStaticDir

Write-Host ""
Write-Host "Build complete. Run start.bat to launch the application." -ForegroundColor Green
Exit-WithPause 0
