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
