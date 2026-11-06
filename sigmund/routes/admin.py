import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, abort, flash, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import func

from .. import config, utils
from ..database.manager import DatabaseManager
from ..database.models import db, User, Activity, BufferActivity, \
    Conversation, Message, Subscription
from ..forms import AddCreditsForm, ExtendSubscriptionForm
from .store import CREDITS_PER_UNIT, _add_librechat_balance, \
    _sync_librechat_subscription

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


def _get_user_or_abort(user_id):
    """Returns the User for the given user_id, or aborts with a 404 if no
    such user exists.
    """
    user = User.query.filter_by(user_id=user_id).first()
    if user is None:
        abort(404)
    return user


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
    active_users_hour = [
        {'user_id': u.user_id, 'username': u.username}
        for u in
        User.query.filter(User.user_id.in_(active_ids_hour))
        .order_by(User.username).all()
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

    # ── Buffer activity stats ────────────────────────────────────────────────
    # Positive tokens = buffer additions (e.g. purchases)
    # Negative tokens = buffer deductions (usage beyond the weekly limit)
    # The helper below always returns the absolute value.
    def _buffer_sum(period_start, positive):
        query = db.session.query(func.sum(BufferActivity.tokens))
        if period_start is not None:
            query = query.filter(BufferActivity.time >= period_start)
        if positive:
            query = query.filter(BufferActivity.tokens > 0)
        else:
            query = query.filter(BufferActivity.tokens < 0)
        total = query.scalar() or 0
        return abs(total)

    buffer_added_24h = _buffer_sum(one_day_ago, True)
    buffer_added_7d  = _buffer_sum(seven_days_ago, True)
    buffer_added_all = _buffer_sum(None, True)
    buffer_used_24h  = _buffer_sum(one_day_ago, False)
    buffer_used_7d   = _buffer_sum(seven_days_ago, False)
    buffer_used_all  = _buffer_sum(None, False)

    # ── Active subscribers ───────────────────────────────────────────────────
    active_sub_ids = [
        uid for (uid,) in
        db.session.query(Subscription.user_id)
        .filter(Subscription.from_date <= now, Subscription.to_date > now)
        .distinct().all()
    ]
    active_subscription_count = len(active_sub_ids)

    user_map = {
        u.user_id: u
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

    def _buffer_tokens_per_user(period_start, positive):
        if not active_sub_ids:
            return {}
        query = db.session.query(
            BufferActivity.user_id, func.sum(BufferActivity.tokens))
        if period_start is not None:
            query = query.filter(BufferActivity.time >= period_start)
        query = query.filter(BufferActivity.user_id.in_(active_sub_ids))
        if positive:
            query = query.filter(BufferActivity.tokens > 0)
        else:
            query = query.filter(BufferActivity.tokens < 0)
        return {
            uid: abs(total) for uid, total in
            query.group_by(BufferActivity.user_id).all()
        }

    buffer_added_7d_per_user = _buffer_tokens_per_user(seven_days_ago, True)
    buffer_used_7d_per_user  = _buffer_tokens_per_user(seven_days_ago, False)

    subscriber_rows = sorted(
        [
            {
                'user_id':         uid,
                'username':        user_map[uid].username if uid in user_map
                                   else f'user_{uid}',
                'suspended':       user_map[uid].suspended if uid in user_map
                                   else False,
                'tokens_7d':        tokens_7d_per_user.get(uid) or 0,
                'tokens_24h':       tokens_24h_per_user.get(uid) or 0,
                'buffer_added_7d':  buffer_added_7d_per_user.get(uid) or 0,
                'buffer_used_7d':   buffer_used_7d_per_user.get(uid) or 0,
            }
            for uid in active_sub_ids
        ],
        key=lambda x: x['tokens_7d'],
        reverse=True,
    )

    # ── All users ────────────────────────────────────────────────────────────
    # Every user is listed, including suspended and unsubscribed ones, so
    # that any account can be reached from the dashboard.
    all_users = User.query.order_by(User.user_id).all()
    all_user_ids = [u.user_id for u in all_users]
    last_activity_map = (
        dict(db.session.query(Activity.user_id, func.max(Activity.time))
             .filter(Activity.user_id.in_(all_user_ids))
             .group_by(Activity.user_id).all())
        if all_user_ids else {})
    tokens_7d_all_map = (
        dict(db.session.query(
                 Activity.user_id, func.sum(Activity.tokens_consumed))
             .filter(Activity.user_id.in_(all_user_ids),
                     Activity.time >= seven_days_ago)
             .group_by(Activity.user_id).all())
        if all_user_ids else {})
    active_sub_id_set = set(active_sub_ids)
    all_user_rows = sorted(
        [
            {
                'user_id':       u.user_id,
                'username':      u.username,
                'suspended':     u.suspended,
                'subscribed':    u.user_id in active_sub_id_set,
                'last_activity': last_activity_map.get(u.user_id),
                'tokens_7d':     tokens_7d_all_map.get(u.user_id) or 0,
            }
            for u in all_users
        ],
        # Most recently active users first, users without activity last
        key=lambda row: row['last_activity'] or datetime.min,
        reverse=True,
    )

    theme = request.cookies.get('theme', config.settings_default['theme'])
    return utils.render(
        'admin.html',
        theme=theme,
        now=now,
        # Active users
        active_count_hour=len(active_users_hour),
        active_users_hour=active_users_hour,
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
        # Buffer activity stats
        buffer_added_24h=buffer_added_24h,
        buffer_added_7d=buffer_added_7d,
        buffer_added_all=buffer_added_all,
        buffer_used_24h=buffer_used_24h,
        buffer_used_7d=buffer_used_7d,
        buffer_used_all=buffer_used_all,
        # Subscriptions
        active_subscription_count=active_subscription_count,
        subscriber_rows=subscriber_rows,
        # All users
        all_user_rows=all_user_rows,
    )


@admin_blueprint.route('/user/<int:user_id>')
@admin_required
def user_overview(user_id):
    """Shows an overview of a single user with the most relevant details:
    account information, subscription state and history, token usage, and
    the extra-credits buffer. From here, the subscription can be extended
    manually and extra credits can be added, as an alternative to Stripe.
    """
    user = _get_user_or_abort(user_id)
    now = datetime.utcnow()

    def _sum_tokens(period_start=None):
        query = db.session.query(func.sum(Activity.tokens_consumed)) \
            .filter(Activity.user_id == user_id)
        if period_start is not None:
            query = query.filter(Activity.time >= period_start)
        return query.scalar() or 0

    tokens_24h = _sum_tokens(now - timedelta(hours=24))
    tokens_7d  = _sum_tokens(now - timedelta(days=7))
    tokens_30d = _sum_tokens(now - timedelta(days=30))
    tokens_all = _sum_tokens()
    weekly_credits_left = int(
        max(0, config.weekly_token_limit - tokens_7d))
    last_activity = db.session.query(func.max(Activity.time)) \
        .filter(Activity.user_id == user_id).scalar()

    # The buffer contains purchased extra credits. Positive entries are
    # additions, negative entries are deductions for usage beyond the
    # weekly limit.
    buffer_balance = db.session.query(func.sum(BufferActivity.tokens)) \
        .filter(BufferActivity.user_id == user_id).scalar() or 0
    buffer_history = BufferActivity.query.filter_by(user_id=user_id) \
        .order_by(BufferActivity.time.desc(),
                  BufferActivity.buffer_activity_id.desc()) \
        .limit(20).all()

    # Subscription records are append-only. The subscription is active while
    # at least one record covers the current time, and it runs until the
    # latest end date of all records.
    subscriptions = Subscription.query.filter_by(user_id=user_id) \
        .order_by(Subscription.from_date.desc(),
                  Subscription.subscription_id.desc()).all()
    subscription_active = any(
        s.from_date is not None and s.to_date is not None
        and s.from_date <= now and s.to_date > now
        for s in subscriptions)
    subscription_end = max(
        (s.to_date for s in subscriptions if s.to_date is not None),
        default=None)
    subscription_last_ended = max(
        (s.to_date for s in subscriptions
         if s.to_date is not None and s.to_date <= now),
        default=None)

    theme = request.cookies.get('theme', config.settings_default['theme'])
    return utils.render(
        'admin-user.html',
        theme=theme,
        now=now,
        user=user,
        last_activity=last_activity,
        # Subscription
        subscription_active=subscription_active,
        subscription_end=subscription_end,
        subscription_last_ended=subscription_last_ended,
        subscriptions=subscriptions,
        # Usage
        tokens_24h=tokens_24h,
        tokens_7d=tokens_7d,
        tokens_30d=tokens_30d,
        tokens_all=tokens_all,
        weekly_token_limit=config.weekly_token_limit,
        weekly_credits_left=weekly_credits_left,
        # Extra credits buffer
        buffer_balance=buffer_balance,
        buffer_history=buffer_history,
        credits_per_unit=CREDITS_PER_UNIT,
        # Forms for manual administration
        extend_form=ExtendSubscriptionForm(),
        add_credits_form=AddCreditsForm(),
    )


@admin_blueprint.route('/user/<int:user_id>/extend-subscription',
                       methods=['POST'])
@admin_required
def extend_subscription(user_id):
    """Manually extends the user's subscription by a fixed number of days.
    Like a Stripe renewal, the extension always starts from now. The user's
    existing Stripe customer id is carried over to the new subscription
    record, so that webhook lookups keep working. The new subscription state
    is synced to LibreChat, mirroring the Stripe webhook.
    """
    user = _get_user_or_abort(user_id)
    form = ExtendSubscriptionForm()
    if not form.validate_on_submit():
        abort(400)
    days = form.days.data
    database = DatabaseManager(None, user.username)
    database.extend_subscription(days)
    _sync_librechat_subscription(database)
    end_date = database.get_subscription_end_date()
    logger.info(
        f'admin {current_user.get_id()} extended the subscription of '
        f'{user.username} ({user.user_id}) by {days} days '
        f'(active until {end_date})')
    flash(
        f'Subscription extended by {days} days. The subscription is now '
        f'active until {end_date.strftime("%Y-%m-%d")}.')
    return redirect(url_for('admin.user_overview', user_id=user_id), code=303)


@admin_blueprint.route('/user/<int:user_id>/add-credits', methods=['POST'])
@admin_required
def add_credits(user_id):
    """Manually adds extra credits to the user's buffer, in the same units
    that the Stripe store uses (CREDITS_PER_UNIT tokens per unit). The
    credits are also added to the user's LibreChat balance, mirroring the
    Stripe webhook.
    """
    user = _get_user_or_abort(user_id)
    form = AddCreditsForm()
    if not form.validate_on_submit():
        abort(400)
    units = form.units.data
    credits = units * CREDITS_PER_UNIT
    database = DatabaseManager(None, user.username)
    database.add_activity_buffer(
        credits,
        f'Manually added {units} x {CREDITS_PER_UNIT:,} extra credits '
        f'(admin: {current_user.get_id()})')
    _add_librechat_balance(
        database, credits, f'admin-credits:{current_user.get_id()}')
    logger.info(
        f'admin {current_user.get_id()} added {credits} extra credits to '
        f'{user.username} ({user.user_id})')
    flash(f'Added {credits:,} extra credits ({units} unit(s)).')
    return redirect(url_for('admin.user_overview', user_id=user_id), code=303)
