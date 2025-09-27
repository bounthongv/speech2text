from google.cloud import speech_v1p1beta1 as speech
import os

def transcribe_audio(file_path):
    # Verify the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    # Initialize the Speech-to-Text client
    try:
        client = speech.SpeechClient()
    except Exception as e:
        print(f"Error initializing client: {e}")
        return

    # Read the local audio file
    with open(file_path, "rb") as audio_file:
        content = audio_file.read()

    # Configure the audio settings
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="lo-LA",
    )

    # Send the synchronous request and get the response
    try:
        response = client.recognize(config=config, audio=audio)
    except Exception as e:
        print(f"Error during API request: {e}")
        return

    # Process and print the results
    if not response.results:
        print("No transcription results returned. The audio might be silent or not in Lao.")
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
        print("Confidence: {}".format(result.alternatives[0].confidence))

if __name__ == "__main__":
    file_path = "bk\\Voice_467_short.wav"  # Use the trimmed file
    transcribe_audio(file_path)