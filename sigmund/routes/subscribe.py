import logging
from pathlib import Path
from datetime import datetime, timedelta
from flask import jsonify, redirect, Blueprint, url_for, request
from flask_login import login_required
from .. import config, utils
from ..database.manager import DatabaseManager
from .app import get_sigmund
import stripe
logger = logging.getLogger('sigmund')
subscribe_blueprint = Blueprint('subscribe', __name__)
stripe.api_key = config.stripe_secret_key


@subscribe_blueprint.route('/')
@login_required
def subscribe():
    """When the user is logged in but not subscribed, the request is redirected
    to the subscribe endpoint. This shows a simple page inviting the user to
    subscribe through Stripe. If the user is already subscribed (which can 
    happen if the endpoint is accessed directly) then the user is redirected
    to the Stripe customer portal.
    """
    if not config.subscription_required:
        return redirect(url_for('app.chat'), code=303)    
    sigmund = get_sigmund()
    if sigmund.database.check_subscription():
        logger.info(f'redirecting {sigmund.user_id} to customer portal')
        redirect(url_for('subscribe.customer_portal'), code=303)
    username = sigmund.user_id
    if '(google)::' in username:
        username = username.split('(google)::')[0] + '(Google)'
    return utils.render('subscribe-now.html', username=username)
    
    
@subscribe_blueprint.route('/create-checkout-session')
@login_required
def create_checkout_session():
    """Prepares the product for checkout and then redirects to Stripe for the
    actual transaction.
    """
    sigmund = get_sigmund()
    logger.info(f'initiating checkout for {sigmund.user_id}')
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=f'{config.server_url}/subscribe/success/{{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{config.server_url}/',
            client_reference_id=sigmund.user_id,
            mode='subscription',
            line_items=[{'price': config.stripe_price_id, 'quantity': 1}],
            **config.stripe_checkout_keywords)
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@subscribe_blueprint.route('/success/<checkout_session_id>')
@login_required
def success(checkout_session_id):
    """This is called by Stripe after a subscription was succesfully finished.
    The actual subscription is activated in the webhook. This happens before
    the success endpoint is called.
    
    An error should not occur at this point. If it does, we show an error page
    inviting the user to try again and offer contact information.
    """
    sigmund = get_sigmund()
    try:
        checkout_session = stripe.checkout.Session.retrieve(
            checkout_session_id)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error ({checkout_session_id}): {e}')
        return utils.render('subscribe-error.html'), 500
    return utils.render('subscribe-success.html')


@subscribe_blueprint.route('/customer-portal')
@login_required
def customer_portal():
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


@subscribe_blueprint.route('/cancel')
@login_required
def cancel():
    """This entrypoint is for internal use and allows a subscription to be
    canceled independently of Stripe. Normally, a subscription would be
    canceled through the webhook.
    """
    sigmund = get_sigmund()
    sigmund.database.cancel_subscription()
    return redirect(url_for('subscribe.subscribe'), code=303)


@subscribe_blueprint.route('/webhook', methods=['POST'])
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
    # checkout.session.completed is sent when the user completes a checkout to
    # start a new subscription. At this point we associate the sigmund user id
    # with the stripe customer and subscription ids. This event is not sent
    # for subscription renewals, which are handled below.
    if event_type == 'checkout.session.completed':
        sigmund_user_id = event_object['client_reference_id']
        database = DatabaseManager(None, sigmund_user_id)
        database.update_subscription(
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id)
        logger.info(
            f'completed checkout for {sigmund_user_id} '
            f'(stripe_customer_id: {stripe_customer_id}, '
            f'stripe_subscription_id: {stripe_subscription_id})')                        
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
            logger.info('subscription doesn\"t exist yet, waiting '
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
