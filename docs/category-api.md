# Category API — frontend integration

Base URL: `/api/v1/category/`. Keep trailing slashes.
List/detail are public. Create/update/delete require a superuser or a user in the `admin` group. Send `Authorization: Bearer <access_token>` for protected requests.

## Endpoints

| Action | Method | URL | Success |
| --- | --- | --- | --- |
| List | GET | `/api/v1/category/` | 200, paginated object |
| Detail | GET | `/api/v1/category/{slug}/` | 200, category object |
| Create | POST | `/api/v1/category/` | 201, category object |
| Replace | PUT | `/api/v1/category/{slug}/` | 200, category object |
| Partial update | PATCH | `/api/v1/category/{slug}/` | 200, category object |
| Delete | DELETE | `/api/v1/category/{slug}/` | 204, empty body |

Use the category **slug**, not UUID, in detail URLs. Deletion is soft deletion; deleted categories disappear from both public and admin endpoints.

## List filters, search, ordering, pagination

| Parameter | Behavior | Default |
| --- | --- | --- |
| `search` | Case-insensitive partial search across title, slug, description | No search |
| `title` | Case-insensitive exact title match | No filter |
| `slug` | Case-insensitive exact slug match | No filter |
| `ordering` | `title`, `-title`, `created_at`, `-created_at`; comma-separated combinations allowed | `-created_at,-id` |
| `page` | Page number, starting at 1 | 1 |
| `page_size` | Items per page, maximum 100 | 20 |

Filters combine with search using AND. Multiple search terms must each match at least one searched field. Invalid/nonpositive page sizes fall back to 20; values above 100 are capped. Invalid or out-of-range pages return 404. An unsupported ordering field falls back to default ordering.

Example: `GET /api/v1/category/?search=python&ordering=title&page=1&page_size=10`

Example list response (illustrative single result):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "7b20815e-591d-4c08-914e-735321f44823",
      "title": "python",
      "slug": "python",
      "description": "Learn Python from scratch",
      "thumbnail": {
        "id": "53570712-c26b-432f-b173-e632176fd5af",
        "url": "https://example.com/python.png",
        "name": "python.png"
      },
      "created_at": "2026-09-29T12:00:00Z",
      "updated_at": "2026-09-29T12:00:00Z",
      "deleted_at": null
    }
  ]
}
```

`count` is the total matching records, before pagination. `next` and `previous` are absolute URLs or null. Detail, create, PUT, and PATCH return the category object inside `results` above directly, without a wrapper. Dates may be null for older records.

## Create and update payloads

POST, PUT, and PATCH accept **multipart/form-data**, not JSON. Let the browser set Content-Type and its boundary.

| Field | Type | POST / PUT | PATCH |
| --- | --- | --- | --- |
| `title` | string, max 255 | Required | Optional |
| `description` | nonempty string | Required | Optional |
| `slug` | unique slug string, max 50 | Optional | Optional |
| `thumbnail` | File | Required | Optional; omission preserves existing file |

Title is trimmed, lowercased, and unique without regard to case. On create, omitted slug is generated from title. Updating title alone preserves the existing slug. If slug changes, use the returned slug for subsequent detail requests. Read-only fields: `id`, timestamps, and the returned thumbnail object. Send a real file under `thumbnail`, not that object, an ID, or a URL. There is no thumbnail-clear operation.

The shared file service currently permits image/video MIME types and PDFs up to 5 MB. For category thumbnails, the frontend should select an image.

Frontend payload objects before conversion to FormData:

```js
const createPayload = {
  title: "Python",
  description: "Learn Python from scratch",
  slug: "python", // optional
  thumbnail: selectedFile, // browser File
};

const patchPayload = {
  description: "Updated Python course collection",
  // thumbnail: replacementFile, // optional
};
```

Example fetch helper:

```js
async function saveCategory({ token, slug, payload, method = "POST" }) {
  const body = new FormData();
  for (const [key, value] of Object.entries(payload)) {
    if (value !== undefined && value !== null) body.append(key, value);
  }
  const url = method === "POST"
    ? "/api/v1/category/"
    : `/api/v1/category/${encodeURIComponent(slug)}/`;
  const response = await fetch(url, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  const data = await response.json();
  if (!response.ok) throw data;
  return data;
}
```

Use `method: "PATCH"` for normal edit forms; PUT requires all required fields and a thumbnail again.

## Delete

```js
const response = await fetch(`/api/v1/category/${encodeURIComponent(slug)}/`, {
  method: "DELETE",
  headers: { Authorization: `Bearer ${token}` },
});
if (response.status !== 204) throw await response.json();
// Success has no JSON body. Refresh the list, stepping back a page if necessary.
```

## Error responses

Missing thumbnail, 400:

```json
{"detail": "Thumbnail is required."}
```

Field validation, 400 (example):

```json
{"title": ["This field is required."]}
```

Upload validation/failure, 400: `{"detail": "<reason>"}`.
Authentication missing/invalid: 401. Authenticated non-admin write: 403. Unknown/deleted slug or invalid page: 404. JSON write request: 415. These use `{"detail": "<message>"}`. Handle field-keyed errors and `detail` errors in the form.
