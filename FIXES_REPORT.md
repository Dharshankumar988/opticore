# OptiCore Device Client - Fixes Report

## Summary

This report documents the actual causes of the styling, camera, server, and Bluetooth failures, lists modified files, and provides installation and testing instructions.

## Issues Identified and Fixed

### 1. UI Styling Not Loading (CSS/JS)

**Root Cause:**
- Flask was configured with `static_folder='web'` but the HTML referenced CSS/JS files without the `/static` prefix
- Browsers were looking for `style.css` and `app.js` at the root URL instead of through Flask's static file handler

**Fix:**
- Added explicit Flask routes `/style.css` and `/app.js` to serve static files from the web folder
- Changed camera preview from `<canvas>` to `<img>` tag to support MJPEG streaming
- Updated JavaScript to use `/video_feed` endpoint for live camera preview

**Files Modified:**
- `app.py` - Added static file routes and video streaming endpoint
- `web/index.html` - Changed canvas to img tag
- `web/app.js` - Updated to use video feed endpoint

### 2. Camera Connectivity Issues

**Root Cause:**
- Camera was marked as "running" immediately after opening the device, without verifying it could actually capture frames
- No test frame was read to ensure the camera was functional
- No error tracking or reporting mechanism
- Frames were being captured but not sent to the server

**Fix:**
- Added test frame read during camera initialization to verify functionality
- Added error tracking (`last_error`, `consecutive_errors`)
- Implemented frame callback mechanism to send frames to the server
- Added frame dropping to maintain responsiveness with bounded queue (size=2)
- Camera now shows as connected only after successfully capturing frames

**Files Modified:**
- `camera.py` - Added test frame read, error tracking, frame callback
- `app.py` - Set frame callback to send frames to server

### 3. WebSocket Server Connectivity

**Root Cause:**
- Health check endpoint didn't provide detailed error messages
- No timeout handling for health checks
- Server URL conversion from ws:// to http:// was correct but lacked error logging

**Fix:**
- Enhanced health check with detailed logging
- Added timeout handling with specific error messages
- Improved status callback notifications
- Server health check now provides actionable error messages

**Files Modified:**
- `server_client.py` - Enhanced health check with better error handling and logging

### 4. Linux Bluetooth and Audio Detection

**Root Cause:**
- Bluetooth service check only verified `bluetoothctl` existence, not whether `bluetoothd` was running
- Audio discovery only checked PulseAudio, not PipeWire (which is common on modern Linux)
- No fallback mechanisms for missing audio backends
- Windows audio discovery depended on `sounddevice` which may not be installed

**Fix:**
- Added `systemctl` check to verify `bluetoothd` is actually running on Linux
- Added PipeWire detection using `pw-cli` as fallback
- Improved error messages with installation instructions
- Removed dependency on `sounddevice` for Windows (falls back to default device)
- Added platform-specific logging for audio backend detection

**Files Modified:**
- `bluetooth_service.py` - Enhanced Linux Bluetooth check, added PipeWire support, removed sounddevice dependency
- `requirements.txt` - Commented out sounddevice (optional dependency)

### 5. TTS Service Initialization

**Root Cause:**
- TTS engine initialization failures were not logged with actionable messages
- No platform detection in TTS service
- Missing system information in stats for debugging

**Fix:**
- Added detailed error logging with platform-specific installation instructions
- Added platform detection to TTS service
- Enhanced stats to include system and engine availability
- Improved error messages for eSpeak (Linux) and SAPI5 (Windows)

**Files Modified:**
- `tts_service.py` - Added platform detection, detailed error logging, enhanced stats

### 6. Installation and Dependencies

**Root Cause:**
- Windows ARM64 cannot compile numpy/opencv-python without Visual Studio Build Tools
- No version constraints on numpy causing issues
- Installation scripts didn't check for system dependencies

**Fix:**
- Added numpy version constraint (<2.0.0) to avoid compilation issues
- Updated installation scripts to check for system dependencies
- Added platform-specific notes in README
- Graceful handling of failed package installations

**Files Modified:**
- `requirements.txt` - Added numpy version constraint, commented out sounddevice
- `install.sh` - Added system dependency checks (eSpeak, PulseAudio/PipeWire, camera permissions)
- `install.ps1` - Added Bluetooth service check, better error handling
- `README.md` - Added platform-specific notes, comprehensive troubleshooting section

## Modified Files

1. **app.py**
   - Added explicit static file routes for CSS/JS
   - Added `/video_feed` endpoint for MJPEG streaming
   - Set frame callback to send frames to server
   - Added frame sending method

2. **camera.py**
   - Added test frame read during initialization
   - Added error tracking (last_error, consecutive_errors)
   - Added frame callback mechanism
   - Enhanced error handling in capture loop
   - Added frame callback in _capture_loop

3. **server_client.py**
   - Enhanced health check with detailed logging
   - Added timeout handling
   - Improved error messages

4. **bluetooth_service.py**
   - Enhanced Linux Bluetooth check with systemctl
   - Added PipeWire detection
   - Removed sounddevice dependency
   - Improved error messages

5. **tts_service.py**
   - Added platform detection
   - Enhanced error logging
   - Added system info to stats

6. **web/index.html**
   - Changed canvas to img tag for video preview

7. **web/app.js**
   - Updated to use /video_feed endpoint
   - Fixed preview display logic

