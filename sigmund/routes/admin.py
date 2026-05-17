import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, abort, request
from flask_login import current_user
from sqlalchemy import func

from .. import config, utils
from ..database.models import db, User, Activity, Conversation, Message, \
    Subscription

logger = logging.getLogger('sigmund')
admin_blueprint = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        user = User.query.filter_by(username=current_user.get_id()).first()
        if user is None or user.user_id not in config.admin_user_ids:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_blueprint.route('/')
@admin_required
def dashboard():
    now             = datetime.utcnow()
    one_hour_ago    = now - timedelta(hours=1)
    one_day_ago     = now - timedelta(hours=24)
    seven_days_ago  = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # ── Active users in the past hour ────────────────────────────────────────
    active_ids_hour = [
        uid for (uid,) in
        db.session.query(Activity.user_id)
        .filter(Activity.time >= one_hour_ago)
        .distinct().all()
    ]
    active_usernames_hour = [
        u.username for u in
        User.query.filter(User.user_id.in_(active_ids_hour)).all()
    ] if active_ids_hour else []

    # ── General user stats ───────────────────────────────────────────────────
    total_users      = User.query.count()
    suspended_users  = User.query.filter_by(suspended=True).count()
    users_active_24h = (db.session.query(Activity.user_id)
                        .filter(Activity.time >= one_day_ago)
                        .distinct().count())
    users_active_7d  = (db.session.query(Activity.user_id)
                        .filter(Activity.time >= seven_days_ago)
                        .distinct().count())
    users_active_30d = (db.session.query(Activity.user_id)
                        .filter(Activity.time >= thirty_days_ago)
                        .distinct().count())

    # ── Conversation & message counts ────────────────────────────────────────
    total_conversations = Conversation.query.count()
    total_messages      = Message.query.count()
    avg_convos_per_user = (round(total_conversations / total_users, 1)
                           if total_users else 0)
    avg_msgs_per_convo  = (round(total_messages / total_conversations, 1)
                           if total_conversations else 0)

    # ── Token stats ──────────────────────────────────────────────────────────
    tokens_24h = (db.session.query(func.sum(Activity.tokens_consumed))
                  .filter(Activity.time >= one_day_ago).scalar() or 0)
    tokens_7d  = (db.session.query(func.sum(Activity.tokens_consumed))
                  .filter(Activity.time >= seven_days_ago).scalar() or 0)
    tokens_all_time = (db.session.query(func.sum(Activity.tokens_consumed))
                       .scalar() or 0)

    # ── Active subscribers ───────────────────────────────────────────────────
    active_sub_ids = [
        uid for (uid,) in
        db.session.query(Subscription.user_id)
        .filter(Subscription.from_date <= now, Subscription.to_date > now)
        .distinct().all()
    ]
    active_subscription_count = len(active_sub_ids)

    user_map = {
        u.user_id: u.username
        for u in User.query.filter(User.user_id.in_(active_sub_ids)).all()
    } if active_sub_ids else {}

    def _sum_tokens(period_start):
        if not active_sub_ids:
            return {}
        return dict(
            db.session.query(
                Activity.user_id, func.sum(Activity.tokens_consumed))
            .filter(Activity.user_id.in_(active_sub_ids),
                    Activity.time >= period_start)
            .group_by(Activity.user_id).all()
        )

    tokens_7d_per_user  = _sum_tokens(seven_days_ago)
    tokens_24h_per_user = _sum_tokens(one_day_ago)
    subscriber_rows = sorted(
        [
            {
                'username':         user_map.get(uid, f'user_{uid}'),
                'tokens_7d':        tokens_7d_per_user.get(uid) or 0,
                'tokens_24h':       tokens_24h_per_user.get(uid) or 0
            }
            for uid in active_sub_ids
        ],
        key=lambda x: x['tokens_7d'],
        reverse=True,
    )

    theme = request.cookies.get('theme', config.settings_default['theme'])
    return utils.render(
        'admin.html',
        theme=theme,
        now=now,
        # Active users
        active_count_hour=len(active_usernames_hour),
        active_usernames_hour=active_usernames_hour,
        # User stats
        total_users=total_users,
        suspended_users=suspended_users,
        users_active_24h=users_active_24h,
        users_active_7d=users_active_7d,
        users_active_30d=users_active_30d,
        # Conversation stats
        total_conversations=total_conversations,
        total_messages=total_messages,
        avg_convos_per_user=avg_convos_per_user,
        avg_msgs_per_convo=avg_msgs_per_convo,
        # Token stats
        tokens_24h=tokens_24h,
        tokens_7d=tokens_7d,
        tokens_all_time=tokens_all_time,
        # Subscriptions
        active_subscription_count=active_subscription_count,
        subscriber_rows=subscriber_rows,
    )
