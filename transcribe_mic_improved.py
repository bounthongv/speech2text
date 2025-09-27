import pyaudio
import wave
import tempfile
import os
import numpy as np
from google.cloud import speech_v1p1beta1 as speech
from scipy import signal
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MicrophoneTranscriber:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.client = speech.SpeechClient()
        
    def record_audio(self, duration=10):
        """Record audio from microphone"""
        p = pyaudio.PyAudio()
        
        print(f"Recording for {duration} seconds...")
        print("Speak clearly into your microphone...")
        
        stream = p.open(format=self.FORMAT,
                       channels=self.CHANNELS,
                       rate=self.RATE,
                       input=True,
                       frames_per_buffer=self.CHUNK)
        
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * duration)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Recording finished!")
        return b''.join(frames)
    
    def process_audio(self, audio_data):
        """Apply audio preprocessing"""
        # Convert to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # 1. Normalize volume
        max_val = np.max(np.abs(audio_np))
        if max_val > 0:
            audio_np = audio_np * (32767 / max_val * 0.8)
        
        # 2. Apply noise reduction (high-pass filter)
        nyquist = self.RATE / 2
        cutoff = 80 / nyquist
        if cutoff < 1.0:
            b, a = signal.butter(4, cutoff, btype='high')
            audio_np = signal.filtfilt(b, a, audio_np)
        
        # 3. Enhance voice frequencies
        voice_low = 300 / nyquist
        voice_high = 3400 / nyquist
        if voice_low < 1.0 and voice_high < 1.0:
            b, a = signal.butter(4, [voice_low, voice_high], btype='band')
            voice = signal.filtfilt(b, a, audio_np)
            audio_np = audio_np + (voice * 0.3)
        
        return audio_np.astype(np.int16).tobytes()
    
    def save_audio(self, audio_data, filename):
        """Save audio data to WAV file"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.RATE)
            wf.writeframes(audio_data)
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio using Google Speech API"""
        try:
            # Configure recognition (using the working settings)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.RATE,
                language_code="lo-LA",
                enable_automatic_punctuation=True,
                max_alternatives=3,
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            print("Transcribing audio...")
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                print("No transcription results. Try speaking louder or closer to the microphone.")
                return None
            
            results = []
            for result in response.results:
                for i, alternative in enumerate(result.alternatives):
                    results.append({
                        'text': alternative.transcript,
                        'confidence': alternative.confidence,
                        'rank': i + 1
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def save_results(self, results, audio_filename):
        """Save transcription results to file"""
        output_file = f"mic_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Microphone Transcription Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Audio file: {audio_filename}\n\n")
            
            if results:
                for result in results:
                    f.write(f"Alternative {result['rank']}:\n")
                    f.write(f"Text: {result['text']}\n")
                    f.write(f"Confidence: {result['confidence']:.2%}\n")
                    f.write("-" * 30 + "\n")
                
                # Calculate average confidence
                avg_conf = sum(r['confidence'] for r in results) / len(results)
                f.write(f"\nAverage Confidence: {avg_conf:.2%}\n")
            else:
                f.write("No transcription results.\n")
        
        print(f"Results saved to: {output_file}")
        return output_file

def main():
    print("\nLao Speech Recognition - Microphone Test")
    print("=" * 50)
    
    transcriber = MicrophoneTranscriber()
    
    while True:
        print("\nOptions:")
        print("1. Record and transcribe (10 seconds)")
        print("2. Record and transcribe (custom duration)")
        print("3. Quit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '3':
            break
        elif choice == '1':
            duration = 10
        elif choice == '2':
            try:
                duration = int(input("Enter recording duration in seconds: "))
                duration = max(1, min(60, duration))  # Limit between 1-60 seconds
            except:
                print("Invalid duration. Using 10 seconds.")
                duration = 10
        else:
            print("Invalid choice.")
            continue
        
        try:
            # Record audio
            raw_audio = transcriber.record_audio(duration)
            
            # Process audio
            processed_audio = transcriber.process_audio(raw_audio)
            
            # Save audio file
            audio_filename = f"mic_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            transcriber.save_audio(processed_audio, audio_filename)
            print(f"Audio saved as: {audio_filename}")
            
            # Transcribe
            results = transcriber.transcribe_audio(processed_audio)
            
            if results:
                print("\nTranscription Results:")
                print("=" * 40)
                
                for result in results:
                    print(f"\nAlternative {result['rank']}:")
                    print(f"Text: {result['text']}")
                    print(f"Confidence: {result['confidence']:.2%}")
                    
                    if result['confidence'] >= 0.8:
                        print("✓ High confidence")
                    elif result['confidence'] >= 0.6:
                        print("⚠ Medium confidence")
                    else:
                        print("❌ Low confidence")
                
                # Save results
                transcriber.save_results(results, audio_filename)
                
                # Provide feedback
                best_confidence = max(r['confidence'] for r in results)
                if best_confidence < 0.6:
                    print("\n💡 Tips to improve microphone transcription:")
                    print("1. Speak closer to the microphone")
                    print("2. Speak more clearly and slowly")
                    print("3. Reduce background noise")
                    print("4. Use a better quality microphone if available")
            else:
                print("\n❌ No transcription results.")
                print("Try speaking louder or adjusting microphone settings.")
        
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
