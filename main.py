"""
Nova AI Desktop Assistant — FastAPI Backend
Run: uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""

import asyncio
import base64
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.nlu import NLUEngine
from core.conversation import ConversationManager
from services.tts import TTSService
from automation.desktop import DesktopAutomation

# ── Load .env ──────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Nova AI Desktop Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

nlu_engine: NLUEngine                     = None
conversation_manager: ConversationManager = None
tts_service: TTSService                   = None
desktop: DesktopAutomation                = None


@app.on_event("startup")
async def startup():
    global nlu_engine, conversation_manager, tts_service, desktop

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("⚠️  GROQ_API_KEY not set — AI features will fail")
    else:
        print("✅ GROQ_API_KEY loaded successfully")

    nlu_engine           = NLUEngine(api_key)
    conversation_manager = ConversationManager()
    tts_service          = TTSService()
    desktop              = DesktopAutomation()

    print("✅ Nova AI Backend ready at http://127.0.0.1:8000")


class TextRequest(BaseModel):
    text: str
    session_id: str = "default"

class AudioRequest(BaseModel):
    audio_b64: str
    session_id: str = "default"


@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "Nova AI running", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "groq_key_set": bool(os.environ.get("GROQ_API_KEY")),
        "tts_available": tts_service.available if tts_service else False,
    }


@app.post("/api/command/text")
async def command_text(req: TextRequest):
    history = conversation_manager.get_history(req.session_id)
    result  = await nlu_engine.process(req.text, history)

    action_result = None
    if result.get("action"):
        action_result = await desktop.execute(result["action"], result.get("params", {}))
        if action_result and action_result.get("message"):
            result["reply"] = action_result["message"]

    conversation_manager.add(req.session_id, req.text, result["reply"])
    audio_b64 = tts_service.synthesize_b64(result["reply"])

    return {
        "reply":         result["reply"],
        "intent":        result.get("intent"),
        "action":        result.get("action"),
        "action_result": action_result,
        "audio_b64":     audio_b64,
    }


@app.post("/api/command/audio")
async def command_audio(req: AudioRequest):
    try:
        audio_bytes = base64.b64decode(req.audio_b64)
    except Exception:
        raise HTTPException(400, "Invalid base64 audio")

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name

    try:
        transcript = await _stt(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)

    if not transcript:
        return {"reply": "Sorry, I didn't catch that.", "transcript": "", "audio_b64": None}

    result = await command_text(TextRequest(text=transcript, session_id=req.session_id))
    result["transcript"] = transcript
    return result


async def _stt(audio_path: str) -> str:
    """
    Transcribe audio using Groq Whisper API (handles webm/wav/mp3/etc.)
    Falls back to Google speech recognition if Groq fails.
    """
    # Primary: Groq Whisper — handles webm natively
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            import httpx
            audio_bytes = Path(audio_path).read_bytes()
            # Detect format from magic bytes
            ext = "webm"
            if audio_bytes[:4] == b"RIFF":
                ext = "wav"
            elif audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
                ext = "mp3"
            elif audio_bytes[:4] == b"OggS":
                ext = "ogg"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": (f"audio.{ext}", audio_bytes, f"audio/{ext}")},
                    data={"model": "whisper-large-v3-turbo", "language": "en"},
                )
            if resp.status_code == 200:
                return resp.json().get("text", "").strip()
            else:
                print(f"Groq STT error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Groq STT exception: {e}")

    # Fallback: convert to WAV with ffmpeg then use SpeechRecognition
    try:
        import subprocess as sp
        wav_path = audio_path + "_converted.wav"
        result = sp.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True, timeout=15
        )
        if result.returncode == 0:
            audio_path = wav_path
    except Exception:
        pass  # No ffmpeg — try raw file anyway

    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.record(src)
        return r.recognize_google(audio)
    except Exception as e:
        print(f"Fallback STT error: {e}")
        return ""



# ── PDF Upload & Summarize ─────────────────────────────────────────────────────
from fastapi import UploadFile, File, Form

class PDFSummarizeRequest(BaseModel):
    pdf_b64:    str
    filename:   str = "document.pdf"
    mode:       str = "summary"   # "summary" | "keypoints" | "qa"
    question:   str = ""          # used when mode == "qa"
    session_id: str = "default"


@app.post("/api/pdf/summarize")
async def pdf_summarize(req: PDFSummarizeRequest):
    """Extract text from PDF and summarise / answer questions via Groq."""
    import base64, io

    # ── Decode PDF ────────────────────────────────────────────────────────────
    try:
        pdf_bytes = base64.b64decode(req.pdf_b64)
    except Exception:
        raise HTTPException(400, "Invalid base64 PDF data")

    # ── Extract text ──────────────────────────────────────────────────────────
    text = await _extract_pdf_text(pdf_bytes)
    if not text or not text.strip():
        return {
            "reply":     "I couldn't extract any text from this PDF. It may be scanned/image-based.",
            "audio_b64": tts_service.synthesize_b64("I couldn't extract text from that PDF."),
        }

    # Trim to avoid token overflow (~12 000 chars ≈ 3 000 tokens)
    MAX_CHARS = 12_000
    truncated = len(text) > MAX_CHARS
    text_chunk = text[:MAX_CHARS]

    # ── Build prompt ──────────────────────────────────────────────────────────
    if req.mode == "keypoints":
        prompt = (
            f"Extract the 8-10 most important key points from this document as a "
            f"numbered list. Be concise.\n\nDocument:\n{text_chunk}"
        )
        intent_label = "key_points"
    elif req.mode == "qa" and req.question:
        prompt = (
            f"Answer this question based ONLY on the document below. "
            f"If the answer isn't in the document, say so.\n\n"
            f"Question: {req.question}\n\nDocument:\n{text_chunk}"
        )
        intent_label = "pdf_qa"
    else:  # default: summary
        prompt = (
            f"Write a clear, concise summary of this document in 3-5 paragraphs. "
            f"Cover the main topic, key findings, and conclusions.\n\nDocument:\n{text_chunk}"
        )
        intent_label = "pdf_summary"

    # ── Call Groq ─────────────────────────────────────────────────────────────
    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, nlu_engine._call_groq, [
            {"role": "system", "content": "You are Nova, a helpful AI assistant. Respond clearly and professionally. Do NOT output JSON — just plain text."},
            {"role": "user",   "content": prompt},
        ])
    except Exception as e:
        raise HTTPException(500, f"AI error: {e}")

    suffix = "\n\n⚠️ Note: Document was truncated to fit AI context window." if truncated else ""
    reply  = raw.strip() + suffix

    # Save to conversation history
    user_msg = f"[PDF: {req.filename}] {req.question or req.mode}"
    conversation_manager.add(req.session_id, user_msg, reply)

    # TTS only for short replies (key points / QA), not full summaries
    audio_b64 = None
    if len(reply) < 600:
        audio_b64 = tts_service.synthesize_b64(reply)

    return {
        "reply":      reply,
        "intent":     intent_label,
        "filename":   req.filename,
        "char_count": len(text),
        "truncated":  truncated,
        "audio_b64":  audio_b64,
    }


async def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Try PyMuPDF first (fast), fall back to pypdf."""
    loop = asyncio.get_event_loop()

    def _extract():
        # Method 1: PyMuPDF (fitz) — best quality
        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = [page.get_text() for page in doc]
            doc.close()
            return "\n\n".join(pages)
        except ImportError:
            pass
        except Exception as e:
            print(f"PyMuPDF error: {e}")

        # Method 2: pypdf — pure Python fallback
        try:
            import pypdf, io
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            return "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except ImportError:
            pass
        except Exception as e:
            print(f"pypdf error: {e}")

        return ""

    return await loop.run_in_executor(None, _extract)


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    return {"history": conversation_manager.get_history(session_id)}

@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str):
    conversation_manager.clear(session_id)
    return {"status": "cleared"}


@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "text":
                result = await command_text(TextRequest(text=data["text"], session_id=session_id))
                await websocket.send_json({"type": "response", **result})
            elif data.get("type") == "audio":
                result = await command_audio(AudioRequest(audio_b64=data["audio_b64"], session_id=session_id))
                await websocket.send_json({"type": "response", **result})
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS error: {e}")