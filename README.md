# OptiCore Device Client

A production-oriented Python client for connecting camera-equipped devices to the OptiCore inference server. Streams video continuously, receives processed detections and OCR results, and communicates results through text-to-speech over system audio.

## Features

- **Continuous Camera Streaming**: Captures and streams video frames to the OptiCore server via WebSocket
- **Real-time Inference**: Receives object detections, tracking IDs, and OCR results from the server
- **Text-to-Speech**: Local TTS engine for accessibility alerts without requiring internet connectivity
- **Bluetooth Audio Support**: Platform-specific Bluetooth audio device discovery and routing
- **Web Dashboard**: Responsive browser-based control interface for configuration and monitoring
- **Alert Management**: Intelligent deduplication, prioritization, and throttling of speech alerts
- **Auto-Reconnection**: Exponential backoff for handling network failures and server restarts
- **Cross-Platform**: Supports Windows and Linux systems

## Architecture

The application is built with a modular, concurrent architecture:

- **`app.py`**: Main entry point, Flask web server, and application orchestration
- **`camera.py`**: Camera discovery, capture, and frame encoding with bounded buffering
- **`server_client.py`**: WebSocket connections for video streaming and event reception
- **`tts_service.py`**: Text-to-speech generation and playback with independent worker thread
- **`bluetooth_service.py`**: Bluetooth device discovery and audio output management
- **`alert_manager.py`**: Alert prioritization, deduplication, and speech throttling
- **`config.py`**: Configuration and environment variable handling
- **`web/`**: Browser dashboard (HTML, CSS, JavaScript)

## Prerequisites

### Windows
- Python 3.8 or higher
- A webcam or compatible camera device
- Administrator access for camera (usually not required)

### Linux
- Python 3.8 or higher
- A webcam or compatible camera device
- PulseAudio or PipeWire for audio
- BlueZ for Bluetooth (optional)
- User in `video` and `audio` groups

## Installation

### Linux

```bash
# Clone the repository
git clone <repository-url>
cd opticore-device-client

# Run installation script
chmod +x install.sh start.sh stop.sh
./install.sh
```

### Windows PowerShell

```powershell
# Clone the repository
git clone <repository-url>
cd opticore-device-client

# Run installation script
.\install.ps1
```

The installation script will:
1. Create a virtual environment
2. Install all Python dependencies
3. Create `.env` from `.env.example` if it doesn't exist

## Configuration

After installation, edit the `.env` file to configure the application:

**Required Settings:**
- `OPTICORE_SERVER_URL`: Your OptiCore server's public URL (from Kaggle/ngrok session)
- `CAMERA_INDEX`: Camera device index (usually 0 for first camera)

**Optional Settings:**
- `HOST/PORT`: Dashboard binding (default: 127.0.0.1:5050)
- `CAMERA_WIDTH/HEIGHT`: Capture resolution (default: 640x480)
- `STREAM_FPS`: Target frame rate (default: 10)
- `JPEG_QUALITY`: Image compression quality (default: 80)
- `TTS_ENABLED`: Enable/disable text-to-speech (default: true)
- `TTS_RATE`: Speech rate in words per minute (default: 175)
- `TTS_VOLUME`: Speech volume 0.0-1.0 (default: 0.8)
- `ALERT_COOLDOWN_SECONDS`: Minimum time between same alerts (default: 5)
- `ALERT_VERBOSITY`: Alert verbosity level (minimal/normal/verbose)

## Usage

### Starting the Application

**Linux:**
```bash
./start.sh
```

**Windows PowerShell:**
```powershell
.\start.ps1
```

The application will:
1. Start the camera capture
2. Connect to the OptiCore server
3. Launch the web dashboard at `http://127.0.0.1:5050`
4. Open the dashboard in your default browser

### Stopping the Application

**Linux:**
```bash
./stop.sh
```

**Windows PowerShell:**
```powershell
.\stop.ps1
```

### Web Dashboard

The dashboard provides controls for:
- Start/stop camera streaming
- Camera selection and configuration
- Server connection testing
- Live camera preview
- Inference results display
- Audio device information
- TTS settings and testing
- Configuration management

## Bluetooth Audio Setup

### Windows
1. Open Windows Settings (Win + I)
2. Go to Devices > Bluetooth & other devices
3. Click "Add Bluetooth or other device"
4. Select "Bluetooth" and follow pairing instructions
5. After pairing, go to Settings > System > Sound
6. Select your Bluetooth device as the output device

