/**
 * NewStory: Current Affairs Plot Unveiler
 * Client Application Logic
 */

// State
const state = {
  activeTab: 'presets',
  activeMode: 'noir',
  presets: [],
  selectedPreset: null,
  selectedImageFile: null,
  currentAudioB64: null,
  audioElement: new Audio(),
  audioContext: null,
  analyser: null,
  sourceNode: null,
  canvas: null,
  canvasCtx: null,
  animationFrameId: null,
  currentStory: null,
  chatHistory: [],
  isRecordingIngest: false,
  mediaRecorderIngest: null,
  audioChunksIngest: [],
  isRecordingChat: false,
  mediaRecorderChat: null,
  audioChunksChat: [],
};

// DOM Elements
const el = {
  tabBtns: document.querySelectorAll('.tab-btn'),
  tabContents: document.querySelectorAll('.tab-content'),
  presetContainer: document.getElementById('preset-container'),
  rawInputText: document.getElementById('raw-input-text'),
  urlInput: document.getElementById('url-input'),
  btnFetchUrl: document.getElementById('btn-fetch-url'),
  urlStatus: document.getElementById('url-status'),
  btnMicIngest: document.getElementById('btn-mic-ingest'),
  voiceSttPreview: document.getElementById('voice-stt-preview'),
  modeBtns: document.querySelectorAll('.mode-btn'),
  speakerSelect: document.getElementById('speaker-select'),
  languageSelect: document.getElementById('language-select'),
  customTwist: document.getElementById('custom-twist'),
  btnGenerate: document.getElementById('btn-generate'),
  loadingSpinner: document.getElementById('loading-spinner'),
  loadingStepText: document.getElementById('loading-step-text'),
  // Theater & Narrator Console
  theaterCard: document.getElementById('theater-card'),
  btnPlayPause: document.getElementById('btn-play-pause'),
  playIcon: document.getElementById('play-icon'),
  voiceMeta: document.getElementById('voice-meta'),
  narratorSub: document.getElementById('narrator-sub'),
  statusIndicator: document.getElementById('status-indicator'),
  waveformCanvas: document.getElementById('waveform-canvas'),
  visualizerIdleText: document.getElementById('visualizer-idle-text'),
  seekSlider: document.getElementById('seek-slider'),
  currTime: document.getElementById('curr-time'),
  totalTime: document.getElementById('total-time'),
  btnDownloadAudio: document.getElementById('btn-download-audio'),
  // Image OCR
  imageDropzone: document.getElementById('image-dropzone'),
  imageFileInput: document.getElementById('image-file-input'),
  dropzonePrompt: document.getElementById('dropzone-prompt'),
  imagePreviewContainer: document.getElementById('image-preview-container'),
  imagePreview: document.getElementById('image-preview'),
  btnRemoveImage: document.getElementById('btn-remove-image'),
  btnOcrExtract: document.getElementById('btn-ocr-extract'),
  ocrStatus: document.getElementById('ocr-status'),
  // Story Display
  emptyState: document.getElementById('empty-state'),
  storyContent: document.getElementById('story-content'),
  storyHeadline: document.getElementById('story-headline'),
  storyLogline: document.getElementById('story-logline'),
  storyAgenda: document.getElementById('story-agenda'),
  playersContainer: document.getElementById('players-container'),
  actsContainer: document.getElementById('acts-container'),
  storyVoiceScript: document.getElementById('story-voice-script'),
  btnReplayScript: document.getElementById('btn-replay-script'),
  // Jargon Buster
  termsContainer: document.getElementById('terms-container'),
  customTermInput: document.getElementById('custom-term-input'),
  btnDecodeTerm: document.getElementById('btn-decode-term'),
  decodedTermResult: document.getElementById('decoded-term-result'),
  quickTermPills: document.querySelectorAll('.quick-term-pill'),
  // QA
  qaCard: document.getElementById('qa-card'),
  chatStream: document.getElementById('chat-stream'),
  chatInput: document.getElementById('chat-input'),
  btnSendQuestion: document.getElementById('btn-send-question'),
  btnMicQuestion: document.getElementById('btn-mic-question'),
};

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  initCanvas();
  setupEventListeners();
  await loadConfigAndPresets();
});

