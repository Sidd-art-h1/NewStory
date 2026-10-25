import os
import io
import base64
import time
import streamlit as st
from PIL import Image

# Import existing application backend modules
from app.config import settings
from app.services.sarvam_service import sarvam_service
from app.services.story_engine import StoryEngine
from app.services.scraper_service import ScraperService

# Page Configuration
st.set_page_config(
    page_title="NewStory | Current Affairs Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism Styling
GLASS_CSS = """
<style>
/* Main Background and Ambient Lights */
.stApp {
    background-color: #040711;
    color: #f8fafc;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.18) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.16) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.08) 0%, transparent 50%);
}

/* Glassmorphic Containers */
.glass-panel {
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(24px) saturate(190%);
    -webkit-backdrop-filter: blur(24px) saturate(190%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-top: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.glass-agenda {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-left: 4px solid #f59e0b;
    border-radius: 0 14px 14px 0;
    padding: 1.25rem;
    margin: 1rem 0;
}

.glass-term {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 0.85rem;
}

/* Centered Surrounding Light Circle for Voice Play */
.voice-center-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 1.5rem;
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 24px;
    margin-bottom: 1.5rem;
    box-shadow: 0 14px 40px -8px rgba(0,0,0,0.5);
}

.play-surround-halo {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0.06) 65%, rgba(255, 255, 255, 0.02) 100%);
    border: 2px solid rgba(255, 255, 255, 0.45);
    box-shadow: 0 0 35px rgba(255, 255, 255, 0.2), inset 0 0 20px rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.85rem auto;
    font-size: 2.2rem;
}

.narrator-badge {
    font-size: 0.82rem;
    font-family: monospace;
    color: #38bdf8;
    background: rgba(6, 182, 212, 0.15);
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    border: 1px solid rgba(6, 182, 212, 0.3);
    display: inline-block;
    margin-top: 0.3rem;
}

/* Badges */
.badge-gold {
    color: #fde68a;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
}

.badge-purple {
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.4);
    color: #c4b5fd;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-family: monospace;
}
</style>
"""
st.markdown(GLASS_CSS, unsafe_allow_html=True)

# Initialize Session State
if "current_story" not in st.session_state:
    st.session_state.current_story = None
if "story_audio_b64" not in st.session_state:
    st.session_state.story_audio_b64 = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "input_text" not in st.session_state:
    presets = ScraperService.get_presets()
    st.session_state.input_text = presets[0]["text"].strip() if presets else ""
if "term_audio_cache" not in st.session_state:
    st.session_state.term_audio_cache = {}

# Sidebar: Controls & Director Persona
with st.sidebar:
    st.markdown("## 🎙️ **NEW`STORY`**")
    st.caption("Current Affairs Voice Agent • The Whole Plot Behind It")
    st.markdown("---")

    st.markdown("### 🎭 Director Persona")
    mode_options = {m["id"]: f"{m['badge']} - {m['name']}" for m in settings.STORY_MODES}
    selected_mode = st.selectbox(
        "Story Narrative Style",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x]
    )

    st.markdown("### 🗣️ Voice & Language")
    speaker_options = {s["id"]: s["name"] for s in settings.AVAILABLE_SPEAKERS}
    selected_speaker = st.selectbox(
        "Sarvam Voice Actor",
        options=list(speaker_options.keys()),
        format_func=lambda x: speaker_options[x]
    )

    lang_options = {l["code"]: l["name"] for l in settings.LANGUAGES}
    selected_lang = st.selectbox(
        "Target Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x]
    )

    st.markdown("### 🎬 Director's Secret Twist (Optional)")
    custom_twist = st.text_input(
        "Focus / Tone instruction",
        placeholder="e.g. Focus on who lost millions, emphasize shadow banking..."
    )

    st.markdown("---")
    st.markdown("### ⚡ Technology Stack")
    st.caption("• **Sarvam 105B Conversations** (LLM Screenplay Engine)")
    st.caption("• **Sarvam Bulbul v3** (Indic Voice Actor TTS)")
    st.caption("• **Sarvam Saaras v3** (Speech-to-Text STT)")
    st.caption("• **Sarvam Doc AI** (Newspaper Layout OCR)")

# Main Layout Header
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.markdown("# 🎙️ **NEW`STORY`**")
    st.markdown("##### *Transform dry news dispatches into thrilling cinematic sagas, decode covert plots, and listen with sovereign Indic voice agents.*")

