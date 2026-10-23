// OptiCore Device Client - Dashboard JavaScript

const API_BASE = '';

// State
let streaming = false;
let statusInterval = null;

// DOM Elements
const elements = {
    connectionStatus: document.getElementById('connection-status'),
    cameraStatus: document.getElementById('camera-status'),
    statFps: document.getElementById('stat-fps'),
    statFramesSent: document.getElementById('stat-frames-sent'),
    statDropped: document.getElementById('stat-dropped'),
    statLatency: document.getElementById('stat-latency'),
    recentErrors: document.getElementById('recent-errors'),
    cameraSelect: document.getElementById('camera-select'),
    resolutionSelect: document.getElementById('resolution-select'),
    fpsSelect: document.getElementById('fps-select'),
    btnStart: document.getElementById('btn-start'),
    btnStop: document.getElementById('btn-stop'),
    cameraPreview: document.getElementById('camera-preview'),
    previewStatus: document.getElementById('preview-status'),
    inferenceResults: document.getElementById('inference-results'),
    detectionBody: document.getElementById('detection-body'),
    ocrText: document.getElementById('ocr-text'),
    currentAudioDevice: document.getElementById('current-audio-device'),
    bluetoothStatus: document.getElementById('bluetooth-status'),
    btnTestSpeech: document.getElementById('btn-test-speech'),
    btnRefreshDevices: document.getElementById('btn-refresh-devices'),
    pairingInstructions: document.getElementById('pairing-instructions'),
    ttsEnabled: document.getElementById('tts-enabled'),
    ttsRate: document.getElementById('tts-rate'),
    ttsRateValue: document.getElementById('tts-rate-value'),
    ttsVolume: document.getElementById('tts-volume'),
    ttsVolumeValue: document.getElementById('tts-volume-value'),
    alertVerbosity: document.getElementById('alert-verbosity'),
    btnMute: document.getElementById('btn-mute'),
    groqEnabled: document.getElementById('groq-enabled'),
    groqStatus: document.getElementById('groq-status'),
    groqModel: document.getElementById('groq-model'),
    btnTestGroq: document.getElementById('btn-test-groq'),
    groqTestResult: document.getElementById('groq-test-result'),
    serverUrl: document.getElementById('server-url'),
    btnTestConnection: document.getElementById('btn-test-connection'),
    btnSaveConfig: document.getElementById('btn-save-config'),
    connectionTestResult: document.getElementById('connection-test-result')
};

// Initialize
async function init() {
    await loadCameras();
    await loadConfig();
    await loadAudioDevices();
    startStatusUpdates();
    setupEventListeners();
}

// Load available cameras
async function loadCameras() {
    try {
        const response = await fetch(`${API_BASE}/api/cameras`);
        const data = await response.json();
        
        elements.cameraSelect.innerHTML = '';
        data.cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera[0];
            option.textContent = camera[1];
            elements.cameraSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load cameras:', error);
    }
}

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();
        
        elements.serverUrl.value = data.server_url;
        elements.cameraSelect.value = data.camera_index;
        elements.ttsEnabled.checked = data.tts_enabled;
        elements.ttsRate.value = data.tts_rate;
        elements.ttsRateValue.textContent = data.tts_rate;
        elements.ttsVolume.value = data.tts_volume * 100;
        elements.ttsVolumeValue.textContent = Math.round(data.tts_volume * 100) + '%';
        elements.alertVerbosity.value = data.alert_verbosity;
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Load audio devices
async function loadAudioDevices() {
    try {
        const response = await fetch(`${API_BASE}/api/audio-devices`);
        const data = await response.json();
        
        const bluetoothDevice = data.devices.find(d => d.is_bluetooth);
        elements.bluetoothStatus.textContent = bluetoothDevice ? 'Yes' : 'No';
        
        // Load pairing instructions
        const pairingResponse = await fetch(`${API_BASE}/api/config`);
        // For now, use static instructions
        elements.pairingInstructions.textContent = getPairingInstructions();
    } catch (error) {
        console.error('Failed to load audio devices:', error);
        elements.bluetoothStatus.textContent = 'Unknown';
    }
}

