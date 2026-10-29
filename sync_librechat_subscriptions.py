"""One-time backfill: pushes every user's current subscription state to
LibreChat.

Run this once, after enabling SIGMUND_LIBRECHAT_ENABLED and before enabling
LibreChat's subscription gate (SUBSCRIPTION_GATE=true in LibreChat's .env).
LibreChat is fail-closed: a user without a synced subscription cannot chat.
After the backfill, the Stripe webhook and the OIDC authorization endpoint
keep the state current (see sigmund/librechat.py).

Usage:

    python sync_librechat_subscriptions.py [username]

Without arguments, all users are synced. With a username, only that user is
synced, which is useful for testing. Requires the same environment as the
server itself (.env is loaded); a user that has not logged into LibreChat
yet is skipped (LibreChat does not know that user yet).
"""
from dotenv import load_dotenv

load_dotenv()

import sys
from datetime import datetime

from sigmund import config, librechat
from sigmund.database.models import User, Subscription
from sigmund.server import create_app

app = create_app()
with app.app_context():
    if not librechat.enabled():
        raise SystemExit(
            'LibreChat sync is disabled or not configured '
            '(SIGMUND_LIBRECHAT_ENABLED / SIGMUND_LIBRECHAT_SECRET)')
    now = datetime.utcnow()
    query = User.query
    if len(sys.argv) > 1:
        query = query.filter_by(username=sys.argv[1])
    users = query.all()
    print(f'Syncing subscription state for {len(users)} user(s) to '
          f'{config.librechat_url}')
    n_synced = n_unsynced = 0
    for user in users:
        record = (Subscription.query
                  .filter(Subscription.user_id == user.user_id)
                  .order_by(Subscription.to_date.desc(),
                            Subscription.from_date.desc())
                  .first())
        active = (record is not None and record.from_date is not None
                  and record.to_date is not None
                  and record.from_date <= now < record.to_date)
        ok = librechat.sync_subscription(
            user.email,
            record.to_date if active else None,
            status='active' if active else None)
        if ok:
            n_synced += 1
        else:
            n_unsynced += 1
        state = (f'active until {record.to_date}' if active
                 else 'inactive')
        result = 'synced' if ok else 'not synced (see the log)'
        print(f'  {user.username}: {state} — {result}')
    print(f'Done: {n_synced} synced, {n_unsynced} not synced. Users that '
          f'have never logged into LibreChat are always unsynced and are '
          f'synced on their first login.')
