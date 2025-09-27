import os
import subprocess
import tempfile
import time
import sys
from google.cloud import speech_v1p1beta1 as speech
from docx import Document  # For saving as .docx

def parse_duration(duration_str):
    """Convert FFmpeg duration (e.g., '00:02:23.42') to seconds."""
    h, m, s = map(float, duration_str.split(':'))
    return h * 3600 + m * 60 + s

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
        sample_rate_hertz=16000,  # Matches the FFmpeg conversion
        language_code="lo-LA",    # Lao language code
        enable_automatic_punctuation=True  # Improves readability
    )

    # Send the audio to Google for transcription
    try:
        response = client.recognize(config=config, audio=audio)
        if not response.results:
            print(f"No transcription for {chunk_file}. Audio might be silent or unclear.")
            return ""
        transcript = response.results[0].alternatives[0].transcript
        print(f"Transcribed {chunk_file}: {transcript}")
        return transcript
    except Exception as e:
        print(f"Error transcribing {chunk_file}: {e}")
        return ""

def transcribe_long_audio(input_file, output_file=None):
    """
    Transcribe a long audio file by splitting it into chunks, converting each chunk,
    and processing it with Google Cloud Speech-to-Text.

    Args:
        input_file (str): Path to the input audio file.
        output_file (str, optional): Path to save the transcript (e.g., 'transcript.txt' or 'transcript.docx').
    """
    # Convert input file path to absolute path and check existence
    input_file = os.path.abspath(input_file)
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Configuration
    ffmpeg_path = "ffmpeg"  # Ensure FFmpeg is in PATH or provide full path
    chunk_duration = 50     # Duration of each chunk in seconds
    overlap = 5             # Overlap between chunks in seconds

    # Create temporary directory for chunks
    with tempfile.TemporaryDirectory(dir=os.path.dirname(input_file)) as temp_dir:
        temp_dir = os.path.abspath(temp_dir)
        print(f"Using temp directory: {temp_dir}")

        # Get audio duration using FFmpeg
        result = subprocess.run(
            [ffmpeg_path, '-i', input_file, '-f', 'null', '-'],
            stderr=subprocess.PIPE, text=True, env=os.environ
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get duration: {result.stderr}")
        duration_line = [line for line in result.stderr.split('\n') if 'Duration:' in line][0]
        duration_str = duration_line.split('Duration: ')[1].split(',')[0].strip()
        total_duration = parse_duration(duration_str)

        # Split audio into chunks and convert each chunk to the required format
        chunks = []
        for start in range(0, int(total_duration), chunk_duration - overlap):
            end = min(start + chunk_duration, total_duration)
            output_chunk = os.path.join(temp_dir, f"chunk_{start}_{end}.wav")
            cmd = [
                ffmpeg_path, '-i', input_file, '-ss', str(start), '-t', str(end - start),
                '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', output_chunk
            ]
            print(f"Executing: {' '.join(cmd)}")
            process = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=os.environ)
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {process.stderr}")

            # Verify chunk file exists and adjust for potential floating-point issues
            max_wait = 10
            for _ in range(max_wait):
                if os.path.exists(output_chunk) and os.path.getsize(output_chunk) > 0:
                    print(f"File {output_chunk} created successfully (size: {os.path.getsize(output_chunk)} bytes).")
                    break
                print(f"Waiting for {output_chunk}...")
                time.sleep(1)
            else:
                raise FileNotFoundError(f"File {output_chunk} not found after {max_wait}s")
            chunks.append(output_chunk)

        # Ensure the last chunk is processed if it exists
        if chunks and os.path.exists(chunks[-1]):
            print(f"Last chunk confirmed: {chunks[-1]}")

        # Transcribe chunks
        print(f"Processing {len(chunks)} chunks from {total_duration:.2f}s audio.")
        transcripts = []
        for chunk in chunks:
            transcript = transcribe_chunk(chunk)
            transcripts.append(transcript)  # Always append, even if empty, for debugging

        # Combine transcripts
        full_transcript = " ".join(filter(None, transcripts))  # Filter out empty strings
        print("Full Transcript:")
        print(full_transcript)

        # Save to file if output_file is specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(full_transcript)
                print(f"Transcript saved as text file to {output_file}")
            except Exception as e:
                print(f"Error saving transcript to {output_file}: {e}")

    return full_transcript

if __name__ == "__main__":
    # Check for correct number of command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python transcribe1.py <input_file> <output_file>")
        sys.exit(1)
    
    # Assign input and output file paths from arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Run transcription
    transcribe_long_audio(input_file, output_file=output_file)