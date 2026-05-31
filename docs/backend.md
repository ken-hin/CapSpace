# Backend (`/backend`)

> Personal reference for the CapSpace backend — the FastAPI service that powers the real-time sports-analytics platform. Covers what each directory is, how the pieces fit together, the data model, and how to run/test it. Successor to the OpenCourt project; currently MLB-focused but built sport-agnostic.

---

## 1. What this is

The backend is an **async Python web service** built on **FastAPI**. It does four jobs:

1. **Serves a versioned REST API** (`/api/...`) for players, games, predictions, and computed stats.
2. **Pushes live game updates** to the SvelteKit frontend over **WebSockets** (`/ws/game/{id}`).
3. **Ingests external sports data** on a schedule via **Celery** background tasks (scrape → transform → store).
4. **Persists everything** in **PostgreSQL + TimescaleDB** (time-series hypertables for odds, stat events, pitches), with **Redis** for caching and live-update pub/sub.

The ML model training/inference lives in the separate top-level `/ml` directory — this backend only *reads* model metadata (`model_registry`) and *stores* the predictions the ML pipeline produces.

---

## 2. Technology stack

| Layer             | Technology                                | Notes                                     |
|-------------------|-------------------------------------------|-------------------------------------------|
| Language          | Python ≥ 3.11                             | Dockerfile pins 3.12-slim                 |
| Web framework     | FastAPI ≥ 0.115                           | async, auto OpenAPI at `/docs` & `/redoc` |
| ASGI server       | Uvicorn (standard) ≥ 0.34                 | `uvicorn app.main:app`                    |
| Config            | pydantic-settings ≥ 2.0                   | env-var driven `Settings`                 |
| ORM               | SQLAlchemy 2.0 (async)                    | `Mapped[...]` / `mapped_column` style     |
| DB driver         | asyncpg ≥ 0.30                            | `postgresql+asyncpg://` DSN               |
| Database          | PostgreSQL + TimescaleDB                  | Supabase-hosted in prod                   |
| Migrations        | Alembic ≥ 1.14                            | `alembic/` dir, async `env.py`            |
| Cache / pub-sub   | Redis ≥ 5.0 (`redis.asyncio`, hiredis)    | DB 0 cache, DB 1 broker, DB 2 results     |
| Task queue        | Celery ≥ 5.0 (Redis broker)               | worker + beat scheduler                   |
| HTTP client       | httpx ≥ 0.28                              | used by scrapers                          |
| Data processing   | pandas ≥ 2.0                              | transform/aggregation helpers             |
| Auth (scaffolded) | python-jose (JWT), passlib (bcrypt)       | `SECRET_KEY`, HS256, 30-min tokens        |
| Packaging         | uv + hatchling (PEP 621)                  | `pyproject.toml`, `uv.lock`               |
| Tests             | pytest, pytest-asyncio, httpx ASGI client | `tests/`                                  |

---

## 3. Architecture at a glance

```mermaid
flowchart TB
    subgraph clients["Clients"]
        FE["SvelteKit frontend<br/>(localhost:5173)"]
    end

    subgraph api["FastAPI app (app/main.py)"]
        direction TB
        MW["CORS middleware + lifespan"]
        REST["REST router /api<br/>players · games · predictions · stats"]
        WS["WebSocket router<br/>/ws/game/{id}"]
        SVC["Service layer<br/>game · player · prediction"]
    end

    subgraph workers["Background (Celery)"]
        BEAT["celery beat<br/>schedule"]
        WORK["celery worker<br/>tasks.py"]
        SCR["Scrapers (BaseScraper)"]
        TRf["Transformers (BaseTransformer)"]
    end

    subgraph stores["Data stores"]
        PG[("PostgreSQL +<br/>TimescaleDB")]
        RD[("Redis<br/>cache · broker · pubsub")]
    end

    EXT["External sports-data<br/>providers"]

    FE -->|HTTP /api| REST
    FE <-->|WebSocket| WS
    REST --> SVC --> PG
    WS <-->|subscribe| RD
    BEAT --> WORK
    WORK --> SCR --> EXT
    SCR --> TRf --> PG
    WORK -->|publish live updates| RD
    REST -.cache.-> RD
    MLPIPE["/ml pipeline<br/>(separate dir)"] -->|writes predictions| PG
    MLPIPE -.reads features/games.-> PG
```

