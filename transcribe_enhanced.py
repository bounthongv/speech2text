import os
import numpy as np
import wave
import pyaudio
from google.cloud import speech_v1p1beta1 as speech
from docx import Document
import tempfile
import time
from scipy import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioEnhancer:
    """Audio preprocessing to improve recognition accuracy"""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
    
    def enhance_audio_file(self, input_file, output_file):
        """Enhance an existing audio file"""
        # Read the audio file
        with wave.open(input_file, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
        # Apply enhancements
        enhanced_audio = self.process_audio(audio_data)
        
        # Save enhanced audio
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(enhanced_audio.tobytes())
        
        return output_file
    
    def process_audio(self, audio_data):
        """Apply audio processing techniques"""
        # Convert to float for processing
        float_data = audio_data.astype(np.float32)
        
        # 1. Normalize volume
        normalized = self.normalize_volume(float_data)
        
        # 2. Apply noise reduction
        denoised = self.reduce_noise(normalized)
        
        # 3. Apply voice enhancement
        enhanced = self.enhance_voice(denoised)
        
        # Convert back to int16
        return enhanced.astype(np.int16)
    
    def normalize_volume(self, audio_data):
        """Normalize audio volume to optimal level"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            # Normalize to 80% of maximum to avoid clipping
            target_level = 32767 * 0.8
            normalized = audio_data * (target_level / max_val)
            return normalized
        return audio_data
    
    def reduce_noise(self, audio_data):
        """Simple noise reduction using spectral subtraction"""
        # Apply high-pass filter to remove low-frequency noise
        nyquist = self.sample_rate / 2
        low_cutoff = 80 / nyquist  # Remove frequencies below 80Hz
        b, a = signal.butter(4, low_cutoff, btype='high')
        filtered = signal.filtfilt(b, a, audio_data)
        return filtered
    
    def enhance_voice(self, audio_data):
        """Enhance voice frequencies (300-3400 Hz)"""
        nyquist = self.sample_rate / 2
        low = 300 / nyquist
        high = 3400 / nyquist
        
        # Apply band-pass filter to enhance voice frequencies
        b, a = signal.butter(4, [low, high], btype='band')
        enhanced = signal.filtfilt(b, a, audio_data)
        
        # Boost the enhanced signal slightly
        return audio_data + (enhanced * 0.3)

def record_enhanced_audio(duration=10, output_file="temp_recording.wav"):
    """Record audio with real-time enhancement"""
    enhancer = AudioEnhancer()
    
    # Audio recording parameters
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 16000
    
    p = pyaudio.PyAudio()
    
    print(f"Recording for {duration} seconds...")
    
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    frames = []
    
    for i in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert to numpy array for processing
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    
    # Enhance the audio
    enhanced_audio = enhancer.process_audio(audio_data)
    
    # Save enhanced audio
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(enhanced_audio.tobytes())
    
    print(f"Enhanced audio saved to {output_file}")
    return output_file

def transcribe_with_confidence(audio_file, min_confidence=0.6):
    """Transcribe audio with confidence filtering and multiple alternatives"""
    client = speech.SpeechClient()
    
    with open(audio_file, "rb") as f:
        content = f.read()
    
    audio = speech.RecognitionAudio(content=content)
    
    # Enhanced configuration for better Lao recognition
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="lo-LA",
        enable_automatic_punctuation=True,
        use_enhanced=True,  # Use enhanced model
        model="latest_long",  # Better for longer audio
        max_alternatives=3,  # Get multiple alternatives
        metadata=speech.RecognitionMetadata(
            interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION,
            microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
            recording_device_type=speech.RecognitionMetadata.RecordingDeviceType.PC,
        )
    )
    
    try:
        response = client.recognize(config=config, audio=audio)
        
        results = []
        for result in response.results:
            for i, alternative in enumerate(result.alternatives):
                confidence = alternative.confidence
                transcript = alternative.transcript
                
                if confidence >= min_confidence:
                    results.append({
                        'text': transcript,
                        'confidence': confidence,
                        'alternative': i
                    })
                    logger.info(f"Alternative {i+1} (conf: {confidence:.2f}): {transcript}")
                else:
                    logger.debug(f"Low confidence alternative ignored (conf: {confidence:.2f}): {transcript}")
        
        return results
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return []

def create_meeting_document(transcription_results, output_file="meeting_notes.docx"):
    """Create a formatted Word document with transcription results"""
    doc = Document()
    
    # Add title
    title = doc.add_heading('Meeting Transcription', 0)
    
    # Add timestamp
    doc.add_paragraph(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph()
    
    # Add transcription results
    doc.add_heading('Transcribed Content:', level=1)
    
    if transcription_results:
        # Group by confidence levels
        high_conf = [r for r in transcription_results if r['confidence'] >= 0.8]
        med_conf = [r for r in transcription_results if 0.6 <= r['confidence'] < 0.8]
        
        if high_conf:
            doc.add_heading('High Confidence Transcriptions:', level=2)
            for result in high_conf:
                p = doc.add_paragraph()
                p.add_run(result['text']).bold = True
                p.add_run(f" (Confidence: {result['confidence']:.2f})")
        
        if med_conf:
            doc.add_heading('Medium Confidence Transcriptions:', level=2)
            for result in med_conf:
                p = doc.add_paragraph()
                p.add_run(result['text'])
                p.add_run(f" (Confidence: {result['confidence']:.2f})")
        
        # Add notes section
        doc.add_page_break()
        doc.add_heading('Notes for Review:', level=1)
        doc.add_paragraph("Please review and correct the transcription above.")
        doc.add_paragraph("Focus on medium confidence items which may need verification.")
        
    else:
        doc.add_paragraph("No transcription results with sufficient confidence.")
    
    doc.save(output_file)
    logger.info(f"Meeting document saved to {output_file}")

def main():
    """Main function for enhanced transcription"""
    print("Enhanced Lao Speech Recognition for Meetings")
    print("=" * 50)
    
    choice = input("Choose option:\n1. Record new audio\n2. Process existing file\nEnter choice (1 or 2): ")
    
    if choice == "1":
        # Record new audio
        duration = int(input("Recording duration in seconds (default 10): ") or "10")
        audio_file = record_enhanced_audio(duration)
    elif choice == "2":
        # Process existing file
        audio_file = input("Enter path to audio file: ").strip()
        if not os.path.exists(audio_file):
            print(f"File not found: {audio_file}")
            return
        
        # Enhance existing file
        enhancer = AudioEnhancer()
        enhanced_file = "enhanced_" + os.path.basename(audio_file)
        audio_file = enhancer.enhance_audio_file(audio_file, enhanced_file)
        print(f"Audio enhanced and saved as: {enhanced_file}")
    else:
        print("Invalid choice")
        return
    
    # Transcribe with confidence filtering
    print("Transcribing audio...")
    results = transcribe_with_confidence(audio_file, min_confidence=0.6)
    
    if results:
        print(f"\nFound {len(results)} transcription results:")
        for result in results:
            print(f"- {result['text']} (confidence: {result['confidence']:.2f})")
        
        # Create meeting document
        create_meeting_document(results)
        print("\nMeeting document created: meeting_notes.docx")
    else:
        print("No transcription results with sufficient confidence.")
        print("Try:")
        print("1. Speaking closer to the microphone")
        print("2. Reducing background noise")
        print("3. Speaking more clearly")

if __name__ == "__main__":
    main()
