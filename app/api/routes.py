import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.config import settings
from app.services.sarvam_service import sarvam_service
from app.services.story_engine import StoryEngine
from app.services.scraper_service import ScraperService

logger = logging.getLogger("routes")
router = APIRouter()

class ExtractUrlRequest(BaseModel):
    url: str

class GenerateStoryRequest(BaseModel):
    text: str
    style: str = "noir"
    language_code: str = "en-IN"
    speaker: str = "aditya"
    pace: float = 1.0
    custom_twist: Optional[str] = None

class SpeakRequest(BaseModel):
    text: str
    speaker: str = "aditya"
    language_code: str = "en-IN"
    pace: float = 1.0

class ChatRequest(BaseModel):
    story_context: str
    user_question: str
    history: List[Dict[str, str]] = []
    speaker: str = "aditya"
    language_code: str = "en-IN"

class ExplainTermRequest(BaseModel):
    term: str
    context: Optional[str] = None
    speaker: str = "aditya"
    language_code: str = "en-IN"

@router.get("/config")
def get_config():
    return {
        "speakers": settings.AVAILABLE_SPEAKERS,
        "languages": settings.LANGUAGES,
        "story_modes": settings.STORY_MODES,
        "presets": ScraperService.get_presets()
    }

@router.get("/presets")
def get_presets():
    return ScraperService.get_presets()

@router.post("/extract-url")
def extract_url(req: ExtractUrlRequest):
    if not req.url or not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL provided.")
    try:
        return ScraperService.extract_from_url(req.url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/generate-story")
def generate_story(req: GenerateStoryRequest):
    if not req.text or len(req.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of news or forum content.")

    try:
        # 1. Build prompt and invoke Sarvam-105b LLM
        prompt = StoryEngine.build_generation_prompt(
            news_text=req.text,
            style=req.style,
            target_language=req.language_code,
            custom_instructions=req.custom_twist
        )
        
        raw_completion = sarvam_service.generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75
        )
        
        # 2. Parse structured story
        story_data = StoryEngine.parse_story_response(raw_completion)
        
        # 3. Generate voice script audio with Sarvam Bulbul TTS
        voice_script = story_data.get("voice_script", "")
        audio_b64 = ""
        if voice_script:
            try:
                audio_b64 = sarvam_service.synthesize_speech(
                    text=voice_script,
                    speaker=req.speaker,
                    language_code=req.language_code,
                    pace=req.pace
                )
            except Exception as tts_err:
                logger.warning(f"TTS synthesis warning: {tts_err}")

        return {
            "status": "success",
            "story": story_data,
            "audio_base64": audio_b64,
            "speaker": req.speaker,
            "language_code": req.language_code
        }
    except Exception as e:
        logger.error(f"Generate story failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form("unknown")
):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio recording received.")
            
        result = sarvam_service.transcribe_audio(
            audio_bytes=content,
            filename=file.filename or "recording.wav",
            content_type=file.content_type or "audio/wav",
            language_code=language_code or "unknown"
        )
        return result
    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speak")
def speak(req: SpeakRequest):
    try:
        audio_b64 = sarvam_service.synthesize_speech(
            text=req.text,
            speaker=req.speaker,
            language_code=req.language_code,
            pace=req.pace
        )
        return {"audio_base64": audio_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def chat_agent(req: ChatRequest):
    try:
        result = sarvam_service.conversational_agent_turn(
            story_context=req.story_context,
            user_question=req.user_question,
            conversation_history=req.history,
            speaker=req.speaker,
            language_code=req.language_code
        )
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr-newspaper")
async def ocr_newspaper(
    file: UploadFile = File(...)
):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty image uploaded.")

        result = sarvam_service.ocr_newspaper_image(
            image_bytes=content,
            filename=file.filename or "newspaper.png",
            content_type=file.content_type or "image/png"
        )
        return result
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-term")
def explain_term(req: ExplainTermRequest):
    if not req.term or not req.term.strip():
        raise HTTPException(status_code=400, detail="Term cannot be empty.")
    try:
        return sarvam_service.explain_term(
            term=req.term.strip(),
            context=req.context,
            speaker=req.speaker,
            language_code=req.language_code
        )
    except Exception as e:
        logger.error(f"Explain term error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
