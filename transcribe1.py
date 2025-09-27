import os
import subprocess
import tempfile
import time
from docx import Document  # Required for .docx files; install with `pip install python-docx`

def transcribe_long_audio(input_file, output_file=None):
    """
    Transcribe a long audio file by splitting it into chunks and processing each chunk.
    Optionally save the transcript to a file.

    Args:
        input_file (str): Path to the input audio file.
        output_file (str, optional): Path to save the transcript (e.g., 'transcript.txt' or 'transcript.docx').
    """
    input_file = os.path.abspath(input_file)
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    ffmpeg_path = "ffmpeg"  # Ensure FFmpeg is in PATH or provide the full path
    chunk_duration = 50     # Duration of each chunk in seconds
    overlap = 5             # Overlap between chunks in seconds

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
        total_duration = sum(x * float(t) for x, t in zip([3600, 60, 1], duration_str.split(':')))

        # Split audio into chunks
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
            print(f"FFmpeg return code: {process.returncode}, Output: {process.stderr}")

            # Verify chunk file exists
            max_wait = 10
            for _ in range(max_wait):
                if os.path.exists(output_chunk) and os.path.getsize(output_chunk) > 0:
                    print(f"File {output_chunk} created successfully.")
                    break
                print(f"Waiting for {output_chunk}...")
                time.sleep(1)
            else:
                raise FileNotFoundError(f"File {output_chunk} not found after {max_wait}s")
            chunks.append(output_chunk)

        # Transcribe chunks (replace with your transcription logic)
        print(f"Processing {len(chunks)} chunks from {total_duration}s audio.")
        transcripts = []
        for chunk in chunks:
            transcript = transcribe_chunk(chunk)  # Placeholder for actual transcription
            if transcript:
                transcripts.append(transcript)

        # Combine transcripts
        full_transcript = " ".join(transcripts)
        print("Full Transcript:")
        print(full_transcript)

        # Save to file if output_file is specified
        if output_file:
            try:
                if output_file.endswith('.docx'):
                    doc = Document()
                    doc.add_paragraph(full_transcript)
                    doc.save(output_file)
                    print(f"Transcript saved as Word document to {output_file}")
                else:  # Default to .txt
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(full_transcript)
                    print(f"Transcript saved as text file to {output_file}")
            except Exception as e:
                print(f"Error saving transcript to {output_file}: {e}")

    return full_transcript

# Placeholder for transcription function (replace with your actual implementation)
def transcribe_chunk(chunk_file):
    # Replace this with your transcription logic (e.g., using Google Speech-to-Text)
    return "Sample transcript from " + chunk_file

# Example usage
if __name__ == "__main__":
    input_file = "D:\\speechrecognition\\bk\\Voice_467_converted.wav"
    output_file = "transcript.txt"  # Or "transcript.docx"
    transcribe_long_audio(input_file, output_file=output_file)