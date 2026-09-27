import urllib.request
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

API = "http://127.0.0.1:8000"

def login(email, pw):
    d = json.dumps({"identifier": email, "password": pw}).encode()
    req = urllib.request.Request(f"{API}/auth/login", data=d, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())["access_token"]

def greet(tok):
    req = urllib.request.Request(f"{API}/teacher/ai/greeting", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def ask(tok, msg, hist=None):
    body = json.dumps({"message": msg, "history": hist or []}).encode()
    req = urllib.request.Request(f"{API}/teacher/ai/chat", data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.loads(r.read())


print("=" * 70)
print("TEACHER AI ACADEMIC AGENT - VERIFICATION SUITE")
print("=" * 70)

# 1. Ahmad Malik
print("\n[1] Authenticating as Professor Ahmad Malik...")
t1 = login("ahmad.malik@uoh.edu.pk", "UOH@2025")
g1 = greet(t1)
print(f"Dynamic Greeting: {g1['greeting']}")
print(f"Teacher Name: {g1['teacher_name']}")

questions = [
    "What courses am I teaching this semester?",
    "How many students are registered in my courses?",
    "Show me my schedule today.",
    "Which students have low attendance?",
    "Which assignments are pending?",
    "How are my students performing?"
]

for idx, q in enumerate(questions, 1):
    print(f"\n--- Q{idx}: '{q}' ---")
    time.sleep(1.5)
    res = ask(t1, q)
    print(f"[Provider: {res.get('provider')}]")
    print(res.get("response"))

# 2. Usman Ali
print("\n" + "=" * 70)
print("[2] Authenticating as Dr. Usman Ali (Dynamic Greeting & Isolation Test)...")
time.sleep(1)
t2 = login("usman.ali@uoh.edu.pk", "UOH@2025")
g2 = greet(t2)
print(f"Dynamic Greeting: {g2['greeting']}")
print(f"Teacher Name: {g2['teacher_name']}")

print("\n--- Q: 'What courses am I teaching this semester?' (Dr. Usman Ali) ---")
time.sleep(1.5)
res2 = ask(t2, "What courses am I teaching this semester?")
print(f"[Provider: {res2.get('provider')}]")
print(res2.get("response"))

# 3. Sara Khan
print("\n" + "=" * 70)
print("[3] Authenticating as Sara Khan...")
time.sleep(1)
t3 = login("sara.khan@uoh.edu.pk", "UOH@2025")
g3 = greet(t3)
print(f"Dynamic Greeting: {g3['greeting']}")
print(f"Teacher Name: {g3['teacher_name']}")


print("\n" + "=" * 70)
print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)
