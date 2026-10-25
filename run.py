import os
import sys
import webbrowser
import time
from pathlib import Path

def main():
    print("=" * 65)
    print(" 🎙️  NEWSTORY: CURRENT AFFAIRS PLOT UNVEILER")
    print("     Powered by Sarvam AI (105B LLM, Bulbul TTS, Saaras STT)")
    print("=" * 65)
    
    # Check .env
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("⚠️ Warning: .env file not found! Please create one with SARVAM_API_KEY.")
    
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    url = f"http://{host}:{port}"
    
    print(f"🚀 Starting voice agent server on {url}")
    print("💡 Open your browser at the URL above to interact with the voice agent.")
    print("=" * 65)
    
    import uvicorn
    uvicorn.run("main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
