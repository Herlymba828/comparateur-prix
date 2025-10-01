-- =====================================================================
-- Script d'initialisation PostgreSQL (paramétrable via psql -v)
-- Exemple d'exécution:
--   psql -U postgres -h localhost -p 5432 -f init_db.sql \
--        -v DB=compare_easy -v USER=postgres -v PASSWORD='change-me'
-- Si aucune variable n'est fournie, des valeurs par défaut sont utilisées.
-- =====================================================================

-- Définir des variables avec valeurs par défaut si non fournies par psql
\if :{?DB}
\else
\set DB soutenance2
\endif
\if :{?USER}
\else
\set USER postgres
\endif
\if :{?PASSWORD}
\else
\set PASSWORD BlackEurtz8282@
\endif

-- Fermer les connexions actives sur la base ciblée (si elle existe)
-- Fermer les connexions actives sur la base ciblée (si elle existe)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = :'DB' AND pid <> pg_backend_pid();

-- Supprimer la base si elle existe
DROP DATABASE IF EXISTS :"DB";

-- Créer le rôle applicatif s'il n'existe pas déjà (sans DO, via gexec)
SELECT 'CREATE ROLE '
       || quote_ident(:'USER')
       || ' LOGIN PASSWORD '
       || quote_literal(:'PASSWORD') AS cmd
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'USER')
\gexec

-- Créer la base en UTF-8 avec locales neutres (template0 pour un contrôle fin)
CREATE DATABASE :"DB"
  WITH OWNER = :"USER"
       ENCODING 'UTF8'
       LC_COLLATE 'C'
       LC_CTYPE   'C'
       TEMPLATE template0
       TABLESPACE pg_default
       CONNECTION LIMIT -1;

-- Se connecter à la base nouvellement créée
\connect :"DB"

-- Extensions utiles (idempotentes)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Assigner le schéma public au rôle applicatif et accorder les droits
ALTER SCHEMA public OWNER TO :"USER";
GRANT ALL ON SCHEMA public TO :"USER";
GRANT USAGE, CREATE ON SCHEMA public TO :"USER";

-- Privilèges par défaut pour les objets créés ultérieurement
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"USER";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :"USER";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO :"USER";

-- Optionnel: durcir les droits publics
-- REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Paramètres de session recommandés
SET TIME ZONE 'UTC';
SET CLIENT_ENCODING = 'UTF8';

-- Résumé
\echo 'Base initialisée: ' :DB ', utilisateur: ' :USER

