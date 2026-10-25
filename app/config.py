import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "NewStory: Current Affairs Plot Unveiler"
    PROJECT_VERSION: str = "1.0.0"
    
    # API Keys
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    KIVI_API_KEY: str = os.getenv("KIVI_API_KEY") or os.getenv("SARVAM_API_KEY", "")
    SARVAM_BASE_URL: str = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
    
    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Models
    LLM_MODEL: str = "sarvam-105b-conversations"
    TTS_MODEL: str = "bulbul:v3"
    STT_MODEL: str = "saaras:v3"
    
    # Speakers for Bulbul:v3
    AVAILABLE_SPEAKERS = [
        {"id": "aditya", "name": "Aditya (Dramatic / Clear)", "gender": "male", "lang": "en-IN / hi-IN"},
        {"id": "simran", "name": "Simran (Expressive / Host)", "gender": "female", "lang": "en-IN / hi-IN"},
        {"id": "kabir", "name": "Kabir (Deep / Investigative)", "gender": "male", "lang": "en-IN / hi-IN"},
        {"id": "priya", "name": "Priya (Articulate / Newsroom)", "gender": "female", "lang": "en-IN / hi-IN"},
        {"id": "ratan", "name": "Ratan (Warm / Documentary)", "gender": "male", "lang": "en-IN / hi-IN"},
        {"id": "ritu", "name": "Ritu (Lively / Storyteller)", "gender": "female", "lang": "en-IN / hi-IN"},
        {"id": "shubh", "name": "Shubh (Punchy / Energetic)", "gender": "male", "lang": "en-IN / hi-IN"},
    ]
    
    # Supported Languages
    LANGUAGES = [
        {"code": "en-IN", "name": "English (India)"},
        {"code": "hi-IN", "name": "Hindi (हिंदी)"},
        {"code": "bn-IN", "name": "Bengali (বাংলা)"},
        {"code": "ta-IN", "name": "Tamil (தமிழ்)"},
        {"code": "te-IN", "name": "Telugu (తెలుగు)"},
        {"code": "kn-IN", "name": "Kannada (ಕನ್ನಡ)"},
        {"code": "mr-IN", "name": "Marathi (मराठी)"},
        {"code": "gu-IN", "name": "Gujarati (ગુજરાતી)"},
    ]
    
    # Story Modes
    STORY_MODES = [
        {
            "id": "noir",
            "name": "Investigative Noir",
            "badge": "🕵️ Noir Expose",
            "description": "Unveils hidden backroom deals, covert motives, and puppet masters behind the headlines."
        },
        {
            "id": "podcast",
            "name": "The Inside Scoop Podcast",
            "badge": "🎙️ Fast-Paced",
            "description": "Dynamic, witty, behind-the-scenes narrative breakdown as if hosted by top investigative podcasters."
        },
        {
            "id": "succession",
            "name": "Corporate / Geopolitical Saga",
            "badge": "⚔️ Throne Drama",
            "description": "Treats boardrooms and international summits like Game of Thrones or Succession."
        },
        {
            "id": "eli5",
            "name": "The Grand Allegory",
            "badge": "📜 Folk Parable",
            "description": "Transforms high-stakes economic or tech affairs into a compelling, clear allegorical fable."
        },
        {
            "id": "hinglish",
            "name": "Desi Masala / Hinglish Plot",
            "badge": "🇮🇳 Masala Twist",
            "description": "High-drama, culturally resonant, code-mixed storytelling with suspenseful plot twists."
        }
    ]

settings = Settings()
