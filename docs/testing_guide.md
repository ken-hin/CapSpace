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

**Current status (2026-08-07):** the DB harness in `conftest.py` is **built and
working** — `test_engine`, `_create_schema`, and `session` are all written, and the
async loop scopes are pinned in `pyproject.toml`. The model tests now run their
bodies (which are still `...` placeholders, so they pass trivially). **Next step:
write the real arrange/act/assert in `test_constraints.py` and
`test_relationships.py`, then the `migrated_db` fixture + `test_hypertables.py`.**
See §8 for how the finished harness works and §9 for the setup snags we hit getting
here.

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

### 3d. Event loops (and the "different loop" error)

Async code doesn't run itself — a single **event loop** drives it. The loop is the
conductor: it starts an `await`, and while that call waits on the database it runs
other ready work, then resumes the first when its answer arrives. One loop, juggling
everything.

The rule that trips people up: **anything created inside async code is bound to the
loop that was running when it was born** — especially database connections. An
`asyncpg` connection made on loop A cannot be used from loop B.

By default `pytest-asyncio` gives *each test its own fresh loop*. That collides with a
**session-scoped** async fixture: `test_engine` builds the engine (and opens
connections) on the session's loop, but a function-scoped test runs on its own new
loop and tries to use those connections — so you get:

```
RuntimeError: ... got Future ... attached to a different loop
```

The fix is to make everything share one loop, via the `pyproject.toml` settings in
§5:

```toml
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

Now fixtures and tests all run on the same session-wide loop, and the engine's
connections are valid everywhere. One distinction worth keeping: **loop scope** (which
event loop something runs on) and **fixture scope** (how often a fixture is rebuilt)
are independent axes. Pinning the loop to "session" does *not* force your `session`
fixture to be session-scoped — it stays function-scoped (fresh, rolled back per test)
while simply running on the shared loop.

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

**Pytest config** — makes async tests run without decorating each one, tells pytest
where tests live, and (the last two lines) pins every async fixture and test to a
single **session-wide event loop**:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
testpaths = ["tests"]
```

The two `*_loop_scope` lines aren't optional polish: without them the session-scoped
`test_engine` and the function-scoped tests run on *different* event loops and you hit
`RuntimeError: got Future ... attached to a different loop`. Setting them also
silences pytest-asyncio's "configuration option is unset" warning. See §3d for what an
event loop is and why this fixes it.

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

As of now the six **model** tests run their bodies and **pass trivially** — a body
of just `...` has no assertions, so it passes. That's the checkpoint that proves the
harness works end to end: collection, config, asyncio, the engine, `create_all`, and
the rollback `session` all function. The two **hypertable** tests still show `E`
(`fixture 'migrated_db' not found`) — expected, because that fixture is the one piece
not built yet. Next you replace each `...` with real arrange / act / assert, and
write `migrated_db`. (The Pydantic deprecation warning is unrelated and harmless.)

---

## 8. The DB harness — how it works

The harness is three fixtures in `conftest.py`, each feeding the next:
`test_engine` → `_create_schema` → `session`. A DB test just names `session` as a
parameter and receives a ready-to-use, auto-rolled-back `AsyncSession`.

### 8a. `test_engine` — the shared connection pool

```python
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()
```

An **engine** is not a connection — it's the *manager* of a pool of connections.
Picture a bank of phone lines to Postgres kept open and ready: code borrows a line,
talks, and hands it back, which is far cheaper than dialing fresh every time.
`create_async_engine` sets that up; `engine.dispose()` hangs up every line at the end
so no connections leak past the run.

It's **`scope="session"`** — built once for the whole run and shared by every test —
because standing up an engine and its pool is relatively expensive. Sharing one
engine is safe; test isolation is *not* the engine's job, it's the `session`
fixture's (see 8c).

On `yield`: a fixture with `yield` is split in two. Everything before `yield` is
setup, the yielded value is handed to whoever asked for it, and everything after
`yield` runs as teardown — with the function *frozen* in place while the tests use
it. Think of it as a "semi-return" that resumes later. That freeze is why the engine
stays alive for the whole session and only disposes at the very end.