// Setup Audio Visualizer Canvas
function initCanvas() {
  if (!el.waveformCanvas) return;
  state.canvas = el.waveformCanvas;
  state.canvasCtx = state.canvas.getContext('2d');
  drawIdleVisualizer();
}

function initWebAudio() {
  if (state.audioContext) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    state.audioContext = new AudioContext();
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 128;
    state.sourceNode = state.audioContext.createMediaElementSource(state.audioElement);
    state.sourceNode.connect(state.analyser);
    state.analyser.connect(state.audioContext.destination);
  } catch (err) {
    console.warn("Web Audio API not supported or autoplay restricted:", err);
  }
}

function drawIdleVisualizer() {
  if (!state.canvas || !state.canvasCtx) return;
  const ctx = state.canvasCtx;
  const width = state.canvas.width;
  const height = state.canvas.height;

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, height / 2);
  ctx.lineTo(width, height / 2);
  ctx.stroke();
}

function renderVisualizerLoop() {
  if (!state.analyser || !state.canvas || !state.canvasCtx) return;

  const bufferLength = state.analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  state.analyser.getByteFrequencyData(dataArray);

  const ctx = state.canvasCtx;
  const width = state.canvas.width;
  const height = state.canvas.height;

  ctx.clearRect(0, 0, width, height);

  const barWidth = (width / bufferLength) * 2.2;
  let barHeight;
  let x = 0;

  for (let i = 0; i < bufferLength; i++) {
    barHeight = (dataArray[i] / 255) * height * 0.9;

    const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
    gradient.addColorStop(0, '#22d3ee');
    gradient.addColorStop(0.5, '#06b6d4');
    gradient.addColorStop(1, '#8b5cf6');

    ctx.fillStyle = gradient;
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#06b6d4';
    
    const y = (height - barHeight) / 2;
    ctx.fillRect(x, y, barWidth - 2, barHeight);

    x += barWidth;
  }

  if (!state.audioElement.paused) {
    state.animationFrameId = requestAnimationFrame(renderVisualizerLoop);
  } else {
    drawIdleVisualizer();
    if (el.visualizerIdleText) el.visualizerIdleText.classList.remove('hidden');
  }
}

// Load Presets & Server Config
async function loadConfigAndPresets() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    state.presets = data.presets || [];
    renderPresets();
  } catch (err) {
    console.error("Failed to load config:", err);
  }
}

function renderPresets() {
  el.presetContainer.innerHTML = '';
  state.presets.forEach((preset, idx) => {
    const card = document.createElement('div');
    card.className = `preset-card ${idx === 0 ? 'active' : ''}`;
    card.innerHTML = `
      <div class="preset-category">${preset.category} • ${preset.source}</div>
      <div class="preset-title">${preset.title}</div>
      <div class="preset-desc">${preset.summary}</div>
    `;
    card.addEventListener('click', () => {
      document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      state.selectedPreset = preset;
      el.rawInputText.value = preset.text.trim();
    });
    el.presetContainer.appendChild(card);
  });

  if (state.presets.length > 0) {
    state.selectedPreset = state.presets[0];
    el.rawInputText.value = state.presets[0].text.trim();
  }
}

