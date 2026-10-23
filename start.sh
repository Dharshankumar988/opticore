#!/bin/bash
# OptiCore Device Client - Start Script for Linux

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ".env file not found. Please run ./install.sh first."
    exit 1
fi

# Check for PID file
PID_FILE="opticore.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "OptiCore is already running (PID: $OLD_PID)"
        echo "Use ./stop.sh to stop it first."
        exit 1
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Start the application in background
echo "Starting OptiCore Device Client..."
nohup python app.py > opticore.log 2>&1 &
APP_PID=$!

# Save PID
echo $APP_PID > "$PID_FILE"

echo "OptiCore started with PID: $APP_PID"
echo "Dashboard should be available at http://127.0.0.1:5050"
echo "Logs are being written to opticore.log"
echo ""
echo "To stop the application, run:"
echo "  ./stop.sh"
