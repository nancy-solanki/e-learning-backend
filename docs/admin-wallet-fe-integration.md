# Frontend integration prompt

Integrate the existing Wallet page shown in the reference screenshot with the backend. Preserve its layout, styling, cards, filters, table, export button and View actions. Replace all sample data and remove the “Sample wallet · Static preview” badge and sample-account wording.

## Access and ownership

This page is for authenticated instructors and admins (admin group or superuser). Hide its navigation for students. Use the existing Bearer-token API client and authentication handling. The backend enforces access. Both roles can access only their own wallet, earnings, transactions, details and exports. Instructors see their own course earnings; admins see their own allocated earnings. A wallet belongs to the signed-in user; it is NOT the platform-wide gross-revenue wallet. Do not send a user ID or wallet ID to these endpoints.

## Endpoints

All routes have trailing slashes:

- GET `/api/v1/wallet/overview/?start=2026-10-03&end=2026-10-10`
- GET `/api/v1/wallet/transactions/?start=2026-10-03&end=2026-10-10&page=1`
- GET `/api/v1/wallet/transactions/{id}/`
- GET `/api/v1/wallet/transactions/export/?start=2026-10-03&end=2026-10-10`

Dates are inclusive UTC calendar dates. If omitted, end defaults to today in UTC and start defaults to the first day of end's month. Use a date-range selector; do not hardcode the screenshot's dates. Invalid dates or reversed ranges return 400.

## Overview contract

All money is a decimal STRING in major currency units, e.g. `"2456.00"`. Use the returned currency for formatting; currently INR, not the screenshot's USD. Do not divide amounts by 100 or hardcode `$`. Use a decimal-safe formatter or the project's existing money utility.

The response has:

- `currency`: `"INR"`
- `as_of`: ISO timestamp of this overview
- `history_started_at`: earliest reliable ledger timestamp
- `history_complete`: whether the requested period starts on/after that timestamp
- `opening_balance`: decimal string or null; posted balance before start, before any pending reservations
- `period`: `{start, end, timezone: "UTC"}`
- `summary`:
  - `available_balance`: live posted balance minus all currently pending withdrawal reservations
  - `period_earnings`, `completed_payouts`, `refunds`: period totals; outflow cards show positive values
  - `earning_count`, `completed_payout_count`, `refund_count`: period record counts
  - `pending_payout_amount`, `pending_payout_count`: current reservations, regardless of selected period
  - `latest_pending_payout_at`: ISO request timestamp or null
- `payout_account`: null or `{type: "bank_transfer", bank_name, account_last4}`

Bind cards to these fields. Label the earning count as “earning transactions” (the current user’s earning postings), not gross course-sale revenue. Only show the reservation sentence when pending_payout_count > 0. For multiple payouts, call the timestamp “Latest request”; the amount is their combined total. If payout_account is null show “No payout account configured”. Do not display a fabricated bank account.

Display opening_balance in the history header. If null show “Opening balance unavailable”. When history_complete is false show “History available from [history_started_at]; selected-period totals may be incomplete.” Existing balances were migrated as dated opening adjustments, not fabricated historical sales. Live available balance is independent of the selected period and will not necessarily reconcile to period totals.

## History, filtering and details

List response: `{count, next, previous, results}`; 20 rows per page. Each row contains:

`{id, reference, description, date, completed_at, type, status, amount, account_last4}`

- id is a UUID for fetching details; reference is the actual reference shown beneath the description (not a fabricated TXN number).
- date and completed_at are ISO timestamps; completed_at can be null. Display dates in UTC consistently with the range.
- type values: `earning`, `withdrawal`, `refund`, `adjustment`. Display Earning, Withdrawal, Refund, Adjustment.
- status values: `completed`, `pending`, `failed`, `cancelled`. Display matching title-case badges; do not map failed to pending.
- amount is signed: earnings positive; withdrawals/refunds negative; adjustments can be either. Render + for positive table amounts.
- account_last4 is the historical destination snapshot when recorded, or an empty string. Never replace it with the current bank account's last4.

Search uses `search` (description or reference). Type uses `type`; status uses `status`. Omit empty/“All” filters. Debounce search, reset page to 1 after any filter/range change, and ignore stale responses. Filters affect history and export, not overview cards. History uses request/creation date; period totals use completion date, so a payout requested earlier may complete in the selected period.

View opens a details drawer/modal populated from the detail endpoint with reference, description, dates, type, status, signed amount and destination last4 if present. Use overview.currency for money formatting.

## Export and UI states

Export requests the CSV endpoint using the active range/search/type/status, without page. Download the authenticated response as a Blob named wallet-transactions.csv. Export includes every matching row, not just the visible page. Handle download errors before creating a file URL.

Provide skeleton/loading, empty history, no search results, retry/error and disabled-export-during-download states. Handle 401 via existing auth flow, 403 as access denied, 404 overview as “Wallet not configured”, and 400 as validation feedback. Do not silently substitute sample data or zero for a failed request.

There is no payout-request button in the reference and no public payout/refund mutation endpoint in this change. Do not add a withdrawal or refund form or imply bank transfers can be initiated here.

Validate integration for a populated wallet, empty wallet, missing account, incomplete history, all filter combinations, pagination, details, CSV, failed requests and successful instructor access, forbidden student access and cross-user isolation for both roles.

# Backend rollout notes

Run `python manage.py migrate` before deploying this FE integration. The single new wallet migration (`0002_wallet_currency_wallet_history_started_at_and_more`) widens wallet amounts to fixed-point decimals and creates a dated opening ledger entry for each existing nonzero balance. Existing `/api/v1/wallet/` remains available, restricted to instructors and admins, each scoped to their own wallet; its money fields serialize as decimal strings. Generic `/api/v1/transaction/` remains a separate customer transaction API and must not be used for this wallet screen.

New successful order credits record ledger entries with unique per-order references, including admin commission shares. Commission division preserves cents and assigns any residual cents deterministically. Existing checkout amount rounding is unchanged.

`apps.wallet.ledger.record_entry` and `settle_withdrawal` are internal services for verified payout/refund integrations, with idempotency, row locking and pending reservation handling. They do not call a bank/payment provider. No real payout/refund provider integration or historical sales reconstruction is included. Do not post directly through ORM writes or edit wallet balances; use ledger services. Refund postings must be supplied with a verified refund reference and the correct wallet allocation by the future payment integration.

The two previously proposed migrations have been consolidated before deployment. If either old migration was already applied to a database, reconcile its migration state before deploying this rewritten migration; do not fake migrations without checking whether opening ledger entries exist.
