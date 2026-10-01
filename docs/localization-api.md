# Localization API — frontend integration

Base URL: `/api/v1/localization/`. Keep trailing slashes. All endpoints require authentication; send `Authorization: Bearer <access_token>`. For POST, PUT, and PATCH, send `Content-Type: application/json`.

Superusers and users in the `admin` group can create, update, delete, restore, and read deleted records. Other authenticated users can only read active records.

## Endpoints

| Action | Method | URL | Success response |
| --- | --- | --- | --- |
| List | GET | `/api/v1/localization/` | 200, paginated object |
| Detail | GET | `/api/v1/localization/{id}/` | 200, localization object |
| Create | POST | `/api/v1/localization/` | 201, localization object |
| Replace | PUT | `/api/v1/localization/{id}/` | 200, localization object |
| Partial update | PATCH | `/api/v1/localization/{id}/` | 200, localization object |
| Delete active record | DELETE | `/api/v1/localization/{id}/` | 204, empty body |
| Restore deleted record | DELETE | `/api/v1/localization/{id}/` | 200, message object |

Use the returned UUID `id` in detail URLs. DELETE toggles the existing deletion state: a second DELETE restores the record. Do not automatically retry DELETE because it can undo the first request. Use detail URLs without list query parameters for mutations.

## Payload objects

POST and PUT require both fields. PATCH accepts either or both.

| Field | Type | Validation |
| --- | --- | --- |
| `language_name` | string | Required for POST/PUT; nonempty, maximum 100 characters |
| `country` | string | Required for POST/PUT; nonempty, maximum 100 characters |

Whitespace is trimmed. Null and blank values are invalid. Duplicate language/country combinations are currently allowed.

POST `/api/v1/localization/` and PUT `/api/v1/localization/{id}/`:

```json
{
  "language_name": "English",
  "country": "India"
}
```

PATCH `/api/v1/localization/{id}/`:

```json
{
  "country": "United Kingdom"
}
```

Exclude backend-generated fields from all write payloads: `id`, `created_at`, `updated_at`, and `deleted_at`. These fields are read-only and ignored if supplied. Deletion status is managed through DELETE.

## Localization response object

Detail, create, PUT, and PATCH return this object directly, without a wrapper (illustrative values):

```json
{
  "id": "7b20815e-591d-4c08-914e-735321f44823",
  "language_name": "English",
  "country": "India",
  "created_at": "2026-10-01T12:00:00Z",
  "updated_at": "2026-10-01T12:00:00Z",
  "deleted_at": null
}
```

Timestamps are ISO 8601 strings; dates may be null for older records. `deleted_at: null` means active; a timestamp means deleted. No `is_deleted` field is included in the response.

## Filters, search, ordering, and pagination

| Parameter | Behavior | Default |
| --- | --- | --- |
| `language_name` | Case-insensitive exact match | No filter |
| `country` | Case-insensitive exact match | No filter |
| `is_deleted` | `true` for deleted, `false` for active | All records visible to the caller |
| `search` | Case-insensitive partial search across language name and country | No search |
| `ordering` | `language_name`, `country`, `created_at`, `updated_at`; prefix `-` for descending; comma-separated combinations allowed | `-created_at,-id` |
| `page` | Page number, starting at 1 | 1 |
| `page_size` | Items per page, maximum 100 | 20 |

Filters and search combine using AND. Multiple search terms must each match at least one searched field. Deleted-record filtering never expands permissions: non-admin users receive zero results for `is_deleted=true`. Invalid/nonpositive page sizes fall back to 20; values above 100 are capped. Invalid or out-of-range pages return 404. Unsupported ordering fields are ignored; if none are supported, default ordering applies.

Example:

```http
GET /api/v1/localization/?country=India&search=eng&is_deleted=false&ordering=language_name&page=1&page_size=10
Authorization: Bearer <access_token>
```

Paginated response (illustrative single match):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "7b20815e-591d-4c08-914e-735321f44823",
      "language_name": "English",
      "country": "India",
      "created_at": "2026-10-01T12:00:00Z",
      "updated_at": "2026-10-01T12:00:00Z",
      "deleted_at": null
    }
  ]
}
```

`count` is the total number of matching records before pagination. `next` and `previous` are absolute page URLs or null. An empty first page returns `count: 0` and `results: []`.

## Delete and restore responses

DELETE of an active record returns **204 with no body**. Do not call `response.json()` for this response.

DELETE of a deleted record restores it and returns **200**:

```json
{
  "message": "Activated successfully"
}
```

Refresh the list after either action and step back a page if the current page becomes empty.

## Frontend request example

```js
async function localizationRequest({ token, id, method = "GET", payload, query }) {
  const base = "/api/v1/localization/";
  const path = id ? `${base}${encodeURIComponent(id)}/` : base;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const response = await fetch(`${path}${params.size ? `?${params}` : ""}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(payload ? { "Content-Type": "application/json" } : {}),
    },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw { status: response.status, data };
  return data;
}

const created = await localizationRequest({
  token,
  method: "POST",
  payload: { language_name: "English", country: "India" },
});

const page = await localizationRequest({
  token,
  query: { search: "eng", is_deleted: false, page: 1, page_size: 20 },
});
```

## Errors

Field validation errors return 400, for example:

```json
{
  "language_name": ["This field is required."],
  "country": ["This field may not be blank."]
}
```

Missing/invalid authentication returns 401. Authenticated non-admin writes return 403. Unknown IDs, records outside the caller's visibility, and invalid pages return 404. These errors generally use `{"detail": "<message>"}`; token errors can include additional fields. Handle both field-keyed errors and `detail` errors.
