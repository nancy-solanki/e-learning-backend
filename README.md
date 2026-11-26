# E-learning Backend

## Development setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12, then create the project environment and install the locked development dependencies:

```bash
uv python install 3.12
uv venv --python 3.12
uv sync --frozen --dev
```

The virtual environment is created at `.venv/` and is intentionally excluded from Git. `uv sync` installs the exact versions in `uv.lock`.

Copy `.env.example` to `.env` and configure the local database and external-service credentials as needed. Run Django commands and tools through `uv run` so they use the project environment:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
uv run pytest
uv run pre-commit run --all-files
```

## CI

GitHub Actions uses Python 3.12, creates the same `.venv`, and installs dependencies with `uv sync --frozen --dev`. Keep `uv.lock` committed and regenerate it after dependency changes with `uv lock`.

## In-app notifications

Notification records are available at `GET /api/v1/users/me/notifications/`.
Mark one as read with `POST /api/v1/users/me/notifications/<id>/read/`.
Authenticated clients can receive new notifications over
`ws(s)://<host>/ws/notifications/`; the websocket uses the `access_token`
cookie and sends messages shaped as `{"type":"notification","data":{...}}`.
Run the ASGI application (`config.asgi:application`) and configure Redis for
the Channels layer in deployed environments.

## Production course search

Production course catalog searches use OpenSearch. Configure `OPENSEARCH_URL`
and, when enabled on the domain, `OPENSEARCH_USERNAME` and
`OPENSEARCH_PASSWORD`. TLS certificate verification is on by default. Before
serving production traffic, run `python manage.py reindex_courses` with
production settings and database access. The command creates the configured
index and indexes existing courses; course and related category, tag, and
instructor changes are then synchronized after database commits. Development
and test settings continue to use the database search filter.

## Deploy with Docker Compose on EC2

The production image runs the Django ASGI application with Daphne, plus a Celery
worker and scheduler. Compose runs Redis locally; configure PostgreSQL (RDS)
and OpenSearch as private services and set their endpoints in `.env`.

On the EC2 instance, install Docker Engine and the Compose plugin, then:

```bash
git clone <repository-url>
cd e-learning-backend
cp .env.docker.example .env
# Edit .env with the real production secrets and service endpoints.
docker compose up -d --build
docker compose run --rm api python manage.py reindex_courses
docker compose exec api python manage.py createsuperuser
docker compose ps
```

The API container waits for PostgreSQL, applies migrations, and collects
static files before starting. Seed data is disabled by default in the container;
create the first administrator through the project's chosen secure provisioning
process. Nginx serves collected static files and proxies HTTP and WebSocket
traffic to the internal Daphne service. Put an HTTPS load balancer in front of
Nginx on port 80, configure its health check path as `/healthz`, and restrict
the EC2 security group so that only the load balancer can reach it. The API
container is not published directly. Do not
commit `.env`. For deployments that use managed Redis instead of the Compose
service, set `REDIS_URL` and `CELERY_BROKER_URL` to the managed endpoints and
remove or disable the local Redis service.
