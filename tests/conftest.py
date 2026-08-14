import pytest
import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from database import db as _db, User, UserSetting

@pytest.fixture
def app():
    """Create and configure a clean Flask application for testing"""
    # Overwrite configuration for testing profile
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        # Teardown
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the application"""
    return app.test_client()

@pytest.fixture
def db(app):
    """A reference to the database object"""
    return _db

@pytest.fixture
def test_user(db):
    """Create a default test user with settings in the in-memory database"""
    user = User(email='test@example.com', full_name='Test User', role='Analyst')
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    
    settings = UserSetting(
        user_id=user.id,
        default_summary_length='medium',
        bias_threshold=0.3,
        pii_masking_enabled=True
    )
    db.session.add(settings)
    db.session.commit()
    return user
