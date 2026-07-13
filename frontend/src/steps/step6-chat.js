// src/steps/step6-chat.js
import { postJSON, postFile, escapeHtml } from '../api.js';
import { state } from '../state.js';

const QUICK_PROMPTS = [
  "What are good protein sources for vegetarians?",
  "How to reduce sodium in my diet?",
  "Suggest a healthy Indian breakfast",
  "How can I replace paneer in my meal plan?",
  "Make tomorrow's lunch lower in calories",
  "Explain my daily micronutrient targets"
];

export function renderChat(root) {
  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <h2 class="step-header">💬 AI Nutrition Coach</h2>
    <p class="step-description">Ask any questions about ingredients, recipe adjustments, daily routines, or ICMR guidelines.</p>

    <!-- Quick Prompts Chips -->
    <div class="section-card" style="padding:1rem;">
      <p style="font-size:0.8rem; text-transform:uppercase; color:var(--text-muted); font-weight:600; margin-bottom:0.4rem;">💡 Quick Questions</p>
      <div id="quickPromptChips" style="display:flex; flex-wrap:wrap; gap:0.4rem;">
        ${QUICK_PROMPTS.map(p => `<span class="chip prompt-chip">${escapeHtml(p)}</span>`).join('')}
      </div>
    </div>

    <!-- Chat container -->
    <div class="section-card chat-container" style="padding:0;">
      <div class="chat-messages" id="chatMessages"></div>
      
      <!-- TTS & Options Panel -->
      <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 1rem; border-top:1px solid var(--border-subtle); background:rgba(255,255,255,0.01);">
        <div style="display:flex; align-items:center; gap:0.8rem; font-size:0.85rem;">
          <label style="display:inline-flex; align-items:center; gap:0.3rem; cursor:pointer;">
            <input type="checkbox" id="ttsToggle" ${state.ttsEnabled ? 'checked' : ''} /> 🔊 Auto-Speak
          </label>
          <button class="btn btn-secondary btn-sm" id="speakLastBtn" style="padding: 0.2rem 0.5rem;">🗣️ Read Last</button>
          <button class="btn btn-secondary btn-sm" id="stopSpeakBtn" style="padding: 0.2rem 0.5rem;">🛑 Stop</button>
        </div>
        
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <select id="chatLanguage" style="width:auto; padding:0.3rem 1.8rem 0.3rem 0.5rem; font-size:0.8rem;">
            <option value="">🌐 Auto-detect Language</option>
            <option value="en">English</option>
            <option value="hi">Hindi (हिंदी)</option>
            <option value="hinglish">Hinglish</option>
          </select>
        </div>
      </div>

      <!-- File Attachment Preview -->
      <div id="attachmentPreview" style="padding:0.5rem 1rem; display:none; border-top:1px solid var(--border-subtle); background:rgba(244,114,182,0.04); font-size:0.85rem; color:var(--accent); align-items:center; gap:0.5rem;">
        <span>📎 Attached: <strong id="attachedFileName"></strong></span>
        <button class="btn btn-secondary btn-sm" id="removeAttachmentBtn" style="padding:0 0.4rem; font-size:0.75rem;">Remove</button>
      </div>

      <!-- Input Bar -->
      <div class="chat-input-bar">
        <!-- Image/File Attachment Button -->
        <label for="chatAttachFile" class="btn btn-secondary" style="padding:0.6rem; border-radius:50%; width:38px; height:38px; justify-content:center;">
          📎
          <input type="file" id="chatAttachFile" accept="image/*,.pdf" style="display:none;" />
        </label>
        
        <!-- Voice Input button -->
        <button class="btn btn-secondary" id="voiceRecordBtn" style="padding:0.6rem; border-radius:50%; width:38px; height:38px; justify-content:center;">
          🎙️
        </button>

        <input type="text" id="chatInput" placeholder="Ask your coach anything..." />
        <button class="btn btn-primary" id="chatSendBtn">Send →</button>
      </div>
    </div>

    <!-- Warnings / Actions Container -->
    <div id="chatSuggestions" style="margin-top:1rem;"></div>
  `;
  root.appendChild(wrapper);

  const messagesDiv = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  const fileInput = document.getElementById('chatAttachFile');
  const previewDiv = document.getElementById('attachmentPreview');
  const previewName = document.getElementById('attachedFileName');
  const removeAttachBtn = document.getElementById('removeAttachmentBtn');
  const voiceBtn = document.getElementById('voiceRecordBtn');
  const languageSelect = document.getElementById('chatLanguage');
  const ttsToggle = document.getElementById('ttsToggle');
  const speakLastBtn = document.getElementById('speakLastBtn');
  const stopSpeakBtn = document.getElementById('stopSpeakBtn');

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let attachedFile = null;

  // Initialize TTS configuration
  ttsToggle.addEventListener('change', (e) => {
    state.ttsEnabled = e.target.checked;
  });

  speakLastBtn.addEventListener('click', speakLastMessage);
  stopSpeakBtn.addEventListener('click', () => {
    window.speechSynthesis.cancel();
  });

  // Load chat history
  renderHistory();

  // Quick prompt chips
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.textContent;
      chatInput.focus();
    });
  });

  // Handle file selection
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      attachedFile = fileInput.files[0];
      previewName.textContent = attachedFile.name;
      previewDiv.style.display = 'flex';
    }
  });

  removeAttachBtn.addEventListener('click', () => {
    attachedFile = null;
    fileInput.value = '';
    previewDiv.style.display = 'none';
  });

  // Send message
  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Voice recording
  voiceBtn.addEventListener('click', async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          voiceBtn.textContent = '🎙️';
          voiceBtn.classList.remove('btn-danger');
          
          // Call voice transcription
          chatInput.placeholder = 'Transcribing voice...';
          const file = new File([audioBlob], 'voice.wav', { type: 'audio/wav' });
          try {
            const resp = await postFile('/api/voice/transcribe', file);
            if (resp && resp.transcript) {
              chatInput.value = resp.transcript;
            }
          } catch (err) {
            console.error('Transcription failed:', err);
          } finally {
            chatInput.placeholder = 'Ask your coach anything...';
          }
        };

        mediaRecorder.start();
        isRecording = true;
        voiceBtn.textContent = '⏹️';
        voiceBtn.classList.add('btn-danger');
      } catch (err) {
        alert('Voice recording permission denied or not supported.');
      }
    } else {
      mediaRecorder.stop();
      isRecording = false;
    }
  });

  function renderHistory() {
    messagesDiv.innerHTML = '';
    
    if (state.chatMessages.length === 0) {
      // Add initial greeting from Assistant
      state.chatMessages.push({
        role: 'assistant',
        content: "Hello! I am your AI Nutrition Coach. How can I help you adjust your meal plan, replace ingredients, or explain your nutrient targets today?"
      });
    }

    state.chatMessages.forEach(msg => {
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`;
      bubble.innerHTML = escapeHtml(msg.content).replace(/\n/g, '<br>');
      messagesDiv.appendChild(bubble);
    });

    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text && !attachedFile) return;

    // Add user message locally
    let userMsg = text;
    if (attachedFile) {
      userMsg = text ? `[Attached: ${attachedFile.name}] ${text}` : `[Attached: ${attachedFile.name}]`;
    }

    state.chatMessages.push({ role: 'user', content: userMsg });
    renderHistory();
    chatInput.value = '';

    // Show typing indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble assistant';
    typingBubble.innerHTML = '<span class="spinner" style="width:12px; height:12px;"></span> Coach is writing...';
    messagesDiv.appendChild(typingBubble);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    let finalQueryText = text;

    // Process image/document upload first
    if (attachedFile) {
      try {
        const attachResp = await postFile('/api/chat-image', attachedFile);
        if (attachResp && attachResp.summary) {
          finalQueryText = `[File summary: ${attachResp.summary}] ${text}`;
        }
      } catch (err) {
        console.error('Attachment analysis failed:', err);
      } finally {
        // Clear attachment preview
        attachedFile = null;
        fileInput.value = '';
        previewDiv.style.display = 'none';
      }
    }

    try {
      const payload = {
        user_id: state.userId,
        message: finalQueryText || 'Describe the attached file.',
        preferred_language: languageSelect.value || null,
        health_profile: state.healthProfile,
        preference_profile: state.preferenceProfile,
        daily_targets: state.nutrientResponse?.daily_targets || null,
        meal_plan: state.mealPlanResponse || null,
        grocery_list: state.groceryResponse || null
      };

      // Call chatbot API
      const resp = await postJSON('/chat', payload);
      typingBubble.remove();

      if (resp && resp.answer) {
        state.chatMessages.push({ role: 'assistant', content: resp.answer });
        renderHistory();

        // Render warnings & suggested actions
        renderSuggestions(resp);

        // Speech synthesis if enabled
        if (state.ttsEnabled) {
          speakText(resp.answer, resp.detected_language || 'English');
        }
      } else {
        throw new Error('Invalid response');
      }
    } catch (e) {
      typingBubble.remove();
      state.chatMessages.push({ role: 'assistant', content: `Sorry, I encountered an error: ${e.message}` });
      renderHistory();
    }
  }

  function renderSuggestions(resp) {
    const sugDiv = document.getElementById('chatSuggestions');
    sugDiv.innerHTML = '';

    const warnings = resp.warnings || [];
    const actions = resp.suggested_actions || [];

    if (warnings.length > 0 || actions.length > 0) {
      const card = document.createElement('div');
      card.className = 'section-card';
      card.innerHTML = '<h3>⚠️ Guidelines & Suggested Actions</h3>';

      warnings.forEach(w => {
        card.innerHTML += `<div class="alert alert-warning">${escapeHtml(w)}</div>`;
      });

      if (actions.length > 0) {
        const actionGrid = document.createElement('div');
        actionGrid.style.display = 'flex';
        actionGrid.style.flexWrap = 'wrap';
        actionGrid.style.gap = '0.5rem';
        actionGrid.style.marginTop = '0.8rem';
        
        actions.forEach(act => {
          const chip = document.createElement('span');
          chip.className = 'chip';
          chip.textContent = act;
          chip.addEventListener('click', () => {
            chatInput.value = act;
            chatInput.focus();
          });
          actionGrid.appendChild(chip);
        });
        card.appendChild(actionGrid);
      }
      sugDiv.appendChild(card);
    }
  }

  function speakText(text, language) {
    window.speechSynthesis.cancel();
    
    // Clean markdown characters so TTS doesn't read them aloud (e.g. asterisks, hashes)
    const cleanText = text
      .replace(/\*\*+/g, '')        // bold asterisks
      .replace(/\*+/g, '')         // bullet asterisks or italics
      .replace(/#+/g, '')          // headers
      .replace(/`+/g, '')          // code ticks
      .replace(/__+/g, '')         // underscores
      .replace(/_+/g, '')
      .replace(/-\s+/g, '')        // hyphen bullets
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // replace markdown links with just their text
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Choose appropriate voice
    const voices = window.speechSynthesis.getVoices();
    let selectedVoice = null;

    if (language.toLowerCase().includes('hindi') || language.toLowerCase().includes('hinglish')) {
      selectedVoice = voices.find(v => v.lang.startsWith('hi-'));
    } else {
      selectedVoice = voices.find(v => v.lang.startsWith('en-IN') || v.lang.startsWith('en-'));
    }

    if (selectedVoice) utterance.voice = selectedVoice;
    window.speechSynthesis.speak(utterance);
  }

  function speakLastMessage() {
    const assistantMsgs = state.chatMessages.filter(m => m.role === 'assistant');
    if (assistantMsgs.length > 0) {
      const lastMsg = assistantMsgs[assistantMsgs.length - 1];
      speakText(lastMsg.content, 'English');
    }
  }
}
