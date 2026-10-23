# OptiCore Device Client - Stop Script for Windows

$ErrorActionPreference = "Stop"

$PID_FILE = "opticore.pid"

if (-not (Test-Path $PID_FILE)) {
    Write-Host "OptiCore is not running (no PID file found)" -ForegroundColor Yellow
    exit 0
}

$processId = Get-Content $PID_FILE

try {
    $process = Get-Process -Id $processId -ErrorAction Stop
    Write-Host "Stopping OptiCore (PID: $processId)..." -ForegroundColor Yellow
    
    # Try graceful shutdown first
    $process.CloseMainWindow() | Out-Null
    
    # Wait up to 5 seconds
    for ($i = 0; $i -lt 5; $i++) {
        Start-Sleep -Seconds 1
        $process.Refresh()
        if ($process.HasExited) {
            Write-Host "OptiCore stopped successfully" -ForegroundColor Green
            Remove-Item $PID_FILE
            exit 0
        }
    }
    
    # Force kill if still running
    Write-Host "Force killing OptiCore..." -ForegroundColor Yellow
    Stop-Process -Id $processId -Force
    Remove-Item $PID_FILE
    Write-Host "OptiCore stopped" -ForegroundColor Green
    
} catch {
    Write-Host "OptiCore process not found (removing stale PID file)" -ForegroundColor Yellow
    Remove-Item $PID_FILE
}
