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

## TTS Services Used

- **Linux**: eSpeak/espeak-ng (install with `sudo apt-get install espeak`)
- **Windows**: SAPI5 (built-in Windows speech synthesis)
- Both are offline and work without internet connection

## Features

- Continuous camera streaming
- Real-time object detection and OCR
- Text-to-speech alerts
- Web dashboard
- Bluetooth audio support
- Auto-reconnection

## Troubleshooting

**Camera not found:** Try different CAMERA_INDEX values (0, 1, 2)

**Server connection failed:** Check OPTICORE_SERVER_URL matches your current ngrok URL

**TTS not working:** Install eSpeak on Linux (`sudo apt-get install espeak`)

**Port in use:** Run stop script first, or change PORT in .env

## License

MIT License

© 2026 Team Opticore. All Rights Reserved.
