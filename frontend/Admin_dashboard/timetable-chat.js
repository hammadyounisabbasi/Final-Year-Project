/* Timetable Studio AI Assistant Client. Fully responsive, markdown-rendered, multi-turn conversational chat. */
const apiOrigin = window.ACOS_CONFIG.API_BASE_URL;
const API = apiOrigin.replace(/\/$/, '') + '/admin/timetable-creator';
const $ = id => document.getElementById(id);
const token = () => localStorage.getItem('access_token') || localStorage.getItem('token') || sessionStorage.getItem('access_token') || '';
const headers = () => ({ Authorization: 'Bearer ' + token(), 'Content-Type': 'application/json' });

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function renderMarkdown(raw) {
  if (!raw) return '';
  // 1. Escape HTML to protect against XSS
  let html = String(raw)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

  // 2. Fenced Code Blocks (```language ... ```)
  html = html.replace(/```([a-zA-Z0-9_-]*)\r?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="chat-code-block"><code class="lang-${esc(lang)}">${code.trim()}</code></pre>`;
  });

  // 3. Inline code (`code`)
  html = html.replace(/`([^`\n]+)`/g, '<code class="chat-inline-code">$1</code>');

  // 4. Tables (| col | col |)
  html = html.replace(/((\|[^\n]+\|\r?\n)((?:\|:?[-]+:?)+\|\r?\n)((?:\|[^\n]+\|\r?\n?)+))/g, (tableMatch) => {
    const lines = tableMatch.trim().split(/\r?\n/).map(l => l.trim());
    if (lines.length < 2) return tableMatch;
    const headerCols = lines[0].split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
    const bodyRows = lines.slice(2).map(row => {
      const cells = row.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
      return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`;
    }).join('');
    return `<div class="chat-table-scroll"><table class="chat-table"><thead><tr>${headerCols.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${bodyRows}</tbody></table></div>`;
  });

  // 5. Headings
  html = html.replace(/^#### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');
  html = html.replace(/^### (.*$)/gim, '<h4 class="chat-h4">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="chat-h3">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="chat-h2">$1</h2>');

  // 6. Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
  html = html.replace(/(^|[^*])\*([^*]+)\*([^*]|$)/g, '$1<em>$2</em>$3');
  html = html.replace(/(^|[^_])_([^_]+)_([^_]|$)/g, '$1<em>$2</em>$3');

  // 7. Blockquotes
  html = html.replace(/^>\s*(.*$)/gim, '<blockquote class="chat-quote">$1</blockquote>');

  // 8. Unordered Lists
  html = html.replace(/^[\*\-]\s+(.*$)/gim, '<li class="chat-li">$1</li>');
  html = html.replace(/((?:<li class="chat-li">.*?<\/li>\s*)+)/gim, '<ul class="chat-ul">$1</ul>');

  // 9. Ordered Lists
  html = html.replace(/^\d+\.\s+(.*$)/gim, '<li class="chat-oli">$1</li>');
  html = html.replace(/((?:<li class="chat-oli">.*?<\/li>\s*)+)/gim, '<ol class="chat-ol">$1</ol>');

  // 10. Paragraphs & Line Breaks
  html = html.replace(/\n\n+/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');

  return `<div class="chat-formatted-body">${html}</div>`;
}

function getFileIconSvg(filename = '') {
  const ext = filename.split('.').pop().toLowerCase();
  if (['png', 'jpg', 'jpeg', 'webp', 'svg'].includes(ext)) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`;
  }
  if (['csv', 'xlsx', 'xls'].includes(ext)) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M8 13h2"/><path d="M8 17h2"/><path d="M14 13h2"/><path d="M14 17h2"/></svg>`;
  }
  if (['pdf'].includes(ext)) {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/></svg>`;
  }
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`;
}

let proposal = [], proof = '', rows = [], baseRows = [], history = [], attachments = [], busy = false, lastRequest = '';
let conversationState = {};
let optionsLoaded = false, optionsLoading = false;

const historyKey = 'timetable-chat:' + token().slice(-24);
try { history = JSON.parse(sessionStorage.getItem(historyKey) || '[]').slice(-50); } catch { history = []; }

function message(role, text, remember = true, files = []) {
  const isUser = role === 'user';
  const bubble = document.createElement('article');
  bubble.className = 'message ' + (isUser ? 'user' : 'assistant');

  const header = document.createElement('div');
  header.className = 'message-header-row';

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar ' + (isUser ? 'user-av' : 'ai-av');
  avatar.innerHTML = isUser
    ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
    : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/><rect x="4" y="8" width="16" height="12" rx="2"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/></svg>`;

  const author = document.createElement('b');
  author.className = 'message-author';
  author.textContent = isUser ? 'You' : 'Timetable Assistant';

  const timeStamp = document.createElement('span');
  timeStamp.className = 'message-time';
  const now = new Date();
  timeStamp.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  header.append(avatar, author, timeStamp);

  const body = document.createElement('div');
  body.className = 'message-body';
  body.innerHTML = renderMarkdown(text);

  bubble.append(header, body);

  if (files && files.length) {
    const attachWrap = document.createElement('div');
    attachWrap.className = 'message-attachments-row';
    files.forEach(file => {
      const chip = document.createElement('div');
      chip.className = 'sent-file-chip';
      chip.innerHTML = `${getFileIconSvg(file.name)} <span>${esc(file.name)}</span> <small>(${esc(file.status || 'Attached')})</small>`;
      attachWrap.append(chip);
    });
    bubble.append(attachWrap);
  }

  $('chat').append(bubble);

  if (remember) {
    history.push({ role: isUser ? 'user' : 'assistant', content: text, files });
    history = history.slice(-50);
    try { sessionStorage.setItem(historyKey, JSON.stringify(history)); } catch (e) { console.warn(e); }
  }

  scrollChat();
  return bubble;
}

function scrollChat() {
  const c = $('chat');
  if (c) c.scrollTo({ top: c.scrollHeight, behavior: 'smooth' });
}

function setBusy(value) {
  busy = value;
  $('typing').hidden = !value;
  $('send').disabled = value;
  document.querySelectorAll('[data-request], #approve, #regenerate, #analyze, #generate').forEach(b => b.disabled = value);
  $('agent-state').textContent = value ? 'Analyzing live constraints…' : 'Ready';
}

function scope() {
  return Object.fromEntries(
    ['department_id', 'semester', 'section', 'teacher_id', 'student_id', 'academic_year']
      .map(k => [k, $(k)?.value])
      .filter(([, v]) => v !== undefined && v !== '')
  );
}

function reference() {
  return attachments.filter(a => a.reviewed).map(a => a.text).join('\n\n');
}

async function call(path, body) {
  const response = await fetch(API + path, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) {
    throw Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  }
  return data;
}

function clearProposal() {
  proposal = [];
  proof = '';
  $('proposal').hidden = true;
  document.querySelectorAll('.result-actions button').forEach(b => b.disabled = true);
}

function render(data) {
  if (data.mode && data.mode !== conversationState.mode) {
    rows = [];
    baseRows = [];
    clearProposal();
  }
  if (data.conversation_state) {
    conversationState = data.conversation_state;
    try { sessionStorage.setItem(historyKey + ':state', JSON.stringify(conversationState)); } catch (e) { console.warn(e); }
  }
  if (data.scope) {
    for (const [key, value] of Object.entries(data.scope)) {
      const input = $(key);
      if (input?.tagName === 'SELECT' && [...input.options].some(o => o.value === String(value))) {
        input.value = String(value);
      }
    }
  }
  rows = data.preview_schedules || data.schedules || rows;
  baseRows = data.schedules || baseRows;

  // Analysis Summary
  $('status').textContent = data.warning || data.summary || data.reply || 'Ready for review.';

  // Pipeline Stepper
  const steps = data.workflow_steps || ['understand_request', 'read_database', 'analyze_workload', 'validate_constraints', 'ready_for_review'];
  $('workflow').innerHTML = steps.map((s, i) => `
    <span class="workflow-step-node ${i === steps.length - 1 ? 'is-current' : 'is-done'}">
      <span class="step-dot"></span>
      <span>${esc(s.replaceAll('_', ' '))}</span>
    </span>
  `).join('<span class="step-arrow">→</span>');

  // Provider
  $('provider').textContent = data.provider_status || 'Live Database Constraints';

  // Limitations
  const limits = data.limitations || ['18 contact hours and 6 scheduled courses are policy defaults.', 'Live university room and teacher availability constraints enforced.'];
  $('limitations').innerHTML = limits.map(l => `<span class="limitation-item">• ${esc(l)}</span>`).join(' ');

  // KPI Metrics Grid
  const conflictCount = data.validation_errors?.length || data.issues?.length || data.metrics?.issues || 0;
  const proposedCount = data.changes?.length || 0;
  const activeCount = data.metrics?.active_schedules || rows.length || 0;

  $('metrics').innerHTML = `
    <div class="kpi-metric-card primary">
      <div class="kpi-icon-wrap">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
      </div>
      <div class="kpi-content">
        <div class="kpi-val">${activeCount}</div>
        <div class="kpi-lbl">${data.mode === 'general' ? 'Weekly Sessions' : 'Active Class Schedules'}</div>
      </div>
    </div>
    <div class="kpi-metric-card ${conflictCount > 0 ? 'danger' : 'success'}">
      <div class="kpi-icon-wrap">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="kpi-content">
        <div class="kpi-val">${conflictCount}</div>
        <div class="kpi-lbl">${conflictCount === 0 ? 'No Schedule Conflicts' : 'Detected Conflicts / Clashes'}</div>
      </div>
    </div>
    <div class="kpi-metric-card ${proposedCount > 0 ? 'warning' : 'neutral'}">
      <div class="kpi-icon-wrap">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
      </div>
      <div class="kpi-content">
        <div class="kpi-val">${proposedCount}</div>
        <div class="kpi-lbl">Proposed Update Sessions</div>
      </div>
    </div>
    <div class="kpi-metric-card info">
      <div class="kpi-icon-wrap">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
      </div>
      <div class="kpi-content">
        <div class="kpi-val">${data.agent_context?.teacher_count || data.agent_context?.teachers?.length || 'Live'}</div>
        <div class="kpi-lbl">Verified Faculty in Scope</div>
      </div>
    </div>
  `;

  // Issues and Conflicts
  const issuesList = data.issues || [];
  if (issuesList.length) {
    $('issues').innerHTML = `
      <div class="conflicts-summary-box">
        <div class="conflicts-summary-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span>Conflict Diagnosis (${issuesList.length} items flagged)</span>
        </div>
        <div class="conflicts-list-cards">
          ${issuesList.map(i => `
            <article class="conflict-item-card">
              <div class="conflict-badge-tag">${esc(i.type || 'Constraint Issue')}</div>
              <p class="conflict-msg">${esc(i.message)}</p>
              ${i.affected?.length ? `
                <details class="conflict-affected-details">
                  <summary>View ${i.affected.length} affected schedule sessions</summary>
                  <div class="affected-items-grid">
                    ${i.affected.map(r => `
                      <div class="affected-session-chip">
                        <b>${esc(r.course_code)}</b> · ${esc(r.teacher)} · <span class="tag">${esc(r.day)} ${esc(r.start_time)}</span> · <span>${esc(r.room)}</span>
                      </div>
                    `).join('')}
                  </div>
                </details>
              ` : ''}
            </article>
          `).join('')}
        </div>
      </div>
    `;
    $('issues').hidden = false;
  } else {
    $('issues').innerHTML = '';
    $('issues').hidden = true;
  }

  renderPreview();
}

function renderPreview() {
  const mode = $('view').value;
  const selected = $('preview-filter').value;
  const key = r => mode === 'teacher' ? `${r.teacher}` : mode === 'department' ? `${r.department}` : `${r.department} · Semester ${r.semester} · Section ${r.section}`;
  const groups = [...new Set(rows.map(key))];

  $('preview-filter').innerHTML = '<option value="">All matching entries</option>' + groups.map(g => `<option ${g === selected ? 'selected' : ''}>${esc(g)}</option>`).join('');
  const visible = rows.filter(r => !$('preview-filter').value || key(r) === $('preview-filter').value);

  const countTag = $('preview-count-tag');
  if (countTag) {
    countTag.textContent = `Showing ${visible.length} of ${rows.length} sessions`;
  }

  let previousGroup = '';
  $('preview-body').innerHTML = visible.map(r => {
    const group = `${r.department} · Semester ${r.semester} · Section ${r.section}`;
    const heading = group !== previousGroup ? `
      <tr class="cohort-heading">
        <th colspan="6">
          <div class="cohort-heading-inner">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <span>${esc(group)} · Academic Year: ${esc(r.academic_year)}</span>
          </div>
        </th>
      </tr>` : '';
    previousGroup = group;

    const isProposed = !!r.proposed;
    const isReadOnly = r.academic_year === 'General/Test';
    const dayClass = r.day ? r.day.toLowerCase().slice(0, 3) : 'mon';

    return heading + `
      <tr class="schedule-row ${isProposed ? 'is-proposed-row' : ''}">
        <td>
          <div class="cohort-cell">
            <span class="cohort-dept-name">${esc(r.department)}</span>
            <div class="cohort-sub-pills">
              <span class="badge-sem">Sem ${esc(r.semester)}</span>
              <span class="badge-sec">Sec ${esc(r.section)}</span>
            </div>
          </div>
        </td>
        <td>
          <div class="course-cell">
            <div class="course-code-tag">${esc(r.course_code)}</div>
            <div class="course-title-label">${esc(r.course_title)}</div>
            <span class="credit-badge">${esc(r.credit_hours)} Credit Hours</span>
          </div>
        </td>
        <td>
          <div class="teacher-cell">
            <div class="teacher-avatar-mini">${esc(r.teacher ? r.teacher[0].toUpperCase() : 'T')}</div>
            <div class="teacher-meta-group">
              <span class="teacher-name-text">${esc(r.teacher)}</span>
              ${r.reason ? `<span class="teacher-reason-pill" title="${esc(r.reason)}">✨ ${esc(r.reason)}</span>` : ''}
            </div>
          </div>
        </td>
        <td>
          <div class="time-cell">
            <span class="day-chip ${dayClass}">${esc(r.day)}</span>
            <span class="time-text">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              ${esc(r.start_time)} – ${esc(r.end_time)}
            </span>
          </div>
        </td>
        <td>
          <div class="room-cell">
            <span class="room-chip">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/></svg>
              ${esc(r.room)}
            </span>
            ${r.class_type ? `<span class="type-tag">${esc(r.class_type)}</span>` : ''}
          </div>
        </td>
        <td>
          <span class="status-pill-badge ${isProposed ? 'proposed' : isReadOnly ? 'readonly' : 'active'}">
            <span class="status-dot-mini"></span>
            ${isReadOnly ? 'Read-only' : isProposed ? 'Proposed Update' : 'Existing Active'}
          </span>
        </td>
      </tr>
    `;
  }).join('');

  $('empty').hidden = !!visible.length;
}

function showProposal(data) {
  clearProposal();
  proposal = data.changes || [];
  proof = data.proposal_token || '';
  $('proposal').hidden = !proposal.length;

  $('change-list').innerHTML = proposal.map(c => `
    <article class="proposal-change-card">
      <div class="proposal-card-badge ${c.action === 'update' ? 'replacement' : 'new'}">
        ${c.action === 'update' ? 'Replacement Session' : 'New Scheduled Session'}
      </div>
      <div class="proposal-slot-details">
        <span class="slot-time"><strong>${esc(c.day_of_week)}</strong> ${esc(c.start_time)}–${esc(c.end_time)}</span>
        <span class="slot-room">📍 ${esc(c.room_location)}</span>
      </div>
      <p class="proposal-reason">${esc(c.reason)}</p>
      ${c.before ? `
        <div class="before-diff-box">
          <span class="diff-tag">Replaces previous:</span>
          <span>${esc(c.before.day_of_week)} ${esc(c.before.start_time)}–${esc(c.before.end_time)} · ${esc(c.before.room_location)}</span>
        </div>
      ` : ''}
    </article>
  `).join('');

  if (!proposal.length) return;
  const card = message('ai', `**${proposal.length} validated timetable changes** are ready for review. Check the proposal details below:`, false);
  const facts = document.createElement('p');
  const first = rows.find(r => r.proposed) || rows[0];
  facts.textContent = first ? `${first.department} · Semester ${first.semester} · Section ${first.section} · ${first.academic_year}` : '';
  card.append(facts);
  const courses = document.createElement('div');
  courses.className = 'result-courses';
  [...new Map(rows.filter(r => r.proposed).map(r => [r.course_id, r])).values()].forEach(r => {
    const item = document.createElement('span');
    item.textContent = `${r.course_code} · ${r.credit_hours} CH · ${r.teacher}`;
    courses.append(item);
  });
  card.append(courses);
  const actions = document.createElement('div');
  actions.className = 'result-actions';
  [
    ['Preview Timetable', () => $('preview').scrollIntoView({ behavior: 'smooth' })],
    ['Download PDF', download],
    ['Regenerate', () => generate(lastRequest)],
    ['Approve & Lock', approval],
    ['Reject', reject]
  ].forEach(([name, fn]) => {
    const b = document.createElement('button');
    b.textContent = name;
    b.onclick = fn;
    actions.append(b);
  });
  card.append(actions);
  scrollChat();
}

async function generate(text, analysis = false) {
  if (busy) return;
  if (attachments.some(a => !a.reviewed)) {
    message('ai', 'Please wait for all attached documents to finish parsing before sending.');
    return;
  }
  setBusy(true);
  try {
    const data = await call('/chat', {
      ...scope(),
      conversation_state: conversationState,
      message: text,
      history: history.slice(-25).map(h => ({ role: h.role, content: h.content })),
      document_reviewed: attachments.every(a => a.reviewed),
      document_text: reference(),
      document_name: attachments.map(a => a.file.name).join(', ').slice(0, 255)
    });
    if (data.preview_schedules || data.mode === 'general') clearProposal();
    render(data);
    message('ai', data.reply || data.summary || 'Analysis complete.');
    if ((data.changes || []).length) {
      lastRequest = text;
      showProposal(data);
    } else if (data.mode === 'general' && data.preview_schedules?.length) {
      lastRequest = text;
      const card = message('ai', 'Read-only General/Test timetable ready.', false);
      const actions = document.createElement('div');
      actions.className = 'result-actions';
      [
        ['Preview Timetable', () => $('preview').scrollIntoView({ behavior: 'smooth' })],
        ['Download PDF', download],
        ['Regenerate', () => generate('Regenerate the timetable')]
      ].forEach(([name, fn]) => {
        const b = document.createElement('button');
        b.textContent = name;
        b.onclick = fn;
        actions.append(b);
      });
      card.append(actions);
    }
  } catch (error) {
    message('ai', 'Unable to complete the request: ' + error.message);
    $('status').textContent = error.message;
  } finally {
    setBusy(false);
  }
}

function reject() {
  if (busy) return;
  clearProposal();
  conversationState.preview = [];
  try { sessionStorage.setItem(historyKey + ':state', JSON.stringify(conversationState)); } catch (e) { console.warn(e); }
  rows = conversationState.mode === 'general' ? [] : baseRows;
  renderPreview();
  message('ai', 'Proposal rejected. No database records were changed.');
}

function approval() {
  if (busy || !proposal.length) return;
  $('approval-summary').textContent = `Save these ${proposal.length} validated timetable sessions? Approved timetables can be published to student and teacher portals.`;
  $('approval-dialog').showModal();
}

async function confirmApproval() {
  $('approval-dialog').close();
  setBusy(true);
  try {
    const data = await call('/approve', { approved: true, proposal_token: proof, changes: proposal });
    clearProposal();
    message('ai', data.message);
    localStorage.setItem('timetable-updated', String(Date.now()));
    const fresh = await call('/analyze', scope());
    render(fresh);
  } catch (error) {
    message('ai', 'Approval failed: ' + error.message);
  } finally {
    setBusy(false);
  }
}

async function download() {
  if (!rows.length) return message('ai', 'Generate or analyze a timetable first before exporting.');
  try {
    const response = await fetch(API + '/pdf', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ schedules: rows })
    });
    if (!response.ok) throw Error('PDF export failed');
    const url = URL.createObjectURL(await response.blob());
    const a = document.createElement('a');
    a.href = url;
    a.download = 'university-timetable.pdf';
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  } catch (error) {
    message('ai', error.message);
  }
}

function renderAttachments() {
  const container = $('attachments');
  if (!container) return;
  container.replaceChildren();

  attachments.forEach(a => {
    const chip = document.createElement('div');
    chip.className = 'composer-attachment-chip ' + (a.reviewed ? 'is-ready' : 'is-loading');

    const icon = document.createElement('div');
    icon.className = 'chip-icon';
    icon.innerHTML = getFileIconSvg(a.file.name);

    const info = document.createElement('div');
    info.className = 'chip-info';
    const name = document.createElement('span');
    name.className = 'chip-name';
    name.textContent = a.file.name;
    const size = document.createElement('span');
    size.className = 'chip-size';
    size.textContent = `${(a.file.size / 1024).toFixed(1)} KB · ${a.status}`;
    info.append(name, size);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'chip-remove-btn';
    removeBtn.setAttribute('aria-label', 'Remove attachment');
    removeBtn.innerHTML = '×';
    removeBtn.onclick = () => {
      attachments = attachments.filter(x => x !== a);
      if (a.url) URL.revokeObjectURL(a.url);
      renderAttachments();
    };

    chip.append(icon, info, removeBtn);
    container.append(chip);
  });
}

async function attach(files) {
  for (const file of Array.from(files)) {
    if (attachments.length >= 4) {
      message('ai', 'You can attach up to four references at a time.');
      break;
    }
    if (file.size > 5 * 1024 * 1024) {
      message('ai', `${file.name} exceeds the 5 MB limit.`);
      continue;
    }
    const item = {
      file,
      status: 'Extracting content…',
      reviewed: false,
      url: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    };
    attachments.push(item);
    renderAttachments();

    const form = new FormData();
    form.append('document', file);
    try {
      const response = await fetch(API + '/document', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token() },
        body: form
      });
      const data = await response.json();
      if (!response.ok) throw Error(data.detail || 'Extraction failed');
      item.text = data.text;
      item.facts = data.facts;
      item.reviewed = !!data.text?.trim();
      item.status = item.reviewed ? 'Parsed & Ready' : 'Empty file';
    } catch (error) {
      item.status = 'Extraction failed';
      message('ai', `Could not read ${file.name}: ${error.message}`);
    }
    renderAttachments();
  }
}

async function loadOptions() {
  if (optionsLoaded || optionsLoading) return;
  optionsLoading = true;
  try {
    const response = await fetch(API + '/options', { headers: headers() });
    if (!response.ok) throw Error('Sign in as an administrator to load timetable data.');
    const d = await response.json();
    for (const [id, list] of [
      ['academic_year', d.academic_years],
      ['department_id', d.departments],
      ['semester', d.semesters],
      ['section', d.sections],
      ['teacher_id', d.teachers],
      ['student_id', d.students]
    ]) {
      const select = $(id);
      if (!select) continue;
      list.forEach(item => {
        const o = document.createElement('option');
        o.value = item.id ?? item;
        o.textContent = item.name ?? item;
        select.append(o);
      });
    }
    $('status').textContent = 'Live database connected. Choose a scope or describe it in chat.';
    optionsLoaded = true;
  } catch (error) {
    $('status').textContent = error.message;
  } finally {
    optionsLoading = false;
  }
}

function autoResizeTextarea(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

const inputEl = $('chat-input');
if (inputEl) {
  inputEl.addEventListener('input', () => autoResizeTextarea(inputEl));
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      $('composer').requestSubmit();
    }
  });
}

$('composer').onsubmit = e => {
  e.preventDefault();
  const text = $('chat-input').value.trim();
  if ((!text && !attachments.length) || busy) return;

  const request = text || 'Use these attachments to prepare the timetable.';
  if (attachments.some(a => !a.reviewed)) {
    message('ai', 'Wait for file extraction to finish before sending.');
    return;
  }

  const sentFiles = attachments.map(a => ({ name: a.file.name, status: a.status }));
  message('user', request, true, sentFiles);
  $('chat-input').value = '';
  autoResizeTextarea($('chat-input'));

  if (/^(approve(?: and upload)?|confirm)[.!]?$/i.test(text)) {
    approval();
    return;
  }
  if (/^reject[.!]?$/i.test(text)) {
    reject();
    return;
  }
  if (/\b(download|export)\b/i.test(request)) {
    download();
    return;
  }
  if (/\b(system|university database|actual)\b/i.test(request)) {
    loadOptions();
  }
  generate(request);
};

document.querySelectorAll('[data-request]').forEach(b => {
  b.onclick = () => {
    const input = $('chat-input');
    input.value = b.dataset.request;
    autoResizeTextarea(input);
    input.focus();
  };
});

document.querySelectorAll('[data-attach]').forEach(b => {
  b.onclick = () => {
    $('file-input').accept = b.dataset.attach || '.pdf,.docx,.xlsx,.csv,.txt,.png,.jpg,.jpeg,.webp';
    $('file-input').click();
  };
});

$('file-input').onchange = e => {
  attach(e.target.files);
  e.target.value = '';
};

['dragenter', 'dragover'].forEach(name => $('composer').addEventListener(name, e => {
  e.preventDefault();
  $('composer').classList.add('is-dragging');
}));

['dragleave', 'drop'].forEach(name => $('composer').addEventListener(name, e => {
  e.preventDefault();
  $('composer').classList.remove('is-dragging');
}));

$('composer').addEventListener('drop', e => {
  e.preventDefault();
  attach(e.dataTransfer.files);
});

$('analyze').onclick = () => generate('Analyze selected timetable using university database', true);
$('generate').onclick = () => generate('Generate actual timetable using university database for selected scope');
$('regenerate').onclick = () => generate('Regenerate the timetable');
$('approve').onclick = approval;
$('reject').onclick = reject;
$('confirm-approval').onclick = confirmApproval;
$('cancel-approval').onclick = () => $('approval-dialog').close();
$('download').onclick = download;
$('view').onchange = () => {
  $('preview-filter').value = '';
  renderPreview();
};
$('preview-filter').onchange = renderPreview;

try {
  conversationState = JSON.parse(sessionStorage.getItem(historyKey + ':state') || '{}');
  rows = conversationState.preview || [];
} catch {
  conversationState = {};
}

// Restore previous messages from session history
history.forEach(h => message(h.role === 'user' ? 'user' : 'ai', h.content, false, h.files || []));

if (!history.length) {
  message('ai', '### Welcome to Timetable AI Assistant\n\nI can help you build and manage university timetables. You can:\n- Ask for **faculty workloads**, **course assignments**, or **available classrooms**.\n- Ask me to **generate a conflict-free timetable** for any department and semester.\n- **Attach curriculum documents or spreadsheets** (PDF, Word, Excel, CSV, Images) for instant schedule planning.\n\nHow can I help you today?', false);
}

$('status').textContent = 'Ready. Chat with the assistant or configure your timetable above.';
renderPreview();

$('department_id').addEventListener('focus', () => {
  if ($('department_id').options.length <= 1) loadOptions();
}, { once: true });
