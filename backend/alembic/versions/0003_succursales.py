"""Module 2 — Restaurants & succursales

Crée la table `succursales` et corrige un défaut de conception du Module 1
découvert en concevant ce module : la clé primaire composite de
`user_roles` (user_id, role_id) empêche un même utilisateur d'avoir le même
rôle à plusieurs succursales (BR2-10). Voir
docs/modules/02-restaurants-succursales/05-modele-donnees.md#52.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "succursales",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address_line", sa.String(200), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("default_locale", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("opening_hours", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'fermeture_temporaire')", name="status_valide"
        ),
    )
    op.create_index("ix_succursales_tenant_id", "succursales", ["tenant_id"])

    op.execute("ALTER TABLE succursales ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE succursales FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON succursales "
        "USING ("
        "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid "
        "OR current_setting('app.is_super_admin', true) = 'true'"
        ")"
    )
    # Pas de contexte `app.auth_lookup` ici : aucun cas d'usage de ce module ne
    # s'exécute avant que le tenant ne soit connu (toutes les routes sont
    # authentifiées) — voir 03-architecture.md#34.

    _fix_user_roles_primary_key()


def _fix_user_roles_primary_key() -> None:
    """user_roles.succursale_id existait déjà (réservée par le Module 1) mais
    la PK composite (user_id, role_id) interdit à BR2-10 de s'appliquer :
    remplacée par une clé de substitution + deux index uniques partiels."""

    op.add_column("user_roles", sa.Column("id", pg.UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE user_roles SET id = gen_random_uuid() WHERE id IS NULL")
    op.alter_column("user_roles", "id", nullable=False)

    op.drop_constraint("pk_user_roles", "user_roles", type_="primary")
    op.create_primary_key("pk_user_roles", "user_roles", ["id"])

    op.execute(
        "CREATE UNIQUE INDEX uq_user_roles_tenant_wide "
        "ON user_roles (user_id, role_id) WHERE succursale_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_user_roles_par_succursale "
        "ON user_roles (user_id, role_id, succursale_id) WHERE succursale_id IS NOT NULL"
    )

    op.create_foreign_key(
        "fk_user_roles_succursale_id_succursales",
        "user_roles",
        "succursales",
        ["succursale_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_roles_succursale_id_succursales", "user_roles", type_="foreignkey")
    op.execute("DROP INDEX IF EXISTS uq_user_roles_par_succursale")
    op.execute("DROP INDEX IF EXISTS uq_user_roles_tenant_wide")
    op.drop_constraint("pk_user_roles", "user_roles", type_="primary")
    op.create_primary_key("pk_user_roles", "user_roles", ["user_id", "role_id"])
    op.drop_column("user_roles", "id")

    op.drop_table("succursales")
