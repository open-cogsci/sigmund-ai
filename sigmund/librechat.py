"""A thin client for LibreChat's subscription API.

Sigmund owns the subscription and the sale of extra credits, but LibreChat
maintains its own copy of both: the subscription state on the user document
(where the subscription gate reads it) and purchased credits in the user's
token balance. This module is the only place where Sigmund talks to
LibreChat's two server-to-server endpoints:

    POST /api/subscription/sync          subscription state
    POST /api/subscription/add-balance   purchased credits

Both endpoints are authenticated with a shared secret
(SIGMUND_LIBRECHAT_SECRET, equal to LibreChat's SUBSCRIPTION_SYNC_SECRET)
and identify the user by their registered email address (User.email, see
DatabaseManager.set_email). This is the same address that the OIDC provider
reports in the email claim, so LibreChat resolves the same user.

The client is deliberately forgiving: every public function logs failures
and returns False, and never raises, because it is called from the Stripe
webhook (which must always answer 200 to Stripe) and from the OIDC
authorization endpoint (which must never block a login).
"""
import logging
from datetime import timezone

import requests

from . import config

logger = logging.getLogger('sigmund')

# The webhook and the authorization endpoint must not hang on a slow or
# unresponsive LibreChat server.
REQUEST_TIMEOUT = 10


def enabled() -> bool:
    """Returns True if the LibreChat client is enabled and configured."""
    if not config.librechat_enabled:
        return False
    if not config.librechat_secret:
        logger.warning(
            'SIGMUND_LIBRECHAT_ENABLED is set but SIGMUND_LIBRECHAT_SECRET '
            'is missing; subscription state is not synced to LibreChat')
        return False
    return True


def _iso_utc(expires_at) -> str:
    """Formats a datetime as an ISO 8601 string with a Z suffix, which is
    what LibreChat's API requires. Naive datetimes are interpreted as UTC
    (Sigmund stores all subscription dates as naive UTC datetimes).
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)
    return expires_at.isoformat().replace('+00:00', 'Z')


def _post(path: str, payload: dict):
    """POSTs a JSON payload to a LibreChat subscription endpoint.

    Returns the parsed response data on success, and None otherwise. A 404
    user_not_found is not treated as an error: it means that the user has
    not logged into LibreChat yet, in which case there is nothing to
    update, and the state is synced when the user does log in (see the
    authorization endpoint in routes/oidc_provider.py).
    """
    url = config.librechat_url + path
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {config.librechat_secret}'},
            timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        logger.error(f'LibreChat request to {url} failed: {e}')
        return None
    try:
        data = response.json()
    except ValueError:
        data = None
    if response.status_code == 200:
        return data if isinstance(data, dict) else {}
    code = (data or {}).get('code', response.status_code)
    if code == 'user_not_found':
        logger.info(
            f'LibreChat does not know the user {payload.get("email")} yet; '
            f'the update is skipped')
        return None
    logger.error(
        f'LibreChat rejected {url} with {response.status_code}: {code}')
    return None


def sync_subscription(email, expires_at, status=None, plan=None) -> bool:
    """Pushes the user's subscription state to LibreChat.

    expires_at is a datetime until which the subscription runs (naive UTC,
    as Sigmund stores subscription dates), or None to deactivate the user
    immediately. The call is idempotent, so it can be retried and repeated.
    """
    if not enabled():
        return False
    payload = {
        'email': email.strip().lower(),
        'expiresAt': None if expires_at is None else _iso_utc(expires_at),
    }
    for key, value in (('status', status), ('plan', plan)):
        if value:
            payload[key] = value
    data = _post('/api/subscription/sync', payload)
    if data is None:
        return False
    logger.info(
        f'synced LibreChat subscription for {payload["email"]} '
        f'(active: {data.get("active")}, until: {data.get("expiresAt")})')
    return True


def add_balance(email, amount, context=None) -> bool:
    """Adds purchased credits to the user's LibreChat token balance.

    The amount transfers 1:1: Sigmund's usage units and LibreChat's token
    credits are both USD-normalized (Sigmund's rate tables are set such
    that 1e7 units correspond to $10, and LibreChat documents 1000 credits
    as $0.001, i.e. 1e7 credits as $10). The call is NOT idempotent: it is
    made only from the Stripe webhook, which delivers each event once.
    """
    if not enabled():
        return False
    payload = {
        'email': email.strip().lower(),
        'amount': int(amount),
    }
    if context:
        payload['context'] = context[:64]
    data = _post('/api/subscription/add-balance', payload)
    if data is None:
        return False
    logger.info(
        f'added {payload["amount"]} credits to the LibreChat balance of '
        f'{payload["email"]} (new balance: {data.get("tokenCredits")})')
    return True
