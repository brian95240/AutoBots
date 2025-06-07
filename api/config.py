# AutoBots API Configuration

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'autobots-secret-key-change-in-production')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
    
    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Spider.cloud API configuration
    SPIDER_API_KEY = os.getenv('SPIDER_API_KEY', 'your-spider-api-key')
    SPIDER_BASE_URL = os.getenv('SPIDER_BASE_URL', 'https://api.spider.cloud/v1')
    
    # Email configuration for GDPR notifications
    EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', 'your-email@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-password')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@autobots.com')
    
    # Performance monitoring
    MONITORING_INTERVAL = int(os.getenv('MONITORING_INTERVAL', '60'))  # seconds
    OPTIMIZATION_INTERVAL = int(os.getenv('OPTIMIZATION_INTERVAL', '300'))  # seconds
    
    # Bot configuration
    SCOUT_BOT_ENABLED = os.getenv('SCOUT_BOT_ENABLED', 'true').lower() == 'true'
    SENTINEL_BOT_ENABLED = os.getenv('SENTINEL_BOT_ENABLED', 'true').lower() == 'true'
    AFFILIATE_BOT_ENABLED = os.getenv('AFFILIATE_BOT_ENABLED', 'true').lower() == 'true'
    OPERATOR_BOT_ENABLED = os.getenv('OPERATOR_BOT_ENABLED', 'true').lower() == 'true'
    ARCHITECT_BOT_ENABLED = os.getenv('ARCHITECT_BOT_ENABLED', 'true').lower() == 'true'
    
    # API rate limiting
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '100'))  # requests per minute
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'autobots.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production
    
    # Production database with connection pooling
    DATABASE_URL = os.getenv('DATABASE_URL')  # Must be set in production
    
    # Production Redis with authentication
    REDIS_URL = os.getenv('REDIS_URL')  # Must be set in production

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Test database
    DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'postgresql://user:pass@localhost/autobots_test')
    
    # Test Redis
    REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

