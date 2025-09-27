import pyaudio
import numpy as np
import json
import os
from scipy import signal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MicrophoneCalibrator:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5
        self.settings_file = 'mic_settings.json'
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Load saved microphone settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        
        return {
            'gain': 1.0,
            'noise_threshold': 0.02,
            'selected_device': 0,
            'noise_profile': None,
            'last_calibration': None
        }
    
    def save_settings(self):
        """Save microphone settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def list_devices(self):
        """List available audio input devices"""
        p = pyaudio.PyAudio()
        devices = []
        
        try:
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Input device
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
        finally:
            p.terminate()
        
        return devices
    
    def measure_noise_profile(self, duration=5):
        """Measure ambient noise profile"""
        logger.info("Measuring ambient noise profile...")
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.settings['selected_device'],
                frames_per_buffer=self.CHUNK
            )
            
            frames = []
            for _ in range(0, int(self.RATE / self.CHUNK * duration)):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.float32))
            
            # Convert to numpy array
            audio_data = np.concatenate(frames)
            
            # Calculate noise profile
            noise_profile = {
                'mean': float(np.mean(audio_data)),
                'std': float(np.std(audio_data)),
                'rms': float(np.sqrt(np.mean(audio_data**2))),
                'peak': float(np.max(np.abs(audio_data))),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update settings
            self.settings['noise_profile'] = noise_profile
            self.save_settings()
            
            return noise_profile
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def calibrate_microphone(self, duration=5):
        """Calibrate microphone gain and noise threshold"""
        logger.info("Starting microphone calibration...")
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.settings['selected_device'],
                frames_per_buffer=self.CHUNK
            )
            
            print("Please speak at a normal volume...")
            frames = []
            for _ in range(0, int(self.RATE / self.CHUNK * duration)):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.float32))
            
            # Convert to numpy array
            audio_data = np.concatenate(frames)
            
            # Calculate optimal gain
            peak_amplitude = float(np.max(np.abs(audio_data)))
            if peak_amplitude > 0:
                target_peak = 0.8  # Target 80% of maximum
                optimal_gain = float(target_peak / peak_amplitude)
            else:
                optimal_gain = 1.0
            
            # Calculate noise threshold
            noise_threshold = float(np.std(audio_data) * 2)  # 2 standard deviations
            
            # Update settings
            self.settings.update({
                'gain': optimal_gain,
                'noise_threshold': noise_threshold,
                'last_calibration': datetime.now().isoformat()
            })
            self.save_settings()
            
            return {
                'gain': optimal_gain,
                'noise_threshold': noise_threshold,
                'peak_amplitude': peak_amplitude
            }
            
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def apply_noise_reduction(self, audio_data):
        """Apply noise reduction based on noise profile"""
        if not self.settings.get('noise_profile'):
            return audio_data
        
        noise_profile = self.settings['noise_profile']
        
        # Apply noise gate
        noise_gate = noise_profile['rms'] * 2
        audio_data[np.abs(audio_data) < noise_gate] = 0
        
        # Apply high-pass filter to remove low frequency noise
        nyquist = self.RATE / 2
        cutoff = 80 / nyquist
        if cutoff < 1.0:
            b, a = signal.butter(4, cutoff, btype='high')
            audio_data = signal.filtfilt(b, a, audio_data)
        
        return audio_data
    
    def process_audio(self, audio_data):
        """Process audio with current settings"""
        # Apply gain
        audio_data = audio_data * self.settings['gain']
        
        # Apply noise reduction
        audio_data = self.apply_noise_reduction(audio_data)
        
        # Apply noise gate
        mask = np.abs(audio_data) < self.settings['noise_threshold']
        audio_data[mask] = 0
        
        return audio_data

def main():
    """Test calibration functionality"""
    calibrator = MicrophoneCalibrator()
    
    print("\nAvailable input devices:")
    devices = calibrator.list_devices()
    for device in devices:
        print(f"[{device['index']}] {device['name']}")
    
    device_index = input("\nSelect input device (number): ")
    try:
        device_index = int(device_index)
        if device_index in [d['index'] for d in devices]:
            calibrator.settings['selected_device'] = device_index
            calibrator.save_settings()
        else:
            print("Invalid device index")
            return
    except ValueError:
        print("Invalid input")
        return
    
    print("\nMeasuring noise profile (keep quiet)...")
    noise_profile = calibrator.measure_noise_profile()
    print("Noise profile:", json.dumps(noise_profile, indent=2))
    
    input("\nPress Enter to start microphone calibration...")
    calibration = calibrator.calibrate_microphone()
    print("\nCalibration results:", json.dumps(calibration, indent=2))
    
    print("\nSettings saved to:", calibrator.settings_file)

if __name__ == '__main__':
    main() 