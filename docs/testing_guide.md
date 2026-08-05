# CapSpace — Backend Testing Guide

A reference for the backend test suite: the concepts behind it, how to set up the
test database, how everything is configured, and how to read the results. Written
while building out the Branch 1 tests, so it doubles as a plain-language glossary
for database + async testing if any of it is still fuzzy.

---

## 1. Where this fits in the project

These tests are the last unchecked item in **Branch 1 (`feat/multi-sport-foundation`)**
of the MLB build plan (`docs/mlb_implementation_plan.md`). The schema, models,
migrations, and seeds are done; Branch 1's "definition of done" also calls for:

- `test_models/test_relationships.py` — foreign-key cascades + 1:1 extensions
- `test_models/test_constraints.py` — unique / not-null constraints reject bad data
- `test_migrations/test_hypertables.py` — TimescaleDB hypertables got created

Once these pass (and `alembic upgrade head` round-trips on a fresh DB), Branch 1
can merge to `main`, unblocking Branch 2 (ingestion) and Branch 3 (Statcast/ML).

**Current status:** the three files exist as commented scaffolds. `pytest` collects
all 8 tests but they error at setup because the `session` and `migrated_db`
fixtures aren't written yet. **Next step: write the `session` fixture in
`conftest.py`.**

---

## 2. The test suite at a glance

```
backend/
├── pyproject.toml                    # deps + pytest config
└── tests/
    ├── conftest.py                   # shared fixtures (the "harness")
    ├── test_models/
    │   ├── test_constraints.py       # DB rejects bad data (unhappy-path tests)
    │   └── test_relationships.py     # cascade delete + 1:1 navigation
    └── test_migrations/
        └── test_hypertables.py       # migration registers hypertables
```

What each file proves:

- **`test_constraints.py`** — that the *database* refuses invalid data. Insert a
  duplicate `(venue_id, season)` ParkFactor, or a row missing a required field,
  and assert it raises. These are "unhappy path" tests: the interesting outcome
  is a rejection.
- **`test_relationships.py`** — that the model *wiring* works at the DB level.
  Delete a `Game` and confirm its `MlbGameDetails` row cascades away; confirm the
  1:1 relationship is navigable both directions and truly 1:1.
- **`test_hypertables.py`** — that the Alembic migration's Timescale step actually
  ran. Run the real migration, then ask Timescale's catalog which tables are
  hypertables.

> These are technically **integration tests**, not classic unit tests: they run
> against a real Postgres/TimescaleDB, because the database is the thing being
> verified. More on why in §3.

---

## 3. Core concepts

### 3a. Database foundations

**Tables, rows, fields.** A table is like a spreadsheet. Columns are *fields*,
each with a type (`Integer`, `String`, `Float`, `DateTime`). A row is one record.
`ParkFactor` has columns `id`, `venue_id`, `season`, `factor_runs`…; one row is a
ballpark's factors for one season.

**Constraints** are rules the database enforces on *every* row, no exceptions —
even if the app code has a bug. That's their value: they're the last line of
defense for trustworthy data. The kinds in your models:

- *Primary key (PK)* — the unique row ID; can't repeat, can't be null. `ParkFactor.id`.
- *NOT NULL* (`nullable=False`) — the field must have a value. `venue_id`, `season`.
- *Unique constraint* — a value or combination can't appear twice.
  `UniqueConstraint("venue_id", "season")` → no two rows for the same park + season.
- *Foreign key (FK)* — a field that must point at a real row in another table.

**Relationships** connect tables via FKs:

- *One-to-many* — one Venue has many ParkFactor rows (one per season). The "many"
  side holds the FK (`ParkFactor.venue_id → venues.id`).
- *One-to-one* — exactly one row on each side. `MlbGameDetails` extends `Game`:
  each game has exactly one details row. Enforced by making `game_id` both the PK
  *and* the FK — since a PK can't repeat, a game can't have two details rows.

**Cascading.** When two tables are linked by a FK, the DB needs to know what to do
with the child when the parent is deleted: block it, null the child's FK, or
*cascade* (delete the children too). `MlbGameDetails.game_id` uses
`ondelete="CASCADE"`, so **deleting a Game auto-deletes its details row.** Analogy:
shredding a folder takes the pages inside with it. Without cascade you'd get an
error or leave an orphan row pointing at a game that no longer exists.

