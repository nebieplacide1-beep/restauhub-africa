"""Partagé par `tests/integration/conftest.py` et `tests/api/conftest.py`
(deux répertoires distincts, donc deux fixtures autouse, mais une seule
implémentation) — voir la note en tête de `tests/integration/conftest.py`."""

import pytest
from sqlalchemy.exc import OperationalError

from src.shared_kernel.db.session import get_engine


async def skip_if_database_unavailable() -> None:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except (OperationalError, OSError) as exc:
        pytest.skip(f"PostgreSQL indisponible pour ce test : {exc}")