**Request lifecycle (REST):** client → CORS middleware → `/api` router → feature router (e.g. `games.py`) → `get_db` dependency opens a request-scoped async session → service function runs the SQLAlchemy query → Pydantic response schema serializes the ORM object → JSON out. The session auto-commits on success, rolls back on exception, and always closes.

**Live updates (WebSocket):** client connects to `/ws/game/{game_id}` → `ConnectionManager` registers the socket under that game → a Redis subscription task listens for that game's channel → Celery ingestion publishes updates to Redis → the manager fans them out to every connected socket for the game.

---

## 4. Directory map

```
backend/
├── app/                      # the application package (everything importable as `app.*`)
│   ├── main.py               # FastAPI app factory, lifespan, CORS, router wiring, /health
│   ├── config.py             # Settings (env-driven) + cached get_settings()
│   ├── dependencies.py       # re-exports get_db / get_redis for Depends()
│   ├── api/                  # HTTP route handlers (thin; delegate to services)
│   ├── services/             # data-access / business logic (SQLAlchemy queries)
│   ├── schemas/              # Pydantic request/response models
│   ├── models/               # SQLAlchemy ORM models (sport-agnostic core)
│   ├── db/                   # engine/session + Redis client
│   ├── websockets/           # live-stats WebSocket router + connection manager
│   ├── ingestion/            # Celery app, tasks, scraper/transformer base classes
│   ├── sports/               # sport-specific code (currently mlb/)
│   └── seeds/                # reference-data seeding (venues, teams)
├── alembic/                  # migration environment + versions/
├── tests/                    # pytest suite (test_api/, test_services/)
├── alembic.ini               # Alembic config (script_location, default DSN)
├── pyproject.toml            # deps + build config (uv / hatchling)
├── uv.lock                   # locked dependency graph
└── Dockerfile                # python:3.12-slim + uv sync + uvicorn
```

---

## 5. Module-by-module

### 5.1 `app/main.py` — entrypoint
Builds the FastAPI app, registers CORS (origins from `CORS_ORIGINS`), includes the `/api` router and the WebSocket router, and exposes `/health`. The **lifespan handler** auto-creates all tables from SQLAlchemy metadata **only when `DEBUG=true`** (dev convenience; production relies on Alembic). On shutdown, it disposes of the async engine.

### 5.2 `app/config.py` — settings
`Settings` (pydantic-settings) reads env vars / `.env`. Key fields: `APP_NAME`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, and JWT settings (`SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`). `get_settings()` is `lru_cache`-wrapped so the whole process shares one immutable instance — safe to use as a dependency. **Defaults are dev-friendly; override secrets in prod.**

### 5.3 `app/db/` — persistence plumbing
- **`session.py`** — async engine (`create_async_engine`, pool_size 20 / max_overflow 10, `echo=DEBUG`) and `async_session` factory (`expire_on_commit=False`). `get_db()` is the request-scoped session dependency (commit/rollback/close pattern).
- **`redis.py`** — shared `redis.asyncio` client (`decode_responses=True`) from `REDIS_URL`; `get_redis()` dependency.

### 5.4 `app/api/` — REST routes
Thin handlers grouped by feature; each is an `APIRouter` with its own prefix/tags, aggregated in `router.py` under `/api`. All routes are async and depend on `get_db`.

| Router           | Prefix             | Endpoints                                                                       |
|------------------|--------------------|---------------------------------------------------------------------------------|
| `players.py`     | `/api/players`     | `GET /` (list, skip/limit) · `GET /{id}` · `POST /` (201)                       |
| `games.py`       | `/api/games`       | `GET /` (list, status filter via `Query`) · `GET /{id}` · `POST /` (201)        |
| `predictions.py` | `/api/predictions` | `GET /game/{game_id}` (read-only)                                               |
| `stats.py`       | `/api/stats`       | `GET /game/{game_id}` · `GET /player/{player_id}?season=` (computed aggregates) |

Plus `GET /health` and `WS /ws/game/{game_id}` registered directly on the app.

### 5.5 `app/services/` — business logic
Keeps SQLAlchemy out of the HTTP layer. One module per domain:
- `game_service.py` — `get_games` (paginated, optional status filter, the newest first), `get_game`, `create_game`.
- `player_service.py` — `get_players`, `get_player`, `create_player`.
- `prediction_service.py` — `get_predictions_for_game` (newest first) plus a **bulk-insert helper** used by the offline ML pipeline to write batches of predictions.

