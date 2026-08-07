-- Rôle applicatif à privilèges limités, distinct du rôle superutilisateur
-- créé par l'image Postgres (POSTGRES_USER). Indispensable : PostgreSQL
-- exempte TOUJOURS un superutilisateur de la Row-Level Security, quels que
-- soient ENABLE/FORCE ROW LEVEL SECURITY sur les tables (voir
-- docs/modules/01-auth-tenants/05-modele-donnees.md#54-row-level-security-référence-croisée).
-- L'application se connecte avec ce rôle ; les migrations Alembic continuent
-- d'utiliser le rôle superutilisateur (propriétaire des tables, nécessaire
-- pour le DDL).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'restauhub_app') THEN
        CREATE ROLE restauhub_app WITH LOGIN PASSWORD 'restauhub_app'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE restauhub TO restauhub_app;
GRANT USAGE ON SCHEMA public TO restauhub_app;

-- S'applique aux tables déjà existantes au moment où ce script tourne (aucune
-- ici, il s'exécute avant les migrations) ET, via ALTER DEFAULT PRIVILEGES,
-- à toutes celles créées ensuite par le rôle superutilisateur (les
-- migrations Alembic) — donc sans intervention manuelle à chaque migration.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO restauhub_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO restauhub_app;
