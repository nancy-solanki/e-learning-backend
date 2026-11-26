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

## S3 media and lecture video delivery

Course/category thumbnails and profile images are uploaded by the API to S3
under `course/`, `category/`, and `avatars/`. Django media storage also uses
the same bucket. Configure `AWS_STORAGE_BUCKET_NAME`, `AWS_REGION`, and
`CLOUDFRONT_DOMAIN`; CloudFront should serve those media prefixes from the
private bucket using Origin Access Control.

Lecture videos upload directly from the browser to a private S3 bucket using
multipart uploads. Use `/api/v1/lecture/uploads/multipart/` as follows:

1. `POST` `{ "filename", "content_type", "size" }` to create an upload. The
   response includes `key`, `upload_id`, and `part_size` (16 MiB by default).
2. Split the file into parts of `part_size` (the last part may be smaller). For
   each part, `PUT` `{ "key", "upload_id", "part_number" }` to the API for a
   short-lived S3 URL. PUT the bytes to that URL and retain the returned ETag.
3. `PATCH` `{ "key", "upload_id", "parts": [{ "ETag", "PartNumber" }] }` to
   complete the multipart upload. `DELETE` `{ "key", "upload_id" }` aborts an
   abandoned upload.
4. Create or update a lecture with the returned `key` as `source`. Lecture
   responses include `playback_url`, the expected HLS playlist on CloudFront.

For PDFs, documents, ZIP archives, and other lecture resources, add
`"kind": "resource"` to the initiation request. Resource uploads accept any
content type and use `MAX_LECTURE_RESOURCE_SIZE` (1 GiB by default). Store the
returned key in the lecture's `resources` JSON data along with the filename,
content type, and size. Request
`GET /api/v1/lecture/resources/download-url/?key=<resource-key>` with an
authenticated account to get a short-lived download URL.

Set `AWS_STORAGE_BUCKET_NAME`, `AWS_REGION`, and `CLOUDFRONT_DOMAIN` in
production. Give the API role S3 `PutObject`, `GetObject`, multipart create,
list-parts, complete, and abort permissions scoped to this bucket. Keep the bucket private and
grant CloudFront read access through Origin Access Control (OAC). The bucket
CORS policy must allow the frontend origin and `PUT`, and expose the `ETag`
response header. Add an S3 lifecycle rule to abort incomplete multipart uploads.

Connect S3 object-created events for `source/` to AWS Elemental MediaConvert (or
an equivalent transcoder). Configure HLS output at
`hls/<upload-token>/master.m3u8`, where `<upload-token>` is the third component
of the source key, and serve the `hls/` prefix through CloudFront. This keeps
video processing off the API and database containers. The playlist URL can
return 404 until transcoding finishes.

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
