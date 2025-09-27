import pyaudio
import wave
import os
import json
import time
import threading
import queue
from google.cloud import speech
import numpy as np
from mic_calibration import MicrophoneCalibrator
from phrase_dictionary import PhraseDictionary

class AudioTranscriber:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        self.calibrator = MicrophoneCalibrator()
        self.phrase_dict = PhraseDictionary()
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.is_recording = False
        self.transcription_thread = None
        
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.transcription_thread = threading.Thread(target=self._process_audio)
        self.recording_thread.start()
        self.transcription_thread.start()
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        if self.transcription_thread:
            self.transcription_thread.join()
    
    def _record_audio(self):
        """Record audio from microphone and add to queue"""
        p = pyaudio.PyAudio()
        
        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.calibrator.settings['selected_device'],
            frames_per_buffer=self.CHUNK
        )
        
        print("* recording")
        
        while self.is_recording:
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                
                # Apply calibration and noise reduction
                processed_audio = self.calibrator.process_audio(audio_data)
                
                # Convert back to bytes
                processed_data = processed_audio.astype(np.float32).tobytes()
                self.audio_queue.put(processed_data)
            except Exception as e:
                print(f"Error recording audio: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("* done recording")
    
    def _process_audio(self):
        """Process audio chunks and get transcriptions"""
        client = speech.SpeechClient()
        
        # Get phrases for speech adaptation
        phrases = self.phrase_dict.get_phrases()
        speech_contexts = []
        
        # Split phrases into chunks of 100 to avoid hitting API limits
        chunk_size = 100
        for i in range(0, len(phrases), chunk_size):
            chunk = phrases[i:i + chunk_size]
            speech_contexts.append(
                speech.SpeechContext(phrases=chunk)
            )
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.RATE,
            language_code="en-US",
            enable_automatic_punctuation=True,
            speech_contexts=speech_contexts,
            model="meeting"  # Use the meeting model for better accuracy
        )
        
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )
        
        def audio_generator():
            while self.is_recording or not self.audio_queue.empty():
                if not self.audio_queue.empty():
                    chunk = self.audio_queue.get()
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                else:
                    time.sleep(0.1)
        
        try:
            requests = audio_generator()
            responses = client.streaming_recognize(streaming_config, requests)
            
            for response in responses:
                if not response.results:
                    continue
                    
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                
                # Apply phrase dictionary corrections
                corrected_transcript = self.phrase_dict.correct_text(transcript)
                
                # If this is a final result, update phrase frequencies
                if result.is_final:
                    words = transcript.split()
                    for word in words:
                        suggestions = self.phrase_dict.find_similar_phrases(word)
                        if suggestions and suggestions[0]['distance'] == 0:
                            self.phrase_dict.increment_frequency(suggestions[0]['suggestion'])
                    
                    self.text_queue.put(("final", corrected_transcript))
                else:
                    self.text_queue.put(("interim", corrected_transcript))
                    
        except Exception as e:
            print(f"Error in transcription: {e}")
    
    def get_transcription(self):
        """Get the next transcription from the queue"""
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return None

def main():
    """Main function to run the transcriber"""
    transcriber = AudioTranscriber()
    
    # First run calibration
    print("\nStarting microphone calibration...")
    print("\nMeasuring noise profile (keep quiet)...")
    transcriber.calibrator.measure_noise_profile()
    
    input("\nPress Enter to start calibration (you'll need to speak)...")
    transcriber.calibrator.calibrate_microphone()
    
    print("\nCalibration complete! Press Enter to start transcribing...")
    input()
    
    try:
        transcriber.start_recording()
        
        while True:
            result = transcriber.get_transcription()
            if result:
                status, text = result
                if status == "final":
                    print("\nFinal:", text)
                else:
                    print("\rInterim:", text, end="", flush=True)
                    
    except KeyboardInterrupt:
        print("\nStopping...")
        transcriber.stop_recording()

if __name__ == "__main__":
    main()
