import os
import numpy as np
import wave
import json
import pyaudio
import tempfile
from google.cloud import speech_v1p1beta1 as speech
from scipy import signal
import logging
from lao_phrases import LaoMeetingPhrases
import time
from datetime import datetime
from docx import Document
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        # Load microphone settings if available
        self.settings_file = 'mic_settings.json'
        self.settings = self.load_mic_settings()
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        
    def load_mic_settings(self):
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

    def process_audio(self, audio_data, apply_settings=True):
        """Apply audio processing with optional settings"""
        # Convert to float for processing
        float_data = audio_data.astype(np.float32)
        
        if apply_settings:
            # Apply gain
            float_data = float_data * self.settings['gain']
            
            # Apply noise threshold
            mask = np.abs(float_data) < self.settings['noise_threshold']
            float_data[mask] = 0
        
        # Normalize volume
        float_data = self.normalize_volume(float_data)
        
        # Apply noise reduction
        float_data = self.reduce_noise(float_data)
        
        # Enhance voice frequencies
        float_data = self.enhance_voice(float_data)
        
        return float_data.astype(np.int16)

    def normalize_volume(self, audio_data):
        """Normalize audio volume to optimal level"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            # Normalize to 80% of maximum to avoid clipping
            target_level = 0.8
            return audio_data * (target_level / max_val)
        return audio_data

    def reduce_noise(self, audio_data):
        """Apply noise reduction"""
        # High-pass filter to remove low frequency noise
        nyquist = self.RATE / 2
        cutoff = 80 / nyquist
        b, a = signal.butter(4, cutoff, btype='high')
        return signal.filtfilt(b, a, audio_data)

    def enhance_voice(self, audio_data):
        """Enhance frequencies in human voice range"""
        nyquist = self.RATE / 2
        low_cut = 300 / nyquist
        high_cut = 3400 / nyquist
        b, a = signal.butter(4, [low_cut, high_cut], btype='band')
        voice = signal.filtfilt(b, a, audio_data)
        return audio_data + (voice * 0.3)

class TranscriptionManager:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.phrases_manager = LaoMeetingPhrases()
        self.client = speech.SpeechClient()
        
    def prepare_audio(self, input_file):
        """Prepare audio file for transcription"""
        logger.info("Preparing audio for transcription...")
        
        # Create temporary file for processed audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            output_file = temp_file.name
        
        # Read and process audio
        with wave.open(input_file, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
            # Process audio
            processed_data = self.audio_processor.process_audio(audio_data)
            
            # Save processed audio
            with wave.open(output_file, 'wb') as out_file:
                out_file.setnchannels(1)
                out_file.setsampwidth(2)
                out_file.setframerate(16000)
                out_file.writeframes(processed_data.tobytes())
        
        return output_file

    def create_recognition_config(self):
        """Create speech recognition configuration"""
        base_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="lo-LA",
            enable_automatic_punctuation=True,
            use_enhanced=True,
            model="latest_long",
            metadata=speech.RecognitionMetadata(
                interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION,
                microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
                recording_device_type=speech.RecognitionMetadata.RecordingDeviceType.PC,
            )
        )
        
        # Add phrase hints
        return self.phrases_manager.create_speech_config(base_config)

    def transcribe_audio(self, audio_file, min_confidence=0.6):
        """Transcribe audio with enhanced settings"""
        logger.info("Starting transcription...")
        
        # Prepare audio
        processed_file = self.prepare_audio(audio_file)
        
        try:
            # Read the processed audio
            with open(processed_file, "rb") as audio_file:
                content = audio_file.read()
            
            # Configure recognition
            audio = speech.RecognitionAudio(content=content)
            config = self.create_recognition_config()
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Process results
            results = []
            for result in response.results:
                for alternative in result.alternatives:
                    confidence = alternative.confidence
                    if confidence >= min_confidence:
                        results.append({
                            'text': alternative.transcript,
                            'confidence': confidence,
                            'words': [{'word': word.word, 'start_time': word.start_time.total_seconds(), 
                                     'end_time': word.end_time.total_seconds()}
                                    for word in alternative.words] if hasattr(alternative, 'words') else []
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return []
            
        finally:
            # Cleanup
            try:
                os.unlink(processed_file)
            except:
                pass

    def save_transcription(self, results, output_file):
        """Save transcription results to file"""
        if not results:
            logger.warning("No transcription results to save")
            return
        
        try:
            if output_file.endswith('.docx'):
                self.save_as_docx(results, output_file)
            else:
                self.save_as_text(results, output_file)
            
            logger.info(f"Transcription saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")

    def save_as_docx(self, results, output_file):
        """Save transcription as Word document"""
        doc = Document()
        
        # Add title
        doc.add_heading('Meeting Transcription', 0)
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add content
        doc.add_heading('Transcription Results', level=1)
        
        for i, result in enumerate(results, 1):
            # Add section for each transcription
            p = doc.add_paragraph()
            p.add_run(f"{i}. ").bold = True
            p.add_run(result['text'])
            
            # Add confidence score
            conf_p = doc.add_paragraph()
            conf_p.add_run(f"Confidence: {result['confidence']:.2%}")
            
            # Add timestamp if available
            if result.get('words'):
                time_p = doc.add_paragraph()
                start = result['words'][0]['start_time']
                end = result['words'][-1]['end_time']
                time_p.add_run(f"Time: {start:.1f}s - {end:.1f}s")
            
            doc.add_paragraph()  # Add spacing
        
        # Add summary
        doc.add_heading('Summary', level=1)
        doc.add_paragraph(f"Total segments: {len(results)}")
        avg_conf = sum(r['confidence'] for r in results) / len(results)
        doc.add_paragraph(f"Average confidence: {avg_conf:.2%}")
        
        doc.save(output_file)

    def save_as_text(self, results, output_file):
        """Save transcription as text file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Meeting Transcription\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"{i}. {result['text']}\n")
                f.write(f"   Confidence: {result['confidence']:.2%}\n")
                if result.get('words'):
                    start = result['words'][0]['start_time']
                    end = result['words'][-1]['end_time']
                    f.write(f"   Time: {start:.1f}s - {end:.1f}s\n")
                f.write("\n")
            
            f.write("\nSummary\n")
            f.write("=" * 20 + "\n")
            f.write(f"Total segments: {len(results)}\n")
            avg_conf = sum(r['confidence'] for r in results) / len(results)
            f.write(f"Average confidence: {avg_conf:.2%}\n")

