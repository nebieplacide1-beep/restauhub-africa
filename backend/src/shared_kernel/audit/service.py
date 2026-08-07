from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared_kernel.audit.models import AuditLogModel


async def record_audit_event(
    session: AsyncSession,
    *,
    action: str,
    result: str,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Écrit un événement d'audit (BR-25). Append-only : ce module n'expose
    volontairement aucune fonction de mise à jour ou de suppression (BR-26).
    """
    session.add(
        AuditLogModel(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            result=result,
            ip_address=ip_address,
            event_metadata=metadata or {},
        )
    )
