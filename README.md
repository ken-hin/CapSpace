# CapSpace

A multi-sport analytics platform built for pre-game ML predictions, live score tracking via WebSockets, and historical stat analysis. MLB is the first sport implemented, with the data model designed to support additional leagues.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 5 + Svelte 5 + Tailwind CSS v4 + shadcn-svelte |
| Charts | D3.js + LayerCake |
| Icons | Lucide Svelte |
| API Server | FastAPI (Python 3.11+) + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Real-Time | FastAPI WebSockets + Redis Pub/Sub |
| Database | PostgreSQL 16 + TimescaleDB |
| Task Queue | Celery + Celery Beat |
| ML | scikit-learn, PyTorch |
| Deployment | Railway (backend) + Supabase (database) |
| Package Mgmt | uv (Python) + Bun (JavaScript) |

## Project Structure

```
CapSpace/
├── backend/
│   ├── pyproject.toml          # Python deps (managed by uv)
│   ├── alembic/                # Database migrations
│   └── app/
│       ├── api/                # REST route handlers (games, players, predictions, stats)
│       ├── db/                 # Async SQLAlchemy engine + Redis client
│       ├── ingestion/          # Celery tasks, base scraper & transformer
│       ├── models/             # SQLAlchemy ORM models (shared across sports)
│       ├── schemas/            # Pydantic request/response schemas
│       ├── seeds/              # Seed scripts (MLB teams, venues, park factors)
│       ├── services/           # Business logic (game, player, prediction)
│       ├── sports/
│       │   └── mlb/            # MLB-specific models, scrapers, services
│       └── websockets/         # Live stat WebSocket handlers
├── frontend/
│   ├── package.json            # JS deps (managed by bun)
│   └── src/
│       ├── lib/
│       │   ├── api/            # Typed API client
│       │   ├── components/     # UI components (shadcn-svelte + custom charts/live)
│       │   ├── stores/         # Svelte stores
│       │   └── websocket.ts    # WebSocket client
│       └── routes/             # SvelteKit pages (games, players, predictions)
├── ml/
│   ├── pyproject.toml          # ML deps (managed by uv)
│   └── src/                    # Feature engineering + model training
└── docker-compose.yml          # Local PostgreSQL/TimescaleDB + Redis
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Bun](https://bun.sh/) — `curl -fsSL https://bun.sh/install | bash`
- Docker & Docker Compose

## Local Setup

### 1. Clone and configure environment

```bash
git clone <repo-url> && cd CapSpace
cp .env.example .env
```

The `.env` defaults work out of the box with Docker Compose. For production, set `SECRET_KEY` to a random string and update `DATABASE_URL` to point at Supabase.

### 2. Start local services (PostgreSQL + Redis)

```bash
docker-compose up -d
```

This starts TimescaleDB on port `5432` and Redis on port `6379`.

### 3. Set up the backend

```bash
cd backend
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

Run database migrations:

```bash
alembic upgrade head
```

Start the API server:

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Seed the database (optional)

```bash
python -m app.seeds.seed_all
```

This loads MLB teams, venues, and park factors.

### 5. Set up the frontend

```bash
cd frontend
bun install
bun run dev
```

Frontend: http://localhost:5173

### 6. Start the Celery worker

In a separate terminal from the `backend/` directory with the virtualenv active:

```bash
celery -A app.ingestion.celery_app worker --loglevel=info --beat
```

### 7. ML environment (optional)

```bash
cd ml
uv venv && source .venv/bin/activate
uv pip install -e .
jupyter lab
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics` | Async PostgreSQL DSN |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `DEBUG` | `true` | Auto-creates DB tables on startup when enabled |
| `SECRET_KEY` | `change-me-to-a-random-string` | JWT signing key — override in production |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed browser origins |

## Deployment

- **Database:** Supabase (managed PostgreSQL + TimescaleDB)
- **Backend + Worker + Redis:** Railway (git push to deploy)
- **Frontend:** Railway or Vercel