**IntegrityError** is the Python exception SQLAlchemy raises when the database
rejects a write for breaking a constraint. Triggers: a duplicate
`(venue_id, season)` (unique), a NULL in a `nullable=False` column (not null), or
a FK pointing at a nonexistent row. It's raised *by the database*. In a test you
deliberately cause one and assert it happens — that's how you prove the guardrail
works.

### 3b. How the app talks to the database

**Transactions.** A group of operations treated as all-or-nothing — like a bank
transfer (debit + credit; if either fails, neither happens). You *begin* a
transaction, do work, then **commit** (make it permanent) or **roll back** (undo
everything since you began). Others don't see half-finished work.

**Rollback** is that undo, and it's the trick that keeps DB tests clean: each test
runs in a transaction that's rolled back at the end, so every row it created
disappears and the next test starts spotless. This is how tests stay *independent*
(no test relies on another running first) — and it's fast, since nothing is
permanently written.

**Sessions.** A SQLAlchemy `Session` is your workspace for a unit of work — the
object you use to `add`, query, and `delete` records. It tracks changes in memory
and manages the transaction underneath. Analogy: a shopping cart — `session.add(x)`
drops an item in; nothing is "charged" until commit.

**Session vs AsyncSession** — same idea, two flavors. A plain `Session` is
*synchronous*: a query blocks your program until the DB answers. An `AsyncSession`
can hand control back while it waits, so a web server juggling many requests
doesn't freeze on each DB call. Your app uses `AsyncSession` (with the `asyncpg`
driver), so your tests must be async too.

**Async, await, flush.**

- *Async* = "concurrent waiting." Normal code runs top-to-bottom and a slow call
  (DB, network) blocks everything. Async code can pause at a slow point, let other
  work run, and resume when the result is ready.
- `async def` marks a function that can pause. `await` marks the pause point —
  "start this and let other things run until it's done." You can only `await`
  inside an `async def`. Every DB call on an `AsyncSession` is awaited.
- **`flush` vs `commit`:** `flush` pushes pending changes to the DB *as SQL, inside
  the current transaction* — so constraints are checked and IDs are generated —
  but doesn't finalize. `commit` does a flush *and* makes it permanent (ending the
  transaction). In tests you often `await session.flush()` so an `IntegrityError`
  surfaces *now* (where `pytest.raises` can catch it) while still letting the
  fixture roll everything back. Analogy: flush = show the cashier your cart to
  check nothing's out of stock; commit = pay and leave.

### 3c. Testing concepts

**Asserting.** An assertion is a claim that must be true; if it's false, the test
fails. `assert result == 5` passes silently when true, fails loudly otherwise.
Every test is: set up a situation, do the thing, assert the outcome. For
"this should fail" cases, use `pytest.raises(IntegrityError)` — a special
assertion that passes *only if* the expected error happens.

**Fixtures** are reusable setup that pytest injects into tests. Instead of every
test repeating "connect, begin a transaction," one fixture does it and *yields* a
ready-to-use thing; any test that names it as a parameter receives it, and pytest
tears it down afterward. Analogy: the *mise en place* a prep cook lays out before
the chef (test) cooks. Your existing `client` fixture is one — it hands tests a
ready HTTP client.

- **The "session fixture"** is the one you're building: it yields an `AsyncSession`
  wrapped in a transaction that rolls back at the end. A test uses it just by
  naming it: `async def test_x(session): ...`
- **"Harness"** = the scaffolding *around* the test (connection, transaction,
  cleanup) so the test body holds only the interesting part. The session fixture
  is that harness.
- **"Clean"** means two things: clean *state* (rollback → each test starts from an
  empty DB, no leakage between tests) and clean *code* (the plumbing lives in one
  place, so test files stay short).
- Naming gotcha: "session fixture" here means "a fixture that yields a DB session."
  A *session-scoped* fixture is a different concept — one that runs once for the
  whole test run. Same word, unrelated meaning.

