# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Jack Security Platform (資安攻防系統) is a web-security learning platform. Users
solve vulnerable-app challenges ("labs"), each backed by an isolated, ephemeral
Docker container launched on demand. Its defining twist over sites like
TryHackMe / PortSwigger: solving a lab is **not** the end — a correct answer
only unlocks a defensive "reflection" form, and submitting that form is what
marks the lab complete and unlocks other users' community solutions. The goal is
to make learners think about *defense*, not just exploitation.

Three top-level parts:

- `backend/` — Django + Django REST Framework API, Celery for async instance
  management. Follows Django's **MVT**: `models.py` (data), `views.py` +
  `tasks.py` (logic), and the SPA is the "template" layer.
- `frontend/` — Vue 3 + Vite + TypeScript SPA (Pinia state, vue-router).
- `labs/` — Self-contained vulnerable web apps (PHP + MySQL, sqli-labs derived),
  each with its own `Dockerfile` / `docker-compose.yml`, published as Docker
  images (e.g. `wick10rt/jack-system-sqli-blind-bool:1.1`). A `Lab.docker_image`
  row points the backend at the image to spin up.

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

- Repo root `.env`: `SECRET_KEY`, `DATABASE_PASSWORD`, `DEBUG`, `ALLOWED_HOSTS`,
  `ADMIN_ACCESS_KEY`. Settings reads this from `BASE_DIR.parent`, i.e. the repo
  root, **not** `backend/`.
- `frontend/.env`: `VITE_API_BASE_URL` (e.g. `http://127.0.0.1:8000/api`) and
  `VITE_ADMIN_ACCESS_KEY` — this must match `ADMIN_ACCESS_KEY` in the repo-root
  `.env` (read in `settings.py` and consumed by `core/middleware.py`).

## Architecture & Key Flows

### Instance lifecycle (the core of the system)

Backend instance management is fully async via Celery and shells out to
`docker-compose`. The data model is `ActiveInstance` (`core/models.py`); the
work happens in `core/tasks.py`, triggered from `core/views.py`. This is the
`B4` (靶機分配服務) + `D1`/`D2` (Docker/容器管理) slice of the design.

- **Launch** (`LaunchInstanceView` → `launch_instance_task`, events EE-5/IE-5):
  the view creates an `ActiveInstance` row with `status="creating"` (empty
  `instance_url`/`container_id`) and returns `202 Accepted` immediately. The
  Celery task builds a per-instance compose file (`build_compose_content`),
  writes it to `<repo-root>/instances/docker-compose-<id>.yml`, brings it up,
  resolves the host-mapped port (`<lab.web_service>:<lab.web_port>`) into
  `instance_url` (host = `INSTANCE_PUBLIC_HOST`), and sets `status="running"`.
  On failure it sets `status="error"` (row kept so the UI can report it). The
  frontend polls `InstanceStatusView` every 3s and switches on `status`.
- **Per-lab compose** (`build_compose_content` in `core/tasks.py`): each `Lab`
  can carry its own `compose_template` (full docker-compose YAML); if blank, a
  default web+MySQL template is used (legacy sqli labs). `Lab.web_service` /
  `Lab.web_port` declare which service/port to expose. The platform **force-
  injects** hardening onto every service (cpus/mem/pids from `INSTANCE_*`
  settings, `no-new-privileges`, `restart: no`) and **strips** author-supplied
  `ports`/`privileged`/`cap_add`, publishing only one controlled
  `127.0.0.1::<web_port>` on the web service. Labs are pure targets; the answer
  model stays a fixed-string match (`SubmitAnswerView`), so non-flag vuln types
  are authored to emit a static flag on success.
- **Constraints** (enforced in `LaunchInstanceView` inside a
  `select_for_update()` transaction): one active instance per user (C-3); a
  global cap of `settings.ACTIVEINSTANCE_LIMIT` (default 30, C-9); instances
  expire `settings.INSTANCE_EXPIRY_MINUTES` (default 30) after creation (C-4).
- **Extend**: `ExtendInstanceView` (`/api/instances/extend/`) pushes `expires_at`
  out by `INSTANCE_EXTENSION_MINUTES`, up to `INSTANCE_MAX_EXTENSIONS` times.
- **Teardown**: `terminate_instance_task` (manual, EE-11/IE-11, via
  `TerminateInstanceView`) and `cleanup_expired_instances` (Celery Beat every
  minute, IE-10) tear down compose projects and delete rows. `reconcile_instances`
  (Beat every 5 min) reconciles Docker↔DB by compose-project label: it kills
  orphan containers with no DB row and flags rows stuck in `creating` past
  `INSTANCE_ORPHAN_GRACE_MINUTES` as `error`.

When changing instance behavior, keep the view (sync DB bookkeeping +
constraints) and the task (actual Docker work) in sync via the `status` field
(`creating`/`running`/`error`).

### Auth

