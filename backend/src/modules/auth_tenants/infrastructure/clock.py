from datetime import UTC, datetime

from src.modules.auth_tenants.application.ports import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
