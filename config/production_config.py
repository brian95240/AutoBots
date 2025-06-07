# AutoBots Production Configuration
# Environment-specific settings for production deployment

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration for AutoBots system"""
    
    # Database Configuration
    DATABASE_URL = "postgresql://neondb_owner:npg_MdRXSxVkq46T@ep-white-leaf-a87kfssa-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 5000
    API_DEBUG = False
    API_WORKERS = 4
    
    # Monitoring Configuration
    MONITORING_HOST = "0.0.0.0"
    MONITORING_PORT = 5001
    MONITORING_DEBUG = False
    
    # Spider.cloud API Configuration
    SPIDER_API_KEY = os.getenv('SPIDER_API_KEY', 'your_spider_api_key_here')
    SPIDER_BASE_URL = "https://api.spider.cloud/v1"
    SPIDER_TIMEOUT = 30
    SPIDER_MAX_RETRIES = 3
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'autobots-production-secret-key-change-this')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Email/Alert Configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USE_TLS = True
    ALERT_EMAIL_USER = os.getenv('ALERT_EMAIL_USER', 'brian95240@gmail.com')
    ALERT_EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD', '')
    ALERT_RECIPIENTS = [
        'brian95240@gmail.com',
        # Add more recipients as needed
    ]
    
    # Bot Configuration
    BOT_CONFIGS = {
        'ScoutBot': {
            'enabled': True,
            'ocr_confidence_threshold': 0.95,
            'spider_ocr_enabled': True,
            'max_concurrent_requests': 10,
            'retry_attempts': 3,
            'timeout': 30
        },
        'SentinelBot': {
            'enabled': True,
            'threat_detection_threshold': 0.7,
            'max_response_time_ms': 50,
            'real_time_monitoring': True,
            'auto_block_critical': True
        },
        'AffiliateBot': {
            'enabled': True,
            'gdpr_compliance_mode': True,
            'auto_purge_enabled': True,
            'data_retention_days': 30,
            'consent_required': True
        },
        'OperatorBot': {
            'enabled': True,
            'vendor_automation': True,
            'max_concurrent_operations': 5,
            'operation_timeout': 300
        },
        'ArchitectBot': {
            'enabled': True,
            'performance_monitoring': True,
            'auto_scaling': True,
            'optimization_interval': 3600
        }
    }
    
    # Performance Thresholds
    PERFORMANCE_THRESHOLDS = {
        'cpu_usage_warning': 80.0,
        'cpu_usage_critical': 95.0,
        'memory_usage_warning': 85.0,
        'memory_usage_critical': 95.0,
        'disk_usage_warning': 90.0,
        'disk_usage_critical': 95.0,
        'response_time_warning': 2000,  # milliseconds
        'response_time_critical': 5000,
        'error_rate_warning': 5.0,  # percentage
        'error_rate_critical': 10.0,
        'threat_detection_rate_warning': 10,  # per minute
        'threat_detection_rate_critical': 20
    }
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "/var/log/autobots/autobots.log"
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Cache Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "autobots:"
    
    # Rate Limiting
    RATE_LIMIT_STORAGE_URL = REDIS_URL
    RATE_LIMIT_DEFAULT = "1000 per hour"
    RATE_LIMIT_API = "100 per minute"
    
    # Monitoring Intervals (seconds)
    MONITORING_INTERVALS = {
        'system_health': 60,
        'bot_status': 30,
        'database_health': 120,
        'api_health': 45,
        'security_metrics': 180,
        'performance_metrics': 30
    }
    
    # Data Retention Policies
    DATA_RETENTION = {
        'bot_logs': 30,  # days
        'system_metrics': 90,  # days
        'monitoring_alerts': 365,  # days
        'audit_logs': 2555,  # 7 years for compliance
        'threat_detections': 365,  # days
        'operations_history': 90  # days
    }
    
    # Backup Configuration
    BACKUP_ENABLED = True
    BACKUP_SCHEDULE = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = 30
    BACKUP_STORAGE_PATH = "/var/backups/autobots"
    
    # Health Check Configuration
    HEALTH_CHECK_ENDPOINTS = [
        '/api/health',
        '/api/bots/status',
        '/api/monitoring/health'
    ]
    
    # Feature Flags
    FEATURES = {
        'real_time_monitoring': True,
        'auto_scaling': True,
        'predictive_analytics': True,
        'advanced_threat_detection': True,
        'gdpr_auto_compliance': True,
        'performance_optimization': True,
        'email_alerts': True,
        'sms_alerts': False,  # Requires additional setup
        'slack_integration': False,  # Requires webhook setup
        'dashboard_analytics': True
    }
    
    # Docker Configuration
    DOCKER_REGISTRY = "docker.io"
    DOCKER_IMAGE_TAG = "latest"
    DOCKER_NETWORK = "autobots-network"
    
    # Deployment Configuration
    DEPLOYMENT_ENVIRONMENT = "production"
    DEPLOYMENT_VERSION = "1.0.0"
    DEPLOYMENT_TIMESTAMP = None  # Set during deployment
    
    @classmethod
    def validate_config(cls):
        """Validate production configuration"""
        errors = []
        
        # Check required environment variables
        required_env_vars = [
            'SPIDER_API_KEY',
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'ALERT_EMAIL_PASSWORD'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate database URL
        if not cls.DATABASE_URL or 'postgresql://' not in cls.DATABASE_URL:
            errors.append("Invalid DATABASE_URL configuration")
        
        # Validate email configuration
        if not cls.ALERT_EMAIL_USER or not cls.ALERT_RECIPIENTS:
            errors.append("Email alert configuration incomplete")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        return True

# Environment-specific configurations
class DevelopmentConfig(ProductionConfig):
    """Development configuration"""
    API_DEBUG = True
    MONITORING_DEBUG = True
    LOG_LEVEL = "DEBUG"
    FEATURES = {**ProductionConfig.FEATURES, 'email_alerts': False}

class TestingConfig(ProductionConfig):
    """Testing configuration"""
    DATABASE_URL = "postgresql://test_user:test_pass@localhost/autobots_test"
    API_DEBUG = True
    LOG_LEVEL = "DEBUG"
    FEATURES = {**ProductionConfig.FEATURES, 'email_alerts': False}

# Configuration factory
def get_config(environment='production'):
    """Get configuration based on environment"""
    configs = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig
    }
    
    config_class = configs.get(environment, ProductionConfig)
    
    # Validate configuration
    config_class.validate_config()
    
    return config_class

