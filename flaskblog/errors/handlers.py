"""
This module defines error handlers for the Flask application.
It includes custom pages for different types of HTTP errors.
"""

from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def error_404(_error):
    """
    Handle 404 Not Found errors by showing a custom 404 error page.
    """
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def error_403(_error):
    """
    Handle 403 Forbidden errors by showing a custom 403 error page.
    """
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def error_500(_error):
    """
    Handle 500 Internal Server Error by showing a custom 500 error page.
    """
    return render_template('errors/500.html'), 500
