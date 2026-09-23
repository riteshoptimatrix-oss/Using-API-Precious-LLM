<?php
/**
 * PreciousEdu AI Chatbot - Frontend
 *
 * CONFIGURATION:
 * Once you deploy the backend to Render, paste your Render web service URL below:
 * Example: 'https://precious-edu-chatbot-api.onrender.com'
 * (Leave as is for local development; it will automatically fallback to http://localhost:8000)
 */
$RENDER_BACKEND_URL = 'https://using-api-precious-llm.onrender.com';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PreciousEdu AI Chatbot</title>
<style>
  :root{
    --bg:#f7f5f2;            /* off-white background */
    --surface:#fffdfb;       /* card / header / input surface, warm white */
    --border:#e7e2da;        /* soft warm border */
    --text:#2b2824;          /* near-black warm text */
    --muted:#8a8479;         /* muted taupe text */
    --accent:#1f1c19;        /* near-black accent (buttons/user bubble) */
    --accent-soft:#efece6;   /* bot bubble background */
    --error-bg:#fde8e8;
    --error-text:#9b1c1c;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; padding: 0; }
  body {
    font-family: 'Inter','Segoe UI',Helvetica,Arial,sans-serif;
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

  .chat-header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 18px 32px;
    display:flex; align-items:center; gap:14px;
    flex-shrink: 0;
  }
  .chat-header .avatar {
    width:40px; height:40px; border-radius:50%;
    background: var(--accent);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:15px; font-weight:600; flex-shrink:0;
  }
  .chat-header h2 {
    margin:0; font-size: 16px; font-weight:600; letter-spacing:-0.01em; color:var(--text);
  }
  .chat-header p { margin:2px 0 0; font-size: 12.5px; color: var(--muted); }

  .chat-body {
    flex: 1;
    padding: 28px 0;
    overflow-y: auto;
    background: var(--bg);
    display:flex; flex-direction:column; gap:14px;
  }
  .chat-body::-webkit-scrollbar { width: 6px; }
  .chat-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

  /* Center the message column but let the container itself be full width */
  .msg-row {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
  }
  .msg-row.user { justify-content: flex-end; }
  .msg-row.bot { justify-content: flex-start; }

  .msg {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14.5px;
    line-height:1.55;
    white-space: pre-wrap;
    animation: fadeIn .25s ease;
  }
  @keyframes fadeIn { from{opacity:0; transform:translateY(4px);} to{opacity:1; transform:translateY(0);} }

  .msg.user {
    background: var(--accent);
    color: #fdfdfc;
    border-bottom-right-radius:6px;
  }
  .msg.bot {
    background: var(--accent-soft);
    color: var(--text);
    border: 1px solid var(--border);
    border-bottom-left-radius:6px;
  }
  .msg.error {
    background: var(--error-bg);
    color: var(--error-text);
    border: 1px solid #f8b4b4;
    border-bottom-left-radius:6px;
  }
  .msg.typing {
    background: var(--accent-soft);
    border: 1px solid var(--border);
    color: var(--muted);
    display:flex; align-items:center; gap:8px;
    border-bottom-left-radius:6px;
    font-size: 13.5px;
  }
  .dots-group { display:inline-flex; align-items:center; gap:4px; }
  .dot { width:6px; height:6px; border-radius:50%; background: var(--muted); display:inline-block; animation: blink 1.2s infinite ease-in-out; }
  .dot:nth-child(2){ animation-delay:.2s; }
  .dot:nth-child(3){ animation-delay:.4s; }
  @keyframes blink { 0%,80%,100%{opacity:.25;} 40%{opacity:1;} }

  .chat-input {
    flex-shrink: 0;
    border-top: 1px solid var(--border);
    background: var(--surface);
    padding: 18px 32px;
  }
  .chat-input-inner {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    display:flex; align-items:center; gap:10px;
  }
  .chat-input input {
    flex:1; padding: 13px 18px; border: 1px solid var(--border);
    background: var(--bg);
    border-radius: 999px; font-size:14.5px; outline:none; color: var(--text);
    transition: border-color .15s ease;
  }
  .chat-input input::placeholder{ color: var(--muted); }
  .chat-input input:focus { border-color: var(--accent); }
  .chat-input button {
    width:44px; height:44px; flex-shrink:0;
    background: var(--accent); color:#fff; border:none; border-radius:50%;
    cursor:pointer; font-size:17px; display:flex; align-items:center; justify-content:center;
    transition: opacity .15s ease, transform .1s ease;
  }
  .chat-input button:hover { opacity:.88; }
  .chat-input button:active { transform: scale(.94); }
  .chat-input button:disabled { opacity:.4; cursor:not-allowed; }

  @media (max-width: 640px){
    .chat-header, .chat-input { padding-left: 16px; padding-right: 16px; }
    .msg-row { padding: 0 16px; }
    .msg { max-width: 85%; }
  }
</style>
</head>
<body>

<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">PE</div>
    <div>
      <h2>PreciousEdu Assistant</h2>
      <p>Ask me anything about the website - in any language</p>
    </div>
  </div>

  <div class="chat-body" id="chatBody">
    <div class="msg-row bot">
      <div class="msg bot">Hi! I'm the PreciousEdu Assistant. Ask me anything about the website - courses, admissions, contact details, and more. You can write in any language you like.</div>
    </div>
  </div>

  <div class="chat-input">
    <div class="chat-input-inner">
      <input type="text" id="userInput" placeholder="Type your message..." autocomplete="off">
      <button id="sendBtn" onclick="sendMessage()" aria-label="Send">➤</button>
    </div>
  </div>
</div>

<script>
// --- Backend Endpoint Configuration ---
// Priority resolution:
// 1. ?api= query parameter
// 2. window.FASTAPI_BACKEND_URL (if injected)
// 3. PHP $RENDER_BACKEND_URL (if configured with your real Render domain)
// 4. Default: http://localhost:8000 for local testing
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

// Persist a unique session id per browser so the backend can group messages by conversation.
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

function appendMessage(text, role, isError = false) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'msg ' + role + (isError ? ' error' : '');
  bubble.textContent = text;
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

  // If server is on Render free tier and cold-starting, update indicator after 5 seconds
  const coldStartTimer = setTimeout(() => {
    if (typingStatusEl) {
      typingStatusEl.textContent = 'Connecting to server (waking up if sleeping)...';
    }
  }, 5000);

  try {
    const controller = new AbortController();
    // 75-second safety timeout to allow for Render Free Tier spin-up
    const timeoutId = setTimeout(() => controller.abort(), 75000);

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
