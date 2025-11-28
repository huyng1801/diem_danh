"""
Configuration File for Face-ID Attendance System
Cấu hình cho hệ thống điểm danh học sinh bằng nhận diện khuôn mặt
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

class Config:
    """Base configuration"""
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Flask-SQLAlchemy Settings
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:123456@localhost:5432/face_id_attendance'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # JWT Configuration
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    JWT_REFRESH_EXPIRATION_HOURS = 30 * 24  # 30 days
    
    # Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/uploads')
    
    # Email Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@faceid.local')
    
    # Application URL (for email links, etc)
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    
    # Face Recognition Settings
    MIN_FACE_IMAGES = 3
    MIN_FACE_CONFIDENCE = 0.8
    DEFAULT_FACE_CONFIDENCE = 0.6
    FACE_DETECTION_MODEL = 'hog'  # 'hog' or 'cnn'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Cache
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_TYPE = 'simple'


# ============================================================================
# DEVELOPMENT CONFIGURATION
# ============================================================================

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    TESTING = False


# ============================================================================
# PRODUCTION CONFIGURATION
# ============================================================================

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Override database URL for production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:123456@localhost:5432/face_id_attendance_prod'
    )


# ============================================================================
# TESTING CONFIGURATION
# ============================================================================

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Disable email for testing
    MAIL_SUPPRESS_SEND = True


# ============================================================================
# CONFIGURATION SELECTION
# ============================================================================

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
