# Voice profile builder for blind users — asks questions aloud, saves answers to JSON.
# pip install gtts pygame openai-whisper sounddevice scipy SpeechRecognition

import argparse, json, os, tempfile, time

# -- TTS: say text out loud using Google TTS + pygame --
def speak(text):
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts = gTTS(text=text, lang="en")
    tts.save(tmp.name)
    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.unload()
    os.remove(tmp.name)

# -- Record mic to a temp wav file --
def record(duration=5, sr=16000):
    import sounddevice as sd
    from scipy.io.wavfile import write
    speak(f"Listening for {duration} seconds.")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="int16")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    write(tmp.name, sr, audio)
    return tmp.name

# -- Transcribe audio to text (whisper first, google fallback) --
def transcribe(path, model_name="small"):
    try:
        import whisper
        return whisper.load_model(model_name).transcribe(path).get("text", "").strip()
    except Exception:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(path) as src:
            return r.recognize_google(r.record(src))

# -- Cleanup helper --
def _rm(path):
    try: os.remove(path)
    except Exception: pass

# -- Ask one question: speak it, record answer, confirm, return text --
def ask(question, duration=5.0, model="small", retries=3):
    answer = ""
    for _ in range(retries):
        speak(question)
        time.sleep(0.4)
        wav = record(duration)
        try:
            answer = transcribe(wav, model)
        except Exception:
            speak("Sorry, couldn't understand. Let me ask again.")
            continue
        finally:
            _rm(wav)

        if not answer:
            speak("Didn't catch that. Let's try again.")
            continue

        speak(f"I heard: {answer}. Is that correct? Say yes or no.")
        time.sleep(0.3)
        cwav = record(3)
        try:
            conf = transcribe(cwav, model).lower()
        except Exception:
            conf = ""
        finally:
            _rm(cwav)

        if any(w in conf for w in ("yes", "yeah", "yep", "correct")):
            speak("Great!")
            return answer
        speak("Okay, let me ask again.")

    speak("Let's move on.")
    return answer

# -- Load questions from questions.txt (key|question per line) --
def load_questions(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "questions.txt")
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, q = line.split("|", 1)
            questions.append((key.strip(), q.strip()))
    return questions

# -- Build profile by asking every question --
def build_profile(duration=5.0, model="small"):
    questions = load_questions()
    return {key: ask(q, duration, model) for key, q in questions}

# -- Save profile dict to JSON --
def save_profile(profile, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    speak(f"Profile saved to {os.path.basename(path)}.")

# -- Entry point --
def main():
    p = argparse.ArgumentParser(description="Voice profile builder for blind users.")
    p.add_argument("-o", "--output", default=os.path.join(os.path.dirname(__file__), "..", "user_profile.json"))
    p.add_argument("-d", "--duration", type=float, default=5.0)
    p.add_argument("-m", "--model", default="small")
    args = p.parse_args()

    speak("Starting profile setup.")
    time.sleep(0.5)
    profile = build_profile(args.duration, args.model)

    speak("Here is your profile summary.")
    for k, v in profile.items():
        speak(f"{k.replace('_',' ').title()}: {v}")
        time.sleep(0.3)

    speak("Saving your profile now.")
    save_profile(profile, os.path.abspath(args.output))
    speak("All done! We'll use this to find restaurants for you. Goodbye!")

if __name__ == "__main__":
    main()