import flet as ft
import sounddevice as sd
import numpy as np
import tempfile
import wave
import threading
import whisper

# Load Whisper model
model = whisper.load_model("small")

def record_audio(duration=2, samplerate=16000):
    """Record audio from microphone."""
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    return audio_data.flatten()

def save_audio_file(audio_data, samplerate=16000):
    """Save recorded audio as a .wav file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(samplerate)
            wav_file.writeframes(audio_data.tobytes())
        return temp_file.name

def recognize_speech(audio_file):
    """Recognize speech using Whisper."""
    result = model.transcribe(audio_file, language="lo", task="transcribe")
    return result['text']

def main(page: ft.Page):
    page.title = "Whisper Lao Speech to Text"
    page.vertical_alignment = ft.MainAxisAlignment.START

    transcribed_text = ft.TextField(multiline=True, width=600, height=300, read_only=True)
    recording = threading.Event()

    def start_recording(e):
        recording.set()
        def record_loop():
            while recording.is_set():
                audio_data = record_audio(duration=2)  # 2-second chunks
                audio_file = save_audio_file(audio_data)
                text = recognize_speech(audio_file)
                transcribed_text.value += text + " "
                page.update()
        threading.Thread(target=record_loop, daemon=True).start()
    
    def stop_recording(e):
        recording.clear()
    
    page.add(
        ft.Row([
            ft.ElevatedButton("Start Recording", on_click=start_recording),
            ft.ElevatedButton("Stop", on_click=stop_recording)
        ]),
        transcribed_text
    )

ft.app(target=main)

#if web
# ft.app(target=main, view=ft.WEB_BROWSER)
  