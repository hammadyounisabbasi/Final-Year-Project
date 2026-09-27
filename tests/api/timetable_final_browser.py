"""Real Admin UI acceptance flow, authenticated against a read-only DB backup.

Runs actual extraction, scheduling, HTTP downloads and Chrome. Only external AI
calls are disabled to verify graceful provider outage. Source DB is never written.
"""
import functools
import json
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tests/api'))
sys.path.insert(0, str(ROOT/'backend/backend'))
sys.path.append(str(ROOT/'tmp/timetable-deps'))
from test_timetable_agent import real_database_copy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin import router
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User, ClassSchedule, StudentTimetable, Course, Teacher, Enrollment
from app.services.timetable_conversation import validate
from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import uvicorn
import pymupdf

OUT = ROOT/'tmp/timetable-final'
OUT.mkdir(exist_ok=True)
TEXT = '''Semester 1
Section A
Courses:
CYB-101 Cyber Security Fundamentals — 3 CH
CSC-101 Programming Fundamentals — 4 CH
MTH-101 Calculus — 3 CH
Teachers:
Dr. Ahmed Khan — CYB-101
Mr. Usman Ali — CSC-101
Ms. Sana Malik — MTH-101
Rooms:
Cyber Security Lab
Computing Lab
Room 301'''
TABLE = [
    ['Course Code', 'Course Name', 'CH', 'Teacher'],
    ['CYB-101', 'Cyber Security Fundamentals', '3', 'Dr. Ahmed Khan'],
    ['CSC-101', 'Programming Fundamentals', '4', 'Mr. Usman Ali'],
    ['MTH-101', 'Calculus', '3', 'Ms. Sana Malik'],
]


def fixtures():
    from reportlab.pdfgen import canvas
    from docx import Document
    from openpyxl import Workbook
    from PIL import Image, ImageDraw, ImageFont
    lines = ['Department: Cybersecurity', 'Semester 1', 'Section A'] + [' | '.join(r) for r in TABLE]
    text = '\n'.join(lines)
    (OUT/'reference.txt').write_text(text, encoding='utf-8')
    (OUT/'reference.csv').write_text('\n'.join(','.join(r) for r in TABLE), encoding='utf-8')
    c = canvas.Canvas(str(OUT/'misleading-name.pdf'), pagesize=(1000, 500))
    for i, line in enumerate(lines): c.drawString(30, 470-i*26, line)
    c.save()
    d = Document(); d.add_paragraph('Department: Cybersecurity'); d.add_paragraph('Semester 1')
    t = d.add_table(rows=0, cols=4)
    for row in TABLE:
        cells = t.add_row().cells
        for cell, value in zip(cells, row): cell.text = value
    d.save(OUT/'reference.docx')
    wb = Workbook(); ws = wb.active
    for row in TABLE: ws.append(row)
    wb.save(OUT/'reference.xlsx')
    img = Image.new('RGB', (1800, 500), 'white'); draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 26)
    draw.text((30, 25), 'Department: Cybersecurity', fill='black', font=font)
    draw.text((30, 70), 'Semester 1', fill='black', font=font)
    for y, row in enumerate(TABLE):
        for x, value in zip([30, 220, 1000, 1130], row): draw.text((x, 135+y*65), value, fill='black', font=font)
    for ext in ['png', 'jpg', 'jpeg', 'webp']: img.save(OUT/f'reference.{ext}')
    c = canvas.Canvas(str(OUT/'scanned.pdf'), pagesize=(900, 250))
    c.drawImage(str(OUT/'reference.png'), 0, 0, width=900, height=250); c.save()
    wb = Workbook(); ws = wb.active; ws.append(['Course Code','Teacher'])
    for row in TABLE[1:]: ws.append([row[0],row[3]])
    ws.append(['CYB-201','Dr. Ahmed Khan']); wb.save(OUT/'teachers.xlsx')
    (OUT/'rooms.csv').write_text('Room\nCyber Security Lab\nComputing Lab\nRoom 301', encoding='utf-8')
    c = canvas.Canvas(str(OUT/'courses.pdf'), pagesize=(1000, 500))
    course_lines = ['Course Code | Course Name | CH | Semester'] + [' | '.join(row[:3]+['1']) for row in TABLE[1:]] + ['CYB-201 | Network Security | 3 | 2']
    for i, line in enumerate(course_lines): c.drawString(30, 470-i*26, line)
    c.save()


