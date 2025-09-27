from google.cloud import speech_v1p1beta1 as speech
import os
import numpy as np
import wave
import tempfile
from scipy import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_audio(input_file, output_file):
    """Preprocess audio to improve recognition accuracy"""
    try:
        # Read the original audio file
        with wave.open(input_file, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            audio_data = np.frombuffer(frames, dtype=np.int16)
        
        # Convert to float for processing
        float_data = audio_data.astype(np.float32)
        
        # 1. Normalize volume to optimal level
        max_val = np.max(np.abs(float_data))
        if max_val > 0:
            target_level = 32767 * 0.8  # 80% of max to avoid clipping
            normalized = float_data * (target_level / max_val)
        else:
            normalized = float_data
        
        # 2. Apply high-pass filter to remove low-frequency noise (below 80Hz)
        nyquist = sample_rate / 2
        low_cutoff = 80 / nyquist
        if low_cutoff < 1.0:  # Ensure valid filter parameters
            b, a = signal.butter(4, low_cutoff, btype='high')
            filtered = signal.filtfilt(b, a, normalized)
        else:
            filtered = normalized
        
        # 3. Enhance voice frequencies (300-3400 Hz)
        voice_low = 300 / nyquist
        voice_high = 3400 / nyquist
        if voice_low < 1.0 and voice_high < 1.0:
            b, a = signal.butter(4, [voice_low, voice_high], btype='band')
            voice_enhanced = signal.filtfilt(b, a, filtered)
            # Combine original with enhanced voice
            enhanced = filtered + (voice_enhanced * 0.3)
        else:
            enhanced = filtered
        
        # Convert back to int16
        processed_audio = enhanced.astype(np.int16)
        
        # Save processed audio
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)  # Ensure 16kHz sample rate
            wav_file.writeframes(processed_audio.tobytes())
        
        logger.info(f"Audio preprocessed and saved to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error preprocessing audio: {e}")
        return input_file  # Return original file if preprocessing fails

def transcribe_audio_enhanced(file_path, min_confidence=0.6):
    """Enhanced transcription with preprocessing and confidence filtering"""
    
    # Verify the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return None

    # Preprocess audio for better recognition
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        processed_file = preprocess_audio(file_path, temp_file.name)

    try:
        # Initialize the Speech-to-Text client
        client = speech.SpeechClient()

        # Read the processed audio file
        with open(processed_file, "rb") as audio_file:
            content = audio_file.read()

        # Configure the audio settings with enhanced options
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="lo-LA",
            enable_automatic_punctuation=True,
            max_alternatives=3,  # Get multiple alternatives
        )

        # Send the synchronous request and get the response
        response = client.recognize(config=config, audio=audio)

        # Process and filter results by confidence
        if not response.results:
            print("No transcription results returned. The audio might be silent or not in Lao.")
            return None

        best_results = []
        all_results = []
        
        for result in response.results:
            for i, alternative in enumerate(result.alternatives):
                confidence = alternative.confidence
                transcript = alternative.transcript
                
                result_data = {
                    'text': transcript,
                    'confidence': confidence,
                    'alternative_rank': i + 1
                }
                
                all_results.append(result_data)
                
                # Only include results above minimum confidence
                if confidence >= min_confidence:
                    best_results.append(result_data)

        # Display results
        print("\n" + "="*60)
        print("TRANSCRIPTION RESULTS")
        print("="*60)
        
        if best_results:
            print(f"\nHIGH CONFIDENCE RESULTS (≥{min_confidence}):")
            for result in best_results:
                print(f"Alternative {result['alternative_rank']}: {result['text']}")
                print(f"Confidence: {result['confidence']:.2f}")
                print("-" * 40)
        
        print(f"\nALL RESULTS:")
        for result in all_results:
            status = "✓" if result['confidence'] >= min_confidence else "⚠"
            print(f"{status} Alt {result['alternative_rank']}: {result['text']}")
            print(f"   Confidence: {result['confidence']:.2f}")
        
        # Return the best result
        if best_results:
            return best_results[0]
        elif all_results:
            print(f"\nWarning: No results above {min_confidence} confidence threshold.")
            print("Returning best available result (use with caution):")
            return all_results[0]
        else:
            return None

    except Exception as e:
        print(f"Error during API request: {e}")
        return None
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(processed_file)
        except:
            pass

def save_result_to_file(result, output_file="transcription_result.txt"):
    """Save transcription result to file"""
    if not result:
        print("No result to save.")
        return
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Lao Speech Transcription Result\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Text: {result['text']}\n")
            f.write(f"Confidence: {result['confidence']:.2f}\n")
            f.write(f"Alternative Rank: {result['alternative_rank']}\n")
        
        print(f"\nResult saved to: {output_file}")
    except Exception as e:
        print(f"Error saving result: {e}")

if __name__ == "__main__":
    # Test with your audio file
    file_path = "bk\\Voice_467_short.wav"  # Use the trimmed file
    
    print("Enhanced Lao Speech Recognition")
    print("Processing audio with preprocessing...")
    
    # Transcribe with enhanced settings
    result = transcribe_audio_enhanced(file_path, min_confidence=0.5)
    
    if result:
        print(f"\nBEST TRANSCRIPTION:")
        print(f"Text: {result['text']}")
        print(f"Confidence: {result['confidence']:.2f}")
        
        # Save result
        save_result_to_file(result)
        
        # Provide feedback based on confidence
        if result['confidence'] >= 0.8:
            print("\n✅ High confidence result - likely accurate")
        elif result['confidence'] >= 0.6:
            print("\n⚠️  Medium confidence - may need review")
        else:
            print("\n❌ Low confidence - likely needs correction")
    else:
        print("\n❌ No usable transcription results.")
        print("\nTips to improve accuracy:")
        print("1. Ensure clear speech without background noise")
        print("2. Speak at normal pace, not too fast or slow")
        print("3. Use a better quality microphone if possible")
        print("4. Record in a quiet environment")
