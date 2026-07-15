# HireSense AI

An explainable, AI-assisted candidate screening and ranking **decision-support** system.

> **HireSense AI never autonomously advances, rejects, or hires a candidate.** Every score is a
> transparent recommendation; every state-changing hiring action requires an authenticated human
> action, which is permanently recorded in the audit log alongside the AI recommendation in effect
> at that time.

This repository is a **runnable, working implementation** of the platform described in the
HireSense AI Software Requirements Specification: a FastAPI backend with a real resume-parsing
pipeline and a transparent, weighted scoring/explainability engine, plus a Next.js + TypeScript +
Tailwind frontend.

---

## What's actually implemented here

This is a real, working MVP, not a set of empty stubs. Out of the box you get:

- JWT authentication with account lockout after repeated failed logins
- Role-based access control (Administrator, HR Staff, Recruiter, Hiring Manager)
- Job requisition management (draft → publish → close) with required/preferred skills
- Resume upload (PDF/DOCX) with **real text extraction, entity/skill extraction, experience
  calculation, and education-level detection** (see `backend/app/services/parser.py`)
- A transparent, configurable, weighted scoring engine that reproduces the SRS's scoring formula
  and produces a full factor-level explanation for every score (see
  `backend/app/services/scoring.py`)
- Candidate ranking, side-by-side comparison, and a human decision workflow (advance/reject/defer/hire)
- An immutable audit log recording every AI recommendation and every human decision together
- An admin panel for adjusting scoring weights (must sum to 100%) and reviewing the audit trail
- A dashboard with a hiring funnel and average-match-score analytics

### Important honesty note about the "AI" in this MVP

The SRS describes a production system using Sentence-Transformers embeddings, an XGBoost
classifier, and SHAP explainability. Training a real classifier and a real SHAP explainer requires
a **labeled historical hiring dataset**, which no one has handed to this project. Building that
pipeline without data would mean either faking the training data (misleading) or shipping a model
that can't actually be evaluated for accuracy or fairness (irresponsible for a hiring tool).

Instead, `backend/app/services/scoring.py` implements a fully transparent, deterministic,
**rule-based** scoring engine that:

- Uses the exact same weighted-category formula from the SRS (skills 35%, experience 25%,
  education 15%, certifications 10%, projects 10%, semantic similarity 5%, all configurable)
- Produces the exact same output shape a trained model + SHAP would (category breakdown,
  matched/missing skills, factor-level explanation, confidence, suitability label)
- Never uses protected attributes (age, gender, race, religion, nationality, marital status,
  photographs) as inputs, anywhere in the pipeline

**To upgrade to a trained ML model:** implement training in `ml/training/` (scaffolded, see
below), save the trained model + a fitted SHAP explainer, and swap the body of
`score_application()` in `backend/app/services/scoring.py` to call them instead of the rule-based
category functions. Every API route, the database schema, and the entire frontend already expect
exactly this output shape, so nothing else needs to change.

---

## Project structure

```
hiresense-ai/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # App entrypoint, CORS, router wiring
│   │   ├── core/            # Config, security (JWT/BCrypt), RBAC dependency
│   │   ├── db/               # SQLAlchemy engine/session
│   │   ├── models/            # ORM models (users, jobs, candidates, scores, audit, settings)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── parser.py      # Resume parsing pipeline (PDF/DOCX → structured profile)
│   │   │   ├── scoring.py     # Weighted scoring + explainability engine
│   │   │   └── skills_taxonomy.py
│   │   ├── api/v1/            # Route modules: auth, users, jobs, applications, admin
│   │   └── seed.py            # Creates demo users, a sample job, default settings
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                 # Next.js 14 (App Router) + TypeScript + Tailwind
│   ├── app/                  # Pages: login, dashboard, jobs, applications, admin
│   ├── components/           # Shell (nav/auth guard), score/status badges
│   ├── lib/                  # Typed API client, shared types
│   └── Dockerfile
├── docker-compose.yml         # Postgres + Redis + backend + frontend
└── .vscode/                   # Debug configs + recommended extensions
```

