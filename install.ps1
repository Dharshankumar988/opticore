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
try {
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some dependencies may have failed to install" -ForegroundColor Yellow
    Write-Host "This is common on Windows ARM64 - see README.md for details" -ForegroundColor Yellow
}

# Check for Bluetooth service
Write-Host ""
Write-Host "Checking system dependencies..."
$btService = Get-Service -Name bthserv -ErrorAction SilentlyContinue
if ($btService -and $btService.Status -eq 'Running') {
    Write-Host "✓ Bluetooth service is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  Bluetooth service not running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: Please edit .env and set OPTICORE_SERVER_URL" -ForegroundColor Red
Write-Host "   Find your server URL from your Kaggle/ngrok session." -ForegroundColor Red
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Green
Write-Host "  .\start.ps1" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Quick Reference" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start:   .\start.ps1" -ForegroundColor Green
Write-Host "To stop:    .\stop.ps1" -ForegroundColor Green
Write-Host "Dashboard:  http://127.0.0.1:5050" -ForegroundColor Green
Write-Host ""
Write-Host "TTS Service: Uses Windows SAPI5 (built-in voices)" -ForegroundColor Yellow
Write-Host "Note: On Windows ARM64, some packages may require Visual Studio Build Tools" -ForegroundColor Yellow
Write-Host ""