with col_header_2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="badge-purple">⚡ Sarvam 105B</span> <span class="badge-purple">Bulbul v3</span>', unsafe_allow_html=True)

st.markdown("---")

# Main Interface: Left Column (Ingestion) & Right Column (Screenplay & Voice)
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 📥 Step 1: Ingest News or Forum Debate")
    
    tab_presets, tab_text, tab_photo, tab_url, tab_voice = st.tabs([
        "⚡ Presets", "📝 Paste Text", "📷 Photo / Scan", "🌐 URL", "🎤 Voice"
    ])

    # Tab 1: Presets
    with tab_presets:
        presets = ScraperService.get_presets()
        preset_titles = [f"{p['category']}: {p['title']}" for p in presets]
        chosen_preset_title = st.selectbox("Choose a high-stakes scenario:", preset_titles)
        chosen_preset = next(p for p in presets if f"{p['category']}: {p['title']}" == chosen_preset_title)
        
        st.info(f"**Source:** {chosen_preset['source']}\n\n{chosen_preset['summary']}")
        if st.button("Use this Preset", use_container_width=True):
            st.session_state.input_text = chosen_preset["text"].strip()
            st.success("Preset loaded into active story draft!")

    # Tab 2: Direct Paste
    with tab_text:
        st.session_state.input_text = st.text_area(
            "Paste article, editorial, Reddit thread, or bulletin:",
            value=st.session_state.input_text,
            height=280
        )

    # Tab 3: Newspaper Photo OCR
    with tab_photo:
        st.markdown("Upload a photo or screenshot of a physical newspaper clipping or column.")
        uploaded_image = st.file_uploader(
            "Upload image (PNG, JPG, WEBP):",
            type=["png", "jpg", "jpeg", "webp"]
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Newspaper Clipping Preview", use_container_width=True)
            if st.button("⚡ Extract Article via Sarvam Doc AI", type="secondary", use_container_width=True):
                with st.spinner("Sarvam Doc AI is digitizing columns and headings..."):
                    try:
                        img_bytes = uploaded_image.getvalue()
                        ocr_res = sarvam_service.ocr_newspaper_image(
                            image_bytes=img_bytes,
                            filename=uploaded_image.name,
                            content_type=uploaded_image.type
                        )
                        st.session_state.input_text = ocr_res["extracted_text"]
                        st.success(f"Extracted {ocr_res['character_count']} characters from newspaper photo!")
                    except Exception as e:
                        st.error(f"Doc AI Error: {e}")

    # Tab 4: URL Fetch
    with tab_url:
        target_url = st.text_input("Enter article / forum webpage URL:")
        if st.button("Fetch & Clean Webpage", use_container_width=True):
            if target_url:
                with st.spinner("Scraping clean article text..."):
                    try:
                        scraped = ScraperService.extract_from_url(target_url)
                        st.session_state.input_text = scraped["text"]
                        st.success(f"Extracted article: '{scraped['title']}' ({len(scraped['text'])} chars)")
                    except Exception as e:
                        st.error(f"Scrape Error: {e}")
            else:
                st.warning("Please enter a valid URL.")

    # Tab 5: Voice Ingestion
    with tab_voice:
        st.markdown("Upload an audio recording of your news prompt or dictation.")
        audio_file = st.file_uploader("Upload audio (WAV, MP3, WEBM):", type=["wav", "mp3", "webm"])
        if audio_file is not None:
            if st.button("Transcribe via Sarvam Saaras STT", use_container_width=True):
                with st.spinner("Transcribing with Sarvam Saaras v3..."):
                    try:
                        stt_res = sarvam_service.transcribe_audio(
                            audio_bytes=audio_file.getvalue(),
                            filename=audio_file.name,
                            content_type=audio_file.type,
                            language_code=selected_lang
                        )
                        st.session_state.input_text = stt_res["transcript"]
                        st.success(f"Transcribed: '{stt_res['transcript']}'")
                    except Exception as e:
                        st.error(f"STT Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    # Generate Story Button
    btn_generate = st.button(
        "⚡ UNVEIL THE PLOT & GENERATE VOICE STORY",
        type="primary",
        use_container_width=True
    )

    if btn_generate:
        if not st.session_state.input_text or len(st.session_state.input_text.strip()) < 20:
            st.error("Please provide at least 20 characters of news or select a preset.")
        else:
            with st.spinner("Sarvam 105B is analyzing covert agendas and power moves..."):
                try:
                    # 1. Prompt Generation
                    prompt = StoryEngine.build_generation_prompt(
                        news_text=st.session_state.input_text,
                        style=selected_mode,
                        target_language=selected_lang,
                        custom_instructions=custom_twist or None
                    )
                    
                    # 2. LLM Completion
                    raw_completion = sarvam_service.generate_chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.75
                    )
                    
                    # 3. Parse Screenplay
                    story_data = StoryEngine.parse_story_response(raw_completion)
                    st.session_state.current_story = story_data
                    
                    # 4. Synthesize Audio
                    voice_script = story_data.get("voice_script", "")
                    if voice_script:
                        with st.spinner(f"Sarvam Bulbul v3 ({selected_speaker}) is narrating the screenplay..."):
                            audio_b64 = sarvam_service.synthesize_speech(
                                text=voice_script,
                                speaker=selected_speaker,
                                language_code=selected_lang
                            )
                            st.session_state.story_audio_b64 = audio_b64
                            
                    st.session_state.chat_history = []
                    st.success("Screenplay and spoken narration ready!")
                except Exception as e:
                    st.error(f"Generation Error: {e}")

# Right Column: Theater & Voice Screenplay
with col_right:
    st.markdown("### 🎭 Step 2: The Stage & Voice Narrator")
    
    if st.session_state.current_story is None:
        st.markdown(
            """
            <div class="glass-panel" style="text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🎭</div>
                <h3>The Stage is Quiet</h3>
                <p style="color: #94a3b8;">Select a scenario or paste news on the left, then click <strong>Unveil the Plot</strong> to hear the untold story behind the headlines.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        story = st.session_state.current_story
        
        # Centered Voice Narrator Console with Light Surrounding Circle
        st.markdown(
            f"""
            <div class="voice-center-container">
                <div class="play-surround-halo">
                    🎙️
                </div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #ffffff;">
                    Cinematic Voice Narration
                </div>
                <div class="narrator-badge">
                    Voice Actor: {selected_speaker.capitalize()} • Bulbul v3
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Audio Player
        if st.session_state.story_audio_b64:
            audio_bytes = base64.b64decode(st.session_state.story_audio_b64)
            st.audio(audio_bytes, format="audio/wav", autoplay=True)
            
            st.download_button(
                label="💾 Download Voice Narration (.wav)",
                data=audio_bytes,
                file_name=f"NewStory-{int(time.time())}.wav",
                mime="audio/wav",
                use_container_width=True
            )

        # Headline & Logline
        st.markdown(f'<div class="badge-purple">"{story.get("logline", "")}"</div>', unsafe_allow_html=True)
        st.markdown(f"## {story.get('headline', 'The Hidden Chronicle')}")
        
        # Covert Agenda
        st.markdown(
            f"""
            <div class="glass-agenda">
                <div class="badge-gold">🎯 The Covert Agenda (Behind the Curtain)</div>
                <p style="margin-top: 0.35rem; color: #f8fafc; font-size: 0.95rem;">{story.get('hidden_agenda', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Key Players Grid
        st.markdown("#### 👥 The Chessboard: Key Players & Stakes")
        players = story.get("key_players", [])
        if players:
            cols = st.columns(min(len(players), 3))
            for i, p in enumerate(players):
                with cols[i % len(cols)]:
                    st.markdown(
                        f"""
                        <div class="glass-panel" style="padding: 1rem;">
                            <strong style="color: #ffffff; font-size: 1rem;">{p.get('name')}</strong><br>
                            <span style="color: #38bdf8; font-size: 0.78rem; font-family: monospace;">Role: {p.get('role')}</span>
                            <p style="color: #94a3b8; font-size: 0.82rem; margin-top: 0.35rem;">{p.get('secret_stake')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Acts
        st.markdown("#### 📜 The Three Dramatic Acts")
        for act in story.get("acts", []):
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 3px solid #38bdf8; padding: 1rem 1.25rem;">
                    <span style="color: #38bdf8; font-weight: 700;">{act.get('act_title')}</span>
                    <p style="color: #cbd5e1; font-size: 0.9rem; margin-top: 0.35rem; line-height: 1.6;">{act.get('content')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Master Voice Script
        with st.expander("🎙️ View Master Spoken Script"):
            st.info(story.get("voice_script", ""))

        st.markdown("---")

        # Jargon Buster Section
        st.markdown("### 💡 Market, Business & Political Jargon Buster")
        st.caption("Complex terms detected in this dispatch, translated into plain-English analogies with voice audio.")
        
        detected_terms = story.get("complex_terms", [])
        if detected_terms:
            for t in detected_terms:
                term_name = t.get("term", "")
                with st.container():
                    st.markdown(
                        f"""
                        <div class="glass-term">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: #ffffff; font-size: 1.05rem;">{term_name}</strong>
                                <span class="badge-purple">{t.get('category', '📈 Concept')}</span>
                            </div>
                            <p style="color: #e2e8f0; font-size: 0.88rem; margin: 0.4rem 0;">{t.get('simple_definition', '')}</p>
                            <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; padding: 0.45rem 0.65rem; border-radius: 0 6px 6px 0; font-size: 0.82rem; color: #fde68a;">
                                💡 <strong>Analogy:</strong> {t.get('eli5_analogy', '')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # On-Demand Spoken Voice for Term
                    if st.button(f"🔊 Listen to Explanation of '{term_name}'", key=f"btn_listen_{term_name}"):
                        with st.spinner(f"Synthesizing explanation for '{term_name}'..."):
                            try:
                                term_res = sarvam_service.explain_term(
                                    term=term_name,
                                    context=t.get("simple_definition"),
                                    speaker=selected_speaker,
                                    language_code=selected_lang
                                )
                                if term_res.get("audio_base64"):
                                    t_audio = base64.b64decode(term_res["audio_base64"])
                                    st.audio(t_audio, format="audio/wav", autoplay=True)
                            except Exception as term_err:
                                st.error(f"Error: {term_err}")

        # On-Demand Term Search
        st.markdown("##### 🔍 Decode Any Custom Concept")
        col_term_in, col_term_btn = st.columns([3, 1])
        with col_term_in:
            custom_term = st.text_input(
                "Search term:",
                placeholder="e.g. Quantitative Easing, Short Squeeze, Lithography, Margin Call...",
                label_visibility="collapsed"
            )
        with col_term_btn:
            btn_decode = st.button("⚡ Decode", use_container_width=True)

        if btn_decode and custom_term:
            with st.spinner(f"Decoding and voicing '{custom_term}'..."):
                try:
                    decoded = sarvam_service.explain_term(
                        term=custom_term,
                        context=story.get("headline"),
                        speaker=selected_speaker,
                        language_code=selected_lang
                    )
                    st.markdown(
                        f"""
                        <div class="glass-term" style="border-color: #06b6d4;">
                            <strong style="color: #ffffff; font-size: 1.05rem;">{decoded.get('term')}</strong> 
                            <span class="badge-purple">{decoded.get('category')}</span>
                            <p style="color: #f1f5f9; font-size: 0.88rem; margin: 0.4rem 0;">{decoded.get('simple_definition')}</p>
                            <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; padding: 0.45rem; font-size: 0.82rem; color: #fde68a;">
                                💡 <strong>Analogy:</strong> {decoded.get('eli5_analogy')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if decoded.get("audio_base64"):
                        st.audio(base64.b64decode(decoded["audio_base64"]), format="audio/wav", autoplay=True)
                except Exception as decode_err:
                    st.error(f"Decode Error: {decode_err}")

        st.markdown("---")

        # Step 3: Interrogate the Narrator (Interactive Agent)
        st.markdown("### 💬 Step 3: Interrogate the Narrator")
        st.caption("Ask questions about covert incentives, follow the money trail, or get translations.")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "audio_b64" in msg and msg["audio_b64"]:
                    st.audio(base64.b64decode(msg["audio_b64"]), format="audio/wav")

        user_q = st.chat_input("Ask the narrator (e.g. 'Who funded this?' or 'What happens next?')...")
        if user_q:
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.write(user_q)

            with st.chat_message("assistant"):
                with st.spinner("The narrator is analyzing the question..."):
                    try:
                        story_ctx = f"{story.get('headline')}\n{story.get('hidden_agenda')}\n{story.get('voice_script')}"
                        ans_res = sarvam_service.conversational_agent_turn(
                            story_context=story_ctx,
                            user_question=user_q,
                            conversation_history=st.session_state.chat_history,
                            speaker=selected_speaker,
                            language_code=selected_lang
                        )
                        answer_text = ans_res["answer_text"]
                        ans_audio_b64 = ans_res.get("audio_base64")
                        
                        st.write(answer_text)
                        if ans_audio_b64:
                            st.audio(base64.b64decode(ans_audio_b64), format="audio/wav", autoplay=True)

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer_text,
                            "audio_b64": ans_audio_b64
                        })
                    except Exception as chat_err:
                        st.error(f"Agent Error: {chat_err}")
