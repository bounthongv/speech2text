import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Usage limits - More generous for Lao community
    FREE_TIER_MINUTES = int(os.environ.get('FREE_TIER_MINUTES', 60))  # 1 hour
    EMAIL_TIER_MINUTES = int(os.environ.get('EMAIL_TIER_MINUTES', 240))  # 4 hours
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    RESULTS_FOLDER = 'results'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Buy Me a Coffee settings
    BMC_USERNAME = os.environ.get('BMC_USERNAME', 'laospeech')
    BMC_URL = f"https://buymeacoffee.com/{BMC_USERNAME}"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