### 5.6 `app/schemas/` — Pydantic models
Request/response contracts (`*Create` for input, `*Response` for output) for `game`, `player`, `prediction`, `team`. These define the JSON shape the API accepts and returns, decoupled from the ORM models.

### 5.7 `app/models/` — sport-agnostic ORM core
`base.py` defines the declarative `Base` and a `TimestampMixin` (`created_at` / `updated_at` server defaults). Core tables:

| Model             | Table               | Purpose                                                                           |
|-------------------|---------------------|-----------------------------------------------------------------------------------|
| `Team`            | `teams`             | franchises; players back-reference                                                |
| `Player`          | `players`           | bio/role; FK → team; sport enum; bats/throws                                      |
| `Game`            | `games`             | schedule, score, status, season, embedded weather fields; FKs → teams + venue     |
| `Venue`           | `venues`            | ballparks/arenas                                                                  |
| `StatEvent`       | `stat_events`       | **TimescaleDB hypertable** — per-event time series (the substrate for `/stats`)   |
| `BookOdds`        | `book_odds`         | **hypertable** on `captured_at` — every odds pull (price, line, implied prob)     |
| `ClosingLine`     | `closing_lines`     | final pre-game line per book/market (for CLV)                                     |
| `Prediction`      | `predictions`       | model outputs: predicted value/prob/distribution, edge %, EV, recommended stake   |
| `ModelRegistry`   | `model_registry`    | trained-model metadata, hyperparams, metrics, `is_active`, optional MLflow run id |
| `FeatureSnapshot` | `feature_snapshots` | versioned feature vectors (JSON) per game/side                                    |
| `BetRecord`       | `bet_records`       | placed bets, stake, settlement result, P&L, captured CLV                          |
| `Injury`          | `injuries`          | player injury status/timeline                                                     |
| `WeatherSnapshot` | `weather_snapshots` | point-in-time weather                                                             |
| `Transaction`     | `transactions`      | roster/transaction log                                                            |
| `IngestionRun`    | `ingestion_runs`    | audit row per ingestion task (counts, status, errors)                             |
| `Sport` (enum)    | —                   | `mlb`, `nba`, `nhl`, `nfl`, `atp` (string-backed)                                 |

The betting/odds models (`BookOdds`, `ClosingLine`, `Prediction`, `BetRecord`) make the platform an edge-finding / CLV-tracking system, not just a stats display.

### 5.8 `app/sports/` — sport-specific extensions
The core is sport-agnostic; per-sport detail lives here. Only **MLB** is implemented:
- `sports/mlb/models/` — MLB-only tables that extend or hang off the core. `MlbGameDetails` and `MlbPlayerProfile` are 1:1 extensions of `Game`/`Player`. Plus `AtBat`, `PitchEvent` ("the Statcast firehose"), `PitcherArsenal`, `BatterVsPitcher`, `GameLineup`, `BullpenAvailability`, `ParkFactor`, `MlbStandings`, `MlbPlayerSeasonStats`, `MlbPlayerSplitStats`.
- `sports/mlb/scrapers/`, `transformers/`, `services/` — package scaffolding for MLB-specific ingestion/domain logic.

Adding a new sport = add a `sports/<code>/` package mirroring this layout; the core models, API, and ingestion framework stay unchanged.

### 5.9 `app/ingestion/` — background data pipeline
- **`celery_app.py`** — Celery app `sports_analytics`; broker on Redis DB 1, results on DB 2; JSON serialization, UTC. **Beat schedule:** `fetch_daily_schedule` daily at 07:00 UTC, `poll_live_games` every 30 s.
- **`tasks.py`** — the scheduled tasks: `fetch_daily_schedule` and `poll_live_games` (both with retries) and `ingest_historical_data(season)` for backfills.
- **`scrapers/base_scraper.py`** — `BaseScraper` ABC: async `fetch_schedule`, `fetch_live_stats`, `fetch_historical_games`. Concrete providers subclass it; the pipeline depends only on the interface.
- **`transformers/base_transformer.py`** — `BaseTransformer` ABC: `transform_game`, `transform_stat_events` — normalize raw provider JSON into model-ready dicts.

