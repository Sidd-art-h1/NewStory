# 🎙️ NewStory: The Current Affairs Plot Unveiler
> **Transforming Dry News & Forum Debates into Thrilling Cinematic Sagas and Interactive Voice Agent Dialogues.**
> Built for Hackathon Excellence using **Sarvam AI** (`sarvam-105b-conversations`, `Bulbul:v3` TTS, `Saaras:v3` STT).

---

## 🌟 The Vision & Pitch
News reports and current affairs forums are often dry, verbose, and full of bureaucratic PR that obscures the real drama. 

**NewStory** is a multimodal voice-first agent that ingests raw news articles, physical newspaper clipping photos, URL dispatches, or forum debates, and exposes **"The Whole Plot Behind It"**:
1. **Newspaper Clipping Photo Intake (OCR)**: Snap a photo of a physical newspaper or screenshot an article; Sarvam Doc AI digitizes the text in seconds.
2. **The Covert Agenda**: What the public was told vs. the hidden incentives and power dynamics.
3. **The Key Players & Stakes**: Who stands to gain billions, who faces ruin, and who is pulling the strings.
4. **Market, Business & Political Jargon Buster**: Automatically detects dense terms (e.g. *Quantitative Easing*, *Margin Calls*, *EUV Lithography*, *Gerrymandering*), delivering plain-English definitions, memorable ELI5 analogies, and spoken audio explanations.
5. **Three-Act Screenplay Drama**: Breaking down the event like a cinematic saga or top-tier investigative podcast.
6. **Cinematic Spoken Narration**: Generated in real time using Sarvam AI's expressive Indic voices (Bulbul v3), rendered with a live glowing audio waveform visualizer.
7. **Interactive Voice Interrogation**: Users can interrupt and cross-examine the narrator via microphone or text (*"Wait, who funded this?"*, *"Explain what happens to ordinary people in Hindi"*), receiving instant conversational spoken responses.

---

## 🏗️ Architecture

```
ChronicleVoice/
├── .env                  # Sarvam API Key, Kivi Key, Host & Port configuration
├── requirements.txt      # Python dependencies
├── run.py                # 1-Click Launcher
├── main.py               # FastAPI Core application & static mounting
├── app/
│   ├── config.py         # Voice actor lists, languages, story modes, and settings
│   ├── services/
│   │   ├── sarvam_service.py   # Sarvam AI Client: STT (Saaras), TTS (Bulbul), LLM (105B)
│   │   ├── story_engine.py     # Prompt engineering for investigative screenplay narratives
│   │   └── scraper_service.py  # Webpage cleaner & high-impact hackathon presets
│   └── api/
│       └── routes.py     # REST endpoints for generation, audio synthesis, and chat
└── static/
    ├── index.html        # Glassmorphism dark-mode UI with visualizer & screenplay theater
    ├── style.css         # Cyberpunk studio styling & animated sound bars
    └── app.js            # Web Audio API visualizer, mic recording, playback controls
```

---

## 🚀 Quickstart (Under 2 Minutes)

### 1. Configure `.env`
Ensure your API keys are in `.env`:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
KIVI_API_KEY=your_sarvam_or_kivi_key_here
PORT=8000
HOST=127.0.0.1
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python run.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## 🎭 Story Persona Modes
- 🕵️ **Investigative Noir**: Uncovers hidden puppet masters, cynical alliances, and backroom leverage.
- 🎙️ **The Inside Scoop Podcast**: Witty, fast-paced, urgent breakdown in the style of top tech/finance podcasters.
- ⚔️ **Succession Saga**: Corporate and geopolitical titans clashing over market dominance and dynastic control.
- 📜 **The Grand Allegory**: Jargon-free folk parable translating complex monetary policy or chip supply chains into memorable tales.
- 🇮🇳 **Desi Masala / Hinglish Plot**: High-drama Bollywood-style narration with dramatic plot twists.

---

## ⚡ Hackathon Presentation Tips
1. **Instant Demo**: Click one of the pre-loaded high-stakes presets (*The Billion-Dollar Silicon Siege* or *The UPI Coup Against Wall Street*) to demonstrate immediate generation without needing external network scraping.
2. **Audio Visualizer**: Point out the live canvas audio visualizer reacting in real time to the voice pitch.
3. **Live Voice Mic**: Click the microphone in the *Voice Ingestion* tab or in the *Interrogate the Narrator* section to showcase real-time Speech-to-Text (`Saaras:v3`).
4. **Multilingual Flexibility**: Toggle between English, Hindi, and regional Indic languages to showcase Sarvam's unique sovereign AI capabilities.
