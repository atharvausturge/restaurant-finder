import pyttsx3
import speech_recognition as sr


# Text-to-Speech (TTS) and Speech-to-Text (STT) functions using pyttsx3 and speech_recognition libraries.
def TTS(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[4].id)
    rate = engine.getProperty("rate")
    engine.setProperty("rate", rate - 75)
    engine.say(text)
    engine.runAndWait()


def _recognize_audio(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return None


def _stt_with_microphone(recognizer):
    with sr.Microphone() as source:
        print("Speak something...")
        audio = recognizer.listen(source)
    return _recognize_audio(recognizer, audio)


def STT():
    recognizer = sr.Recognizer()
    return _stt_with_microphone(recognizer)


if __name__ == "__main__":

    text = input("Enter the text you want to convert to speech: ")
    TTS(text)
    STT()
