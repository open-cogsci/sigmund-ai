import os
os.environ['USE_FLASK_SQLALCHEMY'] = '1'
from flask import Flask, Config, request, redirect
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from werkzeug.exceptions import HTTPException, NotFound
from . import config
from .redis_client import redis_client
from .routes import api_blueprint, app_blueprint, User, store_blueprint, \
    google_login_blueprint, public_blueprint, admin_blueprint
from . import utils
from .database.models import db
import logging
import traceback

logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class SigmundConfig(Config):
    SECRET_KEY = config.flask_secret_key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sigmund.db'
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis_client


def create_app(config_class=SigmundConfig):
    app = Flask(__name__, static_url_path='/static')
    app.config.from_object(config_class)
    # Initialize Flask-Session to activate Redis for session management
    Session(app)
    app.register_blueprint(app_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(store_blueprint, url_prefix='/store')
    app.register_blueprint(google_login_blueprint, url_prefix='/google_login')
    app.register_blueprint(public_blueprint, url_prefix='/public')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    # Initialize the database
    db.init_app(app)
    with app.app_context():
        db.create_all()
    # Initialize login manager
    login_manager = LoginManager()
    # Set up database migration
    migrate = Migrate(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)

    login_manager.init_app(app)

    # Backwards-compatible redirect from the old /subscribe/webhook to the
    # new /store/webhook. This ensures that webhooks continue to work even
    # if the Stripe dashboard hasn't been updated to the new URL yet.
    # Note: Stripe sends POST requests to the webhook, so we redirect all
    # methods and preserve the original request body and headers.
    @app.route('/subscribe/webhook', methods=['POST'])
    def legacy_subscribe_webhook():
        return redirect('/store/webhook', code=307)

    @app.after_request
    def log_request(response):
        user_agent = request.headers.get('User-Agent')
        if user_agent is not None and 'bot' not in user_agent.lower():
            logger.info(f'request: {request.full_path}')
        return response

    @app.errorhandler(NotFound)
    def handle_404(e):
        # Log the requested URL and method for non-existing routes
        logger.info(f'404 Not Found: {request.method} {request.path} '
                    f'Query: {request.query_string.decode("utf-8") or "-"} '
                    f'UA: {request.headers.get("User-Agent", "-")}')
        # Return a standard 404 page without stack trace
        return utils.render('404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Do not print tracebacks for HTTP 404 (already handled above)
        if isinstance(e, HTTPException) and e.code == 404:
            return handle_404(e)

        # Print full traceback for other exceptions
        logger.error("Unhandled exception during request processing:")
        traceback.print_exc()

        # Optionally, special-case other HTTPExceptions (e.g., 400/401/403)
        if isinstance(e, HTTPException):
            # Return the appropriate HTTP status without exposing a traceback
            return utils.render('error.html'), e.code

        # Non-HTTP exceptions -> 500
        return utils.render('error.html'), 500

    return app
