# Database Schema Versioning Plan

## Project
Autonomous Campus Operating System (ACOS)

---

## Purpose

This document tracks changes made to the database schema during the development of the project. Versioning helps maintain a clear history of database updates and ensures future changes are organized.

---

## Schema Version 1.0

**Status:** Initial Version

### Included Modules

- Academic Module
- Administrative Module
- Document Management Module
- Security Module
- Vector Database Design

### Tables

1. Students
2. Courses
3. Enrollments
4. Grades
5. Users
6. Audit_Log
7. Fee_Records
8. Documents
9. Admission_Applications
10. Research_Papers
11. Cryptographic_Hashes
12. Watchdog_Alerts
13. Anti_Cheat_Events
14. Research_Documents
15. Library_Catalog

---

## Future Version 1.1

The following improvements are planned:

- Add Teacher table
- Add Department table
- Add Hostel Management tables
- Add Transport Management tables
- Improve table relationships

---

## Future Version 2.0

- PostgreSQL migration
- SQLAlchemy integration
- FastAPI backend integration
- LangGraph agent integration
- Production deployment

---

## Version Update Rule

Whenever the database changes:

- Update the schema version.
- Update the changelog.
- Commit changes to GitHub.
