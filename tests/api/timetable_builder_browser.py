"""Authenticated browser acceptance test for the structured Admin setup UI."""
import functools
import json
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tests/api"), str(ROOT / "backend/backend")]
sys.path.append(str(ROOT / "tmp/timetable-deps"))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright

from test_timetable_builder import migrated_database_copy
from app.api.admin import router
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import Timetable, User


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    engine, factory = migrated_database_copy()
    db = factory()
    admin = db.query(User).filter_by(role="admin").first()
    access_token = create_access_token({"sub": str(admin.user_id)})
    app = FastAPI()
    app.include_router(router)

    def session():
        connection = factory()
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[get_db] = session
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    backend = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8770, log_level="error"))
    threading.Thread(target=backend.run, daemon=True).start()
    while not backend.started:
        time.sleep(0.05)
    frontend = ThreadingHTTPServer(("127.0.0.1", 8769), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=frontend.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe", headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.add_init_script("localStorage.setItem('access_token', " + json.dumps(access_token) + ")")
            page.route("http://127.0.0.1:8000/**", lambda route: route.continue_(url=route.request.url.replace(":8000", ":8770")))
            page.goto("http://127.0.0.1:8769/frontend/Admin_dashboard/ai-timetable-creator.html")
            page.locator("#builder-status").filter(has_text="departments").wait_for()
            options = page.evaluate("fetch('http://127.0.0.1:8000/admin/timetable-builder/options',{headers:{Authorization:'Bearer '+localStorage.access_token}}).then(r=>r.json())")
            course = next(row for row in options["courses"] if row["course_type"] != "Lab" and any(teacher["department_id"] == row["department_id"] for teacher in options["teachers"]))
            teacher = next((row for row in options["teachers"] if row["id"] == course["assigned_teacher_id"]), None) or next(row for row in options["teachers"] if row["department_id"] == course["department_id"])
            room = next(row for row in options["rooms"] if row["room_type"] == "Classroom")
            page.locator("#builder-department").select_option(str(course["department_id"]))
            page.locator(f"#builder-semesters input[value='{course['semester']}']").check()
            card = page.locator(f".semester-card[data-semester='{course['semester']}']")
            row = card.locator(f".course-setup[data-course-id='{course['id']}']")
            row.locator(".course-enabled").check()
            row.locator(".course-teacher").select_option(str(teacher["id"]))
            row.locator(".course-rooms").select_option([str(room["id"])])
            page.locator("#builder-year").select_option(options["academic_years"][0])
            page.locator("#builder-submit").click()
            page.locator("#builder-status").filter(has_text="Created 1 timetable draft").wait_for()
            self_widths = []
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                self_widths.append((width, page.evaluate("document.documentElement.scrollWidth <= innerWidth")))
            screenshot = ROOT / "tmp" / "timetable-builder-admin.png"
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.screenshot(path=str(screenshot), full_page=True)
            assert all(ok for _, ok in self_widths), self_widths
            assert not errors, errors
            browser.close()
        db.expire_all()
        assert db.query(Timetable).count() == 1
        print("PASS: Admin setup loaded live options, created a persisted draft, and rendered without overflow at desktop/tablet/mobile widths")
    finally:
        backend.should_exit = True
        frontend.shutdown()
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