- JWT via `djangorestframework-simplejwt`. Custom `MyTokenObtainPairView`
  (`core/views.py`) wraps login to return a `redirect_url` and feed django-axes
  brute-force tracking; tokens carry `username` and `is_admin` claims (decoded
  client-side in `frontend/src/stores/auth.ts`). Routes: `/api/auth/login/`,
  `/api/auth/token/refresh/`, `/api/auth/logout/`. Logout blacklists the refresh
  token via the `token_blacklist` app; access token lifetime is 30 min
  (`ACCESS_TOKEN_MINUTES`).
- DRF defaults to `IsAuthenticated` globally; public endpoints (`register`,
  `login`) opt out with `AllowAny`.
- Frontend: `frontend/src/axios.ts` injects the bearer token and transparently
  refreshes on `401` (with a single-flight queue so concurrent 401s share one
  refresh). The `auth` Pinia store persists tokens to `localStorage`.
- Custom `User` model (`AUTH_USER_MODEL = "core.User"`) uses a UUID primary key,
  as do all other models.
- `HideAdminMiddleware` hides `/admin/` from non-staff: access requires staff
  auth or a one-time `?admin_key=<ADMIN_ACCESS_KEY>` query param that sets a
  session flag; otherwise it returns 404. The key is read from settings
  (`ADMIN_ACCESS_KEY`, env-backed); if unset/empty the query-param bypass is
  disabled entirely.

### Completion / reflection state machine

`LabCompletion.status` moves `pending_reflection → completed` (states SE-7 →
SE-10). A correct answer (`SubmitAnswerView`, EE-6) creates/sets
`pending_reflection`; submitting the reflection form (`ReflectionView`, EE-7)
creates the `CommunitySolution` and promotes the status to `completed`. Community
solutions for a lab are only visible to users who have `completed` that lab
(`CommunitySolutionListView`, C-6).

### Security controls (from the design doc, S-series)

- **S1** — password strength: `django-pwned-passwords` + validators requiring
  ≥12 chars and <0.5 similarity to username (`AUTH_PASSWORD_VALIDATORS`).
- **S2** — brute-force lockout: `django-axes` (`AXES_*` in settings). Note the
  code uses `AXES_FAILURE_LIMIT = 20` / 15-min window / 30-min cooloff — the
  design doc's "10 failures" figure is stale; **trust the code**.
- **S3** — SQL-injection defense in the *platform itself*: all DB access goes
  through Django's ORM (parameterized). The vulnerable behavior lives only inside
  `labs/` images, never in `backend/`.

## Code navigation: the cross-reference scheme

The whole codebase is organized around the design doc's ID scheme, mirrored in
filenames (e.g. `F4_LabDetailView.vue`, `B1_useAuthForm.ts`). Inline comments
that used to carry these anchors have been stripped, so this table is now the
primary map. When adding a feature, follow the existing numbering.

| Prefix | Meaning | Where it lives |
| --- | --- | --- |
| `F1`–`F5` | Frontend pages | `frontend/src/views/F*.vue` (F1 login, F2 dashboard, F3 lab list, F4 lab detail). **F5 (admin) is the Django admin site at `/admin/`, not a Vue page.** |
| `B1`–`B5` | Backend service groupings *and* their frontend composables | Backend: view groups in `core/views.py` (B1 auth, B2 lab content, B3 user data, B4 instance allocation, B5 answer check). Frontend: `frontend/src/composables/B*.ts`. |
| `D1`–`D4` | Infrastructure services | D1 Docker runtime, D2 compose/container mgmt (`core/tasks.py`), D3 Postgres (`docker-compose.yml`), D4 admin backend (Django admin). |
| `EE-n` | External (user-triggered) API events | `core/urls.py` routes; EE-0 register … EE-11 terminate instance. |
| `IE-n` | Internal events (service → DB/container) | `core/tasks.py` and view internals. |
| `SE-n` | State-machine transitions | Lab/instance lifecycle (see state machine above). |
| `C-n` | Business constraints | C-1 auth-gated pages, C-2 admin-only, C-3 one instance/user, C-4 30-min expiry, C-5 reflect-before-complete, C-6 completed-gates-solutions, C-7 PBKDF2+SHA256 (Django default hasher), C-8 mandated stack, C-9 30-instance cap. |
| `S-n` | Security controls | See the Security section above. |
| `U/L/CS/LC/AI` | Data-dictionary field IDs | The five models in `core/models.py` (User, Lab, CommunitySolution, LabCompletion, ActiveInstance). |

## Conventions

- Code comments and log messages, where present, are written in Traditional
  Chinese — match that style in `core/`. (Most cross-reference comments have been
  removed; rely on filenames + the table above to navigate.)
- API routes: auth lives at `/api/auth/...` (`myproject/urls.py`); everything
  else is under `/api/` from `core/urls.py`.
- Mandated stack (C-8): Vue.js, Django, Python, Docker, docker-compose,
  PostgreSQL. Development model is waterfall — design is fixed up front, so
  prefer fitting changes into the existing ID scheme over introducing new
  abstractions.
- `DEBUG`, `ALLOWED_HOSTS`, and `ADMIN_ACCESS_KEY` are env-backed in
  `settings.py` (`DEBUG` defaults to `False`). Set `DEBUG=False` and a real
  `ALLOWED_HOSTS` for any deployment.