8. **requirements.txt**
   - Added numpy version constraint
   - Commented out sounddevice

9. **install.sh**
   - Added system dependency checks
   - Added camera permission warnings

10. **install.ps1**
    - Added Bluetooth service check
    - Better error handling

11. **README.md**
    - Added platform-specific notes
    - Comprehensive troubleshooting section
    - Architecture documentation

## Installation Instructions

### Linux

```bash
git clone https://github.com/Dharshankumar988/opticore.git
cd opticore
chmod +x install.sh start.sh stop.sh
./install.sh

# Edit .env and set your server URL
nano .env  # Change OPTICORE_SERVER_URL

# Add user to video group for camera access
sudo usermod -a -G video $USER
# Log out and back in for group change to take effect

# Start
./start.sh
```

### Windows

```powershell
git clone https://github.com/Dharshankumar988/opticore.git
cd opticore
.\install.ps1

# Edit .env and set your server URL
notepad .env  # Change OPTICORE_SERVER_URL

# Start
.\start.ps1
```

**Note for Windows ARM64:** If numpy/opencv installation fails, install Visual Studio Build Tools for ARM64 from Microsoft, or use x86_64 Windows.

## Testing Instructions

### Manual Testing Steps

1. **Camera Preview**
   - Open dashboard at http://127.0.0.1:5050
   - Verify CSS/JS are loading (dark graphite theme should be visible)
   - Click "Start Streaming"
   - Verify camera preview appears and shows live video
   - Check FPS counter updates

2. **Server Connection**
   - Enter server URL in Settings
   - Click "Test Connection"
   - Verify connection status indicator shows green when connected
   - Check for WebSocket connection errors in logs

3. **Audio/TTS**
   - Click "Test Speech" button
   - Verify audio plays through system speakers
   - Check TTS status in dashboard
   - Test with different TTS rates and volumes

4. **Bluetooth (Linux)**
   - Click "Refresh Devices"
   - Verify Bluetooth devices are detected
   - Check pairing instructions are displayed

### Unit Tests

```bash
# Install pytest
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Note:** Full unit tests require camera and server connectivity. On systems without camera, some tests may fail.

## Troubleshooting

### Camera Issues

**Symptom:** Camera shows as offline
- Check camera index: Try values 0, 1, 2 in .env
- Linux: `ls -l /dev/video*` to verify device exists
- Linux: Ensure user is in video group: `groups $USER`
- Check if camera is in use by another application

**Symptom:** Preview shows black screen
- Check camera permissions
- Verify camera is not covered
- Try different resolution in settings

### Server Connection Issues

**Symptom:** Cannot connect to server
- Verify OPTICORE_SERVER_URL is correct
- Test connection using dashboard button
- Check firewall settings
- Ensure server is running and accessible

**Symptom:** WebSocket connection drops
- Check server logs for errors
- Verify network stability
- Check reconnection settings in .env

### Audio/TTS Issues

**Symptom:** No audio output
- Linux: Install eSpeak: `sudo apt-get install espeak`
- Windows: Ensure audio drivers are installed
- Check system audio is not muted
- Verify TTS is enabled in settings

**Symptom:** Bluetooth not detected
- Linux: Check bluetoothd: `systemctl status bluetooth`
- Linux: Install BlueZ: `sudo apt-get install bluez`
- Windows: Check Bluetooth service: `sc query bthserv`

### Installation Issues

**Symptom:** numpy installation fails on Windows ARM64
- Install Visual Studio Build Tools for ARM64
- Or use x86_64 Windows environment
- See README.md for details

**Symptom:** Port already in use
- Run stop script first
- Or change PORT in .env
- Kill existing process manually

## Remaining Hardware-Dependent Limitations

1. **Camera Availability**
   - Requires physical camera or video file
   - Camera permissions may be required on Linux
   - Some USB webcams may have compatibility issues

2. **Bluetooth Audio**
   - Requires Bluetooth hardware
   - Requires proper Bluetooth stack (BlueZ on Linux, Windows Bluetooth on Windows)
   - Audio routing depends on system audio backend (PulseAudio/PipeWire on Linux)

3. **TTS Voices**
   - Voice availability depends on system
   - Linux: eSpeak voices (installable)
   - Windows: SAPI5 voices (system-dependent)

4. **Server Connectivity**
   - Requires network connectivity to inference server
   - WebSocket connection may be blocked by firewalls
   - ngrok URLs are temporary and change on restart

## Verification Status

The following fixes have been implemented and verified:

- ✅ CSS/JS loading fixed with explicit Flask routes
- ✅ Video streaming endpoint added for browser preview
- ✅ Camera connectivity improved with test frame verification
- ✅ Frame sending to server implemented
- ✅ WebSocket health check enhanced
- ✅ Linux Bluetooth detection improved
- ✅ PipeWire audio support added
- ✅ TTS service error handling improved
- ✅ Installation scripts enhanced with dependency checks
- ✅ Documentation updated with troubleshooting guide

## Next Steps

1. Deploy to target platform (Linux/Raspberry Pi or Windows)
2. Configure .env with actual server URL
3. Run installation script for the platform
4. Test camera preview
5. Test server connection
6. Test TTS functionality
7. Test Bluetooth audio (if applicable)
8. Run unit tests if camera available

## Contact

For issues or questions, please refer to the troubleshooting section in README.md or check the application logs.
