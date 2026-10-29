# Syncing subscriptions and credits to LibreChat

Sigmund owns the subscription and the sale of extra credits, but LibreChat
maintains its own copy of both, and gates chat access on them. The client
is in `sigmund/librechat.py`; it talks to two server-to-server endpoints on
the LibreChat server:

| Endpoint | What it does |
|---|---|
| `POST /api/subscription/sync` | Writes the subscription state; LibreChat blocks chat when no active subscription is synced (fail-closed) |
| `POST /api/subscription/add-balance` | Adds purchased credits to the user's token balance, as an auditable ledger transaction |

## Identity: which email is used

Both endpoints identify the user by their **registered email address**
(`user.email`, registered on login, see `DatabaseManager.set_email`). Every
user has one. This is the same address that the OIDC provider reports in
the `email` claim, so LibreChat always resolves the same user.

## When Sigmund calls LibreChat

| Sigmund event | Endpoint | Payload |
|---|---|---|
| Subscription checkout completed (Stripe webhook) | `sync` | `expiresAt` = the new subscription record's `to_date` (now + 50 days), `status: active` |
| Subscription renewal paid (Stripe webhook) | `sync` | same as above |
| Extra credits purchased (Stripe webhook) | `add-balance` | `amount` = purchased credits, `context` = `stripe-checkout:<session id>` |
| User logs into LibreChat (OIDC `/oidc/authorize`) | `sync` | the user's current state, pushed after the access checks pass |

The authorization-endpoint sync closes a gap that the webhook cannot: a
user who subscribes before ever logging into LibreChat is unknown to
LibreChat at that point (the webhook's sync gets a 404 `user_not_found` and
is skipped), so the first login is the moment their state arrives. Because
every login re-pushes the current state, a previously failed webhook sync is
also repaired automatically. Sync failures are logged and never block the
webhook's 200 response to Stripe or the login itself.

## Credit units

Sigmund's usage units and LibreChat's token credits are both
USD-normalized: Sigmund's rate tables are set such that 1e7 units
correspond to $10, and LibreChat documents 1000 credits as $0.001 (i.e.
1e7 credits as $10). Purchased credits therefore transfer **1:1** — one
unit of `CREDITS_PER_UNIT` (10,000,000 tokens) is 10,000,000 LibreChat
credits, i.e. $10 of model usage in either application.

## Settings

    SIGMUND_LIBRECHAT_ENABLED=1
    SIGMUND_LIBRECHAT_URL=http://127.0.0.1:3080
    SIGMUND_LIBRECHAT_SECRET=<LibreChat's SUBSCRIPTION_SYNC_SECRET>

The secret must be equal to `SUBSCRIPTION_SYNC_SECRET` in LibreChat's
`.env`. When the flag is off, or the secret is missing, all sync calls are
silent no-ops (logged once as a warning when enabled without a secret).

## Rollout

1. Set `SUBSCRIPTION_SYNC_SECRET` (and `SUBSCRIPTION_PORTAL_URL`) in
   LibreChat's `.env`; the gate stays off (`SUBSCRIPTION_GATE=false`).
2. Set the three variables above in Sigmund's `.env` and restart Sigmund.
3. Run the one-time backfill, which pushes every user's current state:

       python sync_librechat_subscriptions.py [username]

   Users that have never logged into LibreChat are skipped (404) and are
   synced on their first login instead.
4. Enable LibreChat's gate: `SUBSCRIPTION_GATE=true`. Admins are exempt
   throughout, so there is no lock-out risk.

## Limitations

- `add-balance` is **not** idempotent: a retried request credits twice. It
  is only called from the Stripe webhook, which delivers each event once;
  if Stripe retries a webhook delivery, its signature check makes repeated
  delivery detectable, but a manual replay would credit twice. The response
  reports the new total (`tokenCredits`) for reconciliation.
- Syncs are one-way: LibreChat never writes back to Sigmund. If the two
  disagree (for example after a missed webhook), the next login of the user
  repairs the subscription state, and the balance can be reconciled against
  the ledger transactions that carry the Stripe checkout session id.
- A slow or unreachable LibreChat server slows down the webhook and the
  OIDC authorization by at most `REQUEST_TIMEOUT` (10 s); failures are
  logged and never raise.

## Tests

    pytest tests/cheap/test_librechat.py

Like the other tests in `tests/cheap`, these need Redis to be running. The
HTTP calls to LibreChat are mocked, so no LibreChat server is required.
