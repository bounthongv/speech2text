"""
Lao Speech Recognition - Batch Processing Version
Usage: python transcribe_batch.py <audio_file> [--alternatives]
"""

import sys
import os
from transcribe_final import transcribe_audio_final, save_final_result
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_batch.py <audio_file> [--alternatives]")
        print("Example: python transcribe_batch.py bk/Voice_467_short.wav")
        print("         python transcribe_batch.py my_audio.wav --alternatives")
        return
    
    file_path = sys.argv[1]
    show_alternatives = "--alternatives" in sys.argv
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    
    print(f"Processing: {file_path}")
    print("=" * 50)
    
    # Transcribe audio
    result = transcribe_audio_final(file_path, show_alternatives)
    
    if result:
        print("\nFINAL TRANSCRIPTION:")
        print("-" * 30)
        print(result['final_text'])
        print(f"\nConfidence: {result['average_confidence']:.1%}")
        
        # Quality indicator
        if result['average_confidence'] >= 0.9:
            print("Quality: Excellent ✅")
        elif result['average_confidence'] >= 0.8:
            print("Quality: Very Good ✅")
        elif result['average_confidence'] >= 0.7:
            print("Quality: Good ⚠️")
        elif result['average_confidence'] >= 0.6:
            print("Quality: Fair ⚠️")
        else:
            print("Quality: Poor ❌")
        
        # Save result
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_filename = f"{base_name}_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        save_final_result(result, output_filename, show_alternatives)
        
    else:
        print("❌ No transcription results.")

if __name__ == "__main__":
    main()