// Setup Listeners
function setupEventListeners() {
  // Tabs
  el.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      el.tabBtns.forEach(b => b.classList.remove('active'));
      el.tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      document.getElementById(`tab-${tabId}`).classList.add('active');
      state.activeTab = tabId;
    });
  });

  // Story Modes
  el.modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      el.modeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeMode = btn.getAttribute('data-mode');
    });
  });

  // URL Fetching
  el.btnFetchUrl.addEventListener('click', handleUrlFetch);

  // Voice Ingestion Mic
  el.btnMicIngest.addEventListener('click', toggleVoiceIngest);

  // Newspaper Image OCR
  if (el.imageDropzone) {
    el.imageDropzone.addEventListener('click', () => el.imageFileInput.click());
    el.imageDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      el.imageDropzone.classList.add('dragover');
    });
    el.imageDropzone.addEventListener('dragleave', () => el.imageDropzone.classList.remove('dragover'));
    el.imageDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      el.imageDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleImageFile(e.dataTransfer.files[0]);
      }
    });
  }
  if (el.imageFileInput) {
    el.imageFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleImageFile(e.target.files[0]);
      }
    });
  }
  if (el.btnRemoveImage) {
    el.btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      resetImageInput();
    });
  }
  if (el.btnOcrExtract) {
    el.btnOcrExtract.addEventListener('click', handleOcrExtract);
  }

  // Jargon Buster Custom Decoder
  if (el.btnDecodeTerm) {
    el.btnDecodeTerm.addEventListener('click', () => handleDecodeCustomTerm());
  }
  if (el.customTermInput) {
    el.customTermInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleDecodeCustomTerm();
    });
  }
  if (el.quickTermPills) {
    el.quickTermPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const term = pill.getAttribute('data-term');
        el.customTermInput.value = term;
        handleDecodeCustomTerm(term);
      });
    });
  }

  // Generate Story
  el.btnGenerate.addEventListener('click', handleGenerateStory);

  // Audio Playback
  el.btnPlayPause.addEventListener('click', toggleAudioPlay);
  el.audioElement.addEventListener('timeupdate', updateAudioProgress);
  el.audioElement.addEventListener('ended', onAudioEnded);
  el.audioElement.addEventListener('play', () => {
    initWebAudio();
    if (state.audioContext && state.audioContext.state === 'suspended') {
      state.audioContext.resume();
    }
    el.playIcon.textContent = '⏸';
    el.btnPlayPause.classList.add('playing');
    if (el.theaterCard) el.theaterCard.classList.add('active-playing');
    if (el.narratorSub) el.narratorSub.textContent = 'Playing narration... (Click to pause)';
    if (el.visualizerIdleText) el.visualizerIdleText.classList.add('hidden');
    renderVisualizerLoop();
  });
  el.audioElement.addEventListener('pause', () => {
    el.playIcon.textContent = '▶';
    el.btnPlayPause.classList.remove('playing');
    if (el.theaterCard) el.theaterCard.classList.remove('active-playing');
    if (el.narratorSub) el.narratorSub.textContent = 'Paused (Click to resume)';
  });

  if (el.seekSlider) {
    el.seekSlider.addEventListener('input', (e) => {
      const seekTime = (e.target.value / 100) * state.audioElement.duration;
      state.audioElement.currentTime = seekTime;
    });
  }

  if (el.btnDownloadAudio) {
    el.btnDownloadAudio.addEventListener('click', downloadCurrentAudio);
  }
  if (el.btnReplayScript) {
    el.btnReplayScript.addEventListener('click', () => {
      state.audioElement.currentTime = 0;
      state.audioElement.play();
    });
  }

  // QA Interrogation Chat
  el.btnSendQuestion.addEventListener('click', handleSendQuestion);
  el.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSendQuestion();
  });
  el.btnMicQuestion.addEventListener('click', toggleVoiceChat);
}

// URL Fetch Handler
async function handleUrlFetch() {
  const url = el.urlInput.value.trim();
  if (!url) {
    el.urlStatus.textContent = 'Please enter a valid URL.';
    el.urlStatus.style.color = '#f87171';
    return;
  }

  el.btnFetchUrl.disabled = true;
  el.urlStatus.textContent = 'Fetching and cleaning article...';
  el.urlStatus.style.color = 'var(--primary)';

  try {
    const res = await fetch('/api/extract-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to fetch article');
    }

    const data = await res.json();
    el.rawInputText.value = data.text;
    el.urlStatus.textContent = `Extracted: "${data.title}" (${data.text.length} chars)`;
    el.urlStatus.style.color = 'var(--accent-emerald)';

    // Switch to text tab to preview
    document.querySelector('.tab-btn[data-tab="text"]').click();
  } catch (err) {
    el.urlStatus.textContent = `Error: ${err.message}`;
    el.urlStatus.style.color = '#f87171';
  } finally {
    el.btnFetchUrl.disabled = false;
  }
}

