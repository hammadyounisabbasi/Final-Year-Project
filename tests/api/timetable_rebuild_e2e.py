"""Full browser E2E for the replacement timetable workflow on real DB data."""
import functools, json, sys, threading, time
from collections import defaultdict
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests/api'),str(ROOT/'backend/backend')]
sys.path.append(str(ROOT/'tmp/timetable-deps'))
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright
from test_timetable_builder import migrated_database_copy
from app.api.admin import router as admin_router
from app.api.student import router as student_router
from app.api.teacher import router as teacher_router
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import Enrollment, Teacher, User, Timetable


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def choose_scopes(db):
    groups=defaultdict(dict)
    for enrollment in db.query(Enrollment).filter_by(enrollment_status='Enrolled').all():
        course=enrollment.course
        teacher=db.get(Teacher,course.teacher_id) if course.teacher_id else None
        if enrollment.student.semester!=enrollment.semester or course.status!='Active' or course.course_type=='Lab' or not teacher or teacher.status!='Active': continue
        key=(course.department_id,enrollment.academic_year,enrollment.section or 'A')
        groups[key].setdefault(enrollment.semester,(course,enrollment,teacher))
    key,values=next((key,value) for key,value in groups.items() if len(value)>=2)
    return key,[values[s] for s in sorted(values)[:2]]


def main():
    engine,factory=migrated_database_copy();db=factory();admin=db.query(User).filter_by(role='admin').first()
    (department_id,year,section),scopes=choose_scopes(db)
    app=FastAPI();app.include_router(admin_router);app.include_router(student_router);app.include_router(teacher_router)
    def session():
        value=factory()
        try: yield value
        finally:value.close()
    app.dependency_overrides[get_db]=session;app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
    backend=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8772,log_level='error'));threading.Thread(target=backend.run,daemon=True).start()
    while not backend.started:time.sleep(.05)
    frontend=ThreadingHTTPServer(('127.0.0.1',8771),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=frontend.serve_forever,daemon=True).start()
    errors=[];csv=ROOT/'tmp/e2e-timetable-reference.csv';csv.write_text('Course Code,Course Name,Credit Hours,Teacher\nE2E-101,Planning Reference,3,Example Teacher',encoding='utf-8')
    try:
      with patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(None,None)),sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();page.set_default_timeout(120000);page.on('pageerror',lambda e:errors.append(str(e)))
        page.add_init_script("localStorage.setItem('access_token',"+json.dumps(create_access_token({'sub':str(admin.user_id)}))+')')
        page.route('http://127.0.0.1:8000/**',lambda route:route.continue_(url=route.request.url.replace(':8000',':8772')))
        page.goto('http://127.0.0.1:8771/frontend/Admin_dashboard/ai-timetable-creator.html');page.locator('#builder-status').filter(has_text='departments').wait_for()
        page.locator('#builder-department').select_option(str(department_id));page.locator('#builder-year').select_option(year)
        for course,enrollment,teacher in scopes:
            page.locator(f"#builder-semesters input[value='{enrollment.semester}']").check()
        for course,enrollment,teacher in scopes:
            card=page.locator(f".semester-card[data-semester='{enrollment.semester}']");card.locator('.semester-section').fill(section)
            row=card.locator(f".course-setup[data-course-id='{course.course_id}']");row.locator('.course-enabled').check();row.locator('.course-teacher').select_option(str(teacher.teacher_id));row.locator('.course-rooms option').first.click(modifiers=['Control'])
        page.locator('#builder-submit').click();page.locator('#draft-workspace').wait_for();assert page.locator('#draft-tabs button').count()==2
        published=[]
        for index in range(2):
            page.locator('#draft-tabs button').nth(index).click();page.locator('#draft-generate').click();page.locator('#timetable-grid .session-cell').first.wait_for();assert page.locator('#draft-conflicts .draft-conflict').count()==0
            if index==0:
                page.locator('#timetable-grid .session-cell').first.click();page.locator('#session-dialog').wait_for();page.locator('#session-form button').last.click();page.get_by_text('Session updated and revalidated.').wait_for()
            page.locator('#draft-validate').click();page.get_by_text('Validation passed. Ready for approval.').wait_for();page.locator('#draft-approve').click();page.get_by_text('Timetable approved.',exact=False).wait_for();page.locator('#draft-publish').click();page.get_by_text('Timetable published to Student and Teacher portals.').wait_for();published.append(page.locator('#draft-title').inner_text())
        page.locator('#file-input').set_input_files(str(csv));page.locator('.attachment').wait_for(timeout=30000);page.wait_for_function('!document.querySelector(".attachment").innerText.includes("Processing")');attachment_text=page.locator('.attachment').inner_text();assert 'Ready' in attachment_text,attachment_text;page.locator('#chat-input').fill('Look at this document and tell me how to arrange these courses.');before=page.locator('.message.ai').count();page.locator('#send').click();page.wait_for_function('(count)=>document.querySelectorAll(".message.ai").length>count',arg=before)
        page.screenshot(path=str(ROOT/'tmp/timetable-rebuild-e2e-admin.png'),full_page=True)
        course,enrollment,teacher=scopes[0];student=enrollment.student
        student_ctx=browser.new_context(viewport={'width':1440,'height':1000});student_page=student_ctx.new_page();student_page.add_init_script("localStorage.setItem('access_token',"+json.dumps(create_access_token({'sub':str(student.user_id)}))+')');student_page.route('http://127.0.0.1:8000/**',lambda route:route.continue_(url=route.request.url.replace(':8000',':8772')));student_page.goto('http://127.0.0.1:8771/frontend/Student_dashboard/timetable.html');student_page.wait_for_function('()=>{try{return typeof studentTimetableState==="object"}catch(e){return false}}');student_data=student_page.evaluate('(semester)=>fetch(`http://127.0.0.1:8000/student/timetable?semester=${semester}`,{headers:{Authorization:`Bearer ${localStorage.access_token}`}}).then(r=>r.json())',enrollment.semester);assert course.course_code in json.dumps(student_data);student_page.evaluate('(data)=>renderTimetableUI(data)',student_data);student_page.locator('#timetableTableBody').filter(has_text=course.course_title).wait_for();student_page.screenshot(path=str(ROOT/'tmp/timetable-rebuild-e2e-student.png'),full_page=True)
        teacher_ctx=browser.new_context(viewport={'width':1440,'height':1000});teacher_page=teacher_ctx.new_page();teacher_page.add_init_script("localStorage.setItem('access_token',"+json.dumps(create_access_token({'sub':str(teacher.user_id)}))+')');teacher_page.route('http://127.0.0.1:8000/**',lambda route:route.continue_(url=route.request.url.replace(':8000',':8772')));teacher_page.goto('http://127.0.0.1:8771/frontend/Teacher_dashboard/classes_schedule.html');teacher_page.locator('.schedule-block').filter(has_text=course.course_code).first.wait_for();teacher_page.screenshot(path=str(ROOT/'tmp/timetable-rebuild-e2e-teacher.png'),full_page=True)
        assert not errors,errors;assert db.query(Timetable).filter_by(status='Published').count()==2
        print('PASS: two real semesters configured, generated, previewed, edited/revalidated, approved and published; Student and Teacher portals render canonical published sessions; CSV assistant flow works')
        browser.close()
    finally:
      backend.should_exit=True;frontend.shutdown();db.close();engine.dispose()

if __name__=='__main__':main()
