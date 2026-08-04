# Docker

The stack runs the API, Taskiq processes, and all backing services:

- `api`: Uvicorn on port `8000`
- `worker`: Taskiq workers
- `scheduler`: Taskiq scheduler
- `postgres`, `redis`, and `elasticsearch`: backing services
- `migrate`: an on-demand Alembic tool
- `seed`: an on-demand initial-data tool

## Configuration

`config.yml` is the only application configuration file. Compose mounts it at
`/app/config.yml`; there is no `.env` or Docker-specific config file.

Compose overrides only the PostgreSQL, Redis, Taskiq, and Elasticsearch network
addresses because `0.0.0.0` from the host configuration points to the wrong
process inside a container. All application settings and secrets remain in
`config.yml`.

The included PostgreSQL container uses trust authentication for local Docker
development. Do not use this Compose configuration in production. A deployment
must use authentication, private secrets, Elasticsearch security and TLS, and
must not publish backing-service ports.

For a new checkout, create the ignored local configuration:

```bash
cp config.yml.sample config.yml
```

## Migrations

Migrations are explicit and never run as a side effect of starting the API. The
recommended deployment flow is:

```bash
docker compose up -d postgres redis elasticsearch
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic heads
docker compose run --rm migrate
docker compose run --rm seed
docker compose up --build -d
```

Run `seed` after the first migration of a new database and before starting the
worker and scheduler. It creates the roles, assets (including USD), sources,
and bubbles required by scheduled tasks. The seeder is idempotent, so rerunning
it only creates missing records.

The default `migrate` command is `alembic upgrade head`. Other useful commands
are:

```bash
docker compose run --rm migrate alembic history --verbose
docker compose run --rm migrate alembic downgrade -1
docker compose run --rm migrate alembic upgrade <revision>
```

Review downgrade functions and take a database backup before rolling back.
Create new migration files from the host so they remain in the repository:

```bash
.venv/bin/alembic revision --autogenerate -m "describe the change"
```

## Start

After applying migrations and seeding a new database, start the stack:

```bash
docker compose up --build -d
docker compose ps
```

The API is available at <http://localhost:8000>, with its health endpoint at
<http://localhost:8000/system/health>. Follow application logs with:

```bash
docker compose logs -f api worker scheduler
```

Stop the stack while preserving data with `docker compose down`. To also delete
all local PostgreSQL, Redis, Elasticsearch, and media data, run:

```bash
docker compose down --volumes
```
