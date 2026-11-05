# Instructor panel: content approval flow

Use the authenticated API client and the instructor-management APIs below for
the Instructor panel. Instructors can manage their own courses, sections, and
lectures. Admins moderate these resources through the same management APIs.
Instructors cannot set content status through CRUD; they submit saved
resources for review using the explicit submit actions.

All routes include the `/api/v1` prefix and trailing slashes.

## Browse the content hierarchy

Render instructor content as courses, their sections, and each section's
lectures. Use the management endpoints so drafts and items waiting for review
remain visible to the instructor:

| Content | Instructor list | Create |
| --- | --- | --- |
| Course | `GET /course/instructor/all/` | `POST /course/instructor/all/` |
| Section | `GET /section/instructor/all/?course={course_id}` | `POST /section/instructor/all/` |
| Lecture | `GET /lecture/instructor/all/?course={course_id}&section={section_id}` | `POST /lecture/instructor/all/` |

These lists use the standard paginated envelope (`count`, `next`, `previous`,
`results`) with 20 records per page. Follow `next` to load more. Use detail
routes to retrieve, edit, or soft-delete a resource:

| Content | Detail/update/delete route |
| --- | --- |
| Course | `/course/instructor/all/{id}/` |
| Section | `/section/instructor/all/{id}/` |
| Lecture | `/lecture/instructor/all/{id}/` |

## Status and actions in the panel

Render a status badge from the API value. Suggested labels and actions:

| API status | Panel label and behavior |
| --- | --- |
| `draft` | Draft; show **Submit for approval** when the resource is ready. |
| `in-review` | In review; show that it is awaiting admin approval and disable resubmission. |
| `rejected` | Rejected; show `reject_reason` when present, allow editing, then show **Resubmit for approval**. |
| `published` | Published; public visibility also depends on parent statuses. |
| `approved` | Approved (legacy course status); it is not publicly visible until its status is `published`. |

Submitting should disable the action while the request is pending. On success,
update the resource status from the response and show its confirmation message.
Do not optimistically mark content as published. If submitting a section fails
because it has no non-deleted lectures, show the API validation error and guide
the instructor to add a lecture.

Use these explicit actions to request admin approval:

| Content | Submit action |
| --- | --- |
| Course | `POST /course/instructor/all/{id}/submit/` |
| Section | `POST /section/instructor/all/{id}/submit/` |
| Lecture | `POST /lecture/instructor/all/{id}/submit/` |

Each action returns `200` with the updated workflow state:

```json
{
  "message": "Lecture submitted for review. It will be published once an admin approves it.",
  "status": "in-review"
}
```

The message label is `Course`, `Section`, or `Lecture` to match the resource.
Submitting an already-published or already-in-review item returns a validation
error. A rejected item can be edited and submitted again.

Each resource is reviewed independently. A course is visible to students only
when the course is published. A section requires both itself and its course
to be published. A lecture requires the lecture, its section, and its course
to be published. Consider showing a "Waiting for parent approval" hint for a
published child whose parent is not yet published. A section must have at
least one non-deleted lecture both when submitted and when approved by an
admin.

Instructors may edit content without setting status. Do not send `status` in
create or update payloads; the server rejects instructor status changes with
`400`. Admins approve or reject by updating only `status` through the same
management route, for example `PATCH /lecture/instructor/all/{id}/` with
`{"status":"published"}` or `{"status":"rejected"}`.

On `400`, show field validation errors returned by the API. On `401`, use the
existing session-expiry flow; on `403`, show access denied. A `404` for a
detail/action means the resource does not exist in the instructor's scope.
Filtering does not expand the authenticated instructor's ownership scope.

## Create payload

For a document lecture, send JSON:

```json
{
  "title": "Introduction",
  "description": "An introduction to the course",
  "lecture_type": "document",
  "is_preview": false,
  "document_content": "Lesson content",
  "resources": [],
  "order": 1,
  "course": "8cf1ba1b-83c9-4bab-9e26-5938ba912a15",
  "section": "441b1654-a2d9-4ec1-9e1d-8a9702aa7116"
}
```

Lecture status is admin-controlled. Instructor-created lectures start as
`draft`; omit `status` from create and update payloads, then use the submit
action when they are ready for review. An instructor request that includes
`status` returns `400` with a field validation error.

For video or thumbnail uploads, send `multipart/form-data` using the same
fields; `source` and `thumbnail` accept uploaded files. The server assigns the
authenticated instructor and generates the slug and duration. Do not send
`instructor`, `slug`, `duration`, `reject_reason`, `id`, timestamps, or
`deleted_at`.

## Response objects

Successful create, retrieve, and update responses contain the lecture object.
File values are URLs or `null`; relation values are UUIDs, and `instructor` is
the username:

```json
{
  "id": "fd2738f8-a9bb-4a87-a5f7-02a6c45f9d1b",
  "title": "Introduction",
  "slug": "introduction-1234",
  "description": "An introduction to the course",
  "status": "draft",
  "lecture_type": "document",
  "source": null,
  "is_preview": false,
  "document_content": "Lesson content",
  "reject_reason": null,
  "resources": [],
  "order": 1,
  "thumbnail": null,
  "instructor": "emma",
  "course": "8cf1ba1b-83c9-4bab-9e26-5938ba912a15",
  "section": "441b1654-a2d9-4ec1-9e1d-8a9702aa7116",
  "duration": null,
  "created_at": "2026-10-10T09:00:00Z",
  "updated_at": "2026-10-10T09:00:00Z",
  "deleted_at": null
}
```

A successful delete returns `200` with either
`{"message":"Lecture deleted successfully"}` or
`{"message":"Lecture activated successfully"}`. This endpoint toggles
soft-deletion, so issue DELETE again only when a restore is intended.
Unauthenticated requests return `401`; non-instructor/non-admin users receive
`403`, and a lecture outside an instructor's scope is not found (`404`).
Invalid lecture data or mismatched course/section ownership returns `400` with
field-specific validation errors. Admins can update status only.
