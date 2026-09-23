<?php
/**
 * PreciousEdu AI Chatbot - Frontend
 *
 * CONFIGURATION:
 * Once you deploy the backend to Render, paste your Render web service URL below:
 * Example: 'https://using-api-precious-llm.onrender.com'
 * (Leave as is for local development; it will automatically fallback to http://localhost:8000)
 */
$RENDER_BACKEND_URL = 'https://using-api-precious-llm.onrender.com';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PreciousEdu AI Chatbot | 24/7 Study Abroad Assistant</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#f8f6f2;            /* rich warm pearl background */
    --surface:#ffffff;       /* pure card surface */
    --border:#e6e1d8;        /* subtle warm border */
    --border-hover:#d5cebf;
    --text:#1a1816;          /* deep charcoal text */
    --muted:#736d63;         /* refined taupe text */
    --accent:#171513;        /* obsidian primary accent */
    --accent-soft:#f3efe8;   /* bot message surface */
    --whatsapp-green:#25D366;
    --whatsapp-dark:#128C7E;
    --error-bg:#fde8e8;
    --error-text:#9b1c1c;
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  }
  * { box-sizing: border-box; margin:0; padding:0; }
  html, body { height: 100%; width: 100%; }
  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    overflow: hidden;
  }

  /* Full viewport width & height layout */
  .chat-container {
    width: 100vw;
    height: 100vh;
    background: var(--bg);
    display: flex;
    flex-direction: column;
  }

  /* Premium Header */
  .chat-header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display:flex; align-items:center; justify-content:space-between;
    flex-shrink: 0;
    box-shadow: var(--shadow-sm);
    z-index: 10;
  }
  .header-left {
    display: flex; align-items: center; gap: 14px;
  }
  .chat-header .avatar {
    width:44px; height:44px; border-radius:50%;
    background: linear-gradient(135deg, #2b2724, #12100e);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:16px; font-weight:700; flex-shrink:0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }
  .chat-header h1 {
    margin:0; font-size: 16.5px; font-weight:700; letter-spacing:-0.015em; color:var(--text);
  }
  .header-status {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12.5px; color: var(--muted); font-weight: 500;
  }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    animation: pulseDot 2s infinite ease-in-out;
  }
  @keyframes pulseDot {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.7; }
  }

  .header-actions {
    display: flex; align-items: center; gap: 10px;
  }
  .header-whatsapp-link {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eafaf1; color: var(--whatsapp-dark);
    padding: 8px 14px; border-radius: 999px;
    text-decoration: none; font-size: 13px; font-weight: 600;
    border: 1px solid #bbf0d2;
    transition: all .2s ease;
  }
  .header-whatsapp-link:hover {
    background: #25D366; color: #fff; border-color: #25D366;
    box-shadow: 0 2px 8px rgba(37, 211, 102, 0.3);
  }

  /* Chat Body */
  .chat-body {
    flex: 1;
    padding: 24px 0;
    overflow-y: auto;
    background: var(--bg);
    display:flex; flex-direction:column; gap:16px;
  }
  .chat-body::-webkit-scrollbar { width: 6px; }
  .chat-body::-webkit-scrollbar-thumb { background: var(--border-hover); border-radius: 10px; }

  /* Message Column Container */
  .msg-row {
    width: 100%;
    max-width: 840px;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
  }
  .msg-row.user { justify-content: flex-end; }
  .msg-row.bot { justify-content: flex-start; }

  /* Chat Bubbles */
  .msg {
    max-width: 78%;
    padding: 14px 18px;
    border-radius: 18px;
    font-size: 14.5px;
    line-height: 1.6;
    animation: fadeIn .25s ease;
    word-break: break-word;
  }
  @keyframes fadeIn { from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:translateY(0);} }

  .msg.user {
    background: var(--accent);
    color: #fdfdfc;
    border-bottom-right-radius: 4px;
    font-weight: 450;
    box-shadow: var(--shadow-sm);
  }

  .msg.bot {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
    box-shadow: var(--shadow-sm);
  }

  .msg.error {
    background: var(--error-bg);
    color: var(--error-text);
    border: 1px solid #f8b4b4;
    border-bottom-left-radius: 4px;
  }

  /* Formatted Markdown Content Inside Bot Message */
  .msg.bot p { margin: 0 0 10px 0; }
  .msg.bot p:last-child { margin-bottom: 0; }
  .msg.bot strong { font-weight: 650; color: #111; }
  .msg.bot em { font-style: italic; color: #333; }

  .chat-list {
    margin: 8px 0 12px 18px;
    padding: 0;
  }
  .chat-list li {
    margin-bottom: 6px;
    line-height: 1.55;
  }
  .chat-list li:last-child { margin-bottom: 0; }

  .chat-link {
    color: #0b69a3;
    text-decoration: underline;
    text-underline-offset: 2px;
    font-weight: 500;
  }
  .chat-link:hover { color: #06456c; }

  /* Interactive WhatsApp Quick Action Chip */
  .whatsapp-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    background: #25D366;
    color: #ffffff !important;
    text-decoration: none;
    font-weight: 600;
    font-size: 13.5px;
    padding: 10px 18px;
    border-radius: 999px;
    box-shadow: 0 3px 10px rgba(37, 211, 102, 0.35);
    transition: all .2s ease;
  }
  .whatsapp-chip:hover {
    background: #20bd5a;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.45);
  }

  /* Typing Indicator */
  .msg.typing {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    display:flex; align-items:center; gap:8px;
    border-bottom-left-radius: 4px;
    font-size: 13.5px;
    padding: 12px 16px;
  }
  .dots-group { display:inline-flex; align-items:center; gap:4px; }
  .dot { width:6px; height:6px; border-radius:50%; background: var(--muted); display:inline-block; animation: blink 1.2s infinite ease-in-out; }
  .dot:nth-child(2){ animation-delay:.2s; }
  .dot:nth-child(3){ animation-delay:.4s; }
  @keyframes blink { 0%,80%,100%{opacity:.25;} 40%{opacity:1;} }

  /* Input Footer Bar */
  .chat-input {
    flex-shrink: 0;
    border-top: 1px solid var(--border);
    background: var(--surface);
    padding: 16px 32px 20px;
  }
  .chat-input-inner {
    width: 100%;
    max-width: 840px;
    margin: 0 auto;
    display:flex; align-items:center; gap:10px;
  }
  .chat-input input {
    flex:1; padding: 14px 20px; border: 1px solid var(--border);
    background: var(--bg);
    border-radius: 999px; font-size: 14.5px; outline:none; color: var(--text);
    transition: all .2s ease;
    font-family: inherit;
  }
  .chat-input input::placeholder{ color: var(--muted); }
  .chat-input input:focus {
    border-color: var(--accent);
    background: #fff;
    box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
  }
  .chat-input button {
    width:48px; height:48px; flex-shrink:0;
    background: var(--accent); color:#fff; border:none; border-radius:50%;
    cursor:pointer; font-size:17px; display:flex; align-items:center; justify-content:center;
    transition: all .15s ease;
    box-shadow: var(--shadow-sm);
  }
  .chat-input button:hover { opacity:.9; transform: scale(1.03); }
  .chat-input button:active { transform: scale(.96); }
  .chat-input button:disabled { opacity:.35; cursor:not-allowed; transform:none; }

  @media (max-width: 640px){
    .chat-header, .chat-input { padding-left: 16px; padding-right: 16px; }
    .msg-row { padding: 0 16px; }
    .msg { max-width: 90%; }
    .header-whatsapp-link span { display: none; }
  }
</style>
</head>
<body>

<div class="chat-container">
  <!-- Header -->
  <header class="chat-header">
    <div class="header-left">
      <div class="avatar">PE</div>
      <div>
        <h1>PreciousEdu AI Assistant</h1>
        <div class="header-status">
          <span class="status-dot"></span>
          <span>Online &bull; 24/7 Official Counselor</span>
        </div>
      </div>
    </div>
    <div class="header-actions">
      <a href="https://api.whatsapp.com/send?phone=919879361728&text=Hello!%20I%20have%20an%20inquiry%20regarding%20Precious%20Education..." target="_blank" class="header-whatsapp-link" title="Chat on WhatsApp">
        💬 <span>WhatsApp Helpline</span>
      </a>
    </div>
  </header>

  <!-- Chat Messages -->
  <main class="chat-body" id="chatBody">
    <div class="msg-row bot">
      <div class="msg bot">
        <p><strong>Hello and welcome!</strong> I am your official <strong>PreciousEdu Assistant</strong> for Precious Education and Immigration Consultant (PEIC).</p>
        <p>I can assist you with comprehensive details regarding:</p>
        <ul class="chat-list">
          <li><strong>Study Visas & Admissions</strong> across 300+ universities in Australia, Canada, UK, USA, New Zealand & Singapore</li>
          <li><strong>Work Permits, PR & Express Entry</strong> programs</li>
          <li><strong>IELTS Coaching</strong> at our British Council & IDP authorized center</li>
          <li><strong>100% Free of Cost Profile Assessment & Counseling</strong></li>
        </ul>
        <p>How can I help you today? You may write in English, Hindi, or any language you prefer!</p>
      </div>
    </div>
  </main>

  <!-- Input Area -->
  <footer class="chat-input">
    <div class="chat-input-inner">
      <input type="text" id="userInput" placeholder="Ask about courses, admissions, visas, or contact details..." autocomplete="off">
      <button id="sendBtn" onclick="sendMessage()" aria-label="Send">➤</button>
    </div>
  </footer>
</div>

<script>
// --- Backend Endpoint Configuration ---
const phpRenderUrl = "<?= htmlspecialchars($RENDER_BACKEND_URL, ENT_QUOTES, 'UTF-8'); ?>";
const urlParamApi = new URLSearchParams(window.location.search).get('api');

let resolvedBaseUrl = 'http://localhost:8000';
if (urlParamApi) {
  resolvedBaseUrl = urlParamApi;
} else if (window.FASTAPI_BACKEND_URL) {
  resolvedBaseUrl = window.FASTAPI_BACKEND_URL;
} else if (phpRenderUrl && !phpRenderUrl.includes('YOUR-APP-NAME')) {
  resolvedBaseUrl = phpRenderUrl;
}

const BACKEND_API_URL = resolvedBaseUrl.replace(/\/+$/, '') + '/api/chat';
console.log('[PreciousEdu] Connected to Backend endpoint:', BACKEND_API_URL);

let history = []; // {role: 'user'|'bot', text: '...'}

// Session storage management
function getOrCreateSessionId() {
  let id = localStorage.getItem('pe_chat_session_id');
  if (!id) {
    id = 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 12);
    localStorage.setItem('pe_chat_session_id', id);
  }
  return id;
}
const sessionId = getOrCreateSessionId();

const chatBody = document.getElementById('chatBody');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

userInput.addEventListener('keydown', function(e){
  if (e.key === 'Enter') sendMessage();
});

// Format raw text with rich markdown formatting (bold, lists, auto-links, WhatsApp button)
function formatChatContent(rawText) {
  if (!rawText) return '';

  // 1. Escape basic HTML for security
  let safe = rawText
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 2. Handle markdown links [label](url) if present
  safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, (match, label, url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link">${label === url ? url : label}</a>`;
  });

  // 2b. Bold text: support both **text** and WhatsApp single asterisk *text*
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/(^|[^\*])\*([^\*\n\s][^\*\n]*?[^\*\n\s]|[^\*\n\s])\*([^\*]|$)/g, '$1<strong>$2</strong>$3');

  // 3. Process lists and paragraphs
  const lines = safe.split('\n');
  let inUnorderedList = false;
  let inOrderedList = false;
  let htmlLines = [];

  for (let line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inUnorderedList) {
        htmlLines.push('<ul class="chat-list">');
        inUnorderedList = true;
      }
      htmlLines.push(`<li>${trimmed.substring(2)}</li>`);
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (!inOrderedList) {
        htmlLines.push('<ol class="chat-list">');
        inOrderedList = true;
      }
      const itemContent = trimmed.replace(/^\d+\.\s+/, '');
      htmlLines.push(`<li>${itemContent}</li>`);
    } else {
      if (inUnorderedList) {
        htmlLines.push('</ul>');
        inUnorderedList = false;
      }
      if (inOrderedList) {
        htmlLines.push('</ol>');
        inOrderedList = false;
      }

      if (trimmed === '') {
        // empty line
      } else {
        htmlLines.push(`<p>${line}</p>`);
      }
    }
  }

  if (inUnorderedList) htmlLines.push('</ul>');
  if (inOrderedList) htmlLines.push('</ol>');

  let result = htmlLines.join('');

  // 4. Auto-link emails (info@preciousedu.in)
  result = result.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi, '<a href="mailto:$1" class="chat-link">$1</a>');

  // 5. Auto-link URLs
  result = result.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="chat-link">$1</a>');

  // 6. If contact details or WhatsApp number is present, add an official WhatsApp quick-action button
  if (rawText.includes('9879361728') || rawText.toLowerCase().includes('whatsapp') || rawText.toLowerCase().includes('office address')) {
    result += `
      <div style="margin-top: 10px;">
        <a href="https://api.whatsapp.com/send?phone=919879361728&text=Hello!%20I%20have%20an%20inquiry%20regarding%20Precious%20Education..." target="_blank" class="whatsapp-chip">
          💬 Chat on WhatsApp (+91 9879361728)
        </a>
      </div>
    `;
  }

  return result;
}

