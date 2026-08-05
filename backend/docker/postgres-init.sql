-- POSTGRES_DB already created core_pulse_db; the ai app owns a second one on
-- the same instance, and it is the only database that needs pgvector.
CREATE DATABASE ai_pulse_db;

\connect ai_pulse_db
CREATE EXTENSION IF NOT EXISTS vector;
