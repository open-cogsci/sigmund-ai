import os
os.environ['USE_FLASK_SQLALCHEMY'] = '1'
from flask import Flask, Config, request
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from . import config
from .redis_client import redis_client
from .routes import api_blueprint, app_blueprint, User, subscribe_blueprint, \
    google_login_blueprint, public_blueprint
from .database.models import db
import logging
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
    app.register_blueprint(subscribe_blueprint, url_prefix='/subscribe')
    app.register_blueprint(google_login_blueprint, url_prefix='/google_login')
    app.register_blueprint(public_blueprint, url_prefix='/public')
    # Initialize the databasea
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

    @app.after_request
    def log_request(response):
        user_agent = request.headers.get('User-Agent')
        if user_agent is not None and 'bot' not in user_agent.lower():
            logger.info(f'request: {request.full_path}')
        return response

    return app