Pattern: **scrape (raw) → transform (normalize) → store (ORM)**, with each `IngestionRun` row recording the outcome.

### 5.10 `app/websockets/` — live stats
- **`manager.py`** — `ConnectionManager`: tracks active sockets grouped by `game_id`; `connect`/`disconnect`/`broadcast_to_game`.
- **`live_stats.py`** — `WS /ws/game/{game_id}` handler. Registers the socket, subscribes to Redis for that game, and relays published updates to the client until disconnect.

### 5.11 `app/seeds/` — reference data
`seed_all.py` (`python -m app.seeds.seed_all`) seeds venues first, flushes so they get PKs, then teams (which carry `home_venue_id`), and commits once. MLB venue/team seed data lives in `seeds/sports/mlb/`.

### 5.12 `alembic/` — migrations
Async migration environment (`env.py`) + `versions/`. Current baseline migration: `8610aacd7d0f_sports_agnostic_tables_and_mlb_specific_*`. `alembic.ini` holds the default DSN and logging config. **Production schema changes go through Alembic** (vs. the `DEBUG`-only auto-create in `main.py`).

### 5.13 `tests/` — test suite
`conftest.py` provides an async `client` fixture bound to the app via **in-process ASGI transport** (no socket needed). Split into `test_api/` (endpoint-level) and `test_services/` (service-layer) packages. Note: the package scaffolding and fixtures exist, but concrete `test_*.py` files are not yet written.

---

## 6. Configuration & environment

Settings come from env vars (or `.env`). The important ones:

| Var                           | Default                                                                  | Meaning                              |
|-------------------------------|--------------------------------------------------------------------------|--------------------------------------|
| `APP_NAME`                    | `Sports Analytics Platform`                                              | shown in docs/health                 |
| `DEBUG`                       | `false`                                                                  | enables SQL echo + table auto-create |
| `DATABASE_URL`                | `postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics` | async Postgres DSN                   |
| `REDIS_URL`                   | `redis://localhost:6379/0`                                               | cache DB (broker/results use DB 1/2) |
| `CORS_ORIGINS`                | `["http://localhost:5173"]`                                              | allowed frontend origins             |
| `SECRET_KEY`                  | `change-me-in-production`                                                | JWT signing key — **must override**  |
| `ALGORITHM`                   | `HS256`                                                                  | JWT alg                              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                                                     | token lifetime                       |

See `.env.example` at the repo root.

---

## 7. Running it

**Locally (dev):**
```bash
cd backend
uv sync                       # install deps from uv.lock
# bring up Postgres + Redis (docker-compose at repo root)
alembic upgrade head          # apply migrations  (or set DEBUG=true to auto-create)
python -m app.seeds.seed_all  # seed venues + teams
uvicorn app.main:app --reload # API on :8000, docs at /docs
```

**Background ingestion (separate processes):**
```bash
celery -A app.ingestion.celery_app worker --loglevel=info   # worker
celery -A app.ingestion.celery_app beat   --loglevel=info   # scheduler
```

**Docker:** the `Dockerfile` builds on `python:3.12-slim`, installs deps with `uv sync --no-dev --frozen`, exposes 8000, and runs uvicorn. Orchestrated alongside Postgres/Redis via the repo-root `docker-compose.yml`.

**Tests:**
```bash
cd backend
pytest                        # async ASGI client, no live server needed
```

---

## 8. Conventions & things to remember

- **Async everywhere** — DB sessions, Redis, routes, and scrapers are all async; don't block the event loop.
- **Thin routes, fat services** — handlers in `app/api/` should delegate query/persistence logic to `app/services/`.
- **Sport-agnostic core, sport packages on top** — never put MLB-specific columns on a core model; extend via `sports/mlb/`.
- **Hypertables** — `stat_events`, `book_odds` (and MLB `pitch_events`) are TimescaleDB hypertables with composite PKs including the time column; the time column can't be dropped from the PK.
- **`DEBUG` auto-create is dev-only** — real schema lives in Alembic migrations.
- **Redis DB layout** — 0 = cache/pubsub, 1 = Celery broker, 2 = Celery results.
- **Predictions are written by `/ml`, read by the API** — this service owns the schema and serving, not the modeling.

---

*Last updated: 2026-05-31. Generated from a read-through of the actual backend source.*
