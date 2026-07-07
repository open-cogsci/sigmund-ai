import logging
from flask import jsonify, redirect, Blueprint, url_for, request
from flask_login import login_required
from .. import config, utils
from ..database.manager import DatabaseManager
from .app import get_sigmund
import stripe
logger = logging.getLogger('sigmund')
store_blueprint = Blueprint('store', __name__)
stripe.api_key = config.stripe_secret_key

# Each unit of extra credits corresponds to this many tokens.
CREDITS_PER_UNIT = 10_000_000


@store_blueprint.route('/subscription')
@login_required
def subscription_page():
    """When the user is logged in but not subscribed, the request is redirected
    to the subscription endpoint. This shows a simple page inviting the user to
    subscribe through Stripe. If the user is already subscribed (which can 
    happen if the endpoint is accessed directly) then the user is redirected
    to the Stripe customer portal.
    """
    if not config.subscription_required:
        return redirect(url_for('app.chat'), code=303)    
    sigmund = get_sigmund()
    if sigmund.database.check_subscription():
        logger.info(f'redirecting {sigmund.user_id} to customer portal')
        redirect(url_for('store.subscription_customer_portal'), code=303)
    username = sigmund.username()
    return utils.render('subscribe-now.html', username=username)
    
    
@store_blueprint.route('/create-subscription-checkout-session')
@login_required
def create_subscription_checkout_session():
    """Prepares the subscription product for checkout and then redirects to 
    Stripe for the actual transaction.
    """
    sigmund = get_sigmund()
    logger.info(f'initiating subscription checkout for {sigmund.user_id}')
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=f'{config.server_url}/store/subscription-success/{{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{config.server_url}/',
            client_reference_id=sigmund.user_id,
            mode='subscription',
            line_items=[{'price': config.stripe_subscription_price_id,
                         'quantity': 1}],
            **config.stripe_checkout_keywords)
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@store_blueprint.route('/subscription-success/<checkout_session_id>')
@login_required
def subscription_success(checkout_session_id):
    """This is called by Stripe after a subscription was succesfully finished.
    The actual subscription is activated in the webhook. This happens before
    the success endpoint is called.
    
    An error should not occur at this point. If it does, we show an error page
    inviting the user to try again and offer contact information.
    """
    try:
        stripe.checkout.Session.retrieve(checkout_session_id)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error ({checkout_session_id}): {e}')
        return utils.render('subscribe-error.html'), 500
    return utils.render('subscribe-success.html')


@store_blueprint.route('/subscription-customer-portal')
@login_required
def subscription_customer_portal():
    """The customer portal redirects to Stripe so that the user can manage
    subscription information. This is only valid for users with a current or
    previous subscription.
    
    An error should not occur at this point. If it does, we show an error page
    inviting the user to try again and offer contact information.
    """
    sigmund = get_sigmund()
    customer_id = sigmund.database.get_stripe_customer_id()
    if not customer_id:
        logger.error('No Stripe customer ID found for the user')
        return utils.render('subscribe-error.html'), 404
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=config.server_url)
        return redirect(session.url, code=303)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error: {e}')
        return utils.render('subscribe-error.html'), 500


@store_blueprint.route('/buy-extra-credits')
@login_required
def extra_credits_page():
    """Shows a page where the user can purchase extra credits (a one-time
    payment that adds to the activity buffer). If subscriptions are not
    required, the user is redirected to the chat page.
    """
    if not config.subscription_required:
        return redirect(url_for('app.chat'), code=303)
    sigmund = get_sigmund()
    extra_credits_left = sigmund.limits.extra_credits_left()
    username = sigmund.username()
    return utils.render('buy-extra-credits.html', username=username,
                        extra_credits_left=extra_credits_left)


@store_blueprint.route('/create-extra-credits-checkout-session')
@login_required
def create_extra_credits_checkout_session():
    """Prepares the extra-credits product for a one-time checkout and then
    redirects to Stripe for the actual transaction. The user can specify a
    quantity, where each unit corresponds to CREDITS_PER_UNIT tokens.
    """
    sigmund = get_sigmund()
    # Get the quantity from the query parameters, defaulting to 1.
    # Clamp to a reasonable range to prevent abuse.
    try:
        quantity = int(request.args.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, min(100, quantity))
    logger.info(
        f'initiating extra-credits checkout for {sigmund.user_id} '
        f'(quantity: {quantity})')
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=f'{config.server_url}/store/extra-credits-success/{{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{config.server_url}/store/buy-extra-credits',
            client_reference_id=sigmund.user_id,
            mode='payment',
            line_items=[{'price': config.stripe_extra_credits_price_id,
                         'quantity': quantity}],
            **config.stripe_checkout_keywords)
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@store_blueprint.route('/extra-credits-success/<checkout_session_id>')
@login_required
def extra_credits_success(checkout_session_id):
    """This is called by Stripe after an extra-credits purchase was
    successfully finished. The actual credits are added in the webhook, which
    fires before this endpoint is called.
    
    An error should not occur at this point. If it does, we show an error page
    inviting the user to try again and offer contact information.
    """
    sigmund = get_sigmund()
    extra_credits_left = sigmund.limits.extra_credits_left()
    username = sigmund.username()
    try:
        stripe.checkout.Session.retrieve(checkout_session_id)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error ({checkout_session_id}): {e}')
        return utils.render('subscribe-error.html'), 500
    return utils.render('extra-credits-success.html', username=username,
                        extra_credits_left=extra_credits_left)


