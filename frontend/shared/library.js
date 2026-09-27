(() => {
  'use strict';
  const root = document.getElementById('libraryApp');
  if (!root) return;
  const isAdmin = root.dataset.role === 'admin';
  const API = window.ACOS_CONFIG.API_BASE_URL;
  const authToken = () => localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || localStorage.getItem('token');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[char]);
  function renderAssistantText(value) {
    const lines = esc(value).split(/\r?\n/);
    const output = [];
    let inList = false;
    const inline = line => line
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
      .replace(/`([^`\n]+)`/g, '<code>$1</code>');
    const closeList = () => { if (inList) { output.push('</ul>'); inList = false; } };
    lines.forEach(line => {
      const heading = line.match(/^#{1,3}\s+(.+)$/);
      const bullet = line.match(/^\s*[*-]\s+(.+)$/);
      if (heading) {
        closeList();
        output.push(`<h4>${inline(heading[1])}</h4>`);
      } else if (bullet) {
        if (!inList) { output.push('<ul>'); inList = true; }
        output.push(`<li>${inline(bullet[1])}</li>`);
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
  let history = [], currentQuery = '';
  let stateOwner = 'anonymous';
  try {
    const profile = JSON.parse(localStorage.getItem('student_profile') || '{}');
    stateOwner = profile.user_id || profile.roll_number || profile.username || stateOwner;
  } catch (_) { /* The assistant still works when profile caching is unavailable. */ }
  const stateKey = `library-student-state:${location.pathname}:${stateOwner}`;
  let savedState = {};
  if (!isAdmin) {
    try { savedState = JSON.parse(sessionStorage.getItem(stateKey) || '{}'); } catch (_) { savedState = {}; }
  }
  function saveStudentState(next = {}) {
    if (isAdmin) return;
    savedState = { ...savedState, ...next };
    try { sessionStorage.setItem(stateKey, JSON.stringify(savedState)); } catch (_) { /* Storage is optional. */ }
  }

  async function api(path, options = {}) {
    const token = authToken();
    if (!token) throw new Error('Please sign in to your portal to use the library.');
    let response;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        response = await fetch(`${API}/library${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, ...options.headers } });
        break;
      } catch (_) {
        if (attempt === 2) {
          throw new Error(`Library service is unreachable at ${API}. Make sure the backend is running and retry.`);
        }
        await new Promise(resolve => setTimeout(resolve, 350));
      }
    }
    if (!response.ok) {
      let detail; try { detail = (await response.json()).detail; } catch (_) { }
      throw new Error(response.status === 401 ? 'Your session expired. Please sign in again.' : typeof detail === 'string' ? detail : `Library request failed (${response.status}). Please retry.`);
    }
    if (options.blob) return { blob: await response.blob(), response };
    return response.json();
  }
  const post = (path, body) => api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  function status(message, error = false) { const el = document.getElementById('libStatus'); if (el) { el.textContent = message; el.className = error ? 'lib-status lib-error' : 'lib-status'; } }
  function bookCard(book) {
    const downloads = Number(book.download_count) || 0;
    return `<article class="lib-book" data-book-id="${book.book_id}">
      <div class="book-card-top">
        <div class="book-symbol" aria-hidden="true">📖</div>
        <span class="lib-download-badge" title="Total campus downloads" id="dl-badge-${book.book_id}">📥 ${downloads} download${downloads === 1 ? '' : 's'}</span>
      </div>
      <span class="muted">${esc(book.category || 'General')} · PDF</span>
      <h3>${esc(book.title)}</h3>
      <p class="muted author-line">${esc(book.author || 'Unknown author')}</p>
      <p class="download-note">Ready for secure download</p>
      <div class="book-actions">
        <button type="button" class="secondary" data-view="${book.book_id}">Details</button>
        <button type="button" data-download="${book.book_id}" data-title="${esc(book.title)}">Download PDF</button>
      </div>
    </article>`;
  }
  function bookCards(books) { return books.map(bookCard).join(''); }
  function externalSources(data) {
    const links = [...(data.sources || []), ...(data.search_links || [])].filter(source => /^https?:\/\//i.test(source.url));
    const intro = data.search_status === 'unavailable' ? 'Live external search is unavailable. Try one of these search links.' : 'Additional resources for this topic';
    return `<div class="external-sources"><h3>Beyond the campus collection</h3><p class="muted">${intro}</p>${links.map(source => `<a class="lib-source" href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗<small>${esc(source.kind)} · ${esc(source.description)}</small></a>`).join('')}</div>`;
  }
  const studentMetrics = `<div class="student-stats-grid" id="studentStatsGrid">
    <div class="stat-card">
      <div class="stat-icon-wrap blue"><i data-lucide="book-open"></i></div>
      <div class="stat-info"><h3 id="statTotalBooks">—</h3><p>Available Books</p></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon-wrap emerald"><i data-lucide="download"></i></div>
      <div class="stat-info"><h3 id="statTotalDownloads">—</h3><p>Campus Downloads</p></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon-wrap purple"><i data-lucide="layers"></i></div>
      <div class="stat-info"><h3 id="statCategories">—</h3><p>Subject Categories</p></div>
    </div>
  </div>`;
  const catalog = isAdmin
    ? `<section class="lib-panel"><h2>Shared book catalog</h2><form id="searchForm" class="lib-toolbar"><input id="bookQuery" class="lib-search-input" aria-label="Search books and articles" maxlength="500" placeholder="Search books, topics, authors, or articles"><button type="submit">Search</button><button type="button" class="secondary" id="clearSearch">Show all</button><button type="button" class="secondary" id="syncBooks">Import Books folder</button></form><p id="catalogStatus" class="muted" role="status">Loading books…</p><div id="catalog" class="lib-grid"></div><div id="externalResults"></div></section>`
    : `${studentMetrics}<section class="lib-panel library-search-card"><div class="library-search-head"><h2>Find books and research</h2><p class="muted">Search the campus collection first, then explore relevant articles and learning resources.</p><form id="searchForm" class="library-search-form"><div class="library-search-field"><span aria-hidden="true">⌕</span><input id="bookQuery" aria-label="Search books and articles" maxlength="500" placeholder="Search books, authors, topics, or articles"></div><button type="submit" id="catalogSearchButton">Search</button><button type="button" class="secondary" id="clearSearch">Show all</button></form></div><div class="search-results-bar"><p id="catalogStatus" class="muted" role="status">Loading books…</p><div><button type="button" class="search-chip" data-topic="Artificial Intelligence">AI</button> <button type="button" class="search-chip" data-topic="programming">Programming</button> <button type="button" class="search-chip" data-topic="machine learning">Machine learning</button></div></div><div id="catalog" class="lib-grid" style="padding:0 24px 24px"></div><div id="externalResults" style="padding:0 24px 24px"></div></section>`;
  const adminUpload = `<section class="lib-panel"><h2>Add a book</h2><p class="muted">Upload a PDF from your computer. It will appear in every student's library. Maximum size: 50 MB.</p><form id="uploadForm" class="lib-form"><label>Book title<input name="title" required maxlength="250"></label><label>Author<input name="author" maxlength="200" placeholder="Unknown if unavailable"></label><label>Subject / category<input name="category" maxlength="100" placeholder="e.g. Computer Science"></label><label>Keywords<input name="keywords" maxlength="500" placeholder="e.g. neural networks, machine learning"></label><label class="span-full">Description<textarea name="description" rows="3" maxlength="4000"></textarea></label><label class="span-full">PDF book<input name="file" type="file" accept=".pdf,application/pdf" required></label><div><button type="submit">Upload book</button></div></form></section>`;
  const adminAnalytics = `<section class="lib-panel"><div class="lib-toolbar"><h2>Library activity</h2><label>Period<select id="period"><option value="7">Last 7 days</option><option value="30" selected>Last 30 days</option><option value="90">Last 90 days</option><option value="3650">Last 10 years</option></select></label><button id="refreshAnalytics" class="secondary">Refresh activity</button></div><div id="metrics" class="lib-metrics"></div><div id="analytics"></div></section>`;
  const assistantGreeting = 'Welcome to the University Library. I can help you find books, discover research articles, and choose resources for your studies. What would you like to explore?';
  const floatingChat = `<button class="library-chat-launcher" id="libraryChatLauncher" aria-label="Open Library Assistant" aria-expanded="false" title="Ask Library Assistant">🤖</button><section id="assistant" class="library-chat-drawer" hidden aria-label="Library Assistant"><header class="library-chat-header"><div class="library-chat-title"><span aria-hidden="true">🤖</span><span>Library Assistant</span></div><div class="library-chat-actions"><button id="clearChat" type="button" title="Start a new chat" aria-label="Start a new chat">↺</button><button id="closeLibraryChat" type="button" title="Close assistant" aria-label="Close assistant">×</button></div></header><div class="library-chat-body" id="chatLog" role="log" aria-live="polite"><div class="lib-message"><strong>Library Assistant</strong><div class="message-text">${assistantGreeting}</div></div></div><form id="chatForm" class="library-chat-footer"><textarea id="chatInput" aria-label="Message the library assistant" placeholder="Ask about a book or topic…" rows="1" maxlength="1500" required></textarea><button type="submit" aria-label="Send message" title="Send">➤</button></form><p id="chatStatus" class="library-chat-status" role="status"></p></section><div id="bookDetails" hidden></div>`;
  root.innerHTML = `<section class="lib-hero"><h1>${isAdmin ? 'Library management' : 'Your next discovery starts here'}</h1><p>${isAdmin ? 'Build a shared collection and understand what students are reading, searching for, and downloading.' : 'Explore your campus collection, download books, and ask your library assistant for reading advice and research sources.'}</p></section><div id="libStatus" class="lib-status" role="status" aria-live="polite"></div>${isAdmin ? adminUpload + adminAnalytics : ''}${catalog}${isAdmin ? '' : floatingChat}`;

  function updateStudentMetrics(summary) {
    if (isAdmin) return;
    const totalBooksEl = document.getElementById('statTotalBooks');
    const totalDownloadsEl = document.getElementById('statTotalDownloads');
    const categoriesEl = document.getElementById('statCategories');
    if (!totalBooksEl || !totalDownloadsEl || !categoriesEl) return;
    totalBooksEl.textContent = Number(summary.books) || 0;
    totalDownloadsEl.textContent = Number(summary.downloads) || 0;
    categoriesEl.textContent = Number(summary.categories) || 0;
    if (window.lucide) window.lucide.createIcons();
  }

  function renderBooks(books) {
    document.getElementById('catalog').innerHTML = books.length ? bookCards(books) : '<p class="muted">No campus matches found. Try a broader topic or ask the Library Assistant for external resources.</p>';
    document.getElementById('catalogStatus').textContent = books.length ? `${books.length} book${books.length === 1 ? '' : 's'} ${currentQuery ? 'found for this search' : 'available in the collection'}.` : 'No campus matches found.';
  }

  async function refreshStudentAnalytics() {
    if (isAdmin) return;
    updateStudentMetrics(await api('/analytics/summary'));
  }

  async function loadCatalog() {
    const data = await api(`/books?q=${encodeURIComponent(currentQuery)}`);
    renderBooks(data.books);
    refreshStudentAnalytics().catch(error => status(error.message, true));
    return data.books;
  }

  function closeDetails() {
    const holder = document.getElementById('bookDetails');
    if (holder) {
      holder.hidden = true;
      holder.innerHTML = '';
      saveStudentState({ detail: null });
    }
  }

  function showDetails(book) {
    const holder = document.getElementById('bookDetails');
    if (!holder) return;
    const downloads = Number(book.download_count) || 0;
    holder.hidden = false;
    holder.className = 'library-dialog-backdrop';
    holder.innerHTML = `<div class="library-dialog" role="dialog" aria-modal="true" aria-labelledby="bookDetailTitle">
      <header class="library-dialog-header">
        <h2 id="bookDetailTitle">Book details</h2>
        <button type="button" class="dialog-close" data-close-details aria-label="Close details">×</button>
      </header>
      <div class="library-dialog-body">
        <div class="book-detail-icon" aria-hidden="true">📖</div>
        <h3>${esc(book.title)}</h3>
        <div class="book-detail-meta">
          <div><span>Author</span>${esc(book.author || 'Unknown author')}</div>
          <div><span>Category</span>${esc(book.category || 'General')}</div>
          <div><span>Downloads</span><strong id="modal-dl-count-${book.book_id}">${downloads} campus download${downloads === 1 ? '' : 's'}</strong></div>
          <div><span>Format</span>PDF (Full Access)</div>
          <div><span>Availability</span>${esc(book.status || ((book.available_copies || 0) > 0 ? 'Available' : 'Unavailable'))}</div>
          <div><span>Copies available</span>${esc(book.available_copies ?? 'Not recorded')}</div>
          ${book.publisher ? `<div><span>Publisher</span>${esc(book.publisher)}</div>` : ''}
          ${book.publication_year ? `<div><span>Published</span>${esc(book.publication_year)}</div>` : ''}
          ${book.edition ? `<div><span>Edition</span>${esc(book.edition)}</div>` : ''}
          ${book.language ? `<div><span>Language</span>${esc(book.language)}</div>` : ''}
          ${book.isbn ? `<div><span>ISBN</span>${esc(book.isbn)}</div>` : ''}
          ${book.shelf_location ? `<div><span>Shelf location</span>${esc(book.shelf_location)}</div>` : ''}
        </div>
        <h4>About this book</h4>
        <p>${esc(book.description || 'No description has been added yet. You can still download the PDF and review its contents.')}</p>
        <div class="book-actions">
          <button type="button" class="secondary" data-close-details>Close</button>
          <button type="button" data-download="${book.book_id}" data-title="${esc(book.title)}">Download PDF</button>
        </div>
      </div>
    </div>`;
    holder.querySelector('[data-close-details]')?.focus();
    saveStudentState({ detail: book });
  }

  async function downloadBook(id, button) {
    const label = button.textContent;
    button.disabled = true;
    button.textContent = 'Preparing…';
    try {
      const { blob, response } = await api(`/books/${id}/download`, { blob: true });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${String(button.dataset.title || 'library-book').replace(/[\\/:*?"<>|]/g, '').slice(0, 150) || 'library-book'}.pdf`;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      status('Your PDF download has started.');

      // This value is calculated after the backend commits the activity record.
      const authoritativeCount = Number(response.headers.get('X-Library-Download-Count'));
      const badge = document.getElementById(`dl-badge-${id}`);
      if (badge) {
        const curCount = Number.isFinite(authoritativeCount) ? authoritativeCount : parseInt(badge.textContent.replace(/\D/g, '') || '0', 10) + 1;
        badge.textContent = `📥 ${curCount} download${curCount === 1 ? '' : 's'}`;
      }
      const modalCount = document.getElementById(`modal-dl-count-${id}`);
      if (modalCount) {
        const curCount = Number.isFinite(authoritativeCount) ? authoritativeCount : parseInt(modalCount.textContent.replace(/\D/g, '') || '0', 10) + 1;
        modalCount.textContent = `${curCount} campus download${curCount === 1 ? '' : 's'}`;
      }
      const totalDlEl = document.getElementById('statTotalDownloads');
      if (totalDlEl && totalDlEl.textContent !== '—') {
        totalDlEl.textContent = parseInt(totalDlEl.textContent || '0', 10) + 1;
      }
      refreshStudentAnalytics().catch(error => status(error.message, true));
    }
    catch (error) { status(error.message, true); }
    finally { button.disabled = false; button.textContent = label; }
  }

  root.addEventListener('click', async event => {
    const target = event.target.closest('[data-download],[data-view],[data-close-details],[data-topic]');
    if (!target) {
      // If clicking backdrop outside modal dialog, close modal
      if (event.target.id === 'bookDetails') closeDetails();
      return;
    }
    if (target.dataset.closeDetails !== undefined) return closeDetails();
    if (target.dataset.topic) {
      document.getElementById('bookQuery').value = target.dataset.topic;
      document.getElementById('searchForm').requestSubmit();
      return;
    }
    if (target.dataset.download) return downloadBook(target.dataset.download, target);
    if (target.dataset.view) {
      target.disabled = true;
      try {
        const bookData = await post(`/books/${target.dataset.view}/view`, {});
        showDetails(bookData);
      } catch (error) {
        status(error.message, true);
      } finally {
        target.disabled = false;
      }
    }
  });

  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeDetails(); });

  document.getElementById('searchForm').onsubmit = async event => {
    event.preventDefault();
    const query = document.getElementById('bookQuery').value.trim();
    const button = document.getElementById('catalogSearchButton') || event.submitter;
    if (!query) {
      currentQuery = '';
      document.getElementById('externalResults').innerHTML = '';
      return loadCatalog().catch(error => status(error.message, true));
    }
    button.disabled = true;
    button.textContent = 'Searching…';
    status('Searching the campus collection and verified external sources…');
    try {
      currentQuery = query;
      const data = await post('/search', { query });
      renderBooks(data.books);
      document.getElementById('externalResults').innerHTML = externalSources(data);
      status('Search complete. Browse campus books or open an external source in a new tab.');
    } catch (error) {
      status(error.message, true);
    } finally {
      button.disabled = false;
      button.textContent = 'Search';
    }
  };

  document.getElementById('clearSearch').onclick = () => {
    currentQuery = '';
    document.getElementById('bookQuery').value = '';
    document.getElementById('externalResults').innerHTML = '';
    closeDetails();
    loadCatalog().catch(error => status(error.message, true));
  };

  if (isAdmin) {
    const table = (title, rows, columns) => `<h3 style="margin:24px 0 12px">${title}</h3><div class="lib-table-wrap"><table><thead><tr>${columns.map(([, label]) => `<th>${label}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.map(row => `<tr>${columns.map(([key]) => `<td>${esc(row[key] ?? '—')}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${columns.length}">No activity in this period.</td></tr>`}</tbody></table></div>`;
    const loadAnalytics = async () => {
      const data = await api(`/analytics?days=${document.getElementById('period').value}`);
      document.getElementById('metrics').innerHTML = Object.entries({ books:'Available books', downloads:'Downloads', downloaders:'Unique downloaders', searches:'Searches', questions:'Chat questions', active_users:'Active students' }).map(([key, label]) => `<div class="lib-metric"><strong>${data.summary[key]}</strong><span class="muted">${label}</span></div>`).join('');
      document.getElementById('analytics').innerHTML = table('Downloads and discovery by book', data.books, [['title','Book'],['downloads','Downloads'],['downloaders','Unique downloaders'],['views','Views'],['search_matches','Search matches']]) + table('Department interests', data.departments, [['department','Department'],['title','Book'],['students','Students'],['downloads','Downloads'],['views','Views'],['search_matches','Search matches']]) + table('Student interests', data.interests, [['student','Student'],['roll_number','Roll number'],['department','Department'],['title','Book'],['downloads','Downloads'],['views','Views'],['search_matches','Search matches'],['interest_score','Interest score']]);
    };
    document.getElementById('uploadForm').onsubmit = async event => {
      event.preventDefault();
      const form = event.target, button = event.submitter, file = form.elements.file.files[0];
      if (file.size > 50 * 1024 * 1024) return status('Maximum book size is 50 MB.', true);
      button.disabled = true;
      status('Uploading book…');
      try {
        await api('/books', { method: 'POST', body: new FormData(form) });
        form.reset();
        currentQuery = '';
        await Promise.all([loadCatalog(), loadAnalytics()]);
        status('Book added. It is now available to every student.');
      } catch (error) {
        status(error.message, true);
      } finally {
        button.disabled = false;
      }
    };
    document.getElementById('syncBooks').onclick = async () => {
      try {
        await post('/sync', {});
        await loadCatalog();
        status('Books folder imported.');
      } catch (error) {
        status(error.message, true);
      }
    };
    document.getElementById('refreshAnalytics').onclick = () => loadAnalytics().catch(error => status(error.message, true));
    document.getElementById('period').onchange = () => loadAnalytics().catch(error => status(error.message, true));
    loadAnalytics().catch(error => status(error.message, true));
  } else {
    const drawer = document.getElementById('assistant'), launcher = document.getElementById('libraryChatLauncher'), input = document.getElementById('chatInput'), log = document.getElementById('chatLog');
    const chatRecords = (Array.isArray(savedState.chatRecords) ? savedState.chatRecords : [])
      .filter(record => !(record.role === 'assistant' && String(record.text || '').startsWith('I could not complete that request:')));
    history = chatRecords
      .filter(record => ['user', 'assistant'].includes(record.role) && typeof record.text === 'string' && record.text.trim())
      .map(record => ({ role: record.role, content: record.text.trim() }))
      .slice(-12);
    const openChat = () => { drawer.hidden = false; launcher.setAttribute('aria-expanded', 'true'); saveStudentState({ chatOpen: true }); input.focus(); };
    const closeChat = () => { drawer.hidden = true; launcher.setAttribute('aria-expanded', 'false'); saveStudentState({ chatOpen: false }); launcher.focus(); };
    function responseText(data) {
      // Keep the UI compatible with the library API and common AI gateway shapes.
      const value = data?.reply ?? data?.response ?? data?.answer ?? data?.message?.content ?? data?.message;
      return typeof value === 'string' && value.trim()
        ? value.trim()
        : 'I received your request, but no readable answer was returned. Please try again.';
    }
    function message(role, text, resourceData = null, replaceElement = null) {
      // The portal can re-hydrate this page while an AI request is in flight.
      // Always target the live log instead of a stale element captured by an old handler.
      const activeLog = document.getElementById('chatLog');
      if (!activeLog) return null;
      // If the portal refreshed its library area while the request was in
      // flight, use the current chat log. Otherwise update the visible
      // "checking" bubble in place rather than creating a second reply.
      const canReplace = replaceElement && activeLog.contains(replaceElement);
      const el = canReplace ? replaceElement : document.createElement('div');
      el.className = `lib-message ${role}`;
      el.innerHTML = `<strong>${role === 'user' ? 'You' : 'Library Assistant'}</strong><div class="message-text"></div>`;
      const textElement = el.querySelector('.message-text');
      if (role === 'assistant') textElement.innerHTML = renderAssistantText(text);
      else textElement.textContent = String(text || '');
      if (resourceData && resourceData.show_resources !== false) {
        try {
          const resources = document.createElement('div');
          resources.innerHTML = ((resourceData.books || []).length ? `<h4>In your library</h4><div class="lib-grid">${bookCards(resourceData.books)}</div>` : '') + externalSources(resourceData);
          el.append(resources);
        } catch (_) {
          // Source cards are supplementary; they must never block the answer itself.
        }
      }
      if (!canReplace) activeLog.append(el);
      if (role === 'assistant' && resourceData) {
        // Resource cards can make the completed reply much taller than the
        // drawer. Keep the answer itself in view instead of scrolling past it
        // to the final source card.
        const logRect = activeLog.getBoundingClientRect();
        const messageRect = el.getBoundingClientRect();
        activeLog.scrollTop += messageRect.top - logRect.top - 5;
      } else {
        activeLog.scrollTop = activeLog.scrollHeight;
      }
      return el;
    }
    if (chatRecords.length) {
      log.innerHTML = '';
      chatRecords.forEach(record => message(record.role, record.text, record.resources || null));
    }
    if (savedState.chatOpen) openChat();
    launcher.onclick = openChat;
    document.getElementById('closeLibraryChat').onclick = closeChat;
    document.getElementById('clearChat').onclick = () => {
      history = [];
      chatRecords.length = 0;
      log.innerHTML = `<div class="lib-message"><strong>Library Assistant</strong><div class="message-text">${assistantGreeting}</div></div>`;
      document.getElementById('chatStatus').textContent = '';
      saveStudentState({ chatRecords: [], chatOpen: true });
    };
    document.getElementById('chatForm').onsubmit = async event => {
      event.preventDefault();
      const value = input.value.trim();
      if (!value) return;
      const send = event.target.querySelector('button[type="submit"]');
      send.disabled = true;
      message('user', value);
      const pendingReply = message('assistant', 'Checking the library and preparing your answer…');
      chatRecords.push({ role: 'user', text: value });
      saveStudentState({ chatRecords, chatOpen: true });
      input.value = '';
      document.getElementById('chatStatus').textContent = 'Finding books and sources…';
      try {
        const data = await post('/chat', { message: value, history: history.slice(-12) });
        const reply = responseText(data);
        // Render the answer before optional catalog/source cards are processed.
        message('assistant', reply, data, pendingReply);
        history.push({ role:'user', content:value }, { role:'assistant', content:reply.slice(0,3000) });
        chatRecords.push({ role: 'assistant', text: reply, resources: { books: data.books || [], sources: data.sources || [], search_links: data.search_links || [], search_status: data.search_status, show_resources: data.show_resources } });
        saveStudentState({ chatRecords, chatOpen: true });
        document.getElementById('chatStatus').textContent = data.provider === 'Catalog fallback' ? 'Showing catalog guidance while the AI provider is unavailable.' : '';
      } catch (error) {
        // Display failures inside the conversation so students never see a
        // silent assistant when a request cannot be completed.
        const readableError = error?.message || 'I could not reach the library service. Please try again.';
        message('assistant', `I could not complete that request: ${readableError}`, null, pendingReply);
        saveStudentState({ chatRecords, chatOpen: true });
        document.getElementById('chatStatus').textContent = readableError;
        input.value = value;
      } finally {
        send.disabled = false;
        input.focus();
      }
    };
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        document.getElementById('chatForm').requestSubmit();
      }
    });
  }

  // Rebuild any active details panel if this script is evaluated again after an async page update.
  if (!isAdmin && savedState.detail) showDetails(savedState.detail);

  loadCatalog().catch(error => {
    document.getElementById('catalogStatus').textContent = 'Unable to load the catalog.';
    status(error.message, true);
  });

  const toggle = document.getElementById('sidebarToggleBtn');
  if (toggle) toggle.onclick = () => document.querySelector('.sidebar')?.classList.toggle('mobile-open');

  document.getElementById('globalSearchInput')?.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      const bq = document.getElementById('bookQuery');
      if (bq) {
        bq.value = event.target.value;
        document.getElementById('searchForm').requestSubmit();
      }
    }
  });

  window.toggleNotifications = () => document.getElementById('notificationModal')?.classList.toggle('show');
  window.markNotificationsRead = () => document.getElementById('notificationModal')?.classList.remove('show');
  if (window.lucide) window.lucide.createIcons();
})();
