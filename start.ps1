# OptiCore Device Client - Start Script for Windows

$ErrorActionPreference = "Stop"

# Check if virtual environment exists
if (-not (Test-Path venv)) {
    Write-Host "Virtual environment not found. Please run .\install.ps1 first." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host ".env file not found. Please run .\install.ps1 first." -ForegroundColor Red
    exit 1
}

# Check for PID file
$PID_FILE = "opticore.pid"
if (Test-Path $PID_FILE) {
    $OLD_PID = Get-Content $PID_FILE
    $process = Get-Process -Id $OLD_PID -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "OptiCore is already running (PID: $OLD_PID)" -ForegroundColor Yellow
        Write-Host "Use .\stop.ps1 to stop it first." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "Removing stale PID file" -ForegroundColor Yellow
        Remove-Item $PID_FILE
    }
}

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Start the application
Write-Host "Starting OptiCore Device Client..." -ForegroundColor Green
$process = Start-Process -FilePath "python" -ArgumentList "app.py" -NoNewWindow -PassThru

# Save PID
$process.Id | Out-File -FilePath $PID_FILE

Write-Host "OptiCore started with PID: $($process.Id)" -ForegroundColor Green
Write-Host "Dashboard should be available at http://127.0.0.1:5050" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the application, or run:" -ForegroundColor Yellow
Write-Host "  .\stop.ps1" -ForegroundColor Yellow
Write-Host ""

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
        $process.Refresh()
        if ($process.HasExited) {
            Write-Host "OptiCore process exited" -ForegroundColor Red
            Remove-Item $PID_FILE -ErrorAction SilentlyContinue
            exit 1
        }
    }
} finally {
    # Cleanup on Ctrl+C
    if (Test-Path $PID_FILE) {
        Remove-Item $PID_FILE -ErrorAction SilentlyContinue
    }
}
