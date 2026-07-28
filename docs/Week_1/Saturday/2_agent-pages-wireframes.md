# Agent Pages Wireframes

## Project
**Autonomous Campus Operating System (ACOS)**

**Week:** 1 - Saturday  
**Document Version:** 1.0

---

# 1. Introduction

The Autonomous Campus Operating System (ACOS) consists of multiple AI-powered modules. While the main dashboard provides a high-level overview of the system, each module has its own dedicated page for monitoring, analysis, and decision-making.

This document presents the wireframes for the four primary AI modules required in Week 1.

---

# 2. Academic Advisor Page

## Purpose

The Academic Advisor page provides AI-driven analysis of student academic performance. It helps faculty members and administrators identify at-risk students, monitor academic progress, and generate personalized recommendations.

---

## Page Layout

```
+--------------------------------------------------------------------------------+
| Academic Advisor                     Search Student                            |
+--------------------------------------------------------------------------------+

 Student Information

-------------------------------------------------------------
 Name
 Roll Number
 Department
 Semester
 CGPA
 Academic Status
-------------------------------------------------------------

+------------------------+-----------------------+
| GPA Trend              | Attendance Summary   |
+------------------------+-----------------------+

+------------------------------------------------------------+
| AI Recommendations                                         |
|------------------------------------------------------------|
| • Improve Database Systems performance                     |
| • Attend additional laboratory sessions                    |
| • Eligible for scholarship                                 |
+------------------------------------------------------------+

+------------------------------------------------------------+
| Recent Academic Activity                                   |
|------------------------------------------------------------|
| Quiz Updated                                               |
| Assignment Submitted                                       |
| GPA Calculated                                             |
+------------------------------------------------------------+
```

---

## Main Components

- Student Search
- Student Profile
- GPA Trend Chart
- Attendance Summary
- AI Recommendations
- Course Performance
- Recent Academic Activity

---

## AI Features

- GPA Prediction
- Student Risk Detection
- Scholarship Recommendation
- Course Recommendation
- Academic Performance Analysis

---

# 3. Exam Monitoring Page

## Purpose

The Exam Monitoring page supervises online examinations and uses AI to detect suspicious behavior.

---

## Page Layout

```
+--------------------------------------------------------------------------------+
| Exam Monitoring Dashboard                                                     |
+--------------------------------------------------------------------------------+

 Active Exams      Students Online      Alerts

      5                  320               7

+------------------------------------------------------------+
| Live Camera Monitoring                                     |
|                                                            |
|        Camera Feed Grid                                    |
|                                                            |
+------------------------------------------------------------+

+----------------------+-----------------------+
| Detection Score      | Suspicious Students   |
+----------------------+-----------------------+

+------------------------------------------------------------+
| Anti-Cheat Event Log                                       |
|------------------------------------------------------------|
| Multiple Faces Detected                                    |
| Mobile Phone Detected                                      |
| Looking Away Frequently                                    |
+------------------------------------------------------------+
```

---

## Main Components

- Live Camera Grid
- Active Exams
- Students Online
- Detection Score
- Suspicious Student List
- Event Log

---

## AI Features

- Face Detection
- Multiple Person Detection
- Mobile Phone Detection
- Eye Tracking
- Voice Monitoring
- Cheating Detection

---

# 4. Financial Dashboard

## Purpose

The Financial Dashboard manages student fee payments, financial verification, and reconciliation using AI.

---

## Page Layout

```
+--------------------------------------------------------------------------------+
| Financial Dashboard                                                            |
+--------------------------------------------------------------------------------+

 Total Students

 Fee Collected

 Pending Payments

 Verified Transactions

+------------------------------------------------------------+
| Fee Collection Chart                                       |
+------------------------------------------------------------+

+------------------------------------------------------------+
| Pending Verification                                       |
|------------------------------------------------------------|
| Student 101                                                |
| Student 205                                                |
| Student 450                                                |
+------------------------------------------------------------+

+------------------------------------------------------------+
| AI Reconciliation Results                                  |
|------------------------------------------------------------|
| Auto Verified                                              |
| Duplicate Payments                                         |
| Missing Transactions                                       |
+------------------------------------------------------------+
```

---

## Main Components

- Financial Statistics
- Collection Chart
- Pending Verification
- AI Reconciliation
- Payment History

---

## AI Features

- Automatic Fee Verification
- Duplicate Payment Detection
- Fraud Detection
- Receipt Validation
- Financial Analytics

---

# 5. Security Alerts Page

## Purpose

The Security Alerts page monitors cyber threats, unauthorized activities, and campus security using Zero-Trust AI agents.

---

## Page Layout

```
+--------------------------------------------------------------------------------+
| Security Operations Center                                                     |
+--------------------------------------------------------------------------------+

 Threat Level

 High

 Active Alerts

 18

 Blocked Users

 5

+------------------------------------------------------------+
| Campus Security Map                                        |
+------------------------------------------------------------+

+------------------------------------------------------------+
| Recent Security Alerts                                     |
|------------------------------------------------------------|
| Unauthorized Login Attempt                                |
| Database Modification                                      |
| Suspicious Network Activity                                |
| Multiple Failed Login Attempts                             |
+------------------------------------------------------------+

+------------------------------------------------------------+
| AI Threat Analysis                                         |
|------------------------------------------------------------|
| Risk Score                                                 |
| Recommended Action                                         |
+------------------------------------------------------------+
```

---

## Main Components

- Threat Level
- Active Alerts
- Blocked Users
- Security Map
- Alert Timeline
- AI Threat Analysis

---

## AI Features

- Zero-Trust Verification
- Intrusion Detection
- Login Monitoring
- Threat Classification
- Automated Alert Generation

---

# 6. Navigation Flow

```
Dashboard
    │
    ├── Academic Advisor
    │
    ├── Exam Monitoring
    │
    ├── Financial Dashboard
    │
    └── Security Alerts
```

Users can return to the main dashboard at any time using the navigation sidebar.

---

# 7. Design Standards

All pages follow the same design language.

- Light theme
- Responsive layout
- Fixed navigation sidebar
- Top header with search
- Rounded cards
- Modern charts
- Consistent typography
- Real-time data widgets
- Interactive tables
- AI-generated insights

---

# 8. Shared UI Components

The following components are reused across all pages.

| Component | Purpose |
|-----------|---------|
| Header | Navigation and user profile |
| Sidebar | Module navigation |
| Search Bar | Search records |
| KPI Cards | Display statistics |
| Charts | Data visualization |
| Tables | Structured information |
| Activity Feed | Recent events |
| Notification Panel | System alerts |
| AI Insight Card | AI-generated recommendations |
| Status Badge | Running, Idle, Error indicators |

---

# 9. Expected User Workflow

```
User Login
      │
      ▼
Dashboard
      │
      ▼
Select Module
      │
      ▼
Open Agent Page
      │
      ▼
View Analytics
      │
      ▼
Take Administrative Action
```

---

# 10. Conclusion

The agent-specific pages provide dedicated workspaces for each AI module while maintaining a consistent user experience. Each page focuses on a specific operational area—academics, examinations, finance, or security—and presents relevant analytics, AI insights, and management tools. Together with the main dashboard, these wireframes establish the frontend design foundation for the Autonomous Campus Operating System.