function getPairingInstructions() {
    const platform = navigator.platform;
    if (platform.includes('Win')) {
        return `To pair a Bluetooth speaker or headset:
1. Open Windows Settings (Win + I)
2. Go to Devices > Bluetooth & other devices
3. Click 'Add Bluetooth or other device'
4. Select 'Bluetooth' and follow pairing instructions
5. After pairing, go to Settings > System > Sound
6. Select your Bluetooth device as the output device`;
    } else {
        return `To pair a Bluetooth speaker or headset:
1. Open Bluetooth settings in your desktop environment
2. Put your device in pairing mode
3. Select your device from the list and pair
4. Use audio settings to select output`;
    }
}

// Start status updates
function startStatusUpdates() {
    updateStatus();
    updateGroqStatus();
    statusInterval = setInterval(updateStatus, 1000);
    setInterval(updateGroqStatus, 5000); // Update Groq status less frequently
}

// Update status
async function updateStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const status = await response.json();
        
        // Update connection status
        if (status.server.connected) {
            elements.connectionStatus.textContent = 'Server: Connected';
            elements.connectionStatus.className = 'status-indicator connected';
        } else {
            elements.connectionStatus.textContent = 'Server: Disconnected';
            elements.connectionStatus.className = 'status-indicator disconnected';
        }
        
        // Update camera status
        if (status.camera.running) {
            elements.cameraStatus.textContent = 'Camera: Online';
            elements.cameraStatus.className = 'status-indicator connected';
        } else {
            elements.cameraStatus.textContent = 'Camera: Offline';
            elements.cameraStatus.className = 'status-indicator disconnected';
        }
        
        // Update stats
        elements.statFps.textContent = status.camera.actual_fps.toFixed(1);
        elements.statFramesSent.textContent = status.server.frames_sent;
        elements.statDropped.textContent = status.camera.dropped_frames;
        
        // Update streaming state
        streaming = status.streaming;
        elements.btnStart.disabled = streaming;
        elements.btnStop.disabled = !streaming;
        
        // Update inference results
        if (status.latest_result) {
            updateInferenceResults(status.latest_result);
        }
        
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

