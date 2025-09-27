import speech_recognition as sr

def recognize_lao_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("ກະລຸນາເວົ້າ... (Please speak in Lao)")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="lo-LA")
        print("ຂໍ້ຄວາມທີ່ຈັບໄດ້: ", text)
    except sr.UnknownValueError:
        print("ຂໍອະໄພ, ຂ້ອຍຟັງບໍ່ອອກ.")
    except sr.RequestError:
        print("ຂໍອະໄພ, ມີບັນຫາໃນການເຂົ້າເຖິງ Google Speech API.")

if __name__ == "__main__":
    recognize_lao_speech()
