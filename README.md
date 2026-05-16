# Sports Analytics Platform

A real-time sports analytics platform with pre-game ML predictions, live score tracking, and historical stat analysis.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit + shadcn-svelte + D3.js |
| API Server | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Real-Time | FastAPI WebSockets + Redis Pub/Sub |
| Database | PostgreSQL 16 + TimescaleDB |
| Ingestion | Celery + Celery Beat |
| ML | scikit-learn, PyTorch (local) |
| Deployment | Railway + Supabase |
| Package Mgmt | uv (Python) + Bun (JavaScript) |

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Bun](https://bun.sh/) — `curl -fsSL https://bun.sh/install | bash`
- Docker & Docker Compose

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
```

### 2. Start local services

```bash
docker-compose up -d
```

### 3. Set up the backend

```bash
cd backend
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Run database migrations
alembic revision --autogenerate -m "initial tables"
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

API running at http://localhost:8000 — Swagger UI at http://localhost:8000/docs

### 4. Set up the frontend

```bash
cd frontend
bun install

# Initialize shadcn-svelte
bunx shadcn-svelte@latest init
bunx shadcn-svelte@latest add button card table badge

# Start the dev server
bun run dev
```

Frontend running at http://localhost:5173

### 5. Start the Celery worker

```bash
cd backend
celery -A app.ingestion.celery_app worker --loglevel=info --beat
```

### 6. Set up ML environment (optional)

```bash
cd ml
uv venv
source .venv/bin/activate
uv pip install -e .
jupyter lab
```

## Project Structure

```
sports-analytics/
├── backend/              # FastAPI + SQLAlchemy + Celery
│   ├── pyproject.toml    # Python deps (managed by uv)
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── api/          # API route handlers
│   │   ├── services/     # Business logic
│   │   ├── websockets/   # Live stat handlers
│   │   ├── ingestion/    # Celery tasks + scrapers
│   │   └── db/           # Database + Redis config
│   └── alembic/          # Database migrations
├── frontend/             # SvelteKit + shadcn-svelte
│   ├── package.json      # JS deps (managed by bun)
│   └── src/
│       ├── routes/       # Page routes
│       └── lib/          # Components, stores, API client
├── ml/                   # ML pipeline (local only)
│   ├── pyproject.toml    # ML deps (managed by uv)
│   ├── notebooks/        # Jupyter exploration
│   └── src/              # Feature engineering + training
└── docker-compose.yml
```

## Deployment

- **Database:** Supabase (managed PostgreSQL + TimescaleDB)
- **Backend + Worker + Redis:** Railway (git push to deploy)
- **Frontend:** Railway or Vercel
