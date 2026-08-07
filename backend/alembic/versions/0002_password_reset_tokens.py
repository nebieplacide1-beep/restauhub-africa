"""Mot de passe oublié — table password_reset_tokens

Complète la spécification API validée (docs/modules/01-auth-tenants/06-api-specification.md#61)
qui n'avait pas encore d'implémentation pour `POST /auth/password/forgot`
et `POST /auth/password/reset`.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    op.create_index("ix_password_reset_tokens_tenant_id", "password_reset_tokens", ["tenant_id"])

    # Même schéma de policy que les autres tables pré-authentification (users,
    # invitations, ...) — voir docs/modules/01-auth-tenants/05-modele-donnees.md#54.
    op.execute("ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE password_reset_tokens FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON password_reset_tokens "
        "USING ("
        "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid "
        "OR current_setting('app.is_super_admin', true) = 'true' "
        "OR current_setting('app.auth_lookup', true) = 'true'"
        ")"
    )
    # Le rôle applicatif restreint (backend/db/init/01-app-role.sql) reçoit
    # automatiquement SELECT/INSERT/UPDATE/DELETE via l'ALTER DEFAULT
    # PRIVILEGES posé par la migration 0001 — aucun GRANT explicite requis ici.


def downgrade() -> None:
    op.drop_table("password_reset_tokens")
