import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Load from local path
model_path = "D:/speechRecognition/models/wav2vec2-large-xlsr-53"

processor = Wav2Vec2Processor.from_pretrained(model_path)
model = Wav2Vec2ForCTC.from_pretrained(model_path)

print("Model loaded successfully!")
