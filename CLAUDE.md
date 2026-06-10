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
- `labs/` — Authoring workspace for vulnerable-app sources, intentionally
  shipped empty (only a placeholder `labs/README.md`): whoever deploys the
  platform adds their own lab folders (each self-contained with a `Dockerfile`),
  builds/publishes the image, and points a `Lab.docker_image` row at it (e.g.
  `wick10rt/jack-system-sqli-blind-bool:1.1`). The runtime never reads this
  folder. Historical sqli-labs examples are retrievable via
  `git log -- labs/`.

## Common Commands

The root `docker-compose.yml` only runs infrastructure (Postgres and Redis,
both bound to **`127.0.0.1`** only — `25000`/`6379` — so a compromised lab
container can't pivot to them) — it does **not** run the app itself.

For local dev, `python run.py` (repo root, stdlib-only, cross-platform) is a
one-click launcher that brings up infra + Django runserver + Celery worker/beat
+ Vite dev server and tears them down on Ctrl+C; `python run.py --setup` also
bootstraps venv/deps/migrate first. The manual per-process commands below are
the equivalent it runs.

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
- `frontend/.env`: `VITE_API_BASE_URL` (e.g. `http://127.0.0.1:8000/api`). The
  admin bypass key is **not** shipped to the frontend; staff reach `/admin/` via
  the session set on login. `ADMIN_ACCESS_KEY` (repo-root `.env`, consumed by
  `core/middleware.py`) is a server-side break-glass only.

## Architecture & Key Flows

### Instance lifecycle (the core of the system)

Backend instance management is fully async via Celery and shells out to
Compose via `settings.DOCKER_COMPOSE_CMD` (default `docker compose`, the v2
plugin; set `DOCKER_COMPOSE_CMD=docker-compose` for v1-only hosts). The
`_compose()` helper in `core/tasks.py` builds every Compose invocation. The
data model is `ActiveInstance` (`core/models.py`); the
work happens in `core/tasks.py`, triggered from `core/views.py`. This is the
`B4` (靶機分配服務) + `D1`/`D2` (Docker/容器管理) slice of the design.

- **Launch** (`LaunchInstanceView` → `launch_instance_task`, events EE-5/IE-5):
  the view creates an `ActiveInstance` row with `status="creating"` (empty
  `instance_url`/`container_id`) and returns `202 Accepted` immediately. The
  Celery task builds a per-instance compose file (`build_compose_content`),
  writes it to `<repo-root>/instances/docker-compose-<id>.yml`, brings it up,
  resolves the host-mapped port (`<lab.web_service>:<lab.web_port>`) into
  `instance_url` (host = `INSTANCE_PUBLIC_HOST`), and sets `status="running"`.
  On failure it sets `status="error"` (row kept so the UI can report it); if the
  row was deleted mid-create (user hit terminate), the task tears down and exits
  without retrying. The frontend polls `InstanceStatusView` every 3s and
  switches on `status`.
- **Per-lab compose** (`build_compose_content` in `core/tasks.py`): each `Lab`
  can carry its own `compose_template` (full docker-compose YAML) for arbitrary
  multi-service stacks; if blank, `default_compose_dict(lab)` **dynamically
  builds** the compose from structured fields — `needs_db` (bool; False → web
  container only) and `db_image` (e.g. `mysql:5.6`; mysql images also get the
  `mysql_native_password` command for legacy PHP). `Lab.web_service` /
  `Lab.web_port` declare which service/port to expose; any extra services in a
  custom template run internally (reachable by service name) but are not
  published to the user. The platform **force-
  injects** hardening onto every service (cpus/mem/pids from `INSTANCE_*`
  settings, `no-new-privileges`, `restart: no`, and `cap_drop` of dangerous
  Linux capabilities — `NET_RAW`/`SYS_ADMIN`/`DAC_READ_SEARCH`/… from
  `INSTANCE_CAP_DROP`, the anti-pivot/anti-escape control) and **strips** every
  host-reaching or cross-instance service key (`STRIPPED_SERVICE_KEYS` in
  `core/tasks.py`: `ports`/`privileged`/`cap_add`/`volumes`/`devices`/
  `network_mode`/`pid`/`build`/`container_name`/`deploy`/`labels`…), keeps only
  the top-level `services` block, and publishes only one controlled
  `127.0.0.1::<web_port>` on the web service. A per-lab `web_env` (multi-line
  `KEY=VALUE`) is merged into the web service's environment so BYO images that
  expect different DB env-var names don't have to hand-write a full
  `compose_template`. Labs are pure targets; the answer model stays a
  **case-insensitive** fixed-string match (`SubmitAnswerView`, `.casefold()`), so
  non-flag vuln types are authored to emit a static flag on success — or set
  `requires_answer=False` (the `solution` may be blank) to make the lab a pure
  sandbox: no answer, reflection, or completion, just launch-and-explore.
- **Constraints** (enforced in `LaunchInstanceView` inside a
  `select_for_update()` transaction): one active instance per user (C-3); a
  global cap of `settings.ACTIVEINSTANCE_LIMIT` (default 30, C-9); instances
  expire after `Lab.expiry_minutes` or, if unset, `settings.INSTANCE_EXPIRY_MINUTES`
  (default 30) after creation (C-4).
- **Current** (`CurrentInstanceView`, `/api/instances/current/`): returns the
  caller's live instance (non-error, unexpired) or `204`. The SPA treats the
  server as the source of truth — the `instance` store hydrates from this on load
  (`hydrateFromServer`), so a running instance survives a cleared `localStorage`
  or a second device; `ActiveInstanceSerializer` exposes `lab_id` and
  `max_extensions` (from `INSTANCE_MAX_EXTENSIONS`) for it, so the UI never
  hard-codes the extension cap. A global status bar (`InstanceStatusBar.vue`)
  renders the live countdown + extend/close.
- **Extend**: `ExtendInstanceView` (`/api/instances/extend/`) pushes `expires_at`
  out by `INSTANCE_EXTENSION_MINUTES`, up to `Lab.max_extensions` or (if unset)
  `INSTANCE_MAX_EXTENSIONS` times; the per-lab cap is surfaced to the UI via the
  serializer's `max_extensions`.
- **Teardown**: `terminate_instance_task` (manual, EE-11/IE-11, via
  `TerminateInstanceView`) and `cleanup_expired_instances` (Celery Beat every
  minute, IE-10) tear down compose projects and delete rows. Note
  `TerminateInstanceView` does **not** delete the row itself — the teardown task
  deletes it on completion (and always deletes at the end, success or fail), so
  the user's slot/global-cap stays occupied until the container is actually gone
  (no "close→relaunch" over-provisioning); broker-dispatch failure falls back to
  immediate row delete. `reconcile_instances`
  (Beat every 5 min) reconciles Docker↔DB by compose-project label: it kills
  orphan containers with no DB row and flags rows stuck in `creating` past
  `INSTANCE_ORPHAN_GRACE_MINUTES` as `error`.

When changing instance behavior, keep the view (sync DB bookkeeping +
constraints) and the task (actual Docker work) in sync via the `status` field
(`creating`/`running`/`error`).

### Auth

- JWT via `djangorestframework-simplejwt`. Custom `MyTokenObtainPairView`
  (`core/views.py`) wraps login to return a `redirect_url`; it authenticates
  **once** via the serializer — django-axes counts failures through Django's
  `user_login_failed` signal, so never call `AxesProxyHandler.user_login_failed`
  manually (it would double-count and halve the lockout threshold). Tokens carry
  `username` and `is_admin` claims (decoded client-side in
  `frontend/src/stores/auth.ts`). Routes: `/api/auth/login/`,
  `/api/auth/token/refresh/`, `/api/auth/logout/`. Logout blacklists the refresh
  token via the `token_blacklist` app; access token lifetime is 30 min
  (`ACCESS_TOKEN_MINUTES`); the SPA treats the session as alive while the
  *refresh* token (1 day) is valid and renews access tokens transparently.
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
(`CommunitySolutionListView`, C-6), and the list excludes the viewer's own
solution (it's "other people's solutions"; your own shows in the reflection
form). Labs with `requires_answer=False` opt out of
this whole flow — `SubmitAnswerView`/`ReflectionView` return 400 and no
`LabCompletion` is created — so sandbox labs never enter the state machine.

### Security controls (from the design doc, S-series)

- **S1** — password strength: `pwned-passwords-django` + validators requiring
  ≥12 chars and <0.5 similarity to username (`AUTH_PASSWORD_VALIDATORS`).
- **S2** — brute-force lockout: `django-axes` (`AXES_*` in settings). Note the
  code uses `AXES_FAILURE_LIMIT = 20` / 15-min window / 30-min cooloff — the
  design doc's "10 failures" figure is stale; **trust the code**.
  `AUTHENTICATION_BACKENDS` must stay an ordered **list** with `AxesBackend`
  first, or lockout can be bypassed. Axes locks per-username only, so the login
  endpoint also carries an IP-scoped DRF throttle (`THROTTLE_LOGIN`, default
  30/min) against username-rotation attacks. Behind nginx these IP throttles
  rely on `REST_FRAMEWORK["NUM_PROXIES"]` (default 1) so DRF reads the real
  client IP from `X-Forwarded-For` instead of trusting a spoofable raw header.
- **S3** — SQL-injection defense in the *platform itself*: all DB access goes
  through Django's ORM (parameterized). The vulnerable behavior lives only inside
  the lab images referenced by `Lab.docker_image`, never in `backend/`.

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