### 8b. `_create_schema` — build the tables once, drop them after

```python
@pytest.fixture(scope="session", autouse=True)
async def _create_schema(test_engine):
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)   # committed on block exit
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
```

**`autouse=True`** makes this run automatically for the session — no test has to ask
for it. `create_all` reads every table registered on `Base.metadata` and issues the
`CREATE TABLE`s; this is why all model modules are imported at the top of
`conftest.py` (importing a model *registers* its table, and `create_all` only builds
tables it knows about).

The subtle, important part: **`create_all` must commit before the `yield`.** Here it
runs inside its own `async with test_engine.begin()` block, and that block *commits
when it exits* — the line right before `yield`. That matters because the `session`
fixture opens a **different** connection, and in Postgres one connection cannot see
another connection's *uncommitted* work. If you left `create_all` inside the same
open transaction as the `yield` (an easy mistake — see §9a), the tables would exist
only on that one held-open connection, and every test would fail with
`relation "..." does not exist`. Commit first, and the tables become visible to all
connections.

`run_sync` is a small adapter: `create_all`/`drop_all` are older *synchronous*
SQLAlchemy helpers, and `run_sync` lets an async connection run a sync function.

The matching `drop_all` after `yield` wipes the tables at the end, leaving the test
DB empty. (Leaving it out is also valid — `create_all` skips tables that already
exist — but dropping keeps things clean when models change. We briefly commented
`drop_all` out to *see* the tables via `psql \dt`; that's why they were persisting.)

### 8c. `session` — one rolled-back transaction per test

```python
@pytest.fixture
async def session(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = async_sessionmaker(bind=connection, expire_on_commit=False)
        async with session() as sesh:
            yield sesh
        await transaction.rollback()
```

This is the harness each test plugs into. It's **function-scoped** (the default), so
it runs fresh for every test. The sequence:

1. open a dedicated connection and **begin an outer transaction** on it,
2. bind a session to that same connection and hand it to the test,
3. when the test finishes, close the session and **roll the outer transaction back**.

The rollback is the isolation trick: everything the test inserted vanishes, so the
next test starts clean and no test depends on another. Crucially, it undoes **rows,
not tables** — the schema was committed once in `_create_schema` and stays put; only
the per-test *data* is thrown away. Two separate layers: the schema is the stage
(built once, persists), the rows are the actors (cleared after each scene).

One nice property: because the connection is *already* inside a transaction when the
session starts, SQLAlchemy 2.0 nests the session's work in a **SAVEPOINT** by default
(`join_transaction_mode="conditional_savepoint"`). So even a test that calls
`session.commit()` stays contained — the commit only releases the savepoint, and the
outer `rollback()` still wipes everything. You get real isolation whether or not a
test commits.

`expire_on_commit=False` keeps ORM objects usable *after* a commit. Without it,
SQLAlchemy expires an object's attributes on commit and re-fetches them on next
access — annoying when a test wants to assert on an object it just saved.

(Readability note: the local `session` here shadows the fixture name. It works, but
renaming it `Session` — the convention for a session *factory* — reads cleaner.)

### 8d. Suggested order to write the test bodies

The fixtures are done; these are the remaining `...` bodies to fill:

1. **`test_constraints.py`** — most self-contained; quickest green. Insert bad data,
   `await session.flush()`, and assert `pytest.raises(IntegrityError)`.
2. **`test_relationships.py`** — cascade delete + 1:1 navigation.
3. **`migrated_db` fixture + `test_hypertables.py`** — hardest; runs the real Alembic
   migration (not `create_all`) against the test DB, then queries Timescale's catalog.
   See §3c for why this one needs the migration instead of `create_all`.

---

## 9. Environment gotchas (things that bit us)

Real problems hit while wiring this up, and how each was fixed — so future-you
recognizes the symptom instead of re-debugging from scratch.

### 9a. Tables "don't exist" — `create_all` never committed

**Symptom:** the schema fixture runs without error, but every test fails with
`relation "..." does not exist`, or `psql \dt` shows nothing.

**Cause:** `create_all` ran inside a transaction that stayed open — e.g. the `yield`
sat *inside* the `async with test_engine.begin()` block. `begin()` only commits when
its block exits, so the `CREATE TABLE`s never committed, and the separate connection
each test uses couldn't see them (Postgres hides one connection's uncommitted work
from others).

