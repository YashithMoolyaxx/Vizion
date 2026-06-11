# Vizion

Vizion is an analytics-first social media platform for creators, built with Django, React, MySQL, Redis, Celery, Channels, and Docker.

## Stack

- Backend: Django 5, DRF, JWT, Channels, Celery
- Frontend: React 18 + Vite 5 + Tailwind 3 + Framer Motion + Recharts
- Data layer: MySQL 8 + Redis
- Infra: Docker Compose + Nginx reverse proxy

## Project Structure

- `backend/` Django API + websocket + celery
- `frontend/` React app
- `docker-compose.yml` local production-like orchestration

## Authentication (industry pattern)

- **JWT access token** (15 min) returned in JSON, held in memory on the client
- **Refresh token** stored in **HttpOnly cookie** (`vizion_refresh`, path `/api/auth/`)
- **Django server session** created on login for session-backed flows
- **Silent refresh** via Axios interceptor + `withCredentials`
- Endpoints: `POST /api/auth/login/`, `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/session/`

## Key Features

- Dual auth: JWT + sessions + secure cookies
- Feed + posts + follows foundation
- Smart Collections
  - `POST /api/posts/{id}/save/`
  - `GET /api/collections/`
  - `GET /api/collections/{id}/posts/`
  - `PUT /api/saved/{id}/move/`
  - Celery auto-categorization task (`social.tasks.auto_categorize_saved_post`)
- Post-Live Analytics
  - `POST /api/analytics/batch-events/`
  - `GET /api/analytics/posts/{id}/heatmap/`
  - MySQL bucket math + Redis caching
- Realtime messaging and notifications over WebSockets

## Local Run (Docker)

1. Copy env file:
   - `cp .env.example .env` (or create `.env` on Windows)
2. Start stack:
   - `docker compose up --build`
3. Open app:
   - `http://localhost`
4. Django admin/API:
   - `http://localhost/api/`

## Deployment Notes

- Set `SEED_DEMO=0` in production to skip demo content seeding.
- Keep `VITE_API_URL=/api` so the frontend talks to the reverse proxy.
- Set a strong `DJANGO_SECRET_KEY`, `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, and `ALLOWED_HOSTS` before going live.
- The stack is designed to run behind `nginx` with the frontend at `/` and Django at `/api/`.

## Backend development (without Docker)

1. Create venv and install:
   - `pip install -r backend/requirements.txt`
2. Set `.env` variables
3. Run migrations:
   - `python backend/manage.py migrate`
4. Run API:
   - `python backend/manage.py runserver`
5. Run Celery worker and beat:
   - `celery -A config worker -l info`
   - `celery -A config beat -l info`

## Frontend development

1. Install:
   - `cd frontend && npm install`
2. Run:
   - `npm run dev`

## Notes

- The schema includes all required models, indexes, and constraints.
- Smart Collections and Post-Live Analytics are implemented as first-class features.
- Extend serializers/permissions for stricter production policies before public deployment.
