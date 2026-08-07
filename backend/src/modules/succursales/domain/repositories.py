from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.succursales.domain.entities import Succursale


class SuccursaleRepository(ABC):
    @abstractmethod
    async def add(self, succursale: Succursale) -> None: ...

    @abstractmethod
    async def get_by_id(self, succursale_id: UUID) -> Succursale | None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[Succursale]: ...

    @abstractmethod
    async def list_by_ids(self, succursale_ids: list[UUID]) -> list[Succursale]: ...

    @abstractmethod
    async def update(self, succursale: Succursale) -> None: ...
