import os
from datetime import timedelta

class Config:
    """Base Configuration class"""
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Database Settings (Hybrid Local/Cloud switch)
    # Default to local SQLite, switch to Postgres if DATABASE_URL is set in environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'legal_ai.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # Session / Security Settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in HTTPS Production
    
    # API Rate Limiting defaults
    API_RATE_LIMIT = "60 per minute"

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory DB for fast tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS session cookie

# Dictionary mapping configurations
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
