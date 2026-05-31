"""Sport-specific extensions package.

Houses per-sport subpackages (currently ``mlb``) that extend the sport-agnostic
core with sport-specific ORM models, scrapers, transformers, and services. This
keeps MLB-only concerns (pitch-level data, park factors, arsenals, etc.) cleanly
separated from the shared core in :mod:`app.models`.
"""
