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

# Check for system dependencies
echo ""
echo "Checking system dependencies..."

# Check for eSpeak
if ! command -v espeak &> /dev/null; then
    echo "⚠️  eSpeak not found. Install with: sudo apt-get install espeak"
else
    echo "✓ eSpeak is installed"
fi

# Check for PulseAudio/PipeWire
if command -v pactl &> /dev/null; then
    echo "✓ PulseAudio is installed"
elif command -v pw-cli &> /dev/null; then
    echo "✓ PipeWire is installed"
else
    echo "⚠️  PulseAudio/PipeWire not found. Install with: sudo apt-get install pulseaudio"
fi

# Check for camera permissions
if [ -e /dev/video0 ]; then
    VIDEO_GROUP=$(stat -c "%G" /dev/video0 2>/dev/null || echo "video")
    echo "✓ Camera device found at /dev/video0"
    echo "  Ensure your user is in the '$VIDEO_GROUP' group: sudo usermod -a -G $VIDEO_GROUP \$USER"
else
    echo "⚠️  No camera device found at /dev/video0"
fi

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
echo "Audio: PulseAudio or PipeWire required for Bluetooth audio"
echo "Camera: Ensure user is in 'video' group"
echo ""
