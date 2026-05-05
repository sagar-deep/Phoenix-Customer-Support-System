/* ============================================================
   Phoenix AI – Chat JavaScript  (mood-aware version)
   ============================================================ */

const chatBox    = document.getElementById('chatBox');
const msgInput   = document.getElementById('msgInput');
const sendBtn    = document.getElementById('sendBtn');
const typing     = document.getElementById('typingIndicator');
const ticketList = document.getElementById('ticketList');

// ── Mood → accent colour map ──────────────────────────────
const MOOD_BORDER = {
  info:    "var(--border)",
  warning: "rgba(234,179,8,.4)",
  error:   "rgba(239,68,68,.4)",
  success: "rgba(34,197,94,.4)",
};
const MOOD_ICON = {
  info:    "",
  warning: "",
  error:   "",
  success: "",
};

// ── Render **bold** and `code` in text ───────────────────
function renderText(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g,     '<code>$1</code>');
}

// ── Append a message bubble ───────────────────────────────
function addMsg(text, role, ts, mood) {
  const wrap   = document.createElement('div');
  wrap.className = `msg ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = renderText(text);

  // Apply mood border on bot bubbles
  if (role === 'bot' && mood && MOOD_BORDER[mood]) {
    bubble.style.borderColor = MOOD_BORDER[mood];
  }

  const time   = document.createElement('div');
  time.className = 'ts';
  time.textContent = ts || new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});

  wrap.appendChild(bubble);
  wrap.appendChild(time);
  chatBox.appendChild(wrap);
  scrollBottom();
}

function scrollBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ── Typing indicator ──────────────────────────────────────
function showTyping()  { typing.classList.add('show'); scrollBottom(); }
function hideTyping()  { typing.classList.remove('show'); }

// ── Send message ──────────────────────────────────────────
async function sendMessage() {
  const text = msgInput.value.trim();
  if (!text) return;

  addMsg(text, 'user');
  msgInput.value   = '';
  showTyping();
  sendBtn.disabled = true;

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text }),
    });
    const data = await res.json();
    hideTyping();
    // Support both "reply" and "text" key from backend
    const reply = data.reply || data.text || '⚠️ No response received.';
    addMsg(reply, 'bot', data.timestamp, data.mood);
    loadTickets();
  } catch (e) {
    hideTyping();
    addMsg('⚠️ Connection error. Please try again.', 'bot', null, 'error');
  } finally {
    sendBtn.disabled = false;
    msgInput.focus();
  }
}

// ── Event listeners ───────────────────────────────────────
sendBtn.addEventListener('click', sendMessage);
msgInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') sendMessage();
});

// Quick action buttons
document.querySelectorAll('.qbtn').forEach(btn => {
  btn.addEventListener('click', () => {
    msgInput.value = btn.dataset.msg;
    sendMessage();
  });
});

// Export CSV
document.getElementById('exportBtn').addEventListener('click', () => {
  window.location.href = '/api/export';
});

// Refresh tickets panel
document.getElementById('refreshTickets').addEventListener('click', loadTickets);

// ── Load ticket sidebar ───────────────────────────────────
async function loadTickets() {
  try {
    const res  = await fetch('/api/complaints');
    const data = await res.json();
    if (!data.length) {
      ticketList.innerHTML = '<div class="ticket-empty">No tickets yet</div>';
      return;
    }
    ticketList.innerHTML = data.slice(0, 8).map(t => `
      <div class="ticket-card">
        <div class="ticket-id">${t.ticket_id}</div>
        <div class="ticket-cat">${t.category}</div>
        <div class="ticket-status-${(t.status || '').toLowerCase()}">${t.status}</div>
      </div>
    `).join('');
  } catch(e) { /* silently fail */ }
}

// Init
loadTickets();
