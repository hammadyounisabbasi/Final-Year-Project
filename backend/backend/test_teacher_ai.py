import urllib.request
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

API = "http://127.0.0.1:8000"
TESTS_PASSED = 0
TESTS_FAILED = 0

def login(email, password):
    data = json.dumps({"identifier": email, "password": password}).encode()
    req = urllib.request.Request(f"{API}/auth/login", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["access_token"]

def get_greeting(token):
    req = urllib.request.Request(f"{API}/teacher/ai/greeting", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def chat(token, message, history=None):
    body = json.dumps({"message": message, "history": history or []}).encode()
    req = urllib.request.Request(f"{API}/teacher/ai/chat", data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def test(label, fn):
    global TESTS_PASSED, TESTS_FAILED
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print("="*60)
    try:
        result = fn()
        print(result)
        TESTS_PASSED += 1
        return result
    except Exception as e:
        print(f"FAILED: {e}")
        TESTS_FAILED += 1
        return None

# ---- Teacher 1: Ahmad Malik ----
print("\n*** TEACHER 1: Ahmad Malik ***")
tok1 = login("ahmad.malik@uoh.edu.pk", "UOH@2025")

g1 = test("Dynamic Greeting - Ahmad Malik", lambda: get_greeting(tok1))
if g1:
    assert "Ahmad" in g1["greeting"] or "Malik" in g1["greeting"], "Name missing from greeting!"
    assert g1["teacher_name"] == "Ahmad Malik"
    print("=> Name correctly in greeting:", g1["teacher_name"])

test("Q1: What courses am I teaching?", lambda: chat(tok1, "What courses am I teaching this semester?")["response"][:400])
test("Q2: How many students in my courses?", lambda: chat(tok1, "How many students are registered in my courses?")["response"][:400])
test("Q3: Show my schedule today", lambda: chat(tok1, "Show me my schedule today.")["response"][:400])
test("Q4: Low attendance students", lambda: chat(tok1, "Which students have low attendance?")["response"][:400])
test("Q5: Pending assignments", lambda: chat(tok1, "Which assignments are pending grading?")["response"][:400])
test("Q6: Student performance", lambda: chat(tok1, "How are my students performing?")["response"][:400])

# ---- Teacher 2: Sara Khan (different teacher - test data isolation) ----
print("\n\n*** TEACHER 2: Sara Khan ***")
tok2 = login("sara.khan@uoh.edu.pk", "UOH@2025")

g2 = test("Dynamic Greeting - Sara Khan", lambda: get_greeting(tok2))
if g2:
    assert "Sara" in g2["greeting"] or "Khan" in g2["greeting"], "Name missing!"
    print("=> Name correctly in greeting:", g2["teacher_name"])

test("Q7: Courses for Sara", lambda: chat(tok2, "What courses am I teaching?")["response"][:300])

# Summary
print(f"\n{'='*60}")
print(f"RESULTS: {TESTS_PASSED} passed | {TESTS_FAILED} failed")
print("="*60)
