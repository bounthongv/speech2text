import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wave
import torch
import warnings



# Load Whisper model (small model is recommended for faster results)
model = whisper.load_model("small")
# model = whisper.load_model("small").to(torch.device("cuda")) 
# model = whisper.load_model("large")


# model = whisper.load_model("medium")  # Use 'medium' or 'large' for better accuracy
# model = whisper.load_model("medium").to(torch.device("cuda"))  # Use GPU
# Function to record audio from microphone
warnings.simplefilter("ignore", UserWarning)

def record_audio(duration=5, samplerate=16000):
    print("Recording...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    return audio_data.flatten()

# Save recorded audio as a .wav file
def save_audio_file(audio_data, filename="temp.wav", samplerate=16000):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(samplerate)
            wav_file.writeframes(audio_data.tobytes())
        return temp_file.name

# Recognize speech using Whisper
thai_to_lao_map = {
    "ก": "ກ", "ข": "ຂ", "ฃ": "຃", "ค": "ຄ", "ฅ": "຅", "ฆ": "ຆ",
    "ง": "ງ", "จ": "ຈ", "ฉ": "ຉ", "ช": "ຊ", "ซ": "ຊ", "ฌ": "ຌ", "ญ": "ຍ",
    "ฎ": "ຎ", "ฏ": "ຏ", "ฐ": "ຐ", "ฑ": "ຑ", "ฒ": "ຒ", "ณ": "ຓ",
    "ด": "ດ", "ต": "ຕ", "ถ": "ຖ", "ท": "ທ", "ธ": "ຘ", "น": "ນ",
    "บ": "ບ", "ป": "ປ", "ผ": "ຜ", "ฝ": "ຝ", "พ": "ພ", "ฟ": "ຟ",
    "ภ": "ຠ", "ม": "ມ", "ย": "ຢ", "ร": "ຣ", "ล": "ລ", "ว": "ວ",
    "ศ": "ຨ", "ษ": "ຩ", "ส": "ສ", "ห": "ຫ", "ฬ": "ຬ", "อ": "ອ",
    "ะ": "ະ", "ั": "ັ", "า": "າ", "ำ": "ຳ", "ิ": "ິ", "ี": "ີ",
    "ึ": "ຶ", "ื": "ື", "ุ": "ຸ", "ู": "ູ", "เ": "ເ", "แ": "ແ",
    "โ": "ໂ", "ใ": "ໃ", "ไ": "ໄ", "่": "່", "้": "້", "๊": "໊",
    "๋": "໋", "์": "໌", "ๆ": "ໆ"
}

def convert_thai_to_lao(thai_text):
    """Convert Thai text to Lao script based on character mapping."""
    return "".join(thai_to_lao_map.get(char, char) for char in thai_text)

# Example Usage
thai_text = "สวัสดี"
lao_text = convert_thai_to_lao(thai_text)
print("Converted:", lao_text)  # Expected output: ສະບາຍດີ


def recognize_speech(audio_file):
    print("Recognizing speech...")
    result = model.transcribe(audio_file, language="lo", task="transcribe")  # Force Lao
    thai_text = result['text']
    lao_text = convert_thai_to_lao(thai_text)
    
    print("Recognized (Thai):", thai_text)
    print("Converted (Lao):", lao_text)

# Main function to record and transcribe speech
def main():
    audio_data = record_audio(duration=5)  # Record for 5 seconds
    audio_file = save_audio_file(audio_data)  # Save audio to temporary file
    recognize_speech(audio_file)  # Recognize speech

if __name__ == "__main__":
    main()
