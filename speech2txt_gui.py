import speech_recognition as sr
import tkinter as tk
from tkinter import scrolledtext

def recognize_lao_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="ກຳລັງຟັງ... ກະລຸນາເວົ້າ")
        root.update()  # Update UI

        # recognizer.adjust_for_ambient_noise(source)
        recognizer.adjust_for_ambient_noise(source, duration=1.5)

        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="lo-LA", show_all=True)
        if "alternative" in text:
            best_match = text["alternative"][0]["transcript"]  # Get the most confident result
        else:
            best_match = "ບໍ່ສາມາດຈັບຄຳໄດ້"

        text_box.insert(tk.END, best_match + "\n")

        text_box.insert(tk.END, text + "\n")  # Append recognized text
        status_label.config(text="ກົດປຸ່ມເພື່ອຟັງຄືນ.")
    except sr.UnknownValueError:
        status_label.config(text="ຂໍອະໄພ, ຂ້ອຍຟັງບໍ່ອອກ.")
    except sr.RequestError:
        status_label.config(text="ບັນຫາໃນການເຂົ້າເຖິງ Google Speech API.")

# Create GUI
root = tk.Tk()
root.title("Lao Speech Recognition")
root.geometry("500x300")

status_label = tk.Label(root, text="ກົດປຸ່ມເພື່ອເລີ່ມຟັງ", font=("Arial", 12))
status_label.pack(pady=10)

listen_button = tk.Button(root, text="🎤 Start Listening", font=("Arial", 12), command=recognize_lao_speech)
listen_button.pack(pady=10)

text_box = scrolledtext.ScrolledText(root, width=60, height=10, font=("Arial", 12))
text_box.pack(pady=10)

root.mainloop()
