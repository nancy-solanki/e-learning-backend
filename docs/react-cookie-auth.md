# React migration to HttpOnly cookie authentication

Authentication JWTs now live in backend-set HttpOnly cookies. Login and refresh no
longer return `access` or `refresh` in JSON. Remove token persistence, JWT decoding,
and Authorization interceptors from React. Do not copy JWTs into JavaScript cookies,
localStorage, or sessionStorage. Existing users must sign in again after migration.
The backend still accepts Bearer headers for existing non-browser clients.

## Backend deployment

For local HTTP development, use `config.settings.development` and:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOW_CREDENTIALS=True
AUTH_COOKIE_SECURE=False
AUTH_COOKIE_SAMESITE=Lax
```

Use `localhost` for both frontend and backend (do not mix it with `127.0.0.1`).
For production set `AUTH_COOKIE_SECURE=True`, use HTTPS, and replace both origin
lists with the exact frontend origins including scheme and port, without paths.
Cookies are host-only; no shared cookie domain is needed. Prefer frontend and API
on the same site, such as `app.example.com` and `api.example.com`, with `Lax`.
For genuinely cross-site deployments, set `AUTH_COOKIE_SAMESITE=None` with HTTPS
and Secure cookies. Browser third-party cookie restrictions may still block that
arrangement; use a same-site API/reverse proxy in that case.

Run `python manage.py migrate` to ensure the existing JWT blacklist tables exist.
No new model migration is introduced by this change.

| Cookie | HttpOnly | Path | Default lifetime |
| --- | --- | --- | --- |
| `access_token` | Yes | `/` | 15 minutes |
| `refresh_token` | Yes | `/api/v1/auth/` | 7 days |
| `csrftoken` | No | `/` | Django default |

JWT lifetimes can be configured with `JWT_ACCESS_TOKEN_MINUTES` and
`JWT_REFRESH_TOKEN_DAYS`. Refresh rotates the refresh cookie and blacklists the
previous token. Logout blacklists the refresh cookie and deletes both JWT cookies,
even when the access cookie has expired. A copied access token remains valid until
its expiry; logout does not revoke access JWTs individually.

## API contract

All paths below are relative to `/api/v1/`. All calls use `credentials: "include"`.
All POST/PUT/PATCH/DELETE calls should include `X-CSRFToken`.

| Method and path | Request | Successful response |
| --- | --- | --- |
| GET `auth/csrf/` | None | 200 `{ "csrfToken": "..." }`, sets CSRF cookie |
| POST `auth/sign-in/` | `{ "email": "...", "password": "..." }` | 200 message, sets JWT cookies |
| POST `auth/staff/sign-in/` | Same credentials | 200 message, existing role restrictions apply |
| POST `auth/google/`, `auth/apple/` | Existing provider credential payload | 200 message, sets JWT cookies |
| POST `auth/refresh/` | `{}` | 200 message, rotates JWT cookies |
| POST `auth/sign-out/` | `{}` | 204, no body, clears JWT cookies |
| GET `users/me/` | None | 200 existing user profile response |

Refresh and logout ignore tokens in the request body. Missing/invalid refresh
cookies return 401. Missing/invalid CSRF or untrusted origins return 403. Never
refresh automatically on 403: it may represent a permission or account-status error.
Google/Apple provider credentials are exchanged once and must not be persisted.

## Fetch client (React / Vite)

Create `src/api.js`. Only the CSRF token is kept in memory; it is not an authentication
credential. Fetch it from the API, so React does not need to read a cookie owned by
another hostname. This follows Django's
[AJAX CSRF header guidance](https://docs.djangoproject.com/en/6.0/howto/csrf/).

```js
const BASE = `${import.meta.env.VITE_API_URL.replace(/\/$/, "")}/api/v1/`;
// e.g. VITE_API_URL=http://localhost:8000
let csrfToken;
let csrfPromise;
let refreshPromise;

async function ensureCsrf() {
  if (csrfToken) return csrfToken;
  if (!csrfPromise) {
    csrfPromise = fetch(`${BASE}auth/csrf/`, { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not initialize CSRF");
        csrfToken = (await response.json()).csrfToken;
        return csrfToken;
      })
      .finally(() => { csrfPromise = undefined; });
  }
  return csrfPromise;
}

async function send(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers);
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRFToken", await ensureCsrf());
  }
  // Set Content-Type explicitly for JSON; leave it unset for FormData uploads.
  return fetch(`${BASE}${path}`, {
    ...options, method, headers, credentials: "include",
  });
}

export async function api(path, options = {}, retry = true) {
  let response = await send(path, options);
  // Refresh once for protected resources, never recursively for auth endpoints.
  if (response.status === 401 && retry && !path.startsWith("auth/")) {
    if (!refreshPromise) {
      refreshPromise = send("auth/refresh/", { method: "POST" })
        .finally(() => { refreshPromise = undefined; });
    }
    const refreshed = await refreshPromise;
    if (refreshed.ok) response = await send(path, options);
  }
  if (!response.ok) {
    const error = new Error(`Request failed (${response.status})`);
    error.status = response.status;
    error.body = await response.json().catch(() => null);
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

export async function signIn(email, password) {
  await api("auth/sign-in/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return api("users/me/");
}

export const signOut = () => api("auth/sign-out/", { method: "POST" });
```

The refresh promise coordinates concurrent requests within one tab. If your app
runs simultaneous requests across multiple tabs, coordinate refresh between tabs
(e.g. Web Locks) because each refresh token can be used only once. Retryable request
bodies must be reusable (JSON strings/FormData, not consumed streams).

## React state and startup

Keep the user profile in React Context/state. On startup call `api("users/me/")`:
this restores the session and attempts one refresh if the access cookie expired.
Show a loading state until it finishes. Treat 401 as signed out; surface network
and server errors separately. After `signIn`, put the returned profile into state.
After successful `signOut`, clear the profile and protected query caches. Do not
parse the 204 logout response as JSON. Authorization remains enforced by the API.

Remove localStorage-based route guards and replace them with this loading/user
state. Remove all storage reads/writes for authentication and any persisted auth
store middleware. As a one-time migration, remove only your known old auth keys
from localStorage/sessionStorage; do not clear unrelated preferences. No persistent
browser storage access is needed in the new authentication flow.

If using Axios instead, set `withCredentials: true` on every API request, obtain
`csrfToken` using the endpoint above, and explicitly send `X-CSRFToken` on mutations.
Do not assume Axios can read a CSRF cookie on a different API hostname.

## Browser verification

1. Login: verify both JWT cookies are HttpOnly in DevTools and JSON has no JWTs.
2. Reload: verify `/users/me/` restores the profile without localStorage.
3. Expire/remove only the access cookie: verify refresh succeeds and replaces cookies.
4. Logout: verify both JWT cookies disappear and `/users/me/` returns 401.
5. Omit the CSRF header on a mutation: verify 403. If valid requests get 403, check
   exact trusted origins, credentials, and CSRF initialization.
6. Verify staff and social logins through the same cookie flow in your deployment.
