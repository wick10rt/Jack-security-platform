# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Jack Security Platform is a web security learning platform. Users solve
vulnerable-app challenges ("labs"), each backed by an isolated, ephemeral
Docker container launched on demand. The flow is: submit a correct answer →
write a defensive "reflection" → unlock other users' community solutions.

Three top-level parts:

- `backend/` — Django + Django REST Framework API, with Celery for async
  instance management.
- `frontend/` — Vue 3 + Vite + TypeScript SPA (Pinia state, vue-router).
- `labs/` — Self-contained vulnerable web apps (PHP + MySQL), each with its own
  `Dockerfile` / `docker-compose.yml`, published as Docker images (e.g.
  `wick10rt/jack-system-sqli-blind-bool:1.1`). A `Lab.docker_image` row points
  the backend at the image to spin up.

## Common Commands

The root `docker-compose.yml` only runs infrastructure (Postgres on host port
`25000`, Redis on `6379`) — it does **not** run the app itself.

```bash
# Infrastructure (run first, from repo root)
docker-compose up -d

# Backend (from backend/, venv activated)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver                # http://127.0.0.1:8000
python manage.py test                     # run all tests
python manage.py test core.tests.SomeTest # run a single test class/method

# Celery (from backend/) — both processes are required for instances to work
celery -A myproject worker -l info        # use -P solo on Windows / single-process
celery -A myproject beat -l info          # runs the expired-instance cleanup every minute

# Frontend (from frontend/)
npm run dev          # http://localhost:5173
npm run build        # type-check + production build
npm run type-check   # vue-tsc only
npm run lint         # eslint --fix
npm run format       # prettier
```

## Environment Variables

Two `.env` files are required (neither is committed):

- Repo root `.env`: `SECRET_KEY`, `DATABASE_PASSWORD`. Settings reads this from
  `BASE_DIR.parent`, i.e. the repo root, **not** `backend/`.
- `frontend/.env`: `VITE_API_BASE_URL` (e.g. `http://127.0.0.1:8000/api`) and
  `VITE_ADMIN_ACCESS_KEY` — this must match `ALLOWED_QUERY_VALUE` in
  `backend/core/middleware.py`.

## Architecture & Key Flows

### Instance lifecycle (the core of the system)

Backend instance management is fully async via Celery and shells out to
`docker-compose`. The data model is `ActiveInstance` (`core/models.py`); the
work happens in `core/tasks.py`, triggered from `core/views.py`.

- **Launch** (`LaunchInstanceView` → `launch_instance_task`): the view creates
  an `ActiveInstance` row with placeholder `instance_url`/`container_id` of
  `"creating..."` and returns `202 Accepted` immediately. The Celery task then
  writes a per-instance compose file to `<repo-root>/instances/docker-compose-<id>.yml`,
  brings it up, and resolves the host-mapped port to fill in the real
  `instance_url`. The frontend polls `InstanceStatusView` until the URL is ready.
- **Constraints** (enforced in `LaunchInstanceView` inside a
  `select_for_update()` transaction): one active instance per user; a global cap
  of `ACTIVEINSTANCE_LIMIT = 30`; instances expire 30 minutes after creation.
- **Teardown**: `terminate_instance_task` (manual, via `TerminateInstanceView`)
  and `cleanup_expired_instances` (Celery Beat, every minute) tear down compose
  projects and delete rows. Cleanup dispatches one `terminate_instance_task` per
  expired instance.

When changing instance behavior, keep the view (sync DB bookkeeping +
constraints) and the task (actual Docker work) in sync — placeholder values like
`"creating..."`/`"waiting..."` are load-bearing in the teardown logic.

### Auth

- JWT via `djangorestframework-simplejwt`. Custom `MyTokenObtainPairView`
  (`core/views.py`) wraps login to return a `redirect_url` and feed django-axes
  brute-force tracking; tokens carry `username` and `is_admin` claims (decoded
  client-side in `frontend/src/stores/auth.ts`).
- DRF defaults to `IsAuthenticated` globally; public endpoints (`register`,
  `login`) opt out with `AllowAny`.
- Frontend: `frontend/src/axios.ts` injects the bearer token and transparently
  refreshes on `401` (with a single-flight queue so concurrent 401s share one
  refresh). The `auth` Pinia store persists tokens to `localStorage`.
- Custom `User` model (`AUTH_USER_MODEL = "core.User"`) uses a UUID primary key,
  as do all other models.
- `HideAdminMiddleware` hides `/admin/` from non-staff: access requires staff
  auth or a one-time `?admin_key=<VITE_ADMIN_ACCESS_KEY>` query param that sets a
  session flag; otherwise it returns 404.

### Completion / reflection state machine

`LabCompletion.status` moves `pending_reflection → completed`. A correct answer
(`SubmitAnswerView`) creates/sets `pending_reflection`; submitting the reflection
form (`ReflectionView`) creates the `CommunitySolution` and promotes the status
to `completed`. Community solutions for a lab are only visible to users who have
`completed` that lab (`CommunitySolutionListView`).

## Conventions

- **Comment prefixes are a project-wide cross-reference scheme**, mirrored in
  filenames. Treat them as anchors when navigating: `Fn` = frontend views
  (`F1_LoginView.vue`…`F4_LabDetailView.vue`), `Bn` = backend service groupings /
  frontend composables (`B1`–`B5`), `EE-n` = API endpoints, `C-n` = business
  constraints, `S-n` = security controls, `IE-n` = instance events, `D-n` =
  infrastructure services. When adding a feature, follow the existing numbering.
- Code comments and log messages are written in Traditional Chinese — match that
  style in `core/`.
- API routes: auth lives at `/api/auth/...` (`myproject/urls.py`); everything
  else is under `/api/` from `core/urls.py`.
