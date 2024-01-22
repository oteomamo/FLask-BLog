"""
This module contains unit tests for the Flask Blog application.
"""

import pytest
from flaskblog import create_app, db
from flaskblog.models import User, Post

# Setup for the test environment
@pytest.fixture
def app():
    """
    Create and configure a new app instance for each test.
    """
    _app = create_app()
    _app.config['TESTING'] = True
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return _app

@pytest.fixture
def client(app):
    """
    A test client for the app.
    """
    with app.test_client() as _client:
        with app.app_context():
            db.create_all()
        yield _client

@pytest.fixture
def clean_db(app):
    """
    Set up a clean database before each test.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()

# Test for the home function
def test_home(client):
    """
    Test the home route.
    """
    # Action: make a request to the home route
    response = client.get('/home')

    # Assertions
    assert response.status_code == 200

def test_update_interaction(client):
    """
    Test the update interaction functionality.
    """
    with client.application.app_context():
        # Ensure unique data for each test
        user = User(email='unique-test@example.com', name='Test User')
        post = Post(title='Test Post', content='Test Content', user_email='unique-test@example.com')
        db.session.add(user)
        db.session.add(post)
        db.session.commit()
        post_id = post.id

        # Mocking a user session
        with client.session_transaction() as session:
            session['user'] = {'id': user.id, 'email': 'unique-test@example.com'}

    # Action: send a POST request to update interaction
    response = client.post('/update_interaction', json={
        'id': post_id,
        'action': 'like'
    })

    # Assertions
    assert response.status_code == 200
