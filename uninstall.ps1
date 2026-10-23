# OptiCore Device Client - Uninstallation Script for Windows

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OptiCore Device Client - Uninstallation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Stop the application if running
$PID_FILE = "opticore.pid"
if (Test-Path $PID_FILE) {
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
                break
            }
        }
        
        # Force kill if still running
        if (-not $process.HasExited) {
            Write-Host "Force killing OptiCore..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force
            Remove-Item $PID_FILE
            Write-Host "OptiCore stopped" -ForegroundColor Green
        }
    } catch {
        Write-Host "OptiCore process not found (removing stale PID file)" -ForegroundColor Yellow
        Remove-Item $PID_FILE
    }
}

# Ask about removing virtual environment
if (Test-Path venv) {
    Write-Host ""
    $response = Read-Host "Remove virtual environment? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
        Write-Host "Virtual environment removed" -ForegroundColor Green
    } else {
        Write-Host "Virtual environment kept" -ForegroundColor Green
    }
} else {
    Write-Host "No virtual environment found" -ForegroundColor Green
}

# Ask about removing .env file
if (Test-Path .env) {
    Write-Host ""
    $response = Read-Host "Remove .env configuration file? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing .env file..." -ForegroundColor Yellow
        Remove-Item .env
        Write-Host ".env file removed" -ForegroundColor Green
    } else {
        Write-Host ".env file kept" -ForegroundColor Green
    }
} else {
    Write-Host "No .env file found" -ForegroundColor Green
}

# Ask about removing PID file
if (Test-Path $PID_FILE) {
    Write-Host ""
    $response = Read-Host "Remove PID file? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing PID file..." -ForegroundColor Yellow
        Remove-Item $PID_FILE
        Write-Host "PID file removed" -ForegroundColor Green
    } else {
        Write-Host "PID file kept" -ForegroundColor Green
    }
}

# Ask about removing Python cache
if (Test-Path __pycache__) {
    Write-Host ""
    $response = Read-Host "Remove Python cache (__pycache__)? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing Python cache..." -ForegroundColor Yellow
        Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
        Write-Host "Python cache removed" -ForegroundColor Green
    } else {
        Write-Host "Python cache kept" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Uninstallation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: This does not remove:" -ForegroundColor Yellow
Write-Host "  - Python packages installed globally" -ForegroundColor Yellow
Write-Host "  - Windows system components" -ForegroundColor Yellow
Write-Host ""
$currentDir = Split-Path -Leaf (Get-Location)
Write-Host "To completely remove this directory, run:" -ForegroundColor Yellow
Write-Host "  cd .. ; Remove-Item -Recurse -Force $currentDir" -ForegroundColor Yellow
Write-Host ""
