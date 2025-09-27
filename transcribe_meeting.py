import os
import time
import wave
import pyaudio
import numpy as np
from google.cloud import speech_v1p1beta1 as speech
from docx import Document
import sounddevice as sd
from scipy import signal
import threading
import queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioPreprocessor:
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_size = 1024
        
    def remove_noise(self, audio_chunk):
        """Apply noise reduction using spectral gating"""
        # Convert to frequency domain
        freqs, times, spec = signal.spectrogram(audio_chunk, fs=self.sample_rate)
        # Simple noise reduction - remove low amplitude frequencies
        spec[spec < np.mean(spec) * 1.5] = 0
        # Convert back to time domain
        cleaned = signal.istft(spec)[1]
        return cleaned.astype(np.int16)
    
    def normalize_audio(self, audio_chunk):
        """Normalize audio volume"""
        max_val = np.max(np.abs(audio_chunk))
        if max_val > 0:
            normalized = audio_chunk * (32767 / max_val)
            return normalized.astype(np.int16)
        return audio_chunk

    def process_chunk(self, audio_chunk):
        """Apply all preprocessing steps"""
        # Convert to float for processing
        float_data = audio_chunk.astype(np.float32)
        
        # Apply preprocessing steps
        cleaned = self.remove_noise(float_data)
        normalized = self.normalize_audio(cleaned)
        
        return normalized

class MeetingTranscriber:
    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        self.client = speech.SpeechClient()
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.is_recording = False
        
        # Configure recognition settings
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="lo-LA",
            enable_automatic_punctuation=True,
            use_enhanced=True,  # Use enhanced model
            model="latest_long",  # Use the latest long-form model
            metadata=speech.RecognitionMetadata(
                interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION,
                microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
                recording_device_type=speech.RecognitionMetadata.RecordingDeviceType.PC,
            )
        )

    def start_recording(self):
        """Start recording from microphone"""
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            # Process audio chunk
            processed_audio = self.preprocessor.process_chunk(indata.copy())
            self.audio_queue.put(processed_audio)

        # Start recording stream
        try:
            with sd.InputStream(
                channels=1,
                samplerate=16000,
                dtype=np.int16,
                blocksize=16000,  # 1-second chunks
                callback=audio_callback
            ):
                logger.info("Recording started. Press Ctrl+C to stop.")
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in recording: {e}")
            self.is_recording = False

    def transcribe_stream(self):
        """Process audio queue and perform transcription"""
        streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True
        )

        def generator():
            while self.is_recording or not self.audio_queue.empty():
                if not self.audio_queue.empty():
                    chunk = self.audio_queue.get()
                    yield speech.StreamingRecognizeRequest(audio_content=chunk.tobytes())
                else:
                    time.sleep(0.1)

        try:
            responses = self.client.streaming_recognize(streaming_config, generator())
            
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0]
                
                if result.is_final:
                    confidence = transcript.confidence
                    text = transcript.transcript
                    
                    # Only keep transcriptions with good confidence
                    if confidence > 0.7:
                        self.text_queue.put((text, confidence))
                        logger.info(f"Transcribed (conf: {confidence:.2f}): {text}")
                    else:
                        logger.debug(f"Low confidence ({confidence:.2f}) transcription ignored: {text}")

        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            self.is_recording = False

    def save_transcript(self, output_file):
        """Save transcribed text to file"""
        all_text = []
        
        # Get all transcribed text from queue
        while not self.text_queue.empty():
            text, confidence = self.text_queue.get()
            all_text.append(f"{text} (confidence: {confidence:.2f})")

        if not all_text:
            logger.warning("No transcription to save")
            return

        try:
            if output_file.endswith('.docx'):
                doc = Document()
                doc.add_heading('Meeting Transcript', 0)
                for text in all_text:
                    doc.add_paragraph(text)
                doc.save(output_file)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(all_text))
            logger.info(f"Transcript saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")

def main():
    transcriber = MeetingTranscriber()
    
    # Start recording in a separate thread
    recording_thread = threading.Thread(target=transcriber.start_recording)
    recording_thread.start()
    
    # Start transcription in a separate thread
    transcription_thread = threading.Thread(target=transcriber.transcribe_stream)
    transcription_thread.start()
    
    try:
        # Keep running until user interrupts
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Stopping recording...")
        transcriber.is_recording = False
        
    # Wait for threads to complete
    recording_thread.join()
    transcription_thread.join()
    
    # Save the transcript
    transcriber.save_transcript('meeting_transcript.docx')

if __name__ == "__main__":
    main()