def main():
    """Main function for transcription"""
    print("\nLao Speech Recognition - Optimized for Meetings")
    print("=" * 50)
    
    # Initialize transcription manager
    manager = TranscriptionManager()
    
    # Get input file
    while True:
        file_path = input("\nEnter path to audio file (or 'q' to quit): ").strip()
        if file_path.lower() == 'q':
            break
            
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            continue
        
        # Get output format
        format_choice = input("Choose output format:\n1. Word document (.docx)\n2. Text file (.txt)\nChoice (1/2): ")
        
        output_file = os.path.splitext(file_path)[0] + ('.docx' if format_choice == '1' else '.txt')
        
        # Process and transcribe
        print("\nProcessing audio...")
        results = manager.transcribe_audio(file_path)
        
        if results:
            # Save results
            manager.save_transcription(results, output_file)
            
            # Show summary
            print("\nTranscription Summary:")
            print(f"Total segments: {len(results)}")
            avg_conf = sum(r['confidence'] for r in results) / len(results)
            print(f"Average confidence: {avg_conf:.2%}")
            print(f"\nResults saved to: {output_file}")
        else:
            print("\nNo transcription results. Please try:")
            print("1. Running mic_test.py to optimize microphone settings")
            print("2. Using lao_phrases.py to add common meeting terms")
            print("3. Ensuring clear audio with minimal background noise")

if __name__ == "__main__":
    main()