def main():
    fixtures()
    engine, factory = real_database_copy()
    db = factory(); admin = db.query(User).filter_by(role='admin').first()
    token = create_access_token({'sub': str(admin.user_id)})
    models = (ClassSchedule, StudentTimetable, Course, Teacher, Enrollment)
    def counts(): return {m.__name__: db.query(m).count() for m in models}
    def source_counts():
        import sqlite3
        with sqlite3.connect(f'file:{(ROOT/"database/university.db").as_posix()}?mode=ro', uri=True) as source:
            return {m.__name__: source.execute(f'SELECT COUNT(*) FROM "{m.__tablename__}"').fetchone()[0] for m in models}
    report = {'before': counts(), 'source_before':source_counts(), 'results': {}}
    app = FastAPI(); app.include_router(router)
    def session():
        connection = factory()
        try: yield connection
        finally: connection.close()
    app.dependency_overrides[get_db] = session
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
    backend = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8766, log_level='error'))
    threading.Thread(target=backend.run, daemon=True).start()
    while not backend.started: time.sleep(.05)
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1',8765), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with patch('app.services.ai_providers.AIProviderManager.generate_chat', return_value=(None,None)), sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=False)
            context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
            page = context.new_page(); page.set_default_timeout(60000)
            errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            page.add_init_script('localStorage.setItem("access_token",'+json.dumps(token)+')')
            page.route('http://127.0.0.1:8000/**', lambda route: route.continue_(url=route.request.url.replace(':8000', ':8766')))
            url = 'http://127.0.0.1:8765/frontend/Admin_dashboard/ai-timetable-creator.html'
            def reset():
                page.goto(url); page.evaluate('sessionStorage.clear()'); page.reload()
                page.get_by_label('Message timetable assistant', exact=True).wait_for()
            def send(message):
                page.get_by_label('Message timetable assistant', exact=True).fill(message)
                try:
                    with page.expect_response(lambda r: '/timetable-creator/chat' in r.url) as response:
                        page.locator('#send').click()
                except Exception:
                    report['failure_diagnostics']={'chat':page.locator('#chat').inner_text(),'errors':errors,
                                                   'status':page.locator('#status').inner_text()}
                    page.screenshot(path=str(OUT/'failure.png'),full_page=True)
                    raise
                res = response.value; assert res.status == 200, res.text()
                data = res.json()
                page.wait_for_function('!document.getElementById("send").disabled')
                assert data.get('changes', []) == [] or data.get('mode') == 'system'
                return data
            def ready(files):
                page.locator('#file-input').set_input_files([str(OUT/f) for f in files])
                page.wait_for_function('Array.from(document.querySelectorAll("#attachments .attachment small")).length === '+str(len(files))+' && Array.from(document.querySelectorAll("#attachments .attachment small")).every(e=>e.textContent.includes("Ready") || e.textContent.includes("Failed to read"))', timeout=120000)
                statuses = page.locator('#attachments').inner_text()
                assert 'Failed to read' not in statuses, statuses
            def preview(data, expected=10):
                assert len(data.get('preview_schedules', [])) == expected, data['reply']
                assert not validate(data['preview_schedules'], data['conversation_state']['general_facts'])
                assert page.locator('#preview-body tr.proposed').count() == expected
                assert page.locator('#metrics strong').first.inner_text() == str(expected)
                assert page.locator('#proposal').is_hidden()
                assert not data.get('proposal_token')
            reset()
            data = send('Create a timetable for Cybersecurity.')
            assert 'credit hours' in data['reply'] and 'teacher' in data['reply'] and not data.get('preview_schedules')
            report['results']['missing_details'] = 'passed'
            data = send(TEXT); preview(data)
            assert {r['teacher'] for r in data['preview_schedules']} == {'Dr. Ahmed Khan','Mr. Usman Ali','Ms. Sana Malik'}
            report['results']['chat_exact_data_credit_conflicts'] = '10 sessions, exact teachers, validated'
            data = send('Move CYB-101 to Tuesday.'); preview(data)
            assert all(r['day']=='Tuesday' for r in data['preview_schedules'] if r['course_code']=='CYB-101')
            data = send('Change its teacher to Dr. Farhan.'); preview(data)
            assert all(r['teacher']=='Dr. Farhan' for r in data['preview_schedules'] if r['course_code']=='CYB-101')
            report['results']['move_and_pronoun_teacher_edit'] = 'passed'
            old = data['preview_schedules']
            data = send('Regenerate only Wednesday.'); preview(data)
            assert [r for r in old if r['day']!='Wednesday'] == [r for r in data['preview_schedules'] if r['day']!='Wednesday']
            report['results']['day_regeneration'] = 'other days unchanged'
            for file in ['misleading-name.pdf','scanned.pdf','reference.png','reference.jpg','reference.jpeg','reference.webp','reference.docx','reference.csv','reference.xlsx','reference.txt']:
                reset(); send('Create a timetable for Cybersecurity Semester 1.')
                ready([file]); data=send('Generate the timetable using this file.'); preview(data)
                assert file in page.locator('#chat .sent-attachment').inner_text()
                report['results'][file] = 'visible attachment, actual extraction, 10 validated sessions'
                print('PASS', file, flush=True)
            reset(); send('Create Cybersecurity Semester 1 and 2 timetable.')
            ready(['teachers.xlsx','courses.pdf','rooms.csv']); data=send('Use these files.'); preview(data, 13)
            assert page.locator('#chat .sent-attachment').count() == 3
            report['results']['multiple_attachments'] = '13 sessions across two semesters'
            old = data['preview_schedules']; data=send('Regenerate Semester 2 only.'); preview(data, 13)
            assert [r for r in old if r['semester']==1] == [r for r in data['preview_schedules'] if r['semester']==1]
            report['results']['partial_regeneration'] = 'Semester 1 unchanged, global validation passed'
            with page.expect_request(lambda r: '/timetable-creator/pdf' in r.url) as exported, page.expect_download() as download:
                page.locator('#download').click()
            assert exported.value.post_data_json['schedules'] == data['preview_schedules']
            path = OUT/'latest-browser-download.pdf'; download.value.save_as(path)
            assert download.value.failure() is None
            with pymupdf.open(path) as pdf:
                text = '\n'.join(p.get_text() for p in pdf)
                assert 'Semester 1' in text and 'Semester 2' in text and 'Read-only General/Test timetable' in text
                for row in data['preview_schedules']:
                    for field in ['course_code','course_title','teacher','room','start_time','end_time']:
                        assert row[field] in text, (field,row[field])
                pdf[0].get_pixmap().save(OUT/'download-page-1.png')
            report['results']['browser_pdf_download'] = 'download saved and opened; both semesters and all latest row values verified'
            for width in [1440,768,390]:
                page.set_viewport_size({'width':width,'height':1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                page.screenshot(path=str(OUT/f'preview-{width}.png'), full_page=True)
            report['results']['responsive'] = 'desktop/tablet/mobile: no document overflow'
            reset()
            data=send('Generate a sample Cybersecurity timetable for all eight semesters yourself.')
            preview(data,72)
            with page.expect_download() as download: page.locator('#download').click()
            eight=OUT/'eight-semesters.pdf'; download.value.save_as(eight)
            with pymupdf.open(eight) as pdf:
                text='\n'.join(p.get_text() for p in pdf)
                for semester in range(1,9): assert f'Semester {semester}' in text
            report['results']['eight_semester_pdf'] = 'all eight cohort headings verified in browser download'
            data=send('Generate actual CS Semester 1 timetable using university database.')
            assert data['mode']=='system'
            report['results']['system'] = {'reply':data['reply'], 'changes':len(data['changes']), 'approval':data['approval_state']}
            data=send('Replace actual CS Semester 1 timetable using university database.')
            assert data['changes'] and data.get('proposal_token'), data['reply']
            assert page.locator('#proposal').is_visible()
            assert counts() == report['before']
            report['results']['system_approval_preview'] = 'signed proposal and approval control visible; no save performed'
            data=send('Generate actual Software Engineering Semester 1 timetable using university database.')
            assert not data['changes'] and data['blocking_reasons'], data['reply']
            report['results']['system_missing_records'] = data['reply']
            data=send('Create a General timetable for English Semester 1.')
            assert data['mode']=='general' and not data['changes']
            assert page.locator('#proposal').is_hidden()
            report['results']['mode_switch'] = 'General mode clears System approval controls'
            with page.expect_response(lambda r: '/timetable-creator/document' in r.url) as unreadable:
                page.locator('#file-input').set_input_files({'name':'unreadable.pdf','mimeType':'application/pdf','buffer':b'not a PDF'})
            assert unreadable.value.status == 422
            page.get_by_text('Failed to read:',exact=False).first.wait_for()
            assert 'unreadable.pdf' in page.locator('#chat').inner_text()
            report['results']['failed_attachment'] = 'filename and failed-read state visible; no fabricated content'
            assert not errors, errors
            report['browser_errors'] = errors
            browser.close()
        report['after'] = counts(); assert report['before'] == report['after']
        assert report['source_before'] == source_counts()
    finally:
        report['after'] = counts(); report['source_after'] = source_counts()
        (OUT/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        backend.should_exit=True; server.shutdown(); db.close(); engine.dispose()
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