**Mocking vs. a real test DB.** *Mocking* replaces a real dependency with a fake
that returns canned answers — good when the dependency is slow/external and *not*
what you're testing. Here the database *is* what you're testing (does Postgres
enforce your constraint? does the cascade fire?), so a mock is useless — it'd only
return what you programmed. Instead you run against a real but **separate** test
database: same Postgres/TimescaleDB software, a throwaway DB with your tables but
no real data, so tests can insert, break, and wipe freely. "Dummy" just means
disposable, not different technology. (And don't swap in in-memory SQLite to skip
Docker — it isn't TimescaleDB, and it enforces constraints differently, e.g. FKs
off by default. Test against the same engine you run in production.)

**Schema build (`create_all`) vs. running migrations.** Your *schema* is the
*structure* — tables, columns, types, constraints — as opposed to the data. Two
ways to build it in a test DB:

1. `Base.metadata.create_all` — SQLAlchemy reads your model classes and issues
   `CREATE TABLE` for each, straight from the models. Fast; fine for the
   relationship/constraint tests, which only need the tables + constraints to exist.
2. `alembic upgrade head` — replays your migration files in order, exactly as
   production will. Slower, but it tests the migrations themselves.

The hypertable test *must* use option 2, because `create_all` builds plain tables
and does **not** run your `op.execute("SELECT create_hypertable(...)")` lines —
only the Alembic migration does. That's the whole distinction: model tests build
from models; the migration test runs the migration, because the migration is
what's under test.

**Hypertables & "registration."** TimescaleDB is a Postgres extension for
time-series data — tables with lots of timestamped rows (pitches over time, odds
snapshots over time). A **hypertable** looks like a normal table but Timescale
splits it into time-partitioned "chunks" so range queries stay fast at huge scale.
A plain `CREATE TABLE` gives an ordinary table; it becomes a hypertable only when
you call `create_hypertable('pitch_events', 'pitch_time')` — which lives in your
migration. **"Registered"** means Timescale recorded, in its internal catalog,
that the table is a hypertable (visible in `timescaledb_information.hypertables`).
Why it matters: if someone forgets the `create_hypertable` call, the table still
exists and stores data — silently as a plain table — and you won't notice until
it's huge and slow. The test queries the catalog and asserts `pitch_events`,
`book_odds`, and `stat_events` are registered.

---

## 4. Setting up the test database

The tests need a real TimescaleDB running, and their *own* database on it so they
never touch your dev data.

**1. Start the DB container** (from repo root). Your `docker-compose.yml` defines a
`db` service on `timescale/timescaledb:latest-pg16`, container name
`sports-analytics-db`, exposing port 5432 with DB `sports_analytics`, user
`postgres`, password `password`:

```bash
docker compose up -d db
```

You don't need the `redis` service for these tests — they only touch Postgres.

**2. Create the throwaway test database** once, on that same container:

```bash
docker exec sports-analytics-db createdb -U postgres sports_analytics_test
```

**3. Point the tests at it** via a *separate* engine in `conftest.py` — **not**
`app/db/session.py`'s `engine`, which points at your dev database:

```
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/sports_analytics_test"
```

The session fixture builds an engine from that URL, creates the tables
(`create_all`), and rolls back after each test. The migration test instead runs
`alembic upgrade head` against the test DB (see §3c).

**Why a separate DB and not a mock:** you're verifying real database behavior
(constraints, cascades, hypertables). A mock can't do that, and SQLite isn't
Timescale. Same engine as production = trustworthy tests.

---

## 5. Configuration (`pyproject.toml`)

**Dependency groups** (PEP 735). `test` holds the minimal set to run tests; `dev`
includes it so you get tests + future tooling with no duplication:

```toml
[dependency-groups]
test = [
    "pytest>=7.4",
    "pytest-asyncio>=0.23",
]
dev = [
    {include-group = "test"},
    # later: "ruff", "mypy", "ipython", ...
]
```

**Pytest config** — required so async tests run without decorating each one, and
so pytest knows where tests live:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Notes:

- `httpx` doesn't belong in the test group — it's already a runtime dependency
  (scrapers use it), so it's always installed.
