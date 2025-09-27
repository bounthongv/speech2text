import pyaudio
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import ttk
import queue
import json
import os

class MicrophoneTester:
    def __init__(self):
        self.is_running = False
        self.audio_queue = queue.Queue()
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        
        # Settings file
        self.settings_file = 'mic_settings.json'
        self.settings = self.load_settings()
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Microphone Test & Calibration")
        self.root.geometry("600x500")
        
        # Style
        self.style = ttk.Style()
        self.style.configure("Green.Horizontal.TProgressbar", background='green')
        self.style.configure("Yellow.Horizontal.TProgressbar", background='yellow')
        self.style.configure("Red.Horizontal.TProgressbar", background='red')
        
        # Create widgets
        self.create_widgets()
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        
    def load_settings(self):
        """Load saved microphone settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'gain': 1.0,
            'noise_threshold': 0.02,
            'selected_device': 0
        }
    
    def save_settings(self):
        """Save current microphone settings"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
        self.status_label.config(text="Settings saved successfully!")
        
    def create_widgets(self):
        # Title
        title = ttk.Label(self.root, text="Microphone Test & Calibration", font=("Arial", 16))
        title.pack(pady=10)
        
        # Device selection
        device_frame = ttk.LabelFrame(self.root, text="Microphone Selection")
        device_frame.pack(padx=20, pady=5, fill="x")
        
        devices = self.get_input_devices()
        self.device_var = tk.StringVar(value=devices[0] if devices else "No microphones found")
        device_menu = ttk.OptionMenu(device_frame, self.device_var, self.device_var.get(), *devices)
        device_menu.pack(padx=5, pady=5, fill="x")
        
        # Volume meter
        self.volume_frame = ttk.LabelFrame(self.root, text="Volume Level")
        self.volume_frame.pack(padx=20, pady=5, fill="x")
        
        self.volume_bar = ttk.Progressbar(
            self.volume_frame, 
            length=500, 
            mode='determinate',
            style="Green.Horizontal.TProgressbar"
        )
        self.volume_bar.pack(padx=5, pady=5)
        
        # Gain control
        control_frame = ttk.LabelFrame(self.root, text="Audio Controls")
        control_frame.pack(padx=20, pady=5, fill="x")
        
        ttk.Label(control_frame, text="Gain:").pack(padx=5, pady=2)
        self.gain_scale = ttk.Scale(
            control_frame, 
            from_=0.1, 
            to=5.0, 
            orient="horizontal",
            value=self.settings['gain']
        )
        self.gain_scale.pack(padx=5, pady=2, fill="x")
        
        ttk.Label(control_frame, text="Noise Threshold:").pack(padx=5, pady=2)
        self.threshold_scale = ttk.Scale(
            control_frame, 
            from_=0.0, 
            to=0.1, 
            orient="horizontal",
            value=self.settings['noise_threshold']
        )
        self.threshold_scale.pack(padx=5, pady=2, fill="x")
        
        # Status and buttons
        status_frame = ttk.Frame(self.root)
        status_frame.pack(padx=20, pady=5, fill="x")
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Test", 
            command=self.toggle_test
        )
        self.start_button.pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="Save Settings", 
            command=self.save_settings
        ).pack(side="left", padx=5)
        
        # Results
        self.result_text = tk.Text(self.root, height=4, width=50)
        self.result_text.pack(padx=20, pady=10)
        
    def get_input_devices(self):
        """Get list of available input devices"""
        devices = []
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append(f"{device_info['name']} (Index: {i})")
        return devices
    
    def toggle_test(self):
        """Start/Stop microphone test"""
        if not self.is_running:
            self.start_test()
        else:
            self.stop_test()
    
    def start_test(self):
        """Start microphone testing"""
        self.is_running = True
        self.start_button.config(text="Stop Test")
        
        # Get selected device index
        device_str = self.device_var.get()
        device_index = int(device_str.split("Index: ")[-1].rstrip(")"))
        
        # Start audio stream
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )
        
        self.stream.start_stream()
        self.update_volume_display()
        
    def stop_test(self):
        """Stop microphone testing"""
        self.is_running = False
        self.start_button.config(text="Start Test")
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Process audio data"""
        if self.is_running:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Apply gain
            audio_data = audio_data * self.gain_scale.get()
            
            # Calculate volume level
            volume = np.abs(audio_data).mean()
            
            # Apply noise threshold
            if volume < self.threshold_scale.get():
                volume = 0
            
            self.audio_queue.put(volume)
        
        return (in_data, pyaudio.paContinue)
    
    def update_volume_display(self):
        """Update the volume meter"""
        if self.is_running:
            try:
                # Get volume from queue
                volume = self.audio_queue.get_nowait()
                
                # Update progress bar (scale to 0-100)
                volume_percent = min(100, volume * 100)
                self.volume_bar['value'] = volume_percent
                
                # Update bar color based on level
                if volume_percent < 30:
                    self.volume_bar['style'] = "Red.Horizontal.TProgressbar"
                    status = "Volume too low"
                elif volume_percent > 80:
                    self.volume_bar['style'] = "Red.Horizontal.TProgressbar"
                    status = "Volume too high"
                else:
                    self.volume_bar['style'] = "Green.Horizontal.TProgressbar"
                    status = "Volume optimal"
                
                # Update status
                self.status_label.config(text=status)
                
                # Update settings
                self.settings['gain'] = self.gain_scale.get()
                self.settings['noise_threshold'] = self.threshold_scale.get()
                
                # Show real-time measurements
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, 
                    f"Current Volume: {volume_percent:.1f}%\n"
                    f"Gain: {self.settings['gain']:.1f}\n"
                    f"Noise Threshold: {self.settings['noise_threshold']:.3f}\n"
                    f"Status: {status}"
                )
            
            except queue.Empty:
                pass
            
            self.root.after(50, self.update_volume_display)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.stop_test()
        self.p.terminate()

def main():
    app = MicrophoneTester()
    app.run()

if __name__ == "__main__":
    main()
