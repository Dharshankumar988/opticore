# OptiCore Device Client - Installation Script for Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OptiCore Device Client - Installation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists, if not create from .env.example
if (-not (Test-Path .env)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  IMPORTANT: Please edit .env and set your OPTICORE_SERVER_URL" -ForegroundColor Red
    Write-Host "   Find your server URL from your Kaggle/ngrok session." -ForegroundColor Red
} else {
    Write-Host ".env already exists, skipping creation" -ForegroundColor Green
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Before starting the application:" -ForegroundColor Yellow
Write-Host "1. Edit .env and set OPTICORE_SERVER_URL to your actual server URL" -ForegroundColor Yellow
Write-Host "2. On Windows, pair Bluetooth devices through Settings > Devices" -ForegroundColor Yellow
Write-Host "3. Ensure your camera is connected and accessible" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Green
Write-Host "  .\start.ps1" -ForegroundColor Green
Write-Host ""
