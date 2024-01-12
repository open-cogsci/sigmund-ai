import logging
from flask import Flask, Config
from flask_login import LoginManager
from . import config
from .routes import api_blueprint, app_blueprint

from .database.models import db
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


class HeymansConfig(Config):
    SECRET_KEY = config.flask_secret_key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///heymans.db'


def create_app(config_class=HeymansConfig):
    app = Flask(__name__, static_url_path='/static')
    app.config.from_object(config_class)
    app.register_blueprint(app_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    # Initialize the database
    db.init_app(app)
    with app.app_context():
        db.create_all()
    # Initialize login manager
    login_manager = LoginManager()
    
    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)
        
    login_manager.init_app(app)
    return app
