import whisper
import subprocess

# Define file names
video_file = "D:\Downloads\elon.mp4"  # Change this to your MP4 file
audio_file = "audio.wav"
output_text_file = "transcription.txt"

# Convert MP4 to WAV (if not already extracted)
print("Extracting audio from video...")
subprocess.run(["ffmpeg", "-i", video_file, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_file], check=True)

# Load the Whisper model (Use "small" or "medium" based on what you downloaded)
model = whisper.load_model("medium")

# Transcribe the audio
print("Transcribing audio...")
result = model.transcribe(audio_file)

# Save transcription to a text file
with open(output_text_file, "w", encoding="utf-8") as f:
    f.write(result["text"])

print(f"Transcription completed! Output saved to {output_text_file}")
