"""Module 1 — Authentification & gestion des tenants (schéma initial)

Crée les tables du module (tenants, users, roles, permissions,
user_roles, role_permissions, refresh_tokens, two_factor_secrets,
invitations, audit_logs) et active la Row-Level Security multi-tenant
(docs/modules/01-auth-tenants/05-modele-donnees.md#54-row-level-security-référence-croisée).

Les données de référence (12 rôles + permissions + matrice par défaut) sont
seedées séparément par `backend/scripts/seed_reference_data.py`, pas par
cette migration (séparation schéma / données, voir backend/README.md).

Revision ID: 0001
Revises:
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("default_locale", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="en_essai"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        sa.CheckConstraint(
            "status IN ('en_essai', 'actif', 'suspendu', 'résilié')", name="status_valide"
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("two_factor_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("phone_number", name="uq_users_phone_number"),
        sa.CheckConstraint(
            "email IS NOT NULL OR phone_number IS NOT NULL", name="identifiant_requis"
        ),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table(
        "roles",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("is_system_role", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role_id", pg.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True),
        sa.Column("succursale_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("role_id", pg.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "permission_id", pg.UUID(as_uuid=True), sa.ForeignKey("permissions.id"), nullable=False
        ),
        sa.UniqueConstraint(
            "tenant_id", "role_id", "permission_id", name="uq_role_permission_scope"
        ),
    )
    op.create_index("ix_role_permissions_tenant_id", "role_permissions", ["tenant_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("device_label", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "two_factor_secrets",
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("encrypted_secret", sa.String(255), nullable=False),
        sa.Column(
            "recovery_codes_hashed", pg.ARRAY(sa.String), nullable=False, server_default="{}"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_two_factor_secrets_tenant_id", "two_factor_secrets", ["tenant_id"])

    op.create_table(
        "invitations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("role_id", pg.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("invited_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
        sa.CheckConstraint(
            "email IS NOT NULL OR phone_number IS NOT NULL", name="identifiant_requis"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'expired', 'revoked')", name="status_valide"
        ),
    )
    op.create_index("ix_invitations_tenant_id", "invitations", ["tenant_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("metadata", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])

    _enable_row_level_security()


def _enable_row_level_security() -> None:
    """Défense en profondeur (section 3.3 de l'architecture) : même un bug
    applicatif oubliant un filtre `tenant_id` ne peut pas exposer les
    données d'un autre tenant.

    `NULLIF(current_setting('app.tenant_id', true), '')::uuid` évite une
    erreur de cast quand le GUC est vide (aucun tenant connu) — un cast
    direct de `''::uuid` échoue en PostgreSQL, ce qui ferait échouer TOUTE
    requête passant par une session non tenant-scopée.

    `app.auth_lookup` couvre les cas d'usage qui s'exécutent nécessairement
    avant que le tenant ne soit connu (inscription, connexion, rafraîchissement
    de token, défi 2FA, consultation/acceptation d'invitation) : ce sont des
    points d'entrée fixes et audités du module `auth_tenants`, jamais un
    contournement exposé au reste de l'application.
    """

    tenant_match = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    is_super_admin = "current_setting('app.is_super_admin', true) = 'true'"
    auth_lookup = "current_setting('app.auth_lookup', true) = 'true'"

    for table in ("users", "refresh_tokens", "two_factor_secrets", "invitations", "audit_logs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({tenant_match} OR {is_super_admin} OR {auth_lookup})"
        )

    # role_permissions : une ligne à tenant_id NULL est un défaut global,
    # visible de tous (section 5.2 de la conception des données).
    op.execute("ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON role_permissions "
        f"USING (tenant_id IS NULL OR {tenant_match} OR {is_super_admin} OR {auth_lookup})"
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("invitations")
    op.drop_table("two_factor_secrets")
    op.drop_table("refresh_tokens")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("tenants")
