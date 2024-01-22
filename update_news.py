#!/usr/bin/env python3
# update_news.py

"""
Script to update news articles in the database.

This module, when run, initializes the Flask application context and
triggers the process of fetching and saving the latest news articles
to the database.
"""
from flaskblog import create_app
from flaskblog.models import save_news_to_db

app = create_app()

with app.app_context():
    save_news_to_db()