// Voice Ingestion via Sarvam Saaras STT
async function toggleVoiceIngest() {
  if (!state.isRecordingIngest) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.audioChunksIngest = [];
      state.mediaRecorderIngest = new MediaRecorder(stream);

      state.mediaRecorderIngest.ondataavailable = (e) => {
        if (e.data.size > 0) state.audioChunksIngest.push(e.data);
      };

      state.mediaRecorderIngest.onstop = async () => {
        const audioBlob = new Blob(state.audioChunksIngest, { type: 'audio/wav' });
        await transcribeAndSetIngest(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      state.mediaRecorderIngest.start();
      state.isRecordingIngest = true;
      el.btnMicIngest.classList.add('recording');
      el.btnMicIngest.querySelector('.mic-label').textContent = 'Stop Dictating';
      el.voiceSttPreview.textContent = 'Listening to your voice via microphone...';
      el.voiceSttPreview.classList.remove('empty');
    } catch (err) {
      alert("Microphone access denied or not available: " + err.message);
    }
  } else {
    state.mediaRecorderIngest.stop();
    state.isRecordingIngest = false;
    el.btnMicIngest.classList.remove('recording');
    el.btnMicIngest.querySelector('.mic-label').textContent = 'Hold to Speak';
    el.voiceSttPreview.textContent = 'Transcribing with Sarvam Saaras STT...';
  }
}

