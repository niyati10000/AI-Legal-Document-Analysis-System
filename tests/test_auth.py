import pytest
from flask import session
from database import User, AuditLog

def test_register_user(client, db):
    """Test user registration flow"""
    response = client.post('/register', data={
        'full_name': 'Jane Doe',
        'email': 'jane@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Registration successful" in response.data
    
    # Assert database persistence
    user = User.query.filter_by(email='jane@example.com').first()
    assert user is not None
    assert user.full_name == 'Jane Doe'
    assert user.role == 'Admin'  # First user in database gets Admin role

def test_register_duplicate_email(client, test_user):
    """Test registration with an already existing email address"""
    response = client.post('/register', data={
        'full_name': 'Another Name',
        'email': 'test@example.com', # Duplicate
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"already registered" in response.data

def test_login_user(client, test_user):
    """Test successful user login"""
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Welcome back to LexAI" in response.data
    
    # Assert audit log entry
    log = AuditLog.query.filter_by(action='LOGIN').first()
    assert log is not None
    assert 'test@example.com' in log.details

def test_login_invalid_credentials(client, test_user):
    """Test login failure with incorrect credentials"""
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

def test_logout_user(client, test_user):
    """Test user logout clears sessions"""
    # Log in first
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out successfully" in response.data
    
    # Assert session is empty
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
