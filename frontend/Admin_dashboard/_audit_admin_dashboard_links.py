from pathlib import Path
import re

base_dir = Path('.')
html_files = sorted([p.name for p in base_dir.glob('*.html')])
print('HTML files found:')
for f in html_files:
    print(' -', f)
print('\nChecking links...')

missing = []
problematic = []
for path in sorted(base_dir.glob('*.html')):
    text = path.read_text(encoding='utf-8', errors='ignore')
    for match in re.finditer(r'href=["\\\']([^"\
#]+\.html)["\
\"]', text):
        target = match.group(1)
        if target.startswith('../login_page/') or target.startswith('coming-soon.html'):
            continue
        if target not in html_files:
            missing.append((path.name, target, text.count('\n', 0, match.start()) + 1))
    for match in re.finditer(r'data-page=["\
\"]([^"\
\"]+)["\
\"]', text):
        value = match.group(1)
        if value in {'logout', 'dashboard', 'clerk-watchdog', 'audit-logs', 'help-support', 'help', 'support', 'reports', 'analytics', 'settings'}:
            continue
        if value not in {
            'academic-integrity', 'academic_integrity', 'exam-monitoring', 'exam_monitoring',
            'student-management', 'student_management', 'faculty-management', 'Faculty_management',
            'finance-agent', 'finance_agent', 'hr-administration', 'hr_administration',
            'hostel-agent', 'hostel_agent', 'research-agent', 'research_agent',
            'library-agent', 'library_agent', 'security-agent', 'security_agent',
            'student-services', 'admission-agent', 'it-helpdesk', 'communication-agent',
            'reports', 'analytics', 'settings', 'support', 'help-support', 'help', 'login'
        }:
            problematic.append((path.name, 'data-page', value, text.count('\n', 0, match.start()) + 1))

print('\nMissing file targets:')
for fname, target, line in missing:
    print(f'{fname}:{line} -> {target}')
print(f'\nTotal missing targets: {len(missing)}')

print('\nProblematic data-page values:')
for fname, kind, value, line in problematic:
    print(f'{fname}:{line} -> {kind}={value}')
print(f'\nTotal problematic data-page values: {len(problematic)}')
