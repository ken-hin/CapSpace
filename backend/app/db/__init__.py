"""Database access package.

Holds the infrastructure for talking to external data stores: the async
SQLAlchemy engine/session factory (:mod:`app.db.session`) and the Redis client
(:mod:`app.db.redis`), each of which exposes a FastAPI dependency provider.
"""
