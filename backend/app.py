from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import pyttsx3
import tempfile
import os

app = FastAPI(title="TTS/STT Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "TTS/STT backend is running"}


@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    # Save upload to a temporary file
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp.name) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError as e:
            raise HTTPException(status_code=502, detail=str(e))

        return JSONResponse({"text": text})
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass


@app.post("/tts")
async def tts(payload: dict, background_tasks: BackgroundTasks):
    text = payload.get("text") if isinstance(payload, dict) else None
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required in JSON body")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    filename = tmp.name

    # Synthesize to file
    engine = pyttsx3.init()
    engine.save_to_file(text, filename)
    engine.runAndWait()

    def _cleanup(path: str):
        try:
            os.remove(path)
        except Exception:
            pass

    background_tasks.add_task(_cleanup, filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")
