"""Small CDP smoke test for the local Exam Monitoring assistant UI.

Usage: start the API on :8000, the frontend on :5500, and a Chromium browser
with --remote-debugging-port=9223 pointed at exam-monitoring.html, then run this
module. It intentionally depends only on packages already used by the project.
"""

import json
import time
import urllib.request

import httpx
from websockets.sync.client import connect


def main():
    api = "http://127.0.0.1:8000"
    token = httpx.post(f"{api}/auth/login", json={
        "identifier": "vc.admin@uoh.edu.pk", "password": "UOH@2025"
    }, timeout=20).json()["access_token"]
    targets = json.load(urllib.request.urlopen("http://127.0.0.1:9223/json/list"))
    target = next(item for item in targets if "exam-monitoring.html" in item.get("url", ""))
    with connect(target["webSocketDebuggerUrl"], origin="http://127.0.0.1:9223") as socket:
        request_id = 0

        def command(method, params=None):
            nonlocal request_id
            request_id += 1
            socket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
            while True:
                response = json.loads(socket.recv())
                if response.get("id") == request_id:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response.get("result", {})

        def evaluate(expression, await_promise=False):
            result = command("Runtime.evaluate", {
                "expression": expression, "returnByValue": True, "awaitPromise": await_promise
            })["result"]
            if result.get("subtype") == "error":
                raise RuntimeError(result.get("description"))
            return result.get("value")

        command("Runtime.enable")
        evaluate(f"localStorage.setItem('access_token', {json.dumps(token)})")
        evaluate("sessionStorage.removeItem('exam-assistant-session')")
        command("Page.reload")
        time.sleep(2)
        assert evaluate("document.querySelector('#examAiHeading')?.textContent") == "AI Exam Scheduling Assistant"
        assert evaluate("document.querySelector('#examAiStatus')?.textContent") == "Secure temporary session"
        evaluate("document.querySelector('#adminActionInput').value='Browser regression alert'")
        evaluate("document.querySelector('#btnAddAction').click()")
        assert evaluate("document.querySelector('#alertsList .alert-item h5').textContent") == "Browser regression alert"
        evaluate("document.querySelector('#btnStudentCamTab').click()")
        assert evaluate("document.querySelectorAll('#cctvGrid .camera-card').length") == 2

        def send(message):
            evaluate("document.querySelector('#examAiInput').value=" + json.dumps(message))
            evaluate("document.querySelector('#examAiForm').requestSubmit()")
            for _ in range(60):
                time.sleep(.15)
                if not evaluate("document.querySelector('#examAiSend').disabled"):
                    return
            raise TimeoutError("Assistant UI remained busy")

        send("What departments, semesters, courses, and rooms are currently available in the system?")
        formatted_heading = evaluate("document.querySelector('#examAiMessages .assistant:last-child h4')?.textContent")
        assert formatted_heading == "Current Scheduling Inventory"
        assert not evaluate("document.querySelector('#examAiMessages .assistant:last-child').textContent.includes('###')")
        send("Create a date sheet for CS Semester 6.")
        send("Start exams from 10 November 2026, use morning slots and keep exams on alternate days.")
        date_rows = evaluate("document.querySelectorAll('#examAiTableBody tr').length")
        assert date_rows == 6
        send("Generate the seating plan.")
        seating_rows = evaluate("document.querySelectorAll('#examAiTableBody tr').length")
        assert seating_rows == 6
        send("Move the AI exam to Thursday.")
        ai_day = evaluate("Array.from(document.querySelectorAll('#examAiTableBody tr')).find(row => row.cells[2]?.textContent === 'CSE-606')?.cells[1].textContent")
        assert ai_day == "Thursday"
        send("Change this exam to 2 PM.")
        ai_time = evaluate("Array.from(document.querySelectorAll('#examAiTableBody tr')).find(row => row.cells[2]?.textContent === 'CSE-606')?.cells[5].textContent")
        assert ai_time == "14:00", ai_time
        send("Use Room 5 instead.")
        ai_room = evaluate("Array.from(document.querySelectorAll('#examAiTableBody tr')).find(row => row.cells[2]?.textContent === 'CSE-606')?.cells[7].textContent")
        assert ai_room.endswith("Room 5"), ai_room

        upload = evaluate("""(async () => {
          const data = 'Course,Code,Semester,Section,Room,Capacity\\nArtificial Intelligence,CSE-606,6,A,CSE Faculty Room 1,60\\n';
          const form = new FormData(); form.append('session_id', sessionStorage.getItem('exam-assistant-session'));
          form.append('document', new File([data], 'browser-courses.csv', {type:'text/csv'}));
          const response = await fetch('http://127.0.0.1:8000/admin/exam-assistant/documents', {method:'POST', headers:{Authorization:'Bearer '+localStorage.getItem('access_token')}, body:form});
          const body = await response.json(); return {status:response.status, chunks:body.document?.chunks};
        })()""", await_promise=True)
        assert upload == {"status": 200, "chunks": 1}
        send("Create a date sheet using this file starting 10 November 2026.")
        file_grounded_rows = evaluate("document.querySelectorAll('#examAiTableBody tr').length")
        assert file_grounded_rows == 1
        export = evaluate("""(async () => {
          const response = await fetch('http://127.0.0.1:8000/admin/exam-assistant/export', {method:'POST', headers:{Authorization:'Bearer '+localStorage.getItem('access_token'),'Content-Type':'application/json'}, body:JSON.stringify({session_id:sessionStorage.getItem('exam-assistant-session'),document_type:'date_sheet',format:'pdf'})});
          const bytes = new Uint8Array(await response.arrayBuffer());
          return {status:response.status, signature:String.fromCharCode(...bytes.slice(0,4)), size:bytes.length};
        })()""", await_promise=True)
        assert export["status"] == 200 and export["signature"] == "%PDF" and export["size"] > 1000
        print(json.dumps({"authenticated_ui": True, "markdown_heading_rendered": formatted_heading,
                          "existing_alert_action": True, "existing_camera_toggle": True,
                          "date_rows": date_rows, "seating_rows": seating_rows,
                          "followup_ai_day": ai_day, "followup_ai_time": ai_time, "followup_ai_room": ai_room,
                          "upload": upload, "file_grounded_rows": file_grounded_rows, "pdf_export": export}, indent=2))


if __name__ == "__main__":
    main()
