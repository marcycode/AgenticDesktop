import speech_recognition as sr

def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except Exception as e:
        return "Sorry, couldn't understand."
