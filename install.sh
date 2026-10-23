#!/bin/bash
# OptiCore Device Client - Installation Script for Linux

set -e

echo "=========================================="
echo "OptiCore Device Client - Installation"
echo "=========================================="

# Check if .env exists, if not create from .env.example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env and set your OPTICORE_SERVER_URL"
    echo "   Find your server URL from your Kaggle/ngrok session."
else
    echo ".env already exists, skipping creation"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Please edit .env and set OPTICORE_SERVER_URL"
echo "   Find your server URL from your Kaggle/ngrok session."
echo ""
echo "To start the application, run:"
echo "  ./start.sh"
echo ""
echo "=========================================="
echo "Quick Reference"
echo "=========================================="
echo ""
echo "To start:   ./start.sh"
echo "To stop:    ./stop.sh"
echo "Dashboard:  http://127.0.0.1:5050"
echo ""
echo "TTS Service: Uses eSpeak (install with: sudo apt-get install espeak)"
echo ""
