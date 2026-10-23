# OptiCore Device Client

A Python client for connecting camera devices to the OptiCore inference server. Streams video, receives detections/OCR results, and provides text-to-speech accessibility alerts.

## Quick Start

### Linux
```bash
git clone https://github.com/Dharshankumar988/opticore.git
cd opticore
chmod +x install.sh start.sh stop.sh
./install.sh

# Edit .env and set your server URL
nano .env  # Change OPTICORE_SERVER_URL

# Start
./start.sh
```

### Windows PowerShell
```powershell
git clone https://github.com/Dharshankumar988/opticore.git
cd opticore
.\install.ps1

# Edit .env and set your server URL
notepad .env  # Change OPTICORE_SERVER_URL

# Start
.\start.ps1
```

Dashboard opens at http://127.0.0.1:5050

## Configuration

Edit `.env` file:

**Required:**
```
OPTICORE_SERVER_URL=https://your-ngrok-url.ngrok-free.dev
```

**Optional:**
```
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
STREAM_FPS=10
TTS_ENABLED=true
```

**Groq AI (Optional - for natural-language scene summaries):**
```
GROQ_ENABLED=false
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=5
GROQ_MAX_TOKENS=150
GROQ_COOLDOWN_SECONDS=30
GROQ_MAX_INPUT_TOKENS=500
```

Note: Groq is completely optional. The application runs fully without it. When enabled, it provides brief natural-language summaries of detected scenes. Get an API key at https://console.groq.com/

## Usage

- Open dashboard at http://127.0.0.1:5050
- Click "Start Streaming" to begin
- View detections and OCR results in real-time
- Use TTS settings to configure speech

## Stopping

```bash
./stop.sh    # Linux
.\stop.ps1   # Windows
```

## Requirements

- Python 3.8+
- Camera (webcam or built-in)
- Linux: eSpeak for TTS (`sudo apt-get install espeak`)
- Windows: No extra dependencies (uses built-in SAPI5)

## Platform-Specific Notes

### Windows ARM64 (Surface Pro X, etc.)
On Windows ARM64, numpy and opencv-python may require compilation. If installation fails:
1. Install Visual Studio Build Tools for ARM64 from Microsoft
2. Or use a pre-built wheel if available
3. Alternatively, run on x86_64 Windows or Linux/Raspberry Pi

### Linux/Raspberry Pi
Most dependencies install without issues. Ensure:
- Camera permissions: `sudo usermod -a -G video $USER` (then log out and back in)
- Audio: PulseAudio or PipeWire installed
- Bluetooth: BlueZ installed and running

## TTS Services Used

- **Linux**: eSpeak/espeak-ng (install with `sudo apt-get install espeak`)
- **Windows**: SAPI5 (built-in Windows speech synthesis)
- Both are offline and work without internet connection

## Features

- Continuous camera streaming
- Real-time object detection and OCR
- Text-to-speech alerts
- Web dashboard with dark graphite theme
- Bluetooth audio support
- Auto-reconnection with exponential backoff
- Frame dropping to maintain responsiveness
- Optional Groq AI for natural-language summaries

## Troubleshooting

**Camera not found:**
- Try different CAMERA_INDEX values (0, 1, 2)
- On Linux: Check permissions with `ls -l /dev/video*`
- Ensure camera is not in use by another application
- Check if camera opens with `v4l2-ctl --list-devices` (Linux)

**Server connection failed:**
- Check OPTICORE_SERVER_URL matches your current ngrok URL
- Test connection using the "Test Connection" button in dashboard
- Ensure server is running and accessible
- Check firewall settings

**TTS not working:**
- Linux: Install eSpeak (`sudo apt-get install espeak`)
- Windows: Ensure audio drivers are installed
- Check system audio output is not muted

**Bluetooth not detected:**
- Linux: Ensure bluetoothd is running (`systemctl status bluetooth`)
- Linux: Install BlueZ tools (`sudo apt-get install bluez`)
- Windows: Ensure Bluetooth service is running (`sc query bthserv`)

**Dashboard shows unstyled HTML:**
- Ensure Flask is serving static files correctly
- Check browser console for errors
- Clear browser cache

**Port in use:**
- Run stop script first, or change PORT in .env
- Kill existing process: `taskkill /F /PID <pid>` (Windows) or `kill <pid>` (Linux)

**Installation fails on Windows ARM64:**
- Install Visual Studio Build Tools for ARM64
- Or use x86_64 Windows environment
- See "Platform-Specific Notes" above

## Architecture

- **app.py**: Main Flask application and API routes
- **camera.py**: Camera discovery, capture, and frame encoding
- **server_client.py**: WebSocket client for video streaming and event handling
- **tts_service.py**: Text-to-speech with queue and throttling
- **bluetooth_service.py**: Audio device discovery and routing
- **alert_manager.py**: Alert prioritization and deduplication
- **groq_service.py**: Optional AI summaries (non-blocking)
- **web/**: Frontend dashboard (HTML/CSS/JS)

## License

MIT License

© 2026 Team Opticore. All Rights Reserved.
