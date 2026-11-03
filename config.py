"""
Configuration module for Contract Language Simplifier
Handles environment-based settings and application configuration
"""

import os
from datetime import timedelta
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).parent.absolute()


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    # Local dev: SQLite in instance folder. Production/HF Spaces: set DATABASE_URL to a shared DB (e.g. PostgreSQL).
    _is_serverless = bool(os.environ.get('VERCEL')) or bool(os.environ.get('VERCEL_ENV')) or bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    _is_prod = os.environ.get('FLASK_ENV') == 'production' or _is_serverless
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _is_prod
    SESSION_COOKIE_SAMESITE = 'None' if _is_prod else 'Lax'

    # Database settings
    if _is_serverless:
        DB_PATH = '/tmp/database.db'
        UPLOAD_FOLDER = Path('/tmp/uploads')
        MODEL_CACHE_DIR = Path('/tmp/model_cache')
    else:
        DB_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')
        UPLOAD_FOLDER = BASE_DIR / 'uploads'
        MODEL_CACHE_DIR = BASE_DIR / 'model_cache'

    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLite Options for better concurrency
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = _is_prod
    JWT_COOKIE_SAMESITE = 'None' if _is_prod else 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False
    
    # Upload settings
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    
    # Model settings
    MODEL_CACHE_DIR = BASE_DIR / 'model_cache'
    SIMPLIFICATION_MODEL = 'google/flan-t5-small'
    SUMMARIZATION_MODEL = 'facebook/bart-large-cnn'
    
    # Simplification levels configuration
    SIMPLIFICATION_LEVELS = {
        'basic': {
            'prompt': 'Simplify the following legal text into very simple English that a 10-year-old can understand:',
            'max_length': 512,
            'temperature': 0.7
        },
        'intermediate': {
            'prompt': 'Simplify the following legal text into plain English:',
            'max_length': 512,
            'temperature': 0.5
        },
        'advanced': {
            'prompt': 'Rewrite the following legal text in clearer, more accessible language:',
            'max_length': 512,
            'temperature': 0.3
        }
    }
    
    # Readability thresholds
    READABILITY_THRESHOLDS = {
        'very_easy': (0, 6),
        'easy': (6, 9),
        'fairly_easy': (9, 12),
        'standard': (12, 14),
        'fairly_difficult': (14, 16),
        'difficult': (16, 18),
        'very_difficult': (18, 100)
    }
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    
    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration (Hugging Face Spaces, etc.). Requires DATABASE_URL and secrets."""
    DEBUG = False
    TESTING = False
    JWT_COOKIE_SECURE = True
    # Production database: prefer DATABASE_URL if provided; fall back to Config default
    _prod_db = os.environ.get('DATABASE_URL')
    if _prod_db and _prod_db.startswith('postgres://'):
        _prod_db = _prod_db.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _prod_db or Config.SQLALCHEMY_DATABASE_URI

    # Use environment secrets when available, otherwise fall back to safe defaults
    SECRET_KEY = os.environ.get('SECRET_KEY') or Config.SECRET_KEY
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or Config.JWT_SECRET_KEY


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
