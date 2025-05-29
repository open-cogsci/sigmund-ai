import logging
import requests
import json
import base64
from flask import redirect, Blueprint, request, session, jsonify
from flask_login import login_user
from . import User
from .. import config
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
logger = logging.getLogger('sigmund')
google_login_blueprint = Blueprint('google_login', __name__)


def get_google_provider_cfg():
    return requests.get(config.google_discovery_url).json()
    
    
@google_login_blueprint.route("/")
def login():
    if not config.google_login_enabled:
        return jsonify(success=False, message="Login method disabled"), 403
    from oauthlib.oauth2 import WebApplicationClient
    client = WebApplicationClient(config.google_client_id)
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url.replace('http:', 'https:') + "callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@google_login_blueprint.route("/callback")
def callback():
    from oauthlib.oauth2 import WebApplicationClient
    client = WebApplicationClient(config.google_client_id)
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    try:
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace('http:', 'https:'),
            redirect_url=request.base_url.replace('http:', 'https:'),
            code=code
        )
    except Exception as e:
        logger.warning(f'failed to prepare token request: {e}')
        return redirect('/')
        
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(config.google_client_id, config.google_client_secret),
    )
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))    
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    unique_id = userinfo_response.json()["sub"]
    username = userinfo_response.json()["given_name"]
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if not userinfo_response.json().get("email_verified"):
        logger.info(f'google log-in failed ({username})')
        return redirect('/login_failed')
    logger.info(f'google log-in successful ({username})')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=32,
                     salt=config.encryption_salt,
                     iterations=100000,
                     backend=default_backend())
    session['encryption_key'] = base64.urlsafe_b64encode(
        kdf.derive(unique_id.encode()))
    # We use only part of the unique id, so that the username doesn't allow us
    # to derive the encryption key
    username = f'{username} (google)::{unique_id[:10]}'
    user = User(username)
    login_user(user)
    logger.info(f'initializing encryption key')    
    return redirect('/')