// Update Groq status
async function updateGroqStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/groq/status`);
        const status = await response.json();
        
        elements.groqEnabled.checked = status.enabled;
        
        if (status.enabled) {
            if (status.available) {
                elements.groqStatus.textContent = 'Available';
                elements.groqStatus.className = 'status-indicator connected';
            } else if (status.configured) {
                elements.groqStatus.textContent = 'Configured (unavailable)';
                elements.groqStatus.className = 'status-indicator disconnected';
            } else {
                elements.groqStatus.textContent = 'Not configured';
                elements.groqStatus.className = 'status-indicator disconnected';
            }
            elements.groqModel.textContent = status.model || '--';
        } else {
            elements.groqStatus.textContent = 'Disabled';
            elements.groqStatus.className = 'status-indicator disconnected';
            elements.groqModel.textContent = '--';
        }
    } catch (error) {
        console.error('Failed to update Groq status:', error);
    }
}

// Update inference results
function updateInferenceResults(result) {
    // Update detections table
    if (result.detections && result.detections.length > 0) {
        elements.detectionBody.innerHTML = '';
        result.detections.forEach(det => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${det.class_name}</td>
                <td>${(det.confidence * 100).toFixed(1)}%</td>
                <td>${det.track_id || 'N/A'}</td>
            `;
            elements.detectionBody.appendChild(row);
        });
    } else {
        elements.detectionBody.innerHTML = '<tr><td colspan="3">No detections</td></tr>';
    }
    
    // Update OCR text
    if (result.ocr_results && result.ocr_results.length > 0) {
        elements.ocrText.textContent = result.ocr_results[0].text;
    } else {
        elements.ocrText.textContent = 'No OCR text';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Start streaming
    elements.btnStart.addEventListener('click', async () => {
        const cameraIndex = parseInt(elements.cameraSelect.value);
        try {
            const response = await fetch(`${API_BASE}/api/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_index: cameraIndex })
            });
            const data = await response.json();
            if (data.status === 'started') {
                elements.previewStatus.textContent = 'Streaming...';
            } else {
                elements.previewStatus.textContent = 'Failed to start: ' + (data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Failed to start streaming:', error);
            elements.previewStatus.textContent = 'Failed to start: ' + error.message;
        }
    });
    
    // Stop streaming
    elements.btnStop.addEventListener('click', async () => {
        try {
            const response = await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
            await response.json();
            elements.previewStatus.textContent = 'Camera preview will appear here';
        } catch (error) {
            console.error('Failed to stop streaming:', error);
        }
    });
    
    // Test speech
    elements.btnTestSpeech.addEventListener('click', async () => {
        try {
            await fetch(`${API_BASE}/api/tts/test`, { method: 'POST' });
        } catch (error) {
            console.error('Failed to test speech:', error);
        }
    });
    
    // Refresh devices
    elements.btnRefreshDevices.addEventListener('click', () => {
        loadAudioDevices();
    });
    
    // Mute
    elements.btnMute.addEventListener('click', async () => {
        try {
            await fetch(`${API_BASE}/api/tts/mute`, { method: 'POST' });
        } catch (error) {
            console.error('Failed to mute:', error);
        }
    });
    
    // TTS rate
    elements.ttsRate.addEventListener('input', () => {
        elements.ttsRateValue.textContent = elements.ttsRate.value;
    });
    
    // TTS volume
    elements.ttsVolume.addEventListener('input', () => {
        elements.ttsVolumeValue.textContent = elements.ttsVolume.value + '%';
    });
    
    // Test connection
    elements.btnTestConnection.addEventListener('click', async () => {
        elements.connectionTestResult.style.display = 'none';
        try {
            const response = await fetch(`${API_BASE}/api/health-check`, { method: 'POST' });
            const data = await response.json();
            if (data.healthy) {
                elements.connectionTestResult.textContent = 'Connection successful!';
                elements.connectionTestResult.className = 'success';
            } else {
                elements.connectionTestResult.textContent = 'Connection failed: ' + (data.error || 'Unknown error');
                elements.connectionTestResult.className = 'error';
            }
        } catch (error) {
            elements.connectionTestResult.textContent = 'Connection failed: ' + error.message;
            elements.connectionTestResult.className = 'error';
        }
    });
    
    // Save configuration
    elements.btnSaveConfig.addEventListener('click', async () => {
        const config = {
            server_url: elements.serverUrl.value,
            camera_index: parseInt(elements.cameraSelect.value),
            tts_enabled: elements.ttsEnabled.checked,
            tts_rate: parseInt(elements.ttsRate.value),
            tts_volume: parseInt(elements.ttsVolume.value) / 100,
            alert_verbosity: elements.alertVerbosity.value
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            await response.json();
            alert('Configuration saved!');
        } catch (error) {
            console.error('Failed to save config:', error);
            alert('Failed to save configuration');
        }
    });
    
    // Test Groq connection
    elements.btnTestGroq.addEventListener('click', async () => {
        elements.groqTestResult.style.display = 'none';
        elements.groqTestResult.textContent = 'Testing...';
        elements.groqTestResult.style.display = 'block';
        
        try {
            const response = await fetch(`${API_BASE}/api/groq/test`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                elements.groqTestResult.textContent = `Connection successful! Latency: ${data.latency_ms}ms`;
                elements.groqTestResult.className = 'success';
            } else {
                elements.groqTestResult.textContent = 'Connection failed: ' + (data.error || 'Unknown error');
                elements.groqTestResult.className = 'error';
            }
        } catch (error) {
            elements.groqTestResult.textContent = 'Connection failed: ' + error.message;
            elements.groqTestResult.className = 'error';
        }
    });
}

// Start on load
document.addEventListener('DOMContentLoaded', init);
