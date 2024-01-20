import logging
from pathlib import Path
from flask import jsonify, redirect, Blueprint, url_for, request
from flask_login import login_required
from .. import config, utils
from ..database.manager import DatabaseManager
from .app import get_heymans
import stripe
logger = logging.getLogger('heymans')
subscribe_blueprint = Blueprint('subscribe', __name__)
stripe.api_key = config.stripe_secret_key


@subscribe_blueprint.route('/create-checkout-session')
@login_required
def create_checkout_session():
    """Prepares the product for checkout and then redirects to Stripe for the
    actual transaction.
    """
    heymans = get_heymans()
    logger.info(f'initiating checkout for "{heymans.user_id}"')
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=f'{config.server_url}/subscribe/success/{{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{config.server_url}/',
            client_reference_id=heymans.user_id,
            mode='subscription',
            line_items=[{'price': config.stripe_price_id, 'quantity': 1}],
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@subscribe_blueprint.route('/')
@login_required
def subscribe():
    heymans = get_heymans()
    if heymans.database.check_subscription():
        return utils.render('already-subscribed.html')
    return utils.render('subscribe-now.html',
                        login_text=utils.md(Path('heymans/static/login.md').read_text()))


@subscribe_blueprint.route('/success/<checkout_session_id>')
@login_required
def success(checkout_session_id):
    logger.info(f'subscription successful (checkout_session_id: {checkout_session_id})')
    heymans = get_heymans()
    try:
        checkout_session = stripe.checkout.Session.retrieve(
            checkout_session_id)
        heymans.database.update_subscription(
            stripe_customer_id=checkout_session.customer,
            stripe_subscription_id=checkout_session.subscription)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error: {e}')
        return utils.render('subscribe-success.html'), 500
    return utils.render('subscribe-success.html')


@subscribe_blueprint.route('/customer-portal')
@login_required
def customer_portal():
    heymans = get_heymans()
    customer_id = heymans.database.get_stripe_customer_id()
    if not customer_id:
        logger.error('No Stripe customer ID found for the user')
        return utils.render('subscribe-error.html'), 404
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=config.server_url,
        )
        return redirect(session.url, code=303)
    except stripe.error.StripeError as e:
        logger.error(f'Stripe API error: {e}')
        return utils.render('subscribe-error.html'), 500


@subscribe_blueprint.route('/cancel')
@login_required
def cancel():
    heymans = get_heymans()
    heymans.database.cancel_subscription()
    return redirect(url_for('subscribe.subscribe'), code=303)


@subscribe_blueprint.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.stripe_webhook_secret)
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400
    if event and event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        stripe_customer_id = invoice['customer']
        stripe_subscription_id = invoice['subscription']
        database = DatabaseManager.from_stripe_customer_id(stripe_customer_id)
        if not database:
            return 'Invalid user', 400
        database.update_subscription(
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id)
    elif event and event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        stripe_customer_id = subscription['customer']
        database = DatabaseManager.from_stripe_customer_id(stripe_customer_id)
        if not database:
            return 'Invalid user', 400
        database.cancel_subscription()
    return jsonify(success=True), 200
