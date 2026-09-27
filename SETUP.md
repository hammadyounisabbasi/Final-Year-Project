# Setup Guide

## Requirements

- Python 3.12+
- Git
- A modern browser
- Ollama only if you want the optional local AI provider

## Local installation

From the repository root:

```bash
python -m venv venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# Linux or macOS
source venv/bin/activate
```

Install runtime dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For tests and browser automation, install the development manifest instead:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
```

## Environment configuration

Copy the tracked template to an ignored local file:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Replace `SECRET_KEY` with a random secret. AI keys are optional because deterministic database-grounded fallbacks remain available. Never commit `.env`.

## Database

The SQLite database is generated and intentionally excluded from Git:

```bash
python scripts/setup_database.py
```

The command refuses to overwrite an existing database. To deliberately rebuild it:

```bash
python scripts/setup_database.py --force
```

Use `--without-seed` for an empty schema. The default development database is `database/university.db`.

## Run the application

Start FastAPI from the repository root:

```bash
uvicorn app.main:app --app-dir backend/backend --reload --host 127.0.0.1 --port 8000
```

In a second terminal, serve the frontend:

```bash
python -m http.server 3000 --directory frontend
```

Open:

- Landing page: `http://127.0.0.1:3000/landing_page/index.html`
- Student login: `http://127.0.0.1:3000/login_page/student-login.html`
- API health: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

The shared browser configuration in `frontend/shared/config.js` automatically uses the local API while developing.
Development CORS accepts `localhost` and `127.0.0.1` on any port, including common Live Server ports such as `5500`. Production accepts only the explicit `CORS_ORIGINS` list.

## Verification

```bash
python -m compileall -q backend/backend/app scripts tests
python -m pytest tests/unit -q
```

API and browser suites may create or modify test records, so run them against a disposable database. See `tests/README.md` for the focused commands.

## Production

Production requires HTTPS, a strong `SECRET_KEY`, explicit `CORS_ORIGINS`, and persistent storage for both SQLite and uploads. See [DEPLOYMENT.md](DEPLOYMENT.md) before publishing the repository or creating a Vercel preview.
