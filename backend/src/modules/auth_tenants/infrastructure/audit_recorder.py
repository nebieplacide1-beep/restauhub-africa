from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth_tenants.application.ports import AuditRecorder
from src.shared_kernel.audit.service import record_audit_event


class SqlAlchemyAuditRecorder(AuditRecorder):
    """Lie `shared_kernel.audit.service.record_audit_event` à la session de
    la requête courante (section 3.5 de l'architecture)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        action: str,
        result: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        await record_audit_event(
            self._session,
            action=action,
            result=result,
            tenant_id=tenant_id,
            user_id=user_id,
            ip_address=ip_address,
            metadata=metadata,
        )
