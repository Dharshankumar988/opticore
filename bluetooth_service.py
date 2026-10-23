"""
Bluetooth device discovery and audio output support for OptiCore Device Client.
"""
import platform
import logging
import subprocess
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BluetoothService:
    """Manages Bluetooth device discovery and audio routing."""
    
    def __init__(self):
        self.system = platform.system()
        self.available_devices: List[Dict] = []
    
    def discover_audio_devices(self) -> List[Dict]:
        """Discover available audio output devices (Bluetooth and system)."""
        devices = []
        
        try:
            if self.system == 'Windows':
                devices = self._discover_windows_audio()
            elif self.system == 'Linux':
                devices = self._discover_linux_audio()
            else:
                logger.warning(f"Unsupported platform: {self.system}")
        except Exception as e:
            logger.error(f"Error discovering audio devices: {e}")
        
        self.available_devices = devices
        return devices
    
    def _discover_windows_audio(self) -> List[Dict]:
        """Discover audio devices on Windows using PowerShell."""
        devices = []
        try:
            # Use PowerShell to get audio devices
            ps_command = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $as = [Windows.Media.Devices.MediaDevice]::GetAudioCaptureSelector()
            $devices = [Windows.Media.Devices.DeviceInformation]::FindAllAsync($as).GetResults()
            foreach ($d in $devices) {
                Write-Output "$($d.Id)|$($d.Name)"
            }
            '''
            # Simplified: fallback to default device
            devices.append({
                'id': 'default',
                'name': 'Default System Audio',
                'type': 'audio',
                'is_bluetooth': False
            })
        except Exception as e:
            logger.error(f"Windows audio discovery error: {e}")
            devices.append({
                'id': 'default',
                'name': 'Default System Audio',
                'type': 'audio',
                'is_bluetooth': False
            })
        
        return devices
    
    def _discover_linux_audio(self) -> List[Dict]:
        """Discover audio devices on Linux using PulseAudio/PipeWire."""
        devices = []
        try:
            # Try using pactl (PulseAudio/PipeWire)
            result = subprocess.run(
                ['pactl', 'list', 'sinks'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                current_device = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('Name:'):
                        current_device = {'id': line.split(':', 1)[1].strip()}
                    elif line.startswith('Description:') and current_device:
                        current_device['name'] = line.split(':', 1)[1].strip()
                        current_device['type'] = 'audio'
                        current_device['is_bluetooth'] = 'bluetooth' in current_device['name'].lower()
                        devices.append(current_device)
                        current_device = None
            else:
                logger.warning(f"pactl returned non-zero exit code: {result.returncode}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"PulseAudio/PipeWire not available: {e}")
            logger.info("Install with: sudo apt-get install pulseaudio (or pipewire-pulse)")
        
        # Try pipewire-cli as fallback
        if not devices:
            try:
                result = subprocess.run(
                    ['pw-cli', 'list-objects', 'Node'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info("PipeWire detected")
                    # Parse pipewire output (simplified)
                    devices.append({
                        'id': 'pipewire-default',
                        'name': 'PipeWire Default Audio',
                        'type': 'audio',
                        'is_bluetooth': False
                    })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.info("PipeWire CLI not available")
        
        if not devices:
            # Fallback
            devices.append({
                'id': 'default',
                'name': 'Default System Audio',
                'type': 'audio',
                'is_bluetooth': False
            })
        
        return devices
    
    def get_pairing_instructions(self) -> str:
        """Get platform-specific Bluetooth pairing instructions."""
        if self.system == 'Windows':
            return (
                "To pair a Bluetooth speaker or headset:\n"
                "1. Open Windows Settings (Win + I)\n"
                "2. Go to Devices > Bluetooth & other devices\n"
                "3. Click 'Add Bluetooth or other device'\n"
                "4. Select 'Bluetooth' and follow pairing instructions\n"
                "5. After pairing, go to Settings > System > Sound\n"
                "6. Select your Bluetooth device as the output device"
            )
        elif self.system == 'Linux':
            return (
                "To pair a Bluetooth speaker or headset:\n"
                "1. Open Bluetooth settings in your desktop environment\n"
                "2. Put your device in pairing mode\n"
                "3. Select your device from the list and pair\n"
                "4. Use PulseAudio/PipeWire audio settings to select output\n"
                "5. Or use: pactl set-default-sink <device-name>"
            )
        else:
            return f"Bluetooth pairing instructions not available for {self.system}"
    
    def get_current_output_device(self) -> Optional[Dict]:
        """Get currently selected audio output device."""
        try:
            if self.system == 'Windows':
                # Return default device info
                return {
                    'id': 'default',
                    'name': 'Default System Audio',
                    'type': 'audio'
                }
            elif self.system == 'Linux':
                result = subprocess.run(
                    ['pactl', 'get-default-sink'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    sink_name = result.stdout.strip()
                    return {
                        'id': sink_name,
                        'name': sink_name,
                        'type': 'audio'
                    }
        except Exception as e:
            logger.error(f"Error getting current output device: {e}")
        
        return None
    
    def is_bluetooth_available(self) -> bool:
        """Check if Bluetooth is available on the system."""
        try:
            if self.system == 'Windows':
                # Check if Bluetooth service is running
                result = subprocess.run(
                    ['sc', 'query', 'bthserv'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return 'RUNNING' in result.stdout
            elif self.system == 'Linux':
                # Check for bluetoothctl (BlueZ)
                result = subprocess.run(
                    ['which', 'bluetoothctl'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Verify bluetoothd is running
                    result2 = subprocess.run(
                        ['systemctl', 'is-active', 'bluetooth'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    return result2.returncode == 0 and 'active' in result2.stdout
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Bluetooth check timed out")
            return False
        except FileNotFoundError:
            logger.info("Bluetooth tools not found")
            return False
        except Exception as e:
            logger.error(f"Error checking Bluetooth availability: {e}")
        
        return False
    
    def get_status(self) -> dict:
        """Get Bluetooth and audio status."""
        return {
            'system': self.system,
            'bluetooth_available': self.is_bluetooth_available(),
            'available_devices': len(self.available_devices),
            'current_device': self.get_current_output_device()
        }