@store_blueprint.route('/webhook', methods=['POST'])
def webhook():
    """The webhook is the main mechanism through which Stripe informs the app
    of payments. The webhook is a public entry point, which means that the
    user is not logged in.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.stripe_webhook_secret)
    except ValueError as e:
        logger.error(f'invalid webhook payload: {e}')
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'invalid webhook signature: {e}')
        return 'Invalid signature', 400
    if not event:
        logger.error('webhook contains no event')
        return jsonify(success=True), 200
    event_type = event['type']
    if event_type not in ('checkout.session.completed',
                          'invoice.payment_succeeded'):
        logger.error(f'webhook ignored: {event_type}')
        return jsonify(success=True), 200
    event_object = event['data']['object']
    stripe_customer_id = event_object['customer']
    stripe_subscription_id = event_object.get('subscription', None)
    logger.info(f'webhook event: {event_type}')
    # checkout.session.completed is sent when the user completes a checkout,
    # both for subscriptions and one-time payments. At this point we 
    # distinguish between the two based on the checkout mode.
    if event_type == 'checkout.session.completed':
        checkout_mode = event_object.get('mode', None)
        sigmund_user_id = event_object['client_reference_id']
        if checkout_mode == 'subscription':
            # Associate the sigmund user id with the stripe customer and
            # subscription ids. This event is not sent for subscription 
            # renewals, which are handled below.
            database = DatabaseManager(None, sigmund_user_id)
            database.update_subscription(
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id)
            logger.info(
                f'completed subscription checkout for {sigmund_user_id} '
                f'(stripe_customer_id: {stripe_customer_id}, '
                f'stripe_subscription_id: {stripe_subscription_id})')
        elif checkout_mode == 'payment':
            # A one-time payment for extra credits. Add the credits to the
            # user's activity buffer based on the purchased quantity. Each
            # unit corresponds to CREDITS_PER_UNIT tokens.
            checkout_session_id = event_object['id']
            line_items = stripe.checkout.Session.list_line_items(
                checkout_session_id)
            total_quantity = sum(
                item['quantity'] for item in line_items['data']
                if item.get('quantity'))
            credits = total_quantity * CREDITS_PER_UNIT
            database = DatabaseManager(None, sigmund_user_id)
            database.add_activity_buffer(
                credits,
                f'Purchased {total_quantity} x {CREDITS_PER_UNIT} extra '
                f'credits (Stripe checkout: {checkout_session_id})')
            logger.info(
                f'completed extra-credits checkout for {sigmund_user_id} '
                f'(stripe_customer_id: {stripe_customer_id}, '
                f'checkout_session_id: {checkout_session_id}, '
                f'quantity: {total_quantity}, credits: {credits})')
        else:
            logger.warning(
                f'unexpected checkout mode: {checkout_mode} '
                f'for user {sigmund_user_id}')
    # invoice.payment_succeeded is sent when a payment was successfully 
    # completed, both for new subscriptions and renewals.
    elif event_type == 'invoice.payment_succeeded':
        # Attempt to get the user-specific database instance based on the
        # stripe customer id
        database = DatabaseManager.from_stripe_customer_id(stripe_customer_id)
        # For new subscriptions, this fails because the link between the 
        # stripe customer id and the sigmund user id still needs to be 
        # established in checkout.session.completed, which is fired later.
        if database is None:
            logger.info('subscription doesn"t exist yet, waiting '
                        'for checkout.session.completed')
        # For renewals, this succeeds and we renew the subscription
        else:
            database.update_subscription(
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id)
            logger.info(
                f'received payment for {database.username} '
                f'(stripe_customer_id: {stripe_customer_id}, '
                f'stripe_subscription_id: {stripe_subscription_id})')
    logger.info('webhook successful')
    return jsonify(success=True), 200
