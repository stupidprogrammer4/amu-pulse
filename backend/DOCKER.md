# Docker

`compose.yml` lives at `backend/` and is shared by every backend app, so run
every command below from `backend/`.

The stack runs two applications and the services behind them.

From `api/`:

- `api`: Uvicorn on port `8000`
- `worker`: Taskiq workers
- `scheduler`: Taskiq scheduler
- `migrate`: an on-demand Alembic tool
- `seed`: an on-demand initial-data tool

From `ai/`:

- `ai-api`: Uvicorn on port `8100`
- `ai-worker`: Taskiq workers for the ai app's own queue
- `ai-consumer`: Taskiq worker on the RabbitMQ event bus
- `ai-migrate`: an on-demand Alembic tool

Backing services: `postgres`, `postgres-ai`, `redis`, `rabbitmq`,
`elasticsearch`, and `ollama`.

Each app has its own PostgreSQL instance: `postgres` holds `core_pulse_db`
for `api`, and `postgres-ai` holds `ai_pulse_db` for `ai`. The ai one runs the
`pgvector` image because that app stores embeddings, and ai's first migration
enables the `vector` extension. Neither app can reach the other's database.

## The event bus

Redis carries each app's own background work; RabbitMQ carries only what
crosses between them. The contract lives in `events/`, which both apps install
as a package, and both publish to one topic exchange named `amu.events`.

Each app has one inbox queue bound to its own routing key — `api.events` and
`ai.events` — so a worker on one never consumes the other's messages. A
publisher declares both queues and picks the destination per message; a
consumer declares only its own.

The management UI is at <http://localhost:15672> (`guest` / `guest`).

## Configuration

A YAML file mounted at `/app/config.yml` is the only configuration source.
Neither application reads environment variables or a `.env` file, so nothing
in Compose can override a setting.

Because of that each app has two config files: `config.yml` for running on the
host and `config.docker.yml` for running in a container. They differ only in
the addresses of PostgreSQL, Redis, Elasticsearch, and Ollama, since `0.0.0.0`
points at the wrong process inside a container. Compose mounts the Docker one.
Any setting you change in one belongs in the other too.

All four hold secrets, so all four are git-ignored and never committed. The
`config.yml.sample` in each app is the only tracked configuration file.

The included PostgreSQL container uses trust authentication for local Docker
development. Do not use this Compose configuration in production. A deployment
must use authentication, private secrets, Elasticsearch security and TLS, and
must not publish backing-service ports.

For a new checkout, create the ignored configurations from the samples, then
point each Docker one at the service names (`postgres`, `redis`,
`elasticsearch`, `ollama`) instead of `0.0.0.0`:

```bash
cp api/config.yml.sample api/config.yml
cp api/config.yml.sample api/config.docker.yml
cp ai/config.yml.sample ai/config.yml
cp ai/config.yml.sample ai/config.docker.yml
```

## Models

Ollama starts with an empty model store. Pull what `ai/config.yml` names
before the ai app can answer anything:

```bash
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

The models live in the `ollama-data` volume, so this is a one-time cost.

## Migrations

Both apps have their own Alembic chain — `migrate` for `api` and
`ai-migrate` for `ai`. Neither shares revisions with the other.

Migrations are explicit and never run as a side effect of starting the API. The
recommended deployment flow is:

```bash
docker compose up -d postgres postgres-ai redis rabbitmq elasticsearch
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic heads
docker compose run --rm migrate
docker compose run --rm seed
docker compose run --rm ai-migrate
docker compose up --build -d
```

Run `seed` after the first migration of a new database and before starting the
worker and scheduler. It creates the assets (including USD), sources, and
bubbles required by scheduled tasks. The seeder is idempotent, so rerunning it
only creates missing records.

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
cd api && .venv/bin/alembic revision --autogenerate -m "describe the change"
```

## Start

After applying migrations and seeding a new database, start the stack:

```bash
docker compose up --build -d
docker compose ps
```

The main API is at <http://localhost:8000> and the ai API at
<http://localhost:8100>, each with a `/system/health` endpoint. Follow
application logs with:

```bash
docker compose logs -f api worker scheduler ai-api ai-worker ai-consumer
```

Stop the stack while preserving data with `docker compose down`. To also
delete all local PostgreSQL, Redis, Elasticsearch, media, Ollama model, and ai
artifact data, run:

```bash
docker compose down --volumes
```
