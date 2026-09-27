(function () {
  'use strict';
  const local = ['localhost', '127.0.0.1', ''].includes(location.hostname);
  const origin = window.ACOS_CONFIG.API_BASE_URL;
  const API = origin + '/admin/exam-assistant';
  const byId = id => document.getElementById(id);
  const authToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || sessionStorage.getItem('access_token') || '';
  const auth = json => ({ Authorization: 'Bearer ' + authToken(), ...(json ? { 'Content-Type': 'application/json' } : {}) });
  let sessionId = sessionStorage.getItem('exam-assistant-session') || '';
  let current = { date_sheet: [], seating_plan: [], warnings: [] };
  let previewType = 'date_sheet';
  let busy = false;

  function appendInlineMarkdown(parent, text) {
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
    let cursor = 0;
    for (const match of text.matchAll(pattern)) {
      if (match.index > cursor) parent.append(document.createTextNode(text.slice(cursor, match.index)));
      const token = match[0];
      const element = document.createElement(token.startsWith('**') ? 'strong' : token.startsWith('`') ? 'code' : 'em');
      element.textContent = token.startsWith('**') ? token.slice(2, -2) : token.slice(1, -1);
      parent.append(element);
      cursor = match.index + token.length;
    }
    if (cursor < text.length) parent.append(document.createTextNode(text.slice(cursor)));
  }

  function tableCells(line) {
    return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(value => value.trim());
  }

  function isTableDivider(line) {
    const cells = tableCells(line);
    return cells.length > 1 && cells.every(value => /^:?-{3,}:?$/.test(value));
  }

  function renderAssistantContent(value) {
    const container = document.createElement('div');
    container.className = 'exam-ai-rich';
    const lines = String(value || '').replace(/\r/g, '').split('\n');
    let index = 0;
    while (index < lines.length) {
      const line = lines[index].trim();
      if (!line) { index += 1; continue; }

      if (line.includes('|') && index + 1 < lines.length && isTableDivider(lines[index + 1])) {
        const wrapper = document.createElement('div'); wrapper.className = 'exam-ai-markdown-table-wrap';
        const table = document.createElement('table'); table.className = 'exam-ai-markdown-table';
        const thead = document.createElement('thead'); const headerRow = document.createElement('tr');
        tableCells(line).forEach(value => { const th = document.createElement('th'); appendInlineMarkdown(th, value); headerRow.append(th); });
        thead.append(headerRow); table.append(thead); index += 2;
        const tbody = document.createElement('tbody');
        while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
          const row = document.createElement('tr');
          tableCells(lines[index]).forEach(value => { const td = document.createElement('td'); appendInlineMarkdown(td, value); row.append(td); });
          tbody.append(row); index += 1;
        }
        table.append(tbody); wrapper.append(table); container.append(wrapper); continue;
      }

      const heading = line.match(/^(#{1,4})\s+(.+)$/);
      if (heading) {
        const level = Math.min(4, heading[1].length + 1);
        const element = document.createElement(`h${level}`); appendInlineMarkdown(element, heading[2]); container.append(element); index += 1; continue;
      }

      if (/^[-*]\s+/.test(line)) {
        const list = document.createElement('ul');
        while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) {
          const item = document.createElement('li'); appendInlineMarkdown(item, lines[index].replace(/^\s*[-*]\s+/, '')); list.append(item); index += 1;
        }
        container.append(list); continue;
      }

      if (/^\d+[.)]\s+/.test(line)) {
        const list = document.createElement('ol');
        while (index < lines.length && /^\s*\d+[.)]\s+/.test(lines[index])) {
          const item = document.createElement('li'); appendInlineMarkdown(item, lines[index].replace(/^\s*\d+[.)]\s+/, '')); list.append(item); index += 1;
        }
        container.append(list); continue;
      }

      if (line.startsWith('> ')) {
        const quote = document.createElement('blockquote'); appendInlineMarkdown(quote, line.slice(2)); container.append(quote); index += 1; continue;
      }

      const paragraph = document.createElement('p'); appendInlineMarkdown(paragraph, line); container.append(paragraph); index += 1;
    }
    return container;
  }

  function message(role, value) {
    const node = document.createElement('div');
    node.className = 'exam-ai-message ' + role;
    const meta = document.createElement('span');
    meta.className = 'exam-ai-message-meta';
    meta.textContent = role === 'user' ? 'Administrator' : 'Exam Assistant';
    node.append(meta, role === 'assistant' ? renderAssistantContent(value) : document.createTextNode(value));
    byId('examAiMessages').append(node);
    byId('examAiMessages').scrollTop = byId('examAiMessages').scrollHeight;
  }

  function detail(data, fallback) {
    if (!data) return fallback;
    if (typeof data.detail === 'string') return data.detail;
    return data.detail?.message || fallback;
  }

  async function ensureSession(forceNew) {
    const requested = forceNew ? null : sessionId || null;
    const response = await fetch(API + '/sessions', { method: 'POST', headers: auth(true), body: JSON.stringify({ session_id: requested }) });
    const data = await response.json();
    if (!response.ok) throw Error(detail(data, 'Unable to start an assistant session'));
    sessionId = data.session_id;
    sessionStorage.setItem('exam-assistant-session', sessionId);
    byId('examAiStatus').textContent = 'Secure temporary session';
    return data;
  }

  function setBusy(value, label) {
    busy = value;
    byId('examAiSend').disabled = value;
    byId('examAiAttach').disabled = value;
    byId('examAiStatus').textContent = label || (value ? 'Working…' : 'Secure temporary session');
  }

  async function send(text) {
    if (busy || !text.trim()) return;
    message('user', text.trim());
    setBusy(true, 'Analyzing constraints…');
    try {
      await ensureSession(false);
      const response = await fetch(API + '/chat', { method: 'POST', headers: auth(true), body: JSON.stringify({ session_id: sessionId, message: text.trim() }) });
      const data = await response.json();
      if (!response.ok) throw Error(detail(data, 'The request could not be completed'));
      current = data;
      if (data.intent === 'seating_plan') previewType = 'seating_plan';
      if (data.intent === 'date_sheet') previewType = 'date_sheet';
      message('assistant', data.reply);
      render();
    } catch (error) {
      message('assistant', error.message);
      if (/expired|not found/i.test(error.message)) {
        sessionId = '';
        sessionStorage.removeItem('exam-assistant-session');
      }
    } finally { setBusy(false); }
  }

  async function upload(file) {
    if (!file) return;
    setBusy(true, 'Parsing and embedding file…');
    try {
      await ensureSession(false);
      const form = new FormData();
      form.append('session_id', sessionId);
      form.append('document', file);
      const response = await fetch(API + '/documents', { method: 'POST', headers: auth(false), body: form });
      const data = await response.json();
      if (!response.ok) throw Error(detail(data, 'File processing failed'));
      addFile(data.document);
      message('assistant', `${file.name} was parsed, normalized, embedded, and added to this temporary session (${data.document.chunks} retrievable chunks).`);
    } catch (error) { message('assistant', error.message); }
    finally { setBusy(false); byId('examAiFileInput').value = ''; }
  }

  function addFile(documentInfo) {
    const chip = document.createElement('div');
    chip.className = 'exam-ai-file';
    const icon = document.createElement('i'); icon.className = 'fa-solid fa-file-lines';
    const name = document.createElement('span'); name.textContent = documentInfo.filename;
    const remove = document.createElement('button'); remove.type = 'button'; remove.title = 'Remove temporary file'; remove.textContent = '×';
    remove.onclick = async () => {
      const response = await fetch(`${API}/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentInfo.id)}`, { method: 'DELETE', headers: auth(false) });
      if (response.ok) chip.remove();
    };
    chip.append(icon, name, remove); byId('examAiAttachments').append(chip);
  }

  function render() {
    document.querySelectorAll('.exam-ai-tab').forEach(button => button.classList.toggle('active', button.dataset.type === previewType));
    const rows = current[previewType] || [];
    const head = byId('examAiTableHead'); const body = byId('examAiTableBody');
    head.replaceChildren(); body.replaceChildren();
    byId('examAiEmpty').hidden = !!rows.length;
    byId('examAiTableWrap').hidden = !rows.length;
    const dateColumns = [['Date','date'],['Day','day'],['Course Code','course_code'],['Course Name','course_name'],['Semester / Section','semester_section'],['Start','start_time'],['End','end_time'],['Room','room']];
    const seatColumns = [['Date','date'],['Exam / Course','exam_course'],['Room','room'],['Capacity','capacity'],['Section','section'],['Roll Number Range','roll_number_range'],['Assigned','assigned_students']];
    const columns = previewType === 'date_sheet' ? dateColumns : seatColumns;
    const headerRow = document.createElement('tr');
    columns.forEach(([label]) => { const th = document.createElement('th'); th.textContent = label; headerRow.append(th); }); head.append(headerRow);
    rows.forEach(row => {
      const tr = document.createElement('tr');
      columns.forEach(([, key]) => { const td = document.createElement('td'); td.textContent = row[key] ?? ''; tr.append(td); }); body.append(tr);
    });
    byId('examAiWarnings').replaceChildren();
    (current.warnings || []).forEach(value => { const div = document.createElement('div'); div.textContent = '• ' + value; byId('examAiWarnings').append(div); });
    document.querySelectorAll('[data-exam-export]').forEach(button => { button.disabled = !rows.length; });
  }

  async function exportFile(format) {
    const response = await fetch(API + '/export', { method: 'POST', headers: auth(true), body: JSON.stringify({ session_id: sessionId, document_type: previewType, format }) });
    if (!response.ok) { const data = await response.json(); throw Error(detail(data, 'Export failed')); }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = url; link.download = `${previewType.replace('_', '-')}.${format}`; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  async function reset() {
    if (sessionId) await fetch(`${API}/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE', headers: auth(false) }).catch(() => {});
    sessionId = ''; sessionStorage.removeItem('exam-assistant-session'); current = { date_sheet: [], seating_plan: [], warnings: [] };
    byId('examAiMessages').replaceChildren(); byId('examAiAttachments').replaceChildren();
    await ensureSession(true); welcome(); render();
  }

  function welcome() {
    message('assistant', 'I can build grounded exam date sheets and seating plans from university records, then revise them through conversation. Tell me a department and semester, or attach a relevant file. Proposals are never saved or approved automatically.');
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const form = byId('examAiForm'); if (!form) return;
    form.addEventListener('submit', event => { event.preventDefault(); const input = byId('examAiInput'); const value = input.value; input.value = ''; send(value); });
    byId('examAiInput').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
    byId('examAiAttach').onclick = () => byId('examAiFileInput').click();
    byId('examAiFileInput').onchange = event => upload(event.target.files[0]);
    byId('examAiReset').onclick = reset;
    document.querySelectorAll('.exam-ai-tab').forEach(button => button.onclick = () => { previewType = button.dataset.type; render(); });
    document.querySelectorAll('[data-exam-export]').forEach(button => button.onclick = () => exportFile(button.dataset.examExport).catch(error => message('assistant', error.message)));
    welcome(); render();
    try {
      const restored = await ensureSession(false);
      if (restored.has_seating_plan) previewType = 'seating_plan';
      if (restored.has_date_sheet || restored.has_seating_plan) {
        const response = await fetch(`${API}/sessions/${encodeURIComponent(sessionId)}`, { headers: auth(false) });
        if (response.ok) { current = await response.json(); current.documents?.forEach(addFile); render(); }
      }
    } catch (error) { byId('examAiStatus').textContent = 'Sign in required'; message('assistant', error.message); }
  });
}());
