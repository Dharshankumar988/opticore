#!/bin/bash
# OptiCore Device Client - Stop Script for Linux

PID_FILE="opticore.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "OptiCore is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping OptiCore (PID: $PID)..."
    kill "$PID"
    
    # Wait for process to terminate
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "OptiCore stopped successfully"
            rm "$PID_FILE"
            exit 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "Force killing OptiCore..."
    kill -9 "$PID"
    rm "$PID_FILE"
    echo "OptiCore stopped"
else
    echo "OptiCore process not found (removing stale PID file)"
    rm "$PID_FILE"
fi