The client will automatically use the system's default audio output.

### Linux
1. Open Bluetooth settings in your desktop environment
2. Put your device in pairing mode
3. Select your device from the list and pair
4. Use PulseAudio/PipeWire audio settings to select output
5. Or use command line: `pactl set-default-sink <device-name>`

**Note:** BLE device scanning is for BLE peripherals only, not Bluetooth audio speakers. Audio routing is handled by the operating system's audio stack.

## Server Protocol

The client expects the following server endpoints:

- `GET /health`: Health check endpoint
- `WS /ws/video`: WebSocket endpoint for binary JPEG frames
- `WS /ws/events`: WebSocket endpoint for inference events

### Event Format

Inference events are expected as JSON with the following structure:

```json
{
  "type": "detection|ocr|heartbeat|error",
  "timestamp": 1234567890.123,
  "detections": [
    {
      "class_name": "person",
      "confidence": 0.95,
      "bbox": [x1, y1, x2, y2],
      "track_id": 1
    }
  ],
  "ocr_results": [
    {
      "text": "Sample text",
      "confidence": 0.85,
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

If your server uses a different protocol, the client may need adaptation.

## Testing Without Hardware

### Video File Mode
Set `VIDEO_FILE_PATH` in `.env` to use a video file instead of a camera:
```
VIDEO_FILE_PATH=/path/to/video.mp4
```

### Mock Server Mode
The client can be tested with a mock server. Implement a simple WebSocket server that accepts JPEG frames on `/ws/video` and sends JSON events on `/ws/events` matching the expected format.

## Troubleshooting

### Camera Not Found
- Check camera index with `CameraService.discover_cameras()` in Python
- Ensure camera is not in use by another application
- On Linux, verify user is in the `video` group

### Server Connection Failed
- Verify `OPTICORE_SERVER_URL` is correct and accessible
- Check firewall settings
- Ensure server is running and ngrok tunnel is active
- Test connection using the dashboard's "Test Connection" button

### TTS Not Working
- Verify `TTS_ENABLED=true` in `.env`
- On Linux, install eSpeak: `sudo apt-get install espeak`
- On Windows, pyttsx3 uses built-in SAPI5
- Check system audio output is not muted

### Bluetooth Device Not Found
- On Windows: Ensure device is paired through Windows Settings
- On Linux: Ensure BlueZ is running and device is paired
- The client lists system audio devices, not raw BLE peripherals

### High CPU Usage
- Reduce `STREAM_FPS` in configuration
- Lower `CAMERA_WIDTH` and `CAMERA_HEIGHT`
- Check if unnecessary processes are running

## Optional Groq Integration

Groq LLM integration is optional and disabled by default. To enable:

1. Set `GROQ_ENABLED=true` in `.env`
2. Set `GROQ_API_KEY` to your Groq API key
3. Uncomment `groq>=0.4.0` in `requirements.txt`
4. Reinstall dependencies: `pip install -r requirements.txt`

Groq is used only to summarize selected detection events into concise spoken messages. It does not:
- Send every frame to the LLM
- Execute model output as commands
- Make unsupported claims about danger or distance

## Security Considerations

- The dashboard binds to `127.0.0.1` by default (localhost only)
- API keys are read from server-side environment or `.env` file only
- Secrets are never exposed in browser JavaScript, HTML, or logs
- OCR text is sanitized before display and speech
- Do not commit `.env` file to version control

## Platform Limitations

### Windows
- Bluetooth pairing requires Windows Settings (not automated)
- Audio device listing may be limited without additional libraries
- TTS uses SAPI5 (system voices only)

### Linux
- Audio routing depends on PulseAudio/PipeWire configuration
- Bluetooth support depends on BlueZ and desktop environment
- TTS requires eSpeak or similar engine
- Camera access requires proper group memberships

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate  # Linux
.\\venv\\Scripts\\Activate.ps1  # Windows

# Run tests
pytest tests/
```

### Code Structure

- All modules are designed for independent operation
- Camera capture runs in a separate thread
- WebSocket operations run in an async event loop
- TTS playback runs in a dedicated worker thread
- UI updates are throttled independently

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines here]

## Support

For issues, questions, or contributions, please [specify contact method or repository].
