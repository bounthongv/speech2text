import sys
import re
import queue
import sounddevice as sd
import numpy as np
import wave
from google.cloud import speech_v1p1beta1 as speech
import spacy
from symspellpy import SymSpell, Verbosity

# Initialize SpaCy NLP
nlp = spacy.blank("en")  

# Initialize SymSpell for Lao spell correction
sym_spell = SymSpell()
sym_spell.load_dictionary("lao_words.txt", term_index=0, count_index=1, encoding="utf-8")

# Google Cloud Speech Client
client = speech.SpeechClient()

# Audio Configuration
RATE = 16000
CHANNELS = 1
CHUNK_SIZE = int(RATE / 10)  # 100ms chunks

# Queue for streaming audio
q = queue.Queue()

def callback(indata, frames, time, status):
    """Capture audio stream from microphone."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def load_audio(file_path):
    """Load a WAV audio file and convert it to the correct format."""
    with wave.open(file_path, "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        audio_data = wf.readframes(wf.getnframes())
    return audio_data, rate, channels

def transcribe_audio(file_path):
    """Transcribes an audio file using Google Cloud Speech-to-Text."""
    print(f"📂 Processing file: {file_path}")

    # Load audio data
    audio_data, rate, channels = load_audio(file_path)
    
    if channels != 1:
        print("⚠️ Warning: Audio file is not mono. Convert it before transcribing.")
        return ""

    # Configure recognition settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code="lo-LA",
    )

    # Create audio request
    audio = speech.RecognitionAudio(content=audio_data)

    # Perform transcription
    response = client.recognize(config=config, audio=audio)

    # Extract and return transcription
    text = " ".join(result.alternatives[0].transcript for result in response.results)
    return correct_text(text)

def correct_text(text):
    """
    Apply AI-based contextual corrections:
    - Fix number misinterpretations (e.g., 2005 -> 2025)
    - Correct spelling using SymSpell
    """
    text = re.sub(r'\b2005\b', '2025', text)  # Example number correction

    # Spelling Correction
    words = text.split()
    corrected_words = []
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        corrected_words.append(suggestions[0].term if suggestions else word)
    corrected_text = " ".join(corrected_words)

    return corrected_text

def transcribe_streaming():
    """Streams microphone input to Google Cloud Speech-to-Text with AI corrections."""
    print("🎤 Listening... Speak now!")

    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=np.int16, callback=callback):
        requests = (speech.StreamingRecognizeRequest(audio_content=q.get()) for _ in iter(int, 1))
        streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code="lo-LA",
            ),
            interim_results=True,
        )

        responses = client.streaming_recognize(streaming_config, requests)

        print("📝 Live transcription:")
        for response in responses:
            for result in response.results:
                if result.is_final:
                    corrected_text = correct_text(result.alternatives[0].transcript)
                    print(corrected_text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If an audio file is provided, process it
        audio_file = sys.argv[1]
        transcribed_text = transcribe_audio(audio_file)
        print("📝 Transcription:", transcribed_text)
    else:
        # If no arguments are given, use microphone input
        transcribe_streaming()