async function transcribeAndSetIngest(blob) {
  const formData = new FormData();
  formData.append('file', blob, 'ingest.wav');
  formData.append('language_code', el.languageSelect.value);

  try {
    const res = await fetch('/api/transcribe', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Transcription failed');
    const data = await res.json();
    el.voiceSttPreview.textContent = `Transcribed: "${data.transcript}"`;
    el.rawInputText.value = data.transcript;
  } catch (err) {
    el.voiceSttPreview.textContent = `STT Error: ${err.message}`;
  }
}

// Newspaper Image OCR Handlers
function handleImageFile(file) {
  if (!file.type.startsWith('image/')) {
    alert("Please select a valid image file (PNG, JPG, WEBP).");
    return;
  }
  state.selectedImageFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    el.imagePreview.src = e.target.result;
    el.dropzonePrompt.classList.add('hidden');
    el.imagePreviewContainer.classList.remove('hidden');
    el.btnOcrExtract.disabled = false;
    el.ocrStatus.textContent = `Image ready: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    el.ocrStatus.style.color = 'var(--text-muted)';
  };
  reader.readAsDataURL(file);
}

function resetImageInput() {
  state.selectedImageFile = null;
  el.imageFileInput.value = '';
  el.imagePreview.src = '';
  el.imagePreviewContainer.classList.add('hidden');
  el.dropzonePrompt.classList.remove('hidden');
  el.btnOcrExtract.disabled = true;
  el.ocrStatus.textContent = '';
}

async function handleOcrExtract() {
  if (!state.selectedImageFile) return;

  el.btnOcrExtract.disabled = true;
  el.ocrStatus.textContent = 'Digitizing newspaper clipping with Sarvam Doc AI...';
  el.ocrStatus.style.color = 'var(--primary)';

  const formData = new FormData();
  formData.append('file', state.selectedImageFile);

  try {
    const res = await fetch('/api/ocr-newspaper', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'OCR extraction failed');
    }

    const data = await res.json();
    el.rawInputText.value = data.extracted_text;
    el.ocrStatus.textContent = `Successfully extracted ${data.character_count || data.extracted_text.length} characters from newspaper photo!`;
    el.ocrStatus.style.color = 'var(--accent-emerald)';

    // Switch to text tab so user sees the extracted article
    document.querySelector('.tab-btn[data-tab="text"]').click();
  } catch (err) {
    el.ocrStatus.textContent = `OCR Error: ${err.message}`;
    el.ocrStatus.style.color = '#f87171';
  } finally {
    el.btnOcrExtract.disabled = false;
  }
}

// Generate Story & Voice
async function handleGenerateStory() {
  let inputText = '';
  if (state.activeTab === 'presets' && state.selectedPreset) {
    inputText = state.selectedPreset.text;
  } else {
    inputText = el.rawInputText.value.trim();
  }

  if (!inputText || inputText.length < 20) {
    alert("Please provide at least 20 characters of news or select a preset.");
    return;
  }

  el.btnGenerate.disabled = true;
  el.loadingSpinner.classList.remove('hidden');
  el.loadingStepText.textContent = 'Sarvam 105B is analyzing covert agendas and power moves...';

  const payload = {
    text: inputText,
    style: state.activeMode,
    language_code: el.languageSelect.value,
    speaker: el.speakerSelect.value,
    custom_twist: el.customTwist.value.trim() || null,
    pace: 1.0
  };

  try {
    const res = await fetch('/api/generate-story', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Story generation failed');
    }

    const data = await res.json();
    displayStory(data.story);
    
    if (data.audio_base64) {
      loadAndPlayAudio(data.audio_base64, data.speaker);
    }

    // Enable QA Card
    el.qaCard.classList.remove('hidden');
    state.chatHistory = [];
    el.chatStream.innerHTML = `
      <div class="chat-msg system">
        <span>Story generated! Ask me any follow-up question to probe the narrative or speak via mic.</span>
      </div>
    `;
  } catch (err) {
    alert("Generation Error: " + err.message);
  } finally {
    el.btnGenerate.disabled = false;
    el.loadingSpinner.classList.add('hidden');
  }
}

// Display Story Screenplay
function displayStory(story) {
  state.currentStory = story;
  el.emptyState.classList.add('hidden');
  el.storyContent.classList.remove('hidden');

  el.storyHeadline.textContent = story.headline || 'The Hidden Chronicle';
  el.storyLogline.textContent = `"${story.logline || ''}"`;
  el.storyAgenda.textContent = story.hidden_agenda || '';

  // Players
  el.playersContainer.innerHTML = '';
  if (story.key_players && Array.isArray(story.key_players)) {
    story.key_players.forEach(player => {
      const card = document.createElement('div');
      card.className = 'player-card';
      card.innerHTML = `
        <div class="player-name">${player.name}</div>
        <div class="player-role">Stakes: ${player.role}</div>
        <div class="player-stake">${player.secret_stake}</div>
      `;
      el.playersContainer.appendChild(card);
    });
  }

  // Acts
  el.actsContainer.innerHTML = '';
  if (story.acts && Array.isArray(story.acts)) {
    story.acts.forEach(act => {
      const card = document.createElement('div');
      card.className = 'act-card';
      card.innerHTML = `
        <div class="act-title">${act.act_title}</div>
        <div class="act-content">${act.content}</div>
      `;
      el.actsContainer.appendChild(card);
    });
  }

  // Voice Script
  el.storyVoiceScript.textContent = story.voice_script || '';

  // Render Jargon Buster
  renderJargonBuster(story.complex_terms || []);
}

// Jargon Buster Renderer
function renderJargonBuster(terms) {
  if (!el.termsContainer) return;
  el.termsContainer.innerHTML = '';

  if (!terms || terms.length === 0) {
    el.termsContainer.innerHTML = `
      <div class="empty-terms-msg" style="grid-column: 1 / -1; color: var(--text-dim); font-size: 0.8rem; font-style: italic;">
        No obscure technical jargon detected in this text. Use the decoder box below to query any market, business, or political term!
      </div>
    `;
    return;
  }

  terms.forEach(t => {
    const card = document.createElement('div');
    card.className = 'term-card';
    card.innerHTML = `
      <div class="term-header">
        <span class="term-title">${t.term}</span>
        <span class="term-category">${t.category || '📈 Concept'}</span>
      </div>
      <div class="term-def">${t.simple_definition}</div>
      <div class="term-analogy">💡 <strong>Analogy:</strong> ${t.eli5_analogy}</div>
      <button class="btn-listen-term">
        <span>🔊</span> Listen to Explanation
      </button>
    `;

    const btnListen = card.querySelector('.btn-listen-term');
    btnListen.addEventListener('click', async () => {
      btnListen.disabled = true;
      btnListen.innerHTML = '<span>⏳</span> Synthesizing...';
      try {
        const res = await fetch('/api/explain-term', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            term: t.term,
            context: t.simple_definition,
            speaker: el.speakerSelect.value,
            language_code: el.languageSelect.value
          })
        });
        const data = await res.json();
        if (data.audio_base64) {
          loadAndPlayAudio(data.audio_base64, data.speaker);
        }
      } catch (err) {
        alert("Failed to synthesize term: " + err.message);
      } finally {
        btnListen.disabled = false;
        btnListen.innerHTML = '<span>🔊</span> Listen to Explanation';
      }
    });

    el.termsContainer.appendChild(card);
  });
}

// Custom Term Decoder Handler
async function handleDecodeCustomTerm(termOverride = null) {
  const term = termOverride || (el.customTermInput ? el.customTermInput.value.trim() : '');
  if (!term) return;

  if (el.btnDecodeTerm) el.btnDecodeTerm.disabled = true;
  if (el.decodedTermResult) {
    el.decodedTermResult.classList.remove('hidden');
    el.decodedTermResult.innerHTML = `
      <div style="font-size: 0.82rem; color: var(--primary);">
        ⚡ Sarvam AI is decoding <strong>"${term}"</strong> and synthesizing speech...
      </div>
    `;
  }

  try {
    const res = await fetch('/api/explain-term', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        term: term,
        context: state.currentStory ? state.currentStory.headline : null,
        speaker: el.speakerSelect.value,
        language_code: el.languageSelect.value
      })
    });

    if (!res.ok) throw new Error('Failed to decode term');
    const data = await res.json();

    if (el.decodedTermResult) {
      el.decodedTermResult.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <strong style="color: #ffffff; font-size: 0.95rem;">${data.term}</strong>
          <span class="term-category">${data.category}</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-main); margin-bottom: 0.4rem;">${data.simple_definition}</p>
        <div class="term-analogy" style="margin-bottom: 0.6rem;">💡 <strong>Analogy:</strong> ${data.eli5_analogy}</div>
        <button id="btn-replay-term" class="btn-mini">🔊 Re-listen to Voice Explanation</button>
      `;

      const btnReplay = document.getElementById('btn-replay-term');
      if (btnReplay && data.audio_base64) {
        btnReplay.addEventListener('click', () => {
          loadAndPlayAudio(data.audio_base64, data.speaker);
        });
      }
    }

    if (data.audio_base64) {
      loadAndPlayAudio(data.audio_base64, data.speaker);
    }
  } catch (err) {
    if (el.decodedTermResult) {
      el.decodedTermResult.innerHTML = `<span style="color: #f87171;">Error: ${err.message}</span>`;
    }
  } finally {
    if (el.btnDecodeTerm) el.btnDecodeTerm.disabled = false;
  }
}

