from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.succursales.domain.entities import OpeningHours, Succursale, SuccursaleStatus
from src.modules.succursales.domain.repositories import SuccursaleRepository
from src.modules.succursales.infrastructure.db.models import SuccursaleModel


def _to_domain(model: SuccursaleModel) -> Succursale:
    return Succursale(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        address_line=model.address_line,
        city=model.city,
        country=model.country,
        default_currency=model.default_currency,
        default_locale=model.default_locale,
        status=SuccursaleStatus(model.status),
        opening_hours=OpeningHours(model.opening_hours),
        phone_number=model.phone_number,
        created_at=model.created_at,
    )


class SqlAlchemySuccursaleRepository(SuccursaleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, succursale: Succursale) -> None:
        self._session.add(
            SuccursaleModel(
                id=succursale.id,
                tenant_id=succursale.tenant_id,
                name=succursale.name,
                address_line=succursale.address_line,
                city=succursale.city,
                country=succursale.country,
                default_currency=succursale.default_currency,
                default_locale=succursale.default_locale,
                status=succursale.status.value,
                opening_hours=succursale.opening_hours.schedule,
                phone_number=succursale.phone_number,
            )
        )
        await self._session.flush()

    async def get_by_id(self, succursale_id: UUID) -> Succursale | None:
        model = await self._session.get(SuccursaleModel, succursale_id)
        return _to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID) -> list[Succursale]:
        result = await self._session.execute(
            select(SuccursaleModel)
            .where(SuccursaleModel.tenant_id == tenant_id)
            .order_by(SuccursaleModel.created_at)
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def list_by_ids(self, succursale_ids: list[UUID]) -> list[Succursale]:
        if not succursale_ids:
            return []
        result = await self._session.execute(
            select(SuccursaleModel).where(SuccursaleModel.id.in_(succursale_ids))
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def update(self, succursale: Succursale) -> None:
        model = await self._session.get(SuccursaleModel, succursale.id)
        assert model is not None
        model.name = succursale.name
        model.address_line = succursale.address_line
        model.city = succursale.city
        model.status = succursale.status.value
        model.opening_hours = succursale.opening_hours.schedule
        model.phone_number = succursale.phone_number
        await self._session.flush()