---

## Quick start — Option A: Docker Compose (recommended, closest to production)

Requires Docker and Docker Compose.

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the FastAPI backend (port 8000), and the Next.js frontend (port
3000). On first run, seed the database in a separate terminal:

```bash
docker compose exec backend python -m app.seed
```

Then open **http://localhost:3000** and sign in with one of the seeded accounts below.

---

## Quick start — Option B: run locally without Docker (fastest for development)

The backend defaults to a local **SQLite** file, so you can run it with zero external services.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed                # creates demo users + a sample job
uvicorn app.main:app --reload --port 8000
```

The API is now live at http://localhost:8000 — interactive docs at http://localhost:8000/docs.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000**.

### Seeded demo accounts

| Email                     | Password       | Role            |
|---------------------------|----------------|-----------------|
| admin@hiresense.ai        | Admin123!      | Administrator   |
| hr@hiresense.ai           | HrStaff123!    | HR Staff        |
| manager@hiresense.ai      | Manager123!    | Hiring Manager  |

A sample "Backend Engineer II" job posting is also created, already published, so you can upload a
resume and see scoring immediately.

---

## Opening this in VS Code

```bash
code hiresense-ai.code-workspace   # or just: code .
```

`.vscode/launch.json` includes ready-to-run debug configurations:
- **Backend: FastAPI (uvicorn)** — runs the API with the debugger attached and auto-reload
- **Backend: Seed database** — re-runs the seed script
- **Frontend: Next.js dev server** — runs `npm run dev` in an integrated terminal

Install the recommended extensions when VS Code prompts you (Python, Pylance, Tailwind CSS
IntelliSense, ESLint, Prettier, Docker).

---

## Trying the end-to-end flow

1. Sign in as `admin@hiresense.ai`.
2. Go to **Jobs → Backend Engineer II** (already published).
3. Upload a PDF or DOCX resume under "Upload resumes."
4. Within a couple of seconds, the candidate appears in the ranked applicant list with a score.
5. Click the candidate to see the full score breakdown, matched/missing skills, and the
   plain-language explanation.
6. Record a human decision (Advance / Reject / Defer / Mark hired) — this is logged with the AI
   recommendation that was in effect at that moment.
7. As `admin@hiresense.ai`, visit **Admin** to adjust scoring weights (must sum to 100%) and review
   the audit log.

---

## Configuration

Backend environment variables (`backend/.env`, see `backend/.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./hiresense.db` |
| `SECRET_KEY` | JWT signing secret — **change in production** | dev placeholder |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |
| `UPLOAD_DIR` | Where resume files are stored | `./uploads` |
| `MAX_UPLOAD_MB` | Per-file upload size limit | `10` |

Frontend environment variables (`frontend/.env.local`, see `frontend/.env.local.example`):

| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the backend API | `http://localhost:8000/api/v1` |

---

## Security notes for production use

- Change `SECRET_KEY` to a long, random value and keep it out of source control.
- Put the app behind HTTPS/TLS termination (e.g., a reverse proxy).
- Switch `DATABASE_URL` to PostgreSQL (already wired in `docker-compose.yml`).
- Consider adding a refresh-token revocation table (this MVP's refresh tokens are stateless JWTs).
- Add multi-factor authentication before handling real candidate PII in production — the auth
  service is structured so this is an additive change, not a redesign.

## Known simplifications (by design, for an honest MVP)

- OCR for scanned/image-only resumes is not implemented (would require a Tesseract system
  dependency); such files are flagged rather than silently mis-parsed.
- The "semantic similarity" and "project relevance" scores use lightweight keyword-overlap
  heuristics rather than Sentence-Transformer embeddings, to avoid a multi-hundred-MB model
  download as a hard requirement for running this project. The function boundary
  (`_semantic_similarity_score` / `_projects_score` in `scoring.py`) is where you'd swap in
  embeddings.
- Notifications, model-version history, and a few other SRS modules have working data models and
  endpoints but a minimal UI; extend `frontend/app/` as needed.

---

## License

Provided as-is for internal evaluation and further development.
