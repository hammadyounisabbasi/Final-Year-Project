(function () {
  const pages = [
    ['Core', 'dashboard.html', 'Dashboard', 'grid'], ['Core', 'academic-integrity.html', 'Academic Integrity', 'shield'], ['Core', 'clerk-watchdog.html', 'Clerk Watchdog', 'user'], ['Core', 'exam-monitoring.html', 'Exam Monitoring', 'file'], ['Core', 'student-management.html', 'Student Management', 'students'], ['Core', 'faculty-management.html', 'Faculty Management', 'faculty'], ['Core', 'finance-agent.html', 'Finance', 'wallet'],
    ['Management', 'ai-timetable-creator.html', 'AI Timetable Creator', 'flask'], ['Management', 'library-agent.html', 'Library', 'book'], ['Management', 'hostel-agent.html', 'Hostel', 'building'], ['Management', 'security-agent.html', 'Security', 'lock'], ['Management', 'hr-administration.html', 'HR Administration', 'users'],
    ['System', 'coming-soon.html?feature=Reports', 'Reports', 'chart'], ['System', 'coming-soon.html?feature=Analytics', 'Analytics', 'chart'], ['System', 'coming-soon.html?feature=Settings', 'Settings', 'settings']
  ];
  const icons = { grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>', shield: '<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z"/>', user: '<circle cx="12" cy="8" r="3"/><path d="M5 21c1-4 3-6 7-6s6 2 7 6"/>', file: '<path d="M6 3h9l3 3v15H6z"/><path d="M9 12h6M9 16h6"/>', students: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2"/><path d="M3 21c1-4 3-6 6-6s5 2 6 6M15 16c3 0 5 2 6 5"/>', faculty: '<path d="M4 20v-7l8-4 8 4v7"/><path d="M2 10l10-5 10 5M8 21v-5h8v5"/>', wallet: '<path d="M4 7h15a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h12"/><path d="M16 14h5"/>', flask: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/>', book: '<path d="M4 5a3 3 0 0 1 3-3h10v17H7a3 3 0 0 0-3 3z"/><path d="M4 5v16a3 3 0 0 1 3-3h13"/>', building: '<path d="M3 21h18M5 21V5h14v16M9 9h1M14 9h1M9 13h1M14 13h1"/>', lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>', users: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 21c1-4 3-6 6-6s5 2 6 6M15 16c3 0 5 2 6 5"/>', bell: '<path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>', chart: '<path d="M4 19V5M4 19h16M8 16v-4M12 16V8M16 16V5"/>', settings: '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.3.9a7 7 0 0 0-1.7-1L14.5 3h-5l-.4 2.5a7 7 0 0 0-1.7 1l-2.3-.9-2 3.4L5 11a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.3-.9a7 7 0 0 0 1.7 1l.5 2.5h5l.4-2.5a7 7 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5c.1-.3.1-.7.1-1z"/>' };
  const file = location.pathname.split('/').pop() || 'dashboard.html';
  const current = pages.find(p => p[1].split('?')[0] === file) || pages[0];
  const icon = key => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[key]}</svg>`;
  function nav() {
    return [...new Set(pages.map(page => page[0]))].map(group => {
      const links = pages.filter(page => page[0] === group).map(([, href, label, glyph]) =>
        `<a class="admin-shell-link ${href.split('?')[0] === file ? 'is-active' : ''}" href="${href}">${icon(glyph)}<span>${label}</span></a>`
      ).join('');
      return `<section class="admin-shell-section"><div class="admin-shell-section-title">${group}</div>${links}</section>`;
    }).join('');
  }
  function render() {
    document.body.classList.add('admin-shared-body');
    document.querySelectorAll('#sidebarOverlay, #sidebarBackdrop, .sidebar-overlay, .sidebar-backdrop').forEach(e => e.remove());
    const oldSidebar = document.querySelector('aside#sidebar, aside.sidebar');
    const sidebar = document.createElement('aside'); sidebar.className = 'admin-shell-sidebar'; sidebar.id = 'adminSharedSidebar'; sidebar.setAttribute('aria-label', 'Admin navigation');
    sidebar.innerHTML = `<div class="admin-shell-brand"><img src="../login_page/uoh-logo.png" alt="University of Haripur"><div><strong>University of Haripur</strong><span>Intelligent Ecosystem (IES)</span></div><button class="admin-shell-close" type="button" aria-label="Close navigation">×</button></div><nav class="admin-shell-nav">${nav()}</nav><div class="admin-shell-footer">Admin Portal · Secure Access</div>`;
    if (oldSidebar) oldSidebar.replaceWith(sidebar); else document.body.prepend(sidebar);
    const oldHeader = document.querySelector('header');
    const topbar = document.createElement('header'); topbar.className = 'admin-shell-topbar'; topbar.innerHTML = `<div class="admin-shell-topbar-left"><button class="admin-shell-menu" type="button" aria-label="Open navigation">☰</button><div class="admin-shell-page-label"><strong>${current[2]}</strong><span>Administration Portal</span></div></div><div class="admin-shell-profile"><span>Administrator</span><div class="admin-shell-avatar">A</div></div>`;
    if (oldHeader) { const frame = oldHeader.parentElement; oldHeader.replaceWith(topbar); frame.classList.add('admin-main-frame'); } else document.body.prepend(topbar);
    const overlay = document.createElement('div'); overlay.className = 'admin-shell-overlay'; overlay.setAttribute('aria-hidden', 'true'); document.body.append(overlay);
    const toggle = open => { sidebar.classList.toggle('is-open', open); overlay.classList.toggle('is-open', open); document.body.style.overflow = open ? 'hidden' : ''; };
    topbar.querySelector('.admin-shell-menu').addEventListener('click', () => toggle(true)); sidebar.querySelector('.admin-shell-close').addEventListener('click', () => toggle(false)); overlay.addEventListener('click', () => toggle(false));
    window.toggleSidebar = () => toggle(!sidebar.classList.contains('is-open'));
  }
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', render) : render();
}());
