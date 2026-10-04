# Section search and filters

Available on `GET /api/v1/section/`,
`GET /api/v1/section/course/<slug>/`, and
`GET /api/v1/section/instructor/all/` (requires instructor/admin access).

| Parameter | Value |
| --- | --- |
| `search` | Case-insensitive search across section title, description, and course title |
| `course` | Course UUID |
| `course_slug` | Case-insensitive exact course slug |
| `instructor` | Instructor UUID |
| `status` | `published`, `draft`, or `rejected` |
| `ordering` | `order`, `title`, `created_at`, or `updated_at`; prefix with `-` for descending order; separate multiple fields with commas |

Filters combine with search and pagination. Default ordering is section order,
then newest creation date, then ID to keep ties stable.
Invalid UUIDs and status choices return HTTP 400.

Existing visibility rules still apply: the public list only returns published,
non-deleted sections with active instructors. The course-specific list includes
non-deleted sections of any status from the requested course, as before.
Management lists remain restricted to the instructor's sections unless the user
is an admin. Filters cannot expand these scopes.

Example: `/api/v1/section/?search=introduction&course_slug=python-basics&status=published&ordering=order`
