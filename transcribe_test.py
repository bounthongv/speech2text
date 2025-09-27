from google.cloud import speech_v1p1beta1 as speech
import os
import numpy as np
import wave
from scipy import signal
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_audio(input_file):
    """Preprocess audio file to improve recognition quality"""
    logger.info("Processing audio...")
    
    # Read audio file
    with wave.open(input_file, 'rb') as wav_file:
        frames = wav_file.readframes(-1)
        audio_data = np.frombuffer(frames, dtype=np.int16)
        sample_rate = wav_file.getframerate()
    
    # Convert to float for processing
    float_data = audio_data.astype(np.float32)
    
    # 1. Normalize volume
    max_val = np.max(np.abs(float_data))
    if max_val > 0:
        float_data = float_data * (32767 / max_val * 0.8)
    
    # 2. Apply noise reduction
    nyquist = sample_rate / 2
    cutoff = 80 / nyquist
    if cutoff < 1.0:
        b, a = signal.butter(4, cutoff, btype='high')
        float_data = signal.filtfilt(b, a, float_data)
    
    # 3. Enhance voice frequencies
    voice_low = 300 / nyquist
    voice_high = 3400 / nyquist
    if voice_low < 1.0 and voice_high < 1.0:
        b, a = signal.butter(4, [voice_low, voice_high], btype='band')
        voice = signal.filtfilt(b, a, float_data)
        float_data = float_data + (voice * 0.3)
    
    return float_data.astype(np.int16)

def write_to_output(text, output_file="output.txt", print_console=True):
    """Write text to both console and output file"""
    if print_console:
        print(text)
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(text + '\n')

def transcribe_audio(file_path, min_confidence=0.5):
    """Transcribe audio with output to both console and file"""
    
    # Clear previous output file
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(f"Lao Speech Recognition Results\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
    
    # Verify file exists
    if not os.path.exists(file_path):
        msg = f"File not found: {file_path}"
        write_to_output(msg)
        return
    
    try:
        # Initialize Speech client
        client = speech.SpeechClient()
        
        # Process audio
        audio_data = process_audio(file_path)
        
        # Create recognition config
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="lo-LA",
            enable_automatic_punctuation=True,
        )
        
        # Prepare audio content
        audio = speech.RecognitionAudio(content=audio_data.tobytes())
        
        # Perform transcription
        write_to_output("\nTranscribing audio...")
        write_to_output("=" * 60)
        
        start_time = time.time()
        response = client.recognize(config=config, audio=audio)
        processing_time = time.time() - start_time
        
        # Process results
        if not response.results:
            write_to_output("\nNo transcription results. The audio might be silent or unclear.")
            write_to_output("\nTroubleshooting Tips:")
            write_to_output("1. Ensure clear speech with minimal background noise")
            write_to_output("2. Check that the audio file contains speech")
            write_to_output("3. Try adjusting microphone position/settings")
            return
        
        write_to_output(f"\nProcessing completed in {processing_time:.1f} seconds")
        write_to_output("\nTranscription Results:")
        write_to_output("=" * 60)
        
        total_confidence = 0
        result_count = 0
        
        for i, result in enumerate(response.results, 1):
            write_to_output(f"\nSegment {i}:")
            write_to_output("-" * 30)
            
            for j, alternative in enumerate(result.alternatives, 1):
                confidence = alternative.confidence
                total_confidence += confidence
                result_count += 1
                
                write_to_output(f"\nAlternative {j}:")
                write_to_output(f"Text: {alternative.transcript}")
                write_to_output(f"Confidence: {confidence:.1%}")
                
                if confidence < min_confidence:
                    write_to_output("⚠️  Low confidence - may need verification")
                elif confidence >= 0.8:
                    write_to_output("✓ High confidence result")
        
        # Print summary
        write_to_output("\nTranscription Summary:")
        write_to_output("=" * 60)
        write_to_output(f"Total segments: {len(response.results)}")
        write_to_output(f"Average confidence: {(total_confidence/result_count):.1%}")
        write_to_output(f"Processing time: {processing_time:.1f} seconds")
        
        # Provide feedback
        avg_conf = total_confidence/result_count
        if avg_conf < 0.6:
            write_to_output("\n❌ Poor Recognition Quality")
            write_to_output("Suggestions:")
            write_to_output("1. Speak more clearly and slowly")
            write_to_output("2. Reduce background noise")
            write_to_output("3. Position microphone closer")
        elif avg_conf < 0.8:
            write_to_output("\n⚠️  Moderate Recognition Quality")
            write_to_output("Consider:")
            write_to_output("1. Speaking more clearly")
            write_to_output("2. Reducing ambient noise")
        else:
            write_to_output("\n✓ Good Recognition Quality")
        
        write_to_output(f"\nResults saved to: output.txt")
        
    except Exception as e:
        error_msg = f"Error during transcription: {e}"
        write_to_output(error_msg)
        logger.error(error_msg)

def main():
    write_to_output("\nLao Speech Recognition - Quality Test")
    write_to_output("=" * 60)
    
    while True:
        file_path = input("\nEnter audio file path (or 'q' to quit): ").strip()
        
        if file_path.lower() == 'q':
            break
        
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            continue
        
        # Set confidence threshold
        try:
            conf = float(input("Enter minimum confidence threshold (0.0-1.0) [default: 0.5]: ") or "0.5")
            conf = max(0.0, min(1.0, conf))
        except:
            conf = 0.5
        
        # Perform transcription
        transcribe_audio(file_path, min_confidence=conf)
        
        print("\nPress Enter to process another file, or 'q' to quit.")

if __name__ == "__main__":
    main()
