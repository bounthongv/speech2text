from google.cloud import speech_v1p1beta1 as speech
import os
import numpy as np
import wave
import tempfile
from scipy import signal
import logging
from datetime import datetime

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
            target_level = 32767 * 0.8
            normalized = float_data * (target_level / max_val)
        else:
            normalized = float_data
        
        # 2. Apply high-pass filter to remove low-frequency noise
        nyquist = sample_rate / 2
        low_cutoff = 80 / nyquist
        if low_cutoff < 1.0:
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
            enhanced = filtered + (voice_enhanced * 0.3)
        else:
            enhanced = filtered
        
        # Convert back to int16
        processed_audio = enhanced.astype(np.int16)
        
        # Save processed audio
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(processed_audio.tobytes())
        
        logger.info(f"Audio preprocessed and saved to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error preprocessing audio: {e}")
        return input_file

def transcribe_audio_final(file_path, show_alternatives=False):
    """Final transcription with clean output"""
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return None

    # Preprocess audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        processed_file = preprocess_audio(file_path, temp_file.name)

    try:
        # Initialize Speech client
        client = speech.SpeechClient()

        # Read processed audio
        with open(processed_file, "rb") as audio_file:
            content = audio_file.read()

        # Configure recognition
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="lo-LA",
            enable_automatic_punctuation=True,
            max_alternatives=3,
        )

        # Perform transcription
        response = client.recognize(config=config, audio=audio)

        if not response.results:
            print("No transcription results. The audio might be silent or unclear.")
            return None

        # Process results and select best transcription
        final_transcript = []
        all_alternatives = []
        
        for result in response.results:
            best_alternative = None
            segment_alternatives = []
            
            for alternative in result.alternatives:
                segment_alternatives.append({
                    'text': alternative.transcript,
                    'confidence': alternative.confidence
                })
                
                # Select best alternative (highest confidence)
                if best_alternative is None or alternative.confidence > best_alternative['confidence']:
                    best_alternative = {
                        'text': alternative.transcript,
                        'confidence': alternative.confidence
                    }
            
            if best_alternative:
                final_transcript.append(best_alternative)
                all_alternatives.append(segment_alternatives)

        return {
            'final_text': ' '.join([seg['text'] for seg in final_transcript]),
            'segments': final_transcript,
            'all_alternatives': all_alternatives if show_alternatives else None,
            'average_confidence': sum(seg['confidence'] for seg in final_transcript) / len(final_transcript) if final_transcript else 0
        }

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
    
    finally:
        try:
            os.unlink(processed_file)
        except:
            pass

def save_final_result(result, output_file="final_transcript.txt", show_alternatives=False):
    """Save clean final transcription result"""
    if not result:
        print("No result to save.")
        return
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Lao Speech Transcription - Final Result\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Average Confidence: {result['average_confidence']:.1%}\n\n")
            
            # Main transcription result
            f.write("TRANSCRIPTION:\n")
            f.write("-" * 20 + "\n")
            f.write(f"{result['final_text']}\n\n")
            
            # Quality indicator
            if result['average_confidence'] >= 0.9:
                f.write("Quality: Excellent (≥90%)\n")
            elif result['average_confidence'] >= 0.8:
                f.write("Quality: Very Good (≥80%)\n")
            elif result['average_confidence'] >= 0.7:
                f.write("Quality: Good (≥70%)\n")
            elif result['average_confidence'] >= 0.6:
                f.write("Quality: Fair (≥60%) - May need review\n")
            else:
                f.write("Quality: Poor (<60%) - Needs verification\n")
            
            # Show alternatives only if requested or confidence is low
            if show_alternatives or result['average_confidence'] < 0.8:
                f.write("\n" + "=" * 50 + "\n")
                f.write("DETAILED BREAKDOWN:\n")
                f.write("=" * 50 + "\n\n")
                
                for i, segment in enumerate(result['segments'], 1):
                    f.write(f"Segment {i}:\n")
                    f.write(f"Text: {segment['text']}\n")
                    f.write(f"Confidence: {segment['confidence']:.1%}\n")
                    
                    if result['all_alternatives'] and i <= len(result['all_alternatives']):
                        alternatives = result['all_alternatives'][i-1]
                        if len(alternatives) > 1:
                            f.write("Alternatives:\n")
                            for j, alt in enumerate(alternatives[1:], 2):
                                f.write(f"  {j}. {alt['text']} ({alt['confidence']:.1%})\n")
                    f.write("\n")
        
        print(f"Final result saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving result: {e}")

def main():
    print("\nLao Speech Recognition - Final Version")
    print("=" * 50)
    
    # Default test file
    default_file = "bk/Voice_467_short.wav"
    
    while True:
        print("\nAvailable test files:")
        print("1. Voice_467_short.wav (Default test file)")
        print("2. Enter custom file path")
        print("3. Quit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '3':
            break
        elif choice == '1':
            file_path = default_file
        elif choice == '2':
            file_path = input("Enter full path to audio file: ").strip()
            # Convert relative path to absolute if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.getcwd(), file_path)
        else:
            print("Invalid choice.")
            continue
            
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            print("Make sure to provide the correct path to an audio file.")
            continue
        
        try:
            # Ask user preference for output detail
            detail_choice = input("\nOutput detail level:\n1. Clean final result only\n2. Include alternatives for review\nChoice (1/2) [default: 1]: ").strip()
            show_alternatives = (detail_choice == '2')
        except EOFError:
            # Use default settings in non-interactive mode
            show_alternatives = False
        
        print("\nProcessing audio...")
        result = transcribe_audio_final(file_path, show_alternatives)
        
        if result:
            print("\n" + "="*60)
            print("FINAL TRANSCRIPTION RESULT")
            print("="*60)
            print(f"\nText: {result['final_text']}")
            print(f"Confidence: {result['average_confidence']:.1%}")
            
            # Quality feedback
            if result['average_confidence'] >= 0.9:
                print("✅ Excellent quality transcription")
            elif result['average_confidence'] >= 0.8:
                print("✅ Very good quality transcription")
            elif result['average_confidence'] >= 0.7:
                print("⚠️  Good quality - minor review recommended")
            elif result['average_confidence'] >= 0.6:
                print("⚠️  Fair quality - review recommended")
            else:
                print("❌ Poor quality - verification needed")
            
            # Save result
            output_filename = f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            save_final_result(result, output_filename, show_alternatives)
            
        else:
            print("\n❌ No transcription results.")
            print("Tips:")
            print("1. Ensure clear speech with minimal background noise")
            print("2. Check audio quality and volume levels")
            print("3. Try using mic_test.py to optimize microphone settings")

if __name__ == "__main__":
    main()
