import pyaudio
import wave
import time
import sys
import os
from google.cloud import speech_v1p1beta1 as speech

# Audio recording settings
CHUNK = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1  # Mono
RATE = 16000  # Sample rate (Hz)
CHUNK_DURATION = 5  # Duration of each chunk in seconds
OUTPUT_FILE = "output_mic.txt"  # File to save the final transcript

def record_chunk(chunk_file, duration=CHUNK_DURATION):
    """Record audio from the microphone for a specified duration and save as WAV."""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print(f"Recording {duration} seconds...")
    frames = []

    # Record for the specified duration
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio as a WAV file
    wf = wave.open(chunk_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Saved chunk to {chunk_file}")

def transcribe_chunk(chunk_file):
    """Transcribe a single audio chunk using Google Cloud Speech-to-Text."""
    client = speech.SpeechClient()

    # Read the audio file
    with open(chunk_file, "rb") as audio_file:
        content = audio_file.read()

    # Configure the audio settings for Lao transcription
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="lo-LA",  # Lao language code
        enable_automatic_punctuation=True  # Improves readability
    )

    # Send the audio to Google for transcription
    try:
        response = client.recognize(config=config, audio=audio)
        if not response.results:
            print("No transcription for this chunk. Audio might be silent or unclear.")
            return ""
        transcript = response.results[0].alternatives[0].transcript
        return transcript
    except Exception as e:
        print(f"Error transcribing {chunk_file}: {e}")
        return ""

def transcribe_stream():
    """Record and transcribe audio from the microphone in real-time, saving the final transcript."""
    chunk_idx = 0
    all_transcripts = []  # List to store all chunk transcripts
    print("Starting real-time transcription... Press Ctrl+C to stop.")

    try:
        while True:
            # Record a chunk
            chunk_file = f"temp_chunk_{chunk_idx}.wav"
            record_chunk(chunk_file, duration=CHUNK_DURATION)

            # Transcribe the chunk
            transcript = transcribe_chunk(chunk_file)
            if transcript:
                print(f"Transcript [{chunk_idx}]: {transcript}")
                all_transcripts.append(transcript)
            else:
                print(f"Transcript [{chunk_idx}]: <No transcription>")

            # Clean up temporary file
            if os.path.exists(chunk_file):
                os.remove(chunk_file)

            chunk_idx += 1
            time.sleep(0.1)  # Small delay to avoid overloading

    except KeyboardInterrupt:
        print("\nStopped by user. Saving final transcript...")
        # Combine all transcripts and save to file
        final_transcript = " ".join(filter(None, all_transcripts))
        if final_transcript:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(final_transcript)
            print(f"Final transcript saved to {OUTPUT_FILE}")
        else:
            print("No transcription to save.")
    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        # Clean up any remaining temporary files
        for i in range(chunk_idx + 1):
            temp_file = f"temp_chunk_{i}.wav"
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    transcribe_stream()