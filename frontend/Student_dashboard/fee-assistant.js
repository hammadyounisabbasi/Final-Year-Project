(() => {
  'use strict';

  const token = () => localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || localStorage.getItem('token');
  const apiBase = window.ACOS_CONFIG.API_BASE_URL;
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[char]);

  function tokenOwner(value) {
    try {
      const payload = value.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return String(JSON.parse(decodeURIComponent(escape(atob(payload)))).sub || '');
    } catch (_) {
      return '';
    }
  }

  function renderMarkdown(value) {
    const lines = escapeHtml(value).split(/\r?\n/);
    const output = [];
    let listType = null;
    const inline = line => line
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
      .replace(/`([^`\n]+)`/g, '<code>$1</code>');
    const closeList = () => {
      if (listType) output.push(`</${listType}>`);
      listType = null;
    };
    lines.forEach(line => {
      const heading = line.match(/^#{1,3}\s+(.+)$/);
      const bullet = line.match(/^\s*[-*]\s+(.+)$/);
      const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (heading) {
        closeList();
        output.push(`<h3>${inline(heading[1])}</h3>`);
      } else if (bullet || numbered) {
        const nextType = bullet ? 'ul' : 'ol';
        if (listType !== nextType) {
          closeList();
          output.push(`<${nextType}>`);
          listType = nextType;
        }
        output.push(`<li>${inline((bullet || numbered)[1])}</li>`);
      } else if (line.trim()) {
        closeList();
        output.push(`<p>${inline(line)}</p>`);
      } else {
        closeList();
      }
    });
    closeList();
    return output.join('');
  }

  const authToken = token();
  if (!authToken) return;
  const owner = tokenOwner(authToken);
  const stateKey = owner ? `fee-ai-state:${owner}` : null;
  let saved = {};
  if (stateKey) {
    try { saved = JSON.parse(sessionStorage.getItem(stateKey) || '{}'); } catch (_) { saved = {}; }
  }
  const records = Array.isArray(saved.records) ? saved.records.filter(item => ['user', 'assistant'].includes(item.role) && typeof item.text === 'string') : [];
  let history = records.map(item => ({ role: item.role, content: item.text })).slice(-12);

  document.body.insertAdjacentHTML('beforeend', `
    <button class="fee-ai-launcher" id="feeAiLauncher" type="button" aria-label="Open Fee AI Assistant" aria-expanded="false" title="Ask Fee AI Assistant">🤖</button>
    <section class="fee-ai-drawer" id="feeAiDrawer" hidden aria-label="Fee AI Assistant">
      <header class="fee-ai-header">
        <div class="fee-ai-title"><span aria-hidden="true">🤖</span><span>Fee AI Assistant</span></div>
        <div class="fee-ai-actions">
          <button id="feeAiClear" type="button" aria-label="Start a new chat" title="Start a new chat">↺</button>
          <button id="feeAiClose" type="button" aria-label="Close assistant" title="Close assistant">×</button>
        </div>
      </header>
      <div class="fee-ai-body" id="feeAiBody" role="log" aria-live="polite"></div>
      <form class="fee-ai-footer" id="feeAiForm">
        <textarea id="feeAiInput" rows="1" maxlength="2000" required aria-label="Message the Fee AI Assistant" placeholder="Ask about your fee or a payment issue…"></textarea>
        <button type="submit" aria-label="Send message" title="Send">➤</button>
      </form>
      <p class="fee-ai-status" id="feeAiStatus" role="status"></p>
    </section>`);

  const launcher = document.getElementById('feeAiLauncher');
  const drawer = document.getElementById('feeAiDrawer');
  const body = document.getElementById('feeAiBody');
  const input = document.getElementById('feeAiInput');
  const form = document.getElementById('feeAiForm');
  const status = document.getElementById('feeAiStatus');

  function persist(open) {
    if (!stateKey) return;
    try { sessionStorage.setItem(stateKey, JSON.stringify({ records, open })); } catch (_) { /* optional */ }
  }

  function addMessage(role, text, sources = [], replace = null) {
    const element = replace && body.contains(replace) ? replace : document.createElement('div');
    element.className = `fee-ai-message ${role}`;
    element.innerHTML = `<strong>${role === 'user' ? 'You' : 'Fee AI Assistant'}</strong><div class="fee-ai-text"></div>`;
    const textHolder = element.querySelector('.fee-ai-text');
    if (role === 'assistant') textHolder.innerHTML = renderMarkdown(text);
    else textHolder.textContent = String(text || '');
    const source = sources.find(item => item && item.url);
    if (role === 'assistant' && source) {
      const note = document.createElement('div');
      note.className = 'fee-ai-source';
      const link = document.createElement('a');
      link.href = source.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = source.title || 'Official university source';
      note.append('Official source: ', link);
      element.append(note);
    }
    if (!replace || !body.contains(replace)) body.append(element);
    body.scrollTop = body.scrollHeight;
    return element;
  }

  const greeting = 'Hello! I can explain your authenticated fee record, due dates, payment status, and verified university fee procedures. What would you like to know?';
  if (records.length) records.forEach(item => addMessage(item.role, item.text, item.sources || []));
  else addMessage('assistant', greeting);

  const open = () => { drawer.hidden = false; launcher.setAttribute('aria-expanded', 'true'); persist(true); input.focus(); };
  const close = () => { drawer.hidden = true; launcher.setAttribute('aria-expanded', 'false'); persist(false); launcher.focus(); };
  launcher.addEventListener('click', open);
  document.getElementById('feeAiClose').addEventListener('click', close);
  document.getElementById('feeAiClear').addEventListener('click', () => {
    records.length = 0;
    history = [];
    body.innerHTML = '';
    addMessage('assistant', greeting);
    status.textContent = '';
    persist(true);
  });
  if (saved.open) open();

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    const send = form.querySelector('button[type=submit]');
    const requestHistory = history.slice(-12);
    addMessage('user', message);
    records.push({ role: 'user', text: message });
    history.push({ role: 'user', content: message });
    const pending = addMessage('assistant', 'Checking your fee record and verified university information…');
    input.value = '';
    send.disabled = true;
    status.textContent = 'Preparing your answer…';
    persist(true);
    try {
      const response = await fetch(`${apiBase}/student/fee-ai/chat`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: requestHistory })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || (response.status === 401 ? 'Your session has expired. Please sign in again.' : 'The fee assistant could not complete this request.'));
      const reply = typeof data.response === 'string' && data.response.trim() ? data.response.trim() : 'No readable answer was returned. Please try again.';
      const sources = Array.isArray(data.sources) ? data.sources : [];
      addMessage('assistant', reply, sources, pending);
      records.push({ role: 'assistant', text: reply, sources });
      history.push({ role: 'assistant', content: reply });
      status.textContent = '';
      persist(true);
    } catch (error) {
      const reply = `I could not complete that request: ${error.message || 'Please try again.'}`;
      addMessage('assistant', reply, [], pending);
      records.push({ role: 'assistant', text: reply });
      history.push({ role: 'assistant', content: reply });
      status.textContent = error.message || 'Request failed.';
      persist(true);
    } finally {
      send.disabled = false;
      input.focus();
    }
  });

  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
})();
