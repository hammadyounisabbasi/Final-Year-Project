# ACOS Frontend Web Interface & Portals

> Deployment note: every page loads `shared/config.js`. Local development targets `http://127.0.0.1:8000`; set `DEPLOYED_API_BASE_URL` once in that file when the production API uses a different origin. See [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for Vercel instructions.

> **Modern, Responsive Multi-Portal Web Interface for Students, Faculty, and Administrators with Embedded Context-Grounded AI Assistants**

---

## 🎨 Overview

The **Autonomous Campus Operating System (ACOS)** frontend provides a modern, fast, and accessible user interface tailored for university operations. Built with standard **HTML5**, **CSS3 (Glassmorphism & Flex/Grid)**, and modern **Vanilla JavaScript (ES6+)**, the frontend delivers a rich Single-Page/Multi-Page Application experience without heavy third-party framework overhead.

All portals communicate with the FastAPI backend over REST APIs using JSON payloads and Bearer JWT authentication tokens stored in `localStorage`.

---

## 🖥️ Portal Modules & Directory Structure

```
frontend/
├── README.md                      # Frontend documentation (this file)
│
├── landing_page/                  # Public University Landing Portal
│   ├── index.html                 # University showcase, admissions overview & links
│   ├── style.css                  # Modern glassmorphism hero styling & animations
│   └── app.js                     # Interactive navigation & smooth scroll logic
│
├── login_page/                    # Unified & Role-Specific Authentication Screens
│   ├── student-login.html         # Student portal login interface
│   ├── teacher-login.html         # Faculty member login interface
│   ├── admin-login.html           # Administrator & officer login interface
│   ├── login.css                  # Responsive split-screen login styling & glass cards
│   └── login.js                   # JWT authentication handler, validation & role router
│
├── welcome/                       # Post-Login Gateway & Onboarding Hubs
│   ├── student-home.html          # Student gateway & quick links
│   ├── teacher-home.html          # Faculty gateway & schedule overview
│   └── admin-home.html            # Admin command hub gateway
│
├── Student_dashboard/             # Student Portal (12 Comprehensive Views)
│   ├── stu_dashboard.html         # Main dashboard with stats, shortcuts & AI agent
│   ├── my-courses.html            # Enrolled courses, course outlines & instructors
│   ├── timetable.html             # Dynamic weekly timetable schedule
│   ├── attendance.html            # Course-wise attendance & warning badges (<75%)
│   ├── student-attendance.js      # Attendance data fetching & rendering controller
│   ├── assignments.html           # Course assignments & submission portal
│   ├── student-assignments.js     # Assignment upload & submission controller
│   ├── exams.html                 # Exam datesheets & online assessment portal
│   ├── results.html               # Transcript, GPA progression & Chart.js graph
│   ├── fees.html                  # Fee challans, payment vouchers & receipts
│   ├── library.html               # Digital library catalog & issued books
│   ├── notices.html               # Campus circulars & department notices
│   └── profile.html               # Personal, degree program & department details
│
├── Teacher_dashboard/             # Faculty Portal (11 Views & Controllers)
│   ├── tea-dashboard.html         # Teacher dashboard with metrics & AI assistant
│   ├── my_courses.html            # Assigned courses & section rosters
│   ├── teacher-courses.js         # Course data controller
│   ├── classes_schedule.html      # Weekly teaching schedule & room allocations
│   ├── teacher-schedule.js        # Schedule controller
│   ├── students.html              # Student directory per class & section
│   ├── teacher-students.js        # Student roster controller
│   ├── attendance.html            # Interactive attendance marking sheet
│   ├── teacher-attendance.js      # Attendance submission logic
│   ├── assignments.html           # Assignment creator & submission grader
│   ├── teacher-assignments.js     # Assignment creation & grading controller
│   ├── gradebook.html             # Sessional, midterm, and final grade entry
│   ├── assessments.html           # Online test & assessment builder
│   └── notices.html               # Teacher department notices
│
├── Admin_dashboard/               # Admin Command Center & AI Watchdogs (13 Views)
│   ├── dashboard.html             # Institutional metrics & active watchdog summary
│   ├── dashboard.js               # Admin metrics & event listeners
│   ├── dashboard.css              # Command center styling
│   ├── student-management.html    # Student admissions & status controls
│   ├── faculty-management.html    # Faculty allocations & departments
│   ├── academic-integrity.html    # Academic Integrity AI Watchdog
│   ├── clerk-watchdog.html        # Administrative Clerk Audit Watchdog
│   ├── exam-monitoring.html       # Online & offline exam monitoring
│   ├── finance-agent.html         # Fee & financial auditor agent
│   ├── hostel-agent.html          # Hostel allocation & residency agent
│   ├── library-agent.html         # Library analytics & inventory agent
│   ├── security-agent.html        # Campus security & asset tracking agent
│   ├── research-agent.html        # ORIC & research grant tracking agent
│   ├── hr-administration.html     # Human resources & staff governance
│   └── communication-notifications.html # Campus-wide broadcast notifications
│
├── shared/                        # Shared UI Components & Navbars
│   └── student-topbar.js          # Shared navbar, user badge & logout logic
│
└── assets/                        # Static Branding & Media Assets
    ├── uoh-logo.png               # University seal / logo
    ├── icons/                     # SVG icons & symbols
    └── images/                    # UI illustrations & backgrounds
```

---

## 🔑 Authentication & Session Flow

1. **Login Request**: User inputs credentials on `frontend/login_page/student-login.html` (or teacher/admin login).
2. **JWT Response**: The FastAPI server verifies bcrypt hashes and returns:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
     "token_type": "bearer",
     "role": "student",
     "user_id": 1,
     "username": "hamza.ali24"
   }
   ```
3. **Storage**: The token is stored in browser `localStorage.setItem("access_token", token)`.
4. **API Requests**: Subsequent fetch calls attach the authorization header:
   ```javascript
   const response = await fetch(`${window.ACOS_CONFIG.API_BASE_URL}/student/results`, {
     headers: {
       "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
       "Content-Type": "application/json"
     }
   });
   ```
5. **Unauthorized (401) Redirection**: If a token is expired or missing, scripts automatically wipe `localStorage` and redirect the user back to the login page.

---

## 🤖 Embedded AI Assistant Integration

The student (`stu_dashboard.html`) and faculty (`tea-dashboard.html`) dashboards feature floating AI chat widgets:
- **Dynamic Greetings**: Fetches personalized summaries on page load (`GET /student/ai/greeting` / `GET /teacher/ai/greeting`).
- **Context-Grounded Chat**: Sends queries to `POST /student/ai/chat` or `POST /teacher/ai/chat`.
- **Active Provider Badge**: Displays whether the response was generated by Groq, Gemini, Hugging Face, Ollama, or deterministic DB rules.

---

## 🚀 Running the Frontend

### Option 1: Python Built-in HTTP Server (Recommended)
```bash
# From repository root or frontend/ directory:
cd frontend
python -m http.server 3000
```
Open in your browser:
- **Landing Page**: `http://127.0.0.1:3000/landing_page/index.html`
- **Student Login**: `http://127.0.0.1:3000/login_page/student-login.html`
- **Teacher Login**: `http://127.0.0.1:3000/login_page/teacher-login.html`
- **Admin Login**: `http://127.0.0.1:3000/login_page/admin-login.html`

### Option 2: Direct File Opening
You can open any HTML file directly in Chrome, Edge, or Firefox.
*(Note: Ensure the backend is running on `http://127.0.0.1:8000` to handle API requests).*

### Vercel preview

The root `vercel.json` publishes this directory and routes `/` to the landing page. Import the repository root into Vercel; no frontend build command is required. A functional login still requires the separately hosted FastAPI service and correct CORS/API configuration.