// Audio Engine
function loadAndPlayAudio(base64Wav, speakerName) {
  state.currentAudioB64 = base64Wav;
  const audioSrc = `data:audio/wav;base64,${base64Wav}`;
  state.audioElement.src = audioSrc;
  state.audioElement.load();

  if (el.voiceMeta) el.voiceMeta.textContent = `Narrator: ${speakerName || 'Aditya'} (Bulbul v3)`;
  if (el.narratorSub) el.narratorSub.textContent = 'Playing voice narration... (Click to pause)';
  el.btnPlayPause.disabled = false;
  if (el.seekSlider) el.seekSlider.disabled = false;
  if (el.btnDownloadAudio) el.btnDownloadAudio.disabled = false;

  state.audioElement.play().catch(e => {
    console.log("Autoplay blocked, waiting for user click:", e);
    if (el.narratorSub) el.narratorSub.textContent = 'Ready to play (Click button)';
  });
}

function toggleAudioPlay() {
  if (state.audioElement.paused) {
    state.audioElement.play();
  } else {
    state.audioElement.pause();
  }
}

function updateAudioProgress() {
  const current = state.audioElement.currentTime;
  const duration = state.audioElement.duration || 0;
  
  if (el.currTime) el.currTime.textContent = formatTime(current);
  if (el.totalTime) el.totalTime.textContent = formatTime(duration);

  if (duration > 0 && el.seekSlider) {
    el.seekSlider.value = (current / duration) * 100;
  }
}

