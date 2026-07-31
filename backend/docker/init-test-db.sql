-- POSTGRES_DB only creates the primary db; the test db (used by
-- `pytest -m integration` against postgresql.test_dsn) is created here.
CREATE DATABASE fastamu_test_db;