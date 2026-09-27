import sys, threading, json, functools
import time
import uvicorn
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests/api'),str(ROOT/'backend/backend')]
sys.path.append(str(ROOT/'tmp/timetable-deps'))
from test_timetable_agent import real_database_copy
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.admin import router
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User, ClassSchedule, StudentTimetable
from app.api.student import router as student_router
from app.api.teacher import router as teacher_router
from unittest.mock import patch
from playwright.sync_api import sync_playwright
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler

engine,factory=real_database_copy();db=factory()
admin=db.query(User).filter_by(role='admin').first()
access=create_access_token({'sub':str(admin.user_id)})
app=FastAPI();app.include_router(router);app.include_router(student_router);app.include_router(teacher_router)
def test_database_session():
    session=factory()
    try: yield session
    finally: session.close()
app.dependency_overrides[get_db]=test_database_session
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
backend=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8766,log_level='error'))
threading.Thread(target=backend.run,daemon=True).start()
while not backend.started: time.sleep(.05)
client=TestClient(app)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(QuietHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]
with patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(None,None)),sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=False)
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(120000)
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.add_init_script('localStorage.setItem("access_token",'+json.dumps(access)+')')
    def bridge(route):
        route.continue_(url=route.request.url.replace(':8000',':8766'))
    page.route('http://127.0.0.1:8000/**',bridge)
    page.goto('http://127.0.0.1:8765/frontend/Admin_dashboard/ai-timetable-creator.html')
    page.get_by_text('Live database connected.',exact=False).wait_for()
    for width,height in [(1440,1000),(768,1024),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Page overflow at {width}'
        page.screenshot(path=str(ROOT/f'tmp/timetable-{width}.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.get_by_label('Message timetable assistant',exact=True).fill('Replace Computer Science Semester 1 Section A timetable')
    page.locator('#send').click()
    page.get_by_role('heading',name='Awaiting your approval').wait_for()
    assert page.locator('#preview-body tr.proposed').count()>0
    page.screenshot(path=str(ROOT/'tmp/timetable-generated.png'),full_page=True)
    with page.expect_download() as download:page.locator('#download').click()
    download.value.save_as(ROOT/'tmp/browser-timetable.pdf')
    page.locator('#reject').click();assert page.locator('#proposal').is_hidden()
    page.locator('#regenerate').click();page.get_by_role('heading',name='Awaiting your approval').wait_for()
    page.locator('#approve').click();page.get_by_role('button',name='Keep reviewing').click()
    assert page.locator('#proposal').is_visible()
    page.locator('#approve').click();page.get_by_role('button',name='Confirm and save').click()
    page.get_by_text('Approved and saved',exact=False).wait_for()
    assert page.locator('#proposal').is_hidden()
    page.locator('#file-input').set_input_files(str(ROOT/'tmp/browser-timetable.pdf'))
    page.get_by_role('button',name='Confirm extracted information').wait_for()
    page.get_by_role('button',name='Confirm extracted information').click()
    page.get_by_role('button',name='Remove',exact=True).click()
    assert page.locator('.attachment').count()==0
    import pymupdf
    with pymupdf.open(ROOT/'tmp/browser-timetable.pdf') as pdf:
        pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(ROOT/'tmp/browser-reference.png')
    page.locator('#file-input').set_input_files(str(ROOT/'tmp/browser-reference.png'))
    page.get_by_role('button',name='Confirm extracted information').wait_for()
    assert page.locator('.attachment img').is_visible()
    page.get_by_role('button',name='Confirm extracted information').click()
    page.get_by_role('button',name='Remove',exact=True).click()
    for width,height in [(768,1024),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Populated preview overflow at {width}'
        page.screenshot(path=str(ROOT/f'tmp/timetable-populated-{width}.png'),full_page=True)
    assert not errors,errors
    published=db.query(ClassSchedule).filter_by(status='Active').order_by(ClassSchedule.schedule_id.desc()).first()
    link=db.query(StudentTimetable).filter_by(schedule_id=published.schedule_id).first()
    for person,path in [(published.teacher,'Teacher_dashboard/classes_schedule.html'),(link.student,'Student_dashboard/timetable.html')]:
        portal_context=browser.new_context(viewport={'width':1440,'height':1000})
        portal=portal_context.new_page();portal.set_default_timeout(60000)
        portal.on('pageerror',lambda error:errors.append(str(error)))
        portal.add_init_script('localStorage.setItem("access_token",'+json.dumps(create_access_token({'sub':str(person.user_id)}))+')')
        portal.route('http://127.0.0.1:8000/**',bridge)
        portal.goto('http://127.0.0.1:8765/frontend/'+path)
        if path.startswith('Teacher'):
            portal.locator(f'[data-schedule-id="{published.schedule_id}"]').first.wait_for()
        else:
            portal.wait_for_function('document.querySelector("#semesterSelect").options.length > 0')
            portal.locator('#semesterSelect').select_option(str(published.semester))
            portal.locator('#timetableTableBody .class-name').filter(has_text=published.course.course_code).first.wait_for()
            assert published.teacher.first_name in portal.locator('#timetableTableBody').inner_text()
        portal.screenshot(path=str(ROOT/f'tmp/{person.user.role}-published-timetable.png'),full_page=True)
        portal_context.close()
    assert not errors,errors
    print('PASS: desktop/tablet/mobile overflow, text chat, generated preview, PDF download, reject, regenerate, approval dialog/cancel/save, PDF/image attachment review/remove; no browser exceptions')
    print('PASS: approved timetable visibly rendered in the authenticated Student and Teacher portals')
    browser.close()
backend.should_exit=True;server.shutdown();db.close();engine.dispose()