**Fix:** let the `create_all` block close (and commit) *before* the `yield`, and do
`drop_all` in its own block afterward — the shape in §8b.

### 9b. A moved project folder breaks the venv

**Symptom:** after moving the repo (we moved `CapSpace` from `~/Desktop` to
`~/Developer`), `python` wasn't found, `echo $VIRTUAL_ENV` still pointed at the old
`~/Desktop/...` path even right after activating, and PyCharm couldn't see installed
packages.

**Cause:** **virtualenvs aren't relocatable.** When a venv is created, its absolute
path is baked into `.venv/bin/activate` and into the shebang of every console tool
(`pytest`, `alembic`, …). Moving the folder doesn't rewrite any of that, so it all
still points at the old location.

**Fix:** recreate the venv in place — fast, since `uv.lock` reproduces it exactly:

```bash
cd ~/Developer/CapSpace/backend
rm -rf .venv
uv sync
```

Do the same in `ml/`. Both venvs were rebuilt this way.

### 9c. `uv` "ignores" your activated environment

**Symptom:** `uv sync` warns `VIRTUAL_ENV=... does not match the project environment
path .venv and will be ignored`.

**What to know:** `uv` finds the environment from the **directory you're in** (the
nearest `pyproject.toml`), *not* from whatever venv is activated — so a stale
activated venv is simply ignored, with that warning. Two practical rules:

- `uv run <cmd>`, `uv sync`, `uv add` care about your *location*, not activation.
- Activation (`source .venv/bin/activate`) only matters for **bare** commands like
  `python` or `pytest`. `uv run pytest` sidesteps activation entirely — the tidiest
  way to dodge this whole class of mismatch.

Don't "fix" the warning with `--active` (that targets the wrong venv); just stop
having a stale one activated, or use `uv run`.

### 9d. PyCharm doesn't see the packages

**Symptom:** imports underline red / the interpreter's package list is empty, even
though `uv run python -c "import fastapi"` works fine in the terminal.

**What to check:**

- Point each module's interpreter at its own venv: **Settings → Project → Python
  Interpreter → Add Local Interpreter → Select existing → Virtualenv**, path
  `~/Developer/CapSpace/backend/.venv/bin/python` (and the `ml` one for that module).
  This is a multi-module project — backend and ml each have a separate venv; `uv`
  itself is a single shared tool at `~/.local/bin/uv`.
- **Invalidate Caches only re-indexes** the configured interpreter — it can't repair
  one pointing at a stale path. If the interpreter was created against the old
  location, delete it and add a fresh one.
- Confirm the env independently first: `uv run python -c "import fastapi, sqlalchemy"`.
  If that works, the problem is entirely on the IDE side.

**Connecting PyCharm's Database tool to the Docker Postgres:** the DB runs *inside*
the `sports-analytics-db` container (its data in a Docker named volume), reached from
your Mac through the `5432:5432` port mapping. Add a **PostgreSQL** data source —
host `localhost`, port `5432`, database `sports_analytics_test`, user `postgres`,
password `password`. TimescaleDB is just Postgres + an extension, so the plain
PostgreSQL driver is correct.

### 9e. `pytest tests/conftest.py` builds nothing

**Symptom:** running that collects `0 items` and no tables get created.

**Cause:** `conftest.py` holds *fixtures*, not tests — pytest reads it automatically
to *supply* fixtures; you never run it directly. (A `@pytest.fixture` named `test_*`
is still not collected as a test.) With zero tests collected, the `autouse` schema
fixture never fires.

**Fix:** run real test files/dirs — `uv run pytest tests/test_models -v`, or one test
like `uv run pytest tests/test_models/test_constraints.py::test_engine_connects`.

### 9f. Covered elsewhere

- **`RuntimeError: ... attached to a different loop`** → the event-loop scope fix in
  §3d / §5.
- **Tables persist after the run** → `drop_all` was commented out on purpose to
  inspect them; re-enable it (§8b).

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