- Two things currently sitting in runtime `dependencies` are really dev tooling and
  could move to a group later: `sphinx` (docs) and `pandas-stubs` (type stubs).
  Not urgent. `lxml`/`playwright` are fine in runtime since the scraper uses them
  (`playwright` needs `playwright install` to fetch its browser binaries).

---

## 6. The uv workflow

- After **hand-editing** deps in `pyproject.toml`, run **`uv sync`**. It re-locks
  if needed *and* installs — one command. You rarely need `uv lock` alone.
- Use `uv lock` by itself only to update the lockfile without installing, or to
  bump versions: `uv lock --upgrade` / `uv lock --upgrade-package <name>`.
- `uv add <pkg>` / `uv remove <pkg>` edit `pyproject.toml`, re-lock, *and* sync in
  one shot — nothing to run after.
- `uv run pytest` auto-locks + syncs before running, so it self-heals.
- **Commit `uv.lock` to git.** You sync across machines — the lockfile guarantees
  identical resolved versions on both, instead of drift.

---

## 7. Running the tests & reading the output

Run from `backend/`:

```bash
uv run pytest
```

**Reading the header** — it confirms your setup:

- `configfile: pyproject.toml`, `testpaths: tests` → config is being read.
- `asyncio: mode=Mode.AUTO` → `asyncio_mode = "auto"` took effect (async tests need
  no decorator).
- `collected N items` → tests were discovered and imported cleanly.

**ERROR vs FAILED** — different meanings:

- **ERROR** = something broke *around* the test, in setup/teardown (e.g. a fixture
  couldn't be provided). The test body never ran.
- **FAILED** = the body ran and an assertion (or unexpected exception) failed.

Right now all tests show `E` with `fixture 'session' not found` /
`fixture 'migrated_db' not found` — expected, because those fixtures are still
pseudocode. That's a *good* checkpoint: collection + config + asyncio all work; only
the fixtures are missing.

Once the `session` fixture exists (and the test DB is up), the six model tests will
run their bodies and **pass trivially** — a body of just `...` has no assertions, so
it passes. That confirms the harness works; then you replace each `...` with real
arrange / act / assert. (The Pydantic deprecation warning is unrelated and harmless.)

---

## 8. The session fixture — your next step

Mental model, three pieces (all scaffolded in `conftest.py`):

1. **Test engine** — an `AsyncSession`-capable engine pointed at
   `sports_analytics_test` (a `session`-scoped fixture; built once).
2. **Schema setup** — before tests run, `Base.metadata.create_all` on that engine
   so the test DB has your tables. (Import all model modules first so
   `Base.metadata` "sees" every table.)
3. **Session fixture** — for each test: open a connection, begin a transaction,
   bind a session to it, `yield` the session, then roll the transaction back.

Rough shape (pseudocode — fill in the real calls):

```python
@pytest.fixture
async def session(test_engine):
    async with test_engine.connect() as conn:
        txn = await conn.begin()
        Session = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with Session() as s:
            yield s
        await txn.rollback()
```

Once this resolves against a running test DB, the model tests stop erroring at
setup and start executing.

**Suggested order to implement:**

1. `session` fixture in `conftest.py` (+ test engine + schema setup)
2. `test_constraints.py` — most self-contained; quickest green
3. `test_relationships.py` — cascade + 1:1 navigation
4. `test_hypertables.py` — hardest; runs the real migration, queries the catalog

---

## Appendix — one-time housekeeping (from this session)

An earlier peek at the feat branch left `main`'s version of four files in the
working tree. None of your committed work was affected. If you haven't already
cleaned it up, run from the repo root:

```bash
rm -f .git/index.lock
git restore backend/app/seeds/seed_all.py \
            backend/app/sports/mlb/models/__init__.py \
            backend/app/sports/mlb/models/park_factor.py \
            backend/pyproject.toml
rm -f backend/app/seeds/sports/mlb/seed_park_factors_2025.py \
      backend/tests/test_models/_wtest.tmp
```

Don't run `git clean -fd` — it would delete the new (untracked) test scaffolds.
Afterward `git status` should show only the new `tests/` files and modified
`conftest.py` + `pyproject.toml`.
