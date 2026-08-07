"""Voir tests/integration/conftest.py — même garde, répertoire différent."""

import pytest_asyncio

from src.tests.db_guard import skip_if_database_unavailable


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _require_database():
    await skip_if_database_unavailable()
