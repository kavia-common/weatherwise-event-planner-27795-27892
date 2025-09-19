# WeatherWise Events - Backend (FastAPI)

## Introduction
This backend provides REST endpoints for event planning, live weather retrieval, suitability scoring, and recommendations. It is built with FastAPI and integrates with Open‑Meteo and OpenStreetMap Nominatim for weather and geocoding.

## Prerequisites
- Python 3.10+
- pip
- (Optional) virtualenv

## Setup

### 1. Clone and enter the backend folder
The backend lives at `weatherwise-event-planner-27795-27892/events_backend`.

### 2. Create and populate environment file
Copy `.env.example` to `.env` and adjust values:
- ENV, DEBUG
- CORS_ALLOW_ORIGINS: include your frontend origin(s). The app will automatically add `http://localhost:3000` for local dev if not present.
- Optional integration keys: WEATHER_API_BASE_URL, WEATHER_API_KEY
- Optional email fields: EMAIL_SENDER, EMAIL_SMTP_URL
- Optional SITE_URL

See `events_backend/.env.example` for details.

### 3. Install dependencies
```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the server (development)
```
# Recommended (respects HOST and PORT from .env; defaults to 0.0.0.0:3001)
python -m src.api.run

# Alternatively specify explicitly:
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 3001
```
The API will be available at http://localhost:3001 by default (unless PORT is overridden).

## Available Commands
- Run dev server: `python -m src.api.run` (uses HOST/PORT from .env; defaults to 0.0.0.0:3001)
- Run tests (if any added): `pytest`
- Lint (flake8): `flake8`

## Environment Variables
These are read in `src/core/config.py` via python‑dotenv:
- ENV: Runtime environment (default: development)
- DEBUG: Enable debug mode (true/false)
- CORS_ALLOW_ORIGINS: Comma‑separated list of allowed origins. The application ensures `http://localhost:3000` is allowed during development unless `"*"` is used.
- WEATHER_API_BASE_URL, WEATHER_API_KEY: Optional placeholders for alternative weather providers
- EMAIL_SENDER, EMAIL_SMTP_URL: Optional placeholders for future SMTP/email integration
- SITE_URL: Optional public site base URL

## CORS and Frontend Coordination
- The backend uses FastAPI’s CORSMiddleware. Set `CORS_ALLOW_ORIGINS` in `.env` to include your frontend URL(s).
- During local development:
  - Backend: http://localhost:8000
  - Frontend: http://localhost:3000
  - Ensure `CORS_ALLOW_ORIGINS=http://localhost:3000` in `.env`
- A wildcard `*` is acceptable only for development or controlled environments.

## OpenAPI and API Docs
- Interactive docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- A frozen copy is kept at `events_backend/interfaces/openapi.json`
- To regenerate the static OpenAPI file:
  ```
  python -m src.api.generate_openapi
  ```

## Post‑MVP Upgrade Notes
- Email: replace the console email service in `src/services/notifications.py` with an SMTP or SaaS provider using `EMAIL_SMTP_URL` and credentials.
- Persistence: swap `InMemoryEventsRepository` with a database‑backed implementation.
- Weather provider: for enterprise use, configure `WEATHER_API_BASE_URL` and `WEATHER_API_KEY` and implement a provider client accordingly.