function appendMessage(text, role, isError = false) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'msg ' + role + (isError ? ' error' : '');

  if (role === 'bot' && !isError) {
    bubble.innerHTML = formatChatContent(text);
  } else {
    bubble.textContent = text;
  }

  row.appendChild(bubble);
  chatBody.appendChild(row);
  chatBody.scrollTop = chatBody.scrollHeight;
  return row;
}

function appendTyping() {
  const row = document.createElement('div');
  row.className = 'msg-row bot';
  const bubble = document.createElement('div');
  bubble.className = 'msg typing bot';
  bubble.innerHTML = '<span class="dots-group"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span><span class="typing-status">Thinking...</span>';
  row.appendChild(bubble);
  chatBody.appendChild(row);
  chatBody.scrollTop = chatBody.scrollHeight;
  return row;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(text, 'user');
  history.push({ role: 'user', text: text });
  userInput.value = '';
  sendBtn.disabled = true;

  const typingEl = appendTyping();
  const typingStatusEl = typingEl.querySelector('.typing-status');

  // Friendly indicator if Render free tier is cold starting
  const coldStartTimer = setTimeout(() => {
    if (typingStatusEl) {
      typingStatusEl.textContent = 'Connecting to server (waking up if sleeping)...';
    }
  }, 5000);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 75000); // 75s timeout for Render free tier

    const res = await fetch(BACKEND_API_URL, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        message: text,
        history: history.slice(0, -1),
        session_id: sessionId
      }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    clearTimeout(coldStartTimer);

    const rawText = await res.text();
    let data;
    try {
      data = JSON.parse(rawText);
    } catch (parseErr) {
      console.error('FastAPI backend did not return valid JSON. Raw response:', rawText);
      throw new Error(`Server returned non-JSON response (HTTP ${res.status}).`);
    }

    typingEl.remove();

    if (data.reply) {
      appendMessage(data.reply, 'bot');
      history.push({ role: 'bot', text: data.reply });
    } else {
      appendMessage("Received unexpected response structure from server.", 'bot', true);
    }

  } catch (err) {
    clearTimeout(coldStartTimer);
    console.error('Chat request failed:', err);
    typingEl.remove();

    let errMsg = 'Connection error: Could not reach the backend server.';
    if (err && err.name === 'AbortError') {
      errMsg = 'The server took longer than 75s to respond. If hosted on Render Free Tier, instances spin down after inactivity and may take 30-50s to wake up. Please try sending your message again.';
    } else if (err && err.message) {
      errMsg = `Error: ${err.message}\n(Backend: ${BACKEND_API_URL})`;
    }

    appendMessage(errMsg, 'bot', true);
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}
</script>

</body>
</html>
