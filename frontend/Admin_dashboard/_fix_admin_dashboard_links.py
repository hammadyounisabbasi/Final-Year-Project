from pathlib import Path

replacements = {
    'data-page="academic_integrity"': 'data-page="academic-integrity"',
    'data-page="exam_monitoring"': 'data-page="exam-monitoring"',
    'data-page="student_management"': 'data-page="student-management"',
    'data-page="Faculty_management"': 'data-page="faculty-management"',
    'data-page="finance_agent"': 'data-page="finance-agent"',
    'data-page="research_agent"': 'data-page="research-agent"',
    'data-page="hostel_agent"': 'data-page="hostel-agent"',
    'data-page="library_agent"': 'data-page="library-agent"',
    'data-page="security_agent"': 'data-page="security-agent"',
    '../login_page/admin-../login_page/admin-login.html': '../login_page/admin-login.html',
    'href="logout.html"': 'href="../login_page/admin-login.html"',
    'href="support.html"': 'href="coming-soon.html?feature=Support"',
    'href="help-support.html"': 'href="coming-soon.html?feature=Support"',
    'href="help-coming-soon.html?feature=Support"': 'href="coming-soon.html?feature=Support"',
    'href="reports.html"': 'href="coming-soon.html?feature=Reports"',
    'href="analytics.html"': 'href="coming-soon.html?feature=Analytics"',
    'href="settings.html"': 'href="coming-soon.html?feature=Settings"',
    'href="communication.html"': 'href="coming-soon.html?feature=Communication"',
    'href="communication-agent.html"': 'href="coming-soon.html?feature=Communication%20Agent"',
    'href="student-services.html"': 'href="coming-soon.html?feature=Student%20Services"',
    'href="admission-agent.html"': 'href="coming-soon.html?feature=Admission%20Agent"',
    'href="it-helpdesk.html"': 'href="coming-soon.html?feature=IT%20Helpdesk"',
    'href="audit-logs.html"': 'href="coming-soon.html?feature=Audit%20Logs"',
    'href="hostel-management.html"': 'href="coming-soon.html?feature=Hostel%20Management"',
    'href="security-operations.html"': 'href="coming-soon.html?feature=Security%20Operations"',
}

base_dir = Path('.')
html_paths = sorted(base_dir.glob('*.html'))
changed_files = []
for path in html_paths:
    text = path.read_text(encoding='utf-8', errors='ignore')
    new_text = text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8', newline='\n')
        changed_files.append(path.name)

# Update dashboard.js route map
route_map_block = '''const routes = {
        dashboard: "dashboard.html",
        "academic-integrity": "academic-integrity.html",
        academic_integrity: "academic-integrity.html",
        "clerk-watchdog": "clerk-watchdog.html",
        clerk_watchdog: "clerk-watchdog.html",
        "exam-monitoring": "exam-monitoring.html",
        exam_monitoring: "exam-monitoring.html",
        "student-management": "student-management.html",
        student_management: "student-management.html",
        "faculty-management": "faculty-management.html",
        Faculty_management: "faculty-management.html",
        "finance-agent": "finance-agent.html",
        finance_agent: "finance-agent.html",
        "hr-administration": "hr-administration.html",
        hr_administration: "hr-administration.html",
        "hostel-agent": "hostel-agent.html",
        hostel_agent: "hostel-agent.html",
        "research-agent": "research-agent.html",
        research_agent: "research-agent.html",
        "library-agent": "library-agent.html",
        library_agent: "library-agent.html",
        "security-agent": "security-agent.html",
        security_agent: "security-agent.html",
        "communication-agent": "coming-soon.html?feature=Communication%20Agent",
        "student-services": "coming-soon.html?feature=Student%20Services",
        "admission-agent": "coming-soon.html?feature=Admission%20Agent",
        "it-helpdesk": "coming-soon.html?feature=IT%20Helpdesk",
        "audit-logs": "coming-soon.html?feature=Audit%20Logs",
        "hostel-management": "coming-soon.html?feature=Hostel%20Management",
        "security-operations": "coming-soon.html?feature=Security%20Operations",
        reports: "coming-soon.html?feature=Reports",
        analytics: "coming-soon.html?feature=Analytics",
        settings: "coming-soon.html?feature=Settings",
        support: "coming-soon.html?feature=Support"
    };'''

dashboard_js = base_dir / 'dashboard.js'
if dashboard_js.exists():
    text = dashboard_js.read_text(encoding='utf-8', errors='ignore')
    new_text = text
    start = text.find('const routes = {')
    end = text.find('};', start)
    if start != -1 and end != -1:
        end += 2
        new_text = text[:start] + route_map_block + text[end:]
        if new_text != text:
            dashboard_js.write_text(new_text, encoding='utf-8', newline='\n')
            changed_files.append('dashboard.js')

# Create acoming-soon.html placeholder if missing
coming_path = base_dir / 'coming-soon.html'
if not coming_path.exists():
    coming_path.write_text(
        '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coming Soon - Admin Dashboard</title>
    <style>
        body { margin: 0; font-family: Inter, system-ui, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: rgba(15,23,42,0.95); border: 1px solid rgba(148,163,184,0.18); border-radius: 24px; padding: 40px; max-width: 520px; text-align: center; box-shadow: 0 30px 80px rgba(15,23,42,0.45); }
        h1 { margin: 0 0 18px; font-size: clamp(2rem, 4vw, 3rem); color: #fff; }
        p { color: #cbd5e1; line-height: 1.75; margin-bottom: 28px; }
        .feature { font-weight: 700; color: #38bdf8; }
        .button { display: inline-flex; align-items: center; justify-content: center; padding: 14px 24px; border-radius: 999px; background: #2563eb; color: white; text-decoration: none; font-weight: 600; transition: background 0.2s ease; }
        .button:hover { background: #1d4ed8; }
        .note { margin-top: 18px; color: #94a3b8; font-size: 0.95rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Feature Coming Soon</h1>
        <p>This page is a placeholder for features that are not yet available in the admin dashboard.</p>
        <p class="note">If you arrived here by mistake, use the link below to return to the dashboard.</p>
        <a class="button" href="dashboard.html">Return to Dashboard</a>
    </div>
</body>
</html>
''', encoding='utf-8', newline='\n')
    changed_files.append('coming-soon.html')

print('updated files:')
for name in changed_files:
    print(name)
