import io
import time
import zipfile
import base64
import logging
import httpx
from PIL import Image
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from sarvamai import SarvamAI
from app.config import settings

logger = logging.getLogger("sarvam_service")

class SarvamService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        if not self.api_key:
            raise ValueError("No SARVAM_API_KEY provided in .env or settings.")
        self.client = SarvamAI(api_subscription_key=self.api_key)

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Calls Sarvam-105b chat completions.
        """
        chosen_model = model or settings.LLM_MODEL
        try:
            kwargs = {
                "model": chosen_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 2048
            }
                
            res = self.client.chat.completions(**kwargs)
            choice = res.choices[0]
            content = choice.message.content
            if not content:
                content = getattr(choice.message, "reasoning_content", None)
            return content or ""
        except Exception as e:
            logger.error(f"Error calling Sarvam chat completions: {e}")
            raise RuntimeError(f"Sarvam LLM Error: {str(e)}")

    def synthesize_speech(
        self,
        text: str,
        speaker: str = "aditya",
        language_code: str = "en-IN",
        pace: float = 1.0,
        model: str = "bulbul:v3"
    ) -> str:
        """
        Converts text to speech using Sarvam Bulbul TTS.
        Returns base64 encoded audio string (WAV).
        """
        # Clean text of markdown asterisks or special characters for cleaner TTS
        cleaned_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        
        # Max length per TTS chunk safe bound is ~1500 chars
        if len(cleaned_text) > 1500:
            cleaned_text = cleaned_text[:1495] + "..."

        try:
            res = self.client.text_to_speech.convert(
                text=cleaned_text,
                language_code=language_code,
                speaker=speaker,
                pace=pace,
                model=model
            )
            if res.audios and len(res.audios) > 0:
                return res.audios[0]
            raise ValueError("Sarvam TTS returned empty audio list.")
        except Exception as e:
            logger.error(f"Error calling Sarvam TTS: {e}")
            raise RuntimeError(f"Sarvam TTS Error: {str(e)}")

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "input.wav",
        content_type: str = "audio/wav",
        language_code: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Transcribes speech audio using Sarvam Saaras STT.
        """
        try:
            audio_tuple = (filename, audio_bytes, content_type)
            res = self.client.speech_to_text.transcribe(
                file=audio_tuple,
                model=settings.STT_MODEL,
                language_code=language_code if language_code != "unknown" else None
            )
            return {
                "transcript": res.transcript,
                "language_code": getattr(res, "language_code", "en-IN"),
                "timestamps": getattr(res, "timestamps", None)
            }
        except Exception as e:
            logger.error(f"Error calling Sarvam STT: {e}")
            raise RuntimeError(f"Sarvam STT Error: {str(e)}")

    def conversational_agent_turn(
        self,
        story_context: str,
        user_question: str,
        conversation_history: List[Dict[str, str]],
        speaker: str = "aditya",
        language_code: str = "en-IN"
    ) -> Dict[str, Any]:
        """
        Answers a user follow-up question in-character about the story,
        and generates spoken audio.
        """
        system_prompt = f"""
You are the master narrator and investigative insider behind this current affairs saga.
You know the whole plot, the secret deals, the key players, and the unspoken motives.

STORY CONTEXT:
\"\"\"
{story_context}
\"\"\"

Answer the user's question directly, insightfully, and conversationally in 2 to 4 sentences.
Maintain your engaging, dramatic, insider persona.
Do not use bullet points or markdown syntax. Keep it natural to be spoken aloud.
"""
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-4:]:  # last 4 turns
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_question})

        answer_text = self.generate_chat_completion(messages, temperature=0.7)
        audio_base64 = self.synthesize_speech(
            text=answer_text,
            speaker=speaker,
            language_code=language_code
        )

        return {
            "answer_text": answer_text,
            "audio_base64": audio_base64,
            "speaker": speaker
        }

    def ocr_newspaper_image(
        self,
        image_bytes: bytes,
        filename: str = "newspaper.png",
        content_type: str = "image/png"
    ) -> Dict[str, Any]:
        """
        Extracts text from a newspaper article picture or screenshot using Sarvam Doc AI.
        """
        # Validate and normalize image with PIL
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert RGBA/P to RGB if JPEG or standardize to PNG
            buf = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                img.convert("RGB").save(buf, format="PNG")
            else:
                img.save(buf, format="PNG")
            cleaned_bytes = buf.getvalue()
            safe_filename = filename.rsplit(".", 1)[0] + ".png" if "." in filename else "newspaper.png"
        except Exception as img_err:
            logger.warning(f"PIL image normalization warning: {img_err}")
            cleaned_bytes = image_bytes
            safe_filename = filename

        # 1. Start Doc AI Digitise job
        try:
            file_payload = [(safe_filename, cleaned_bytes, "image/png")]
            job_init = self.client.doc_ai.digitise(file=file_payload)
            job_id = job_init.job_id
        except Exception as e:
            logger.error(f"Error starting Sarvam Doc AI: {e}")
            raise RuntimeError(f"Sarvam Doc AI Digitise error: {str(e)}")

        # 2. Poll for completion (typically takes 1-3 seconds)
        max_attempts = 15
        for _ in range(max_attempts):
            time.sleep(1.0)
            status_obj = self.client.doc_ai.get_status(job_id=job_id)
            status_str = getattr(status_obj, "status", "")
            if status_str == "completed":
                break
            elif status_str in ("failed", "error"):
                raise RuntimeError(f"Sarvam Doc AI processing failed: {status_obj}")

        # 3. Retrieve presigned zip URL and extract HTML text
        try:
            download_obj = self.client.doc_ai.get_download_url(job_id=job_id)
            r = httpx.get(download_obj.url, timeout=20.0)
            r.raise_for_status()

            z = zipfile.ZipFile(io.BytesIO(r.content))
            extracted_paragraphs = []
            
            for fname in z.namelist():
                if fname.endswith(".html"):
                    html_content = z.read(fname).decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html_content, "html.parser")
                    # Extract headings and paragraphs
                    for tag in soup.find_all(["h1", "h2", "h3", "p", "div", "span"]):
                        text = tag.get_text(strip=True)
                        if len(text) > 20 and text not in extracted_paragraphs:
                            extracted_paragraphs.append(text)

            full_extracted_text = "\n\n".join(extracted_paragraphs)
            if not full_extracted_text:
                # Fallback to any text inside html
                for fname in z.namelist():
                    if fname.endswith(".html"):
                        soup = BeautifulSoup(z.read(fname).decode("utf-8", errors="ignore"), "html.parser")
                        full_extracted_text = soup.get_text(separator="\n", strip=True)
                        if full_extracted_text:
                            break

            return {
                "job_id": job_id,
                "extracted_text": full_extracted_text or "No text could be extracted from this image.",
                "character_count": len(full_extracted_text)
            }
        except Exception as parse_err:
            logger.error(f"Error extracting Doc AI zip result: {parse_err}")
            raise RuntimeError(f"Failed to read OCR output from Sarvam Doc AI: {str(parse_err)}")

    def explain_term(
        self,
        term: str,
        context: Optional[str] = None,
        speaker: str = "aditya",
        language_code: str = "en-IN"
    ) -> Dict[str, Any]:
        """
        Explains complex terms in markets, business, finance, or politics in plain language,
        with a memorable analogy and spoken audio.
        """
        import json
        import re

        prompt = f"""
You are an expert market analyst, business strategist, and political decoder.
Explain the following term clearly for an intelligent audience without using dense academic or financial jargon.

TERM: "{term}"
{f'CONTEXT: "{context}"' if context else ''}

Return a valid JSON object matching this schema:
{{
  "term": "{term}",
  "category": "One of: 📈 Markets & Finance, 💼 Business & Strategy, 🏛️ Geopolitics & Policy, ⚙️ Tech & Supply Chain",
  "simple_definition": "A 1-2 sentence plain-English definition stripping away buzzwords.",
  "eli5_analogy": "A brilliant real-world analogy (e.g. 'Think of it like...').",
  "voice_script": "A lively, engaging 30-50 word spoken explanation meant to be voiced aloud. No asterisks."
}}
Return ONLY valid JSON.
"""
        raw = self.generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )

        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except Exception:
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except Exception:
                    data = {}
            else:
                data = {}

        if not data:
            data = {
                "term": term,
                "category": "💼 Business & Markets",
                "simple_definition": f"A specialized concept describing how transactions, governance, or market dynamics operate.",
                "eli5_analogy": "Imagine a marketplace where buyers and sellers adjust rules based on who holds the biggest stack of chips.",
                "voice_script": f"{term} is a critical mechanism in modern affairs that dictates who holds the upper hand and where the money flows."
            }

        voice_script = data.get("voice_script", data.get("simple_definition", ""))
        audio_b64 = ""
        try:
            audio_b64 = self.synthesize_speech(
                text=voice_script,
                speaker=speaker,
                language_code=language_code
            )
        except Exception as e:
            logger.warning(f"Failed to synthesize audio for term: {e}")

        data["audio_base64"] = audio_b64
        data["speaker"] = speaker
        return data

sarvam_service = SarvamService()
