"""
This module initializes the Flask application and its extensions. It also
registers the necessary blueprints and sets up OAuth for authentication.
"""

from datetime import datetime
from os import environ as env

from flask import Flask, make_response, jsonify, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth

from flaskblog.config import Config

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()

def create_app(config_class=Config):
    """
    Create and configure an instance of the Flask application.
    Args:
        config_class: The configuration class to use for the application.

    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    app.config['SECRET_KEY'] = env.get("APP_SECRET_KEY") or 'a-very-secret-key'

    oauth.init_app(app)
    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
        redirect_uri='https://cop4521.oteomamo.com/callback'
    )

    @app.template_filter('datetimeformat')
    def datetimeformat(value, date_format='%Y-%m-%d %H:%M'):
        try:
            timestamp = int(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value).strftime(date_format)
            except ValueError:
                return value

        return datetime.fromtimestamp(timestamp).strftime(date_format)
    
    @app.after_request
    def set_security_headers(response):
        """
        Set security headers on each response.
        """
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # or 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    # pylint: disable=import-outside-toplevel
    from flaskblog.main.routes import main
    from flaskblog.errors.handlers import errors
    # pylint: enable=import-outside-toplevel
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
