# FE integration prompt: admin enrollment management

Implement the admin-only Enrollments page and enrollment-details modal using the supplied screenshots as the visual reference. Use the existing frontend components, API client, authentication, and styling conventions. Replace sample rows and counts with the APIs below. Retain the lavender layout, summary cards, student/course table, search, course dropdown, export button, and accessible details modal.

## Authorization

- Only show the navigation item and page to users whose authenticated profile `role` array includes `admin`. The profile is available from `GET /api/v1/users/me/`. Use existing authentication state rather than creating another login flow.
- The existing API scopes its queryset by role: admins (including superusers) see all active enrollments, instructors see enrollments for their own courses, and learners see their own enrollments. Only admins receive the enriched reporting response described below, including learner email. The summary, course-options, and export actions require admin privileges and return 403 to other roles. Handle 401 through the existing session-expiry flow and 403 with an access-denied screen. Do not display stale enrollment data after either response or after logout.
- Use the existing credentialed API client. These are GET endpoints; do not introduce enrollment creation, editing, or deletion controls.

## Endpoints

All paths include trailing slashes.

| Purpose | GET endpoint | Response |
| --- | --- | --- |
| Table | `/api/v1/enroll/management/` | Paginated enrollment rows |
| Details | `/api/v1/enroll/management/{id}/` | One enrollment row |
| Summary cards | `/api/v1/enroll/management/summary/` | Summary object |
| Course dropdown | `/api/v1/enroll/management/courses/` | Paginated `{id, title, slug}` options |
| CSV download | `/api/v1/enroll/management/export/` | CSV attachment |

Use the existing `/api/v1/enroll/management/` viewset for this page. It also continues to serve learner/instructor views with their existing response format and access scope. There is no separate `/enroll/admin/` route.

The table and course-options response envelope is:

```json
{"count": 42, "next": "...", "previous": null, "results": []}
```

Pages contain up to 20 records. Send `page=1`, `page=2`, etc.; the API does not support a configurable page size. Load subsequent course-options pages so the dropdown includes all available options. Options include courses with at least one non-deleted enrollment, including unpublished courses.

## Search and filters

The table, summary, and export accept the same filters:

- `search`: learner username, first/last name, email, course title, or enrollment UUID. Search is case-insensitive; multiple words must all match.
- `course`: selected course UUID; omit for “All courses”.
- `course_slug`: optional case-insensitive exact slug.
- `user`: optional learner UUID.
- `created_at_after`, `created_at_before`: optional inclusive `YYYY-MM-DD` dates, interpreted in the backend's configured timezone.
- `ordering`: `created_at`, `-created_at`, `user__first_name`, `-user__first_name`, `user__last_name`, or `-user__last_name`. Default is newest enrollment first.

Debounce search by about 300 ms, cancel or ignore stale responses, reset the table to page 1 when filters change, and refresh summary using the same filters. Summary counts cover all matching records, not just the current page. Invalid UUID/date filter values return 400; show the API validation error.

Course options are independent of the table filters. Only send pagination to `/courses/`.

## Enrollment row and details

Example shape (UUID placeholders below must be replaced with actual API values):

```json
{
  "id": "<enrollment UUID>",
  "user": {
    "id": "<user UUID>",
    "username": "emma",
    "first_name": "Emma",
    "last_name": "Wilson",
    "full_name": "Emma Wilson",
    "avatar": "",
    "email": "emma@example.com"
  },
  "course": {"id": "<course UUID>", "title": "Course title", "slug": "course-slug"},
  "created_at": "2026-10-10T09:00:00Z",
  "total_lessons": 32,
  "completed_lessons": null,
  "progress": null,
  "status": "unknown",
  "access": null,
  "progress_tracking_available": false
}
```

- Use `user.full_name`, falling back to username, and show email below it. Use avatar when present, otherwise initials.
- Show `course.title` and the enrollment ID. IDs are UUIDs, not `ENR-1006` identifiers. You may truncate the UUID in the table, but provide the full value in the modal and copy action; use the full UUID for requests and keys.
- Format `created_at` in the user's locale. It can be null for legacy data; display “Unavailable” in that case.
- `total_lessons` counts non-deleted published lectures in non-deleted published sections. It can be zero.
- Fetch details when View is selected; handle loading, error, and 404 states. Use the same row fields in the modal. Support Escape, focus trapping, focus restoration, and both Close controls.

## Progress limitation — required UI behavior

The backend currently has no lesson-completion records. The admin response uses null for unknown progress; the legacy learner/instructor response still contains a placeholder zero for compatibility. Do not interpret that placeholder as tracked progress, infer progress from enrollment dates, or display the screenshot's sample completion values.

Current summary shape:

```json
{
  "total_enrollments": 42,
  "in_progress": null,
  "completed": null,
  "not_started": null,
  "unknown": 42,
  "progress_tracking_available": false
}
```

Display the actual total count. Display “—” on the other three cards with “Progress tracking unavailable”. In the table and modal show “Progress unavailable” and, optionally, “32 lessons” using `total_lessons`. Do not render a 0% progress bar or classify unknown progress as “Not started”. Show an “Unknown” status badge. Disable the status dropdown with an explanatory hint; no status query parameter is supported yet.

No access-duration policy is stored either: when `access` is null, show “Not specified” instead of the screenshot's “Lifetime access”. Remove “Sample data / Static preview” labels. Do not replace unavailable values with mock data.

## Export and states

Fetch `/export/` with the current search/course/date filters and ordering, using the authenticated client, then download the response as a Blob named `enrollments.csv`. Do not send page: export includes every matching record. Show an exporting state and disable duplicate export clicks; check the HTTP status before downloading so an error response is not saved as a CSV.

CSV columns are Enrollment ID, Student, Email, Course, Enrolled on, Total lessons, Completed lessons, Progress (%), Status, Access. Unknown completion/access values are empty cells; status is `unknown`.

Provide initial skeletons, retryable errors, an empty state when no enrollments match, and table pagination. Verify admin access, student/instructor denial, search by UUID and learner/course name, course filtering, modal opening/closing, export of all filtered pages, and truthful unavailable-progress rendering.
