"""
Module for defining database models for the Flask application.

This module contains definitions for various database models
used throughout the Flask application, including user and post models.
"""

import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
#from flask import current_app as app
from flaskblog import db

logger = logging.getLogger(__name__)

class BaseNewsItem(db.Model):
    """
    Abstract Base Model
    """
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    by = db.Column(db.String(120), nullable=True)
    descendants = db.Column(db.Integer, nullable=True)
    kids = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    text = db.Column(db.String(5000), nullable=True)
    time = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(120), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)

    def dummy_method_one(self):
        """
        A dummy method
        """

    def dummy_method_two(self):
        """
        Another dummy method
        """


class User(db.Model):
    """
    User Model
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    nickname = db.Column(db.String(120), nullable=True)
    picture = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<User '{self.email}'>"

    def dummy_method_three(self):
        """
        Another dummy method
        """


class UserInteraction(db.Model):
    """
    User Interaction Mode
    """

    __tablename__ = 'user_interaction'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    interaction = db.Column(db.String(10), nullable=False)

    user = db.relationship('User', backref=db.backref('interactions', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('interactions', lazy='dynamic'))

    def dummy_method_four(self):
        """
        A dummy method
        """

    def dummy_method_five(self):
        """
        Another dummy method
        """


class NewsItem(BaseNewsItem):
    """
    NewsItem Model
    """
    def dummy_method_eight(self):
        """
        A dummy method
        """

    def dummy_method_nine(self):
        """
        Another dummy method
        """

class Post(BaseNewsItem):
    """
    Post Model
    """
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_email = db.Column(db.String(120), nullable=False)

    def dummy_method_six(self):
        """
        A dummy method
        """

    def dummy_method_seven(self):
        """
        Another dummy method
        """


def truncate_text_and_url(details):
    """
    Helper function to truncate text and URL
    """

    if 'text' in details and len(details['text']) > 5000:
        details['text'] = details['text'][:5000]

    if 'url' in details:
        details['url'] = details['url'][:500] if len(details['url']) > 500 else details['url']
    else:
        details['url'] = 'No URL available for this post.'

    return details

def fetch_hn_ids():
    """
    Fetch the top story IDs from Hacker News.
    """
    url = "https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()
    return []


def fetch_hn_news_details(item_id):
    """
    Fetch details for a Hacker News item by ID.
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json?print=pretty"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            details = response.json()
            details = truncate_text_and_url(details)
            logger.info("Details fetched for item %s", item_id)
            return details
    except requests.RequestException as e:
        logger.error("Error fetching details for item %s: %s", item_id, e)
    return None


def fetch_hn_news_details_bulk(item_ids):
    """
    Fetch details for a bulk of Hacker News items by their IDs.
    """
    #base_url = "https://hacker-news.firebaseio.com/v0/item/{}.json?print=pretty"

    with ThreadPoolExecutor(max_workers=10) as executor:
        details_list = list(executor.map(fetch_hn_news_details, item_ids))

    return details_list

logger = logging.getLogger(__name__)

def save_news_to_db():
    """
    Save the latest news items from Hacker News to the database.
    """
    try:
        ids = fetch_hn_ids()[:30]
        details_list = fetch_hn_news_details_bulk(ids)
        details_list = [details for details in details_list if details]
        existing_ids = {item.id for item in NewsItem.query.with_entities(NewsItem.id)
        .filter(NewsItem.id.in_(ids)).all()}

        new_details = [details for details in details_list if details['id'] not in existing_ids]

        news_items = []
        for details in new_details:
            details = truncate_text_and_url(details)
            if 'kids' in details:
                details['kids'] = ','.join(map(str, details['kids']))

            valid_keys = {k: v for k, v in details.items() if hasattr(NewsItem, k)}
            news_items.append(NewsItem(**valid_keys))

        if news_items:
            db.session.bulk_save_objects(news_items)
            db.session.commit()
    except requests.RequestException as e:
        logger.error("Error saving news to DB: %s", e)
