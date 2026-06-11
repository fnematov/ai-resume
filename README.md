# AI Resume — Multi-Tenant Resume Filtering Platform

Candidates upload resumes to an organization's **Telegram bot**; an **AI** scores each resume
against a specific vacancy and returns a match % with reasons; org admins review a **ranked
list** of applicants in a web admin panel. Multi-tenant: organizations self-register, a
super-admin approves them, and each org brings its own Telegram bot + AI key.

## Architecture

| App | Stack | Purpose |
|-----|-------|---------|
| `backend/` | FastAPI · SQLAlchemy 2 (async) · Celery · PostgreSQL · Redis | API for Telegram webhooks **and** the admin panel; background scoring worker |
| `frontend/` | Vue 3 · TypeScript · Vite · Tailwind · shadcn-vue conventions | Admin panel (org dashboard + super-admin moderation) |

Services (docker-compose): `api`, `worker`, `db` (Postgres), `redis`, `frontend` (nginx).

**Candidate flow:** `t.me/<orgbot>?start=job_<id>` deep-links a candidate to a vacancy (a bare
`/start` lists the org's open roles). They upload a resume → the worker normalizes it
(PDF/image natively; DOC/DOCX via LibreOffice), sends it to the org's AI provider, and stores
a structured result: **match %, matched/missing skills, strengths, concerns, summary**.

## Key design decisions

- **Provider-agnostic AI** (`backend/app/services/ai/`): one `AIProvider` interface, with
  `ClaudeProvider` and `OpenAIProvider`. Each org picks a provider + model and supplies its own key.
- **Per-org Telegram bots:** each org saves its bot token; the platform registers a webhook per
  org and verifies the `X-Telegram-Bot-Api-Secret-Token` header.
- **Row-level multi-tenancy** via `org_id` on every tenant-owned row.
- **Secrets encrypted at rest** (Fernet): bot tokens and AI keys are never returned in plaintext.

## Quick start (local development)

```bash
cp .env.example .env
cp docker-compose.override.yml.example docker-compose.override.yml   # hot-reload + local ports
# In .env set FRONTEND_PORT=5173 and API_PORT=8000 for the usual local ports.

docker compose up -d --build        # db, redis, api (runs migrations), worker, frontend
```

- Admin panel: http://localhost:5173
- API docs: http://localhost:8000/docs
- Default super-admin: `admin@airesume.io` / `admin12345` (from `.env`)

The override mounts the source for hot-reload and exposes Postgres (5434) and Redis (6380)
on the host. Without it (i.e. on a server) the stack runs in production mode.

## Deploy to a server

The base `docker-compose.yml` is production-ready: images are baked, the api runs migrations
on start, the worker runs the Celery **beat** scheduler, and **db/redis are not exposed to the
host** (internal network only). Only the admin panel (and optionally the api) get host ports —
**configurable, with non-standard defaults** so they don't clash with other services.

```bash
git clone git@github.com:fnematov/ai-resume.git && cd ai-resume
cp .env.example .env
# Edit .env — REQUIRED:
#   JWT_SECRET        openssl rand -hex 32
#   ENCRYPTION_KEY    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   SUPERADMIN_*      your admin credentials
#   PUBLIC_BASE_URL   your panel's public HTTPS domain (webhooks go here)
#   FRONTEND_PORT     host port for the panel (default 8090)
#   API_PORT          host port for the api  (default 8010)

docker compose up -d --build        # NOTE: no override file on the server => production mode
```

Then put a reverse proxy (nginx / Caddy / Traefik) with your domain + HTTPS in front of
`FRONTEND_PORT`. The panel's nginx proxies `/api` to the backend, so the admin panel **and**
the Telegram/Calendly webhooks both work through that one domain — set `PUBLIC_BASE_URL` to it.

**Only ONE host port is bound in production** (the admin panel) — everything else lives on
the internal docker network. This is conflict-free with an existing host Postgres / Redis /
nginx:

| Service | Host port | Note |
|---------|-----------|------|
| frontend (nginx) | `${FRONTEND_PORT}` (default **8090**) | The single public port. Your host nginx reverse-proxies your domain here. Never 80/443. |
| api | — | Internal only; reached via the frontend nginx `/api` proxy. (To expose it directly, add `ports` to the api service.) |
| Postgres | — | Internal only. The container's Postgres is on the docker network and **does not touch your host's 5432**. |
| Redis | — | Internal only. |

Example host-nginx server block:

```nginx
server {
    server_name hire.yourcompany.com;
    client_max_body_size 20m;
    location / { proxy_pass http://127.0.0.1:8090; proxy_set_header Host $host; }
    # add your certbot/TLS config
}
```

> Keep `ENCRYPTION_KEY` stable for a deployment — it decrypts stored bot tokens and AI keys.

## Telegram webhooks in local dev

Telegram must reach your API over **public HTTPS**. Run a tunnel and point `PUBLIC_BASE_URL` at it:

```bash
cloudflared tunnel --url http://localhost:8000     # or: ngrok http 8000
# Put the https URL into .env as PUBLIC_BASE_URL, then: docker compose up -d api
```

When an org saves its bot token (Settings page), the API calls `setWebhook` automatically using
`PUBLIC_BASE_URL`.

## End-to-end walkthrough

1. **Register** an organization at `/register`.
2. Sign in as the **super-admin** → **Organizations** → **Approve** it.
3. Sign in as the **org admin** → **Settings**: connect a Telegram bot (token from @BotFather)
   and an AI provider + API key.
4. **Vacancies** → create an "open" role → copy its `t.me/<bot>?start=job_<id>` link.
5. A candidate opens the link in Telegram and uploads a resume → the bot offers to add an
   optional **cover letter** (text or file); it's folded into the AI analysis.
6. The application appears under the vacancy, transitions `pending → scored`, and shows the
   match % and reasons. The table sorts highest-match first.

You can also **manually upload** a resume from the vacancy page (bypasses Telegram).

## Recruitment pipeline (Phase 2 — ATS)

Beyond ranking, the platform runs the full hiring workflow:

- **Pipeline board** — `/vacancies/:id/pipeline`: drag candidates across stages
  (new → screening → shortlisted → test task → interview → offer → hired, plus rejected).
- **One-click actions** on the application page — Send test task / Invite to interview /
  Send offer / Reject. Each renders a per-org **message template** (`{{candidate_name}}`,
  `{{job_title}}`, `{{company}}`, `{{scheduling_link}}`…) and delivers it via the Telegram bot.
- **Cover letters** — after uploading a resume the candidate can optionally add a cover letter
  (text or file); it's included in the AI score and shown on the application page.
- **Two-way chat** — candidate replies appear as a conversation thread; the recruiter can reply.
- **AI-graded test tasks** — the candidate's submitted file is scored against the task by the
  same AI engine; the grade shows on the application page.
- **Calendly scheduling** — connect a Calendly token in Settings; interview invites carry a
  per-application link. When the candidate books, a webhook records the interview (time +
  Google Meet link) and advances the stage. Connect Google Calendar inside Calendly for the
  Meet/Calendar automation.
- **PDF offer letters** — offers generate a branded PDF (DOCX → PDF via LibreOffice) attached
  to the Telegram message.
- **GDPR** — consent is recorded on apply; candidates can send `/forget` to erase their data;
  Settings has a retention window (a Celery beat task purges expired candidates) + privacy notice.
- **Hybrid automation** — Settings → Automation rules: score windows trigger auto-reject /
  auto-shortlist / templated messages right after scoring (first matching rule wins).

### Dev workflow note
`docker-compose.override.yml` mounts the source and runs `uvicorn --reload`, so backend code
changes apply without a rebuild. The Celery worker has no hot-reload — run
`docker compose restart worker` after changing worker/handler/service code.

## Development

```bash
# Backend tests (mocked AI + extraction)
docker compose run --rm --no-deps --entrypoint sh -v "$(pwd)/backend:/app" api -c "python -m pytest -q"

# Frontend type-check + build
cd frontend && npm install && npm run build

# Frontend dev server (proxies /api -> http://localhost:8000)
cd frontend && npm run dev
```

### Database migrations

```bash
# Autogenerate after model changes (source mounted so the file lands on the host):
docker compose run --rm --no-deps --entrypoint alembic -v "$(pwd)/backend:/app" api revision --autogenerate -m "describe change"
docker compose build api    # bake the new migration into the image
docker compose run --rm --no-deps --entrypoint alembic api upgrade head
```

The `api` container also runs `alembic upgrade head` automatically on startup.

## Project layout

```
backend/app/
  api/v1/        auth, organizations, vacancies, applications, analytics, telegram
  core/          config, db, security (JWT + Fernet), deps (auth/tenant scoping), seed
  models/        organizations, users, vacancies, candidates, applications
  schemas/       Pydantic request/response models
  services/
    ai/          provider-agnostic scoring (base, claude, openai_provider)
    extraction/  normalize PDF/image/DOC/DOCX -> ResumeDocument
    telegram/    httpx client, webhook handler, Redis chat-state
    storage/     resume file storage (local; swappable for S3)
  workers/       Celery app + score_application task
frontend/src/
  api/           axios client + typed endpoints
  components/ui/ shadcn-vue style primitives
  views/         login, register, dashboard, vacancies, application detail, settings, admin/*
```