function onAudioEnded() {
  el.playIcon.textContent = '▶';
  el.btnPlayPause.classList.remove('playing');
  if (el.theaterCard) el.theaterCard.classList.remove('active-playing');
  if (el.narratorSub) el.narratorSub.textContent = 'Narration completed (Click to replay)';
  if (el.seekSlider) el.seekSlider.value = 0;
  if (el.currTime) el.currTime.textContent = '0:00';
  drawIdleVisualizer();
  if (el.visualizerIdleText) el.visualizerIdleText.classList.remove('hidden');
}

function formatTime(secs) {
  if (isNaN(secs)) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function downloadCurrentAudio() {
  if (!state.currentAudioB64) return;
  const link = document.createElement('a');
  link.href = `data:audio/wav;base64,${state.currentAudioB64}`;
  link.download = `NewStory-${Date.now()}.wav`;
  link.click();
}

// QA Interrogation Follow-up
async function handleSendQuestion(textOverride = null) {
  const question = textOverride || el.chatInput.value.trim();
  if (!question) return;

  el.chatInput.value = '';
  appendChatMessage('user', question);

  const storyContext = state.currentStory 
    ? `${state.currentStory.headline}\n${state.currentStory.hidden_agenda}\n${state.currentStory.voice_script}`
    : 'No current story.';

  const payload = {
    story_context: storyContext,
    user_question: question,
    history: state.chatHistory,
    speaker: el.speakerSelect.value,
    language_code: el.languageSelect.value
  };

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Agent failed to reply');
    const data = await res.json();

    appendChatMessage('agent', data.answer_text);
    state.chatHistory.push({ role: 'user', content: question });
    state.chatHistory.push({ role: 'assistant', content: data.answer_text });

    if (data.audio_base64) {
      loadAndPlayAudio(data.audio_base64, data.speaker);
    }
  } catch (err) {
    appendChatMessage('system', `Error: ${err.message}`);
  }
}

function appendChatMessage(role, text) {
  const msg = document.createElement('div');
  msg.className = `chat-msg ${role}`;
  msg.textContent = text;
  el.chatStream.appendChild(msg);
  el.chatStream.scrollTop = el.chatStream.scrollHeight;
}

// Voice Chat Recording
async function toggleVoiceChat() {
  if (!state.isRecordingChat) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.audioChunksChat = [];
      state.mediaRecorderChat = new MediaRecorder(stream);

      state.mediaRecorderChat.ondataavailable = (e) => {
        if (e.data.size > 0) state.audioChunksChat.push(e.data);
      };

      state.mediaRecorderChat.onstop = async () => {
        const audioBlob = new Blob(state.audioChunksChat, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'question.wav');
        formData.append('language_code', el.languageSelect.value);

        try {
          const res = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          if (data.transcript) {
            handleSendQuestion(data.transcript);
          }
        } catch (e) {
          console.error("Voice question STT failed:", e);
        }
        stream.getTracks().forEach(track => track.stop());
      };

      state.mediaRecorderChat.start();
      state.isRecordingChat = true;
      el.btnMicQuestion.classList.add('recording');
    } catch (err) {
      alert("Microphone error: " + err.message);
    }
  } else {
    state.mediaRecorderChat.stop();
    state.isRecordingChat = false;
    el.btnMicQuestion.classList.remove('recording');
  }
}
