#!/bin/bash
# OptiCore Device Client - Uninstallation Script for Linux

set -e

echo "=========================================="
echo "OptiCore Device Client - Uninstallation"
echo "=========================================="
echo ""

# Stop the application if running
PID_FILE="opticore.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping OptiCore (PID: $PID)..."
        kill "$PID"
        
        # Wait for process to terminate
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "OptiCore stopped successfully"
                rm "$PID_FILE"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Force killing OptiCore..."
            kill -9 "$PID"
            rm "$PID_FILE"
            echo "OptiCore stopped"
        fi
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Ask about removing virtual environment
if [ -d "venv" ]; then
    echo ""
    read -p "Remove virtual environment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing virtual environment..."
        rm -rf venv
        echo "Virtual environment removed"
    else
        echo "Virtual environment kept"
    fi
else
    echo "No virtual environment found"
fi

# Ask about removing .env file
if [ -f ".env" ]; then
    echo ""
    read -p "Remove .env configuration file? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing .env file..."
        rm .env
        echo ".env file removed"
    else
        echo ".env file kept"
    fi
else
    echo "No .env file found"
fi

# Ask about removing log files
if [ -f "opticore.log" ]; then
    echo ""
    read -p "Remove log files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing log files..."
        rm -f opticore.log
        echo "Log files removed"
    else
        echo "Log files kept"
    fi
fi

# Ask about removing Python cache
if [ -d "__pycache__" ] || [ -d "tests/__pycache__" ]; then
    echo ""
    read -p "Remove Python cache (__pycache__)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing Python cache..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        echo "Python cache removed"
    else
        echo "Python cache kept"
    fi
fi

echo ""
echo "=========================================="
echo "Uninstallation complete!"
echo "=========================================="
echo ""
echo "Note: This does not remove system packages like:"
echo "  - eSpeak (if installed)"
echo "  - PulseAudio/PipeWire (if installed)"
echo "  - BlueZ (if installed)"
echo ""
echo "To remove these system packages, run:"
echo "  sudo apt-get remove espeak pulseaudio bluez"
echo ""
CURRENT_DIR=$(basename "$(pwd)")
echo "To completely remove this directory, run:"
echo "  cd .. && rm -rf $CURRENT_DIR"
echo ""
