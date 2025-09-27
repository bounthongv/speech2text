import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torchaudio

model_path = "D:/speechRecognition/models/wav2vec2-large-xlsr-53"

# Load Model & Processor
processor = Wav2Vec2Processor.from_pretrained(model_path)
model = Wav2Vec2ForCTC.from_pretrained(model_path)

# Load Audio File (replace with your file)
waveform, sample_rate = torchaudio.load("test_audio.wav")
resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
waveform = resampler(waveform).squeeze()

# Process Audio
input_values = processor(waveform, sampling_rate=16000, return_tensors="pt").input_values

# Get Predictions
with torch.no_grad():
    logits = model(input_values).logits
predicted_ids = torch.argmax(logits, dim=-1)

# Decode Prediction
transcription = processor.batch_decode(predicted_ids)[0]
print("Transcription:", transcription)
