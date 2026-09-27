# Deployment Guide

This repository is prepared for a GitHub-hosted source workflow and a Vercel frontend preview. The frontend is static; the FastAPI backend is stateful and must run on a persistent Python host.

## Architecture

- Vercel serves `frontend/` using the root `vercel.json`.
- FastAPI runs as a separate service using `backend/backend/app/main.py`.
- SQLite and uploaded files must live on persistent storage. Do not place the current backend in a disposable serverless function: writes to the database and `uploads/` must survive restarts.

## 1. Prepare GitHub

Before the first push, confirm that `.env`, `database/*.db`, `backend/backend/uploads/`, `tmp/`, virtual environments, and generated indexes are not staged:

```bash
git status --short
git check-ignore .env database/university.db backend/backend/uploads tmp
```

The included GitHub Actions workflow compiles the Python source and runs the unit suite on pushes and pull requests.

## 2. Deploy the backend

Use a Python 3.12 service with a persistent disk. From the repository root:

```bash
pip install -r requirements.txt
python scripts/setup_database.py --database /persistent/path/university.db --without-seed
uvicorn app.main:app --app-dir backend/backend --host 0.0.0.0 --port 8000
```

Set these environment variables in the hosting dashboard:

```env
APP_ENV=production
DEBUG=false
SECRET_KEY=<a random value of at least 32 characters>
DATABASE_URL=sqlite:////persistent/path/university.db
UPLOAD_DIR=/persistent/path/uploads
LIBRARY_BOOKS_DIR=/persistent/path/library-books
CORS_ORIGINS=https://your-project.vercel.app
```

Add only the AI provider keys you use. Never upload `.env` to GitHub. Verify `https://your-api-host/health` after deployment.

For an isolated demonstration environment only, omit `--without-seed` to load the documented test accounts. Never expose those known credentials as a real production deployment.

## 3. Point the frontend at the backend

If both services do not share an origin, edit `DEPLOYED_API_BASE_URL` in `frontend/shared/config.js` and set it to the public HTTPS FastAPI origin. Leave it empty for local development or a same-origin reverse proxy.

## 4. Deploy the frontend to Vercel

Import the GitHub repository into Vercel and keep the repository root as the project root. `vercel.json` already selects `frontend/` as the static output and routes `/` to the landing page. No build or install command is required.

After deployment, test:

1. Landing page and all three login pages load over HTTPS.
2. Browser network requests target the public API, never `127.0.0.1`.
3. Login works for each role.
4. File upload/download works and survives a backend restart.
5. The backend rejects an origin not listed in `CORS_ORIGINS`.

## Current platform boundary

The backend is SQLite-specific, including migrations and several raw SQL queries. A PostgreSQL deployment requires a separate migration/compatibility project; changing only `DATABASE_URL` is not sufficient.
