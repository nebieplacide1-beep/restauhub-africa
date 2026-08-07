"""Ces tests nécessitent une vraie base PostgreSQL (la Row-Level Security
n'existe pas en SQLite) : `docker compose up -d db && alembic upgrade head
&& python scripts/seed_reference_data.py`, puis `pytest`. Ils se
désactivent automatiquement (skip) si la base n'est pas joignable — voir
backend/README.md."""

import pytest_asyncio

from src.tests.db_guard import skip_if_database_unavailable


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _require_database():
    await skip_if_database_unavailable()
