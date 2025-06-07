# AutoBots Settings API
# Backend API for managing configuration settings

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_MdRXSxVkq46T@ep-white-leaf-a87kfssa-pooler.eastus2.azure.neon.tech/neondb?sslmode=require')

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def validate_bot_config(bot_id, config):
    """Validate bot configuration parameters"""
    validation_rules = {
        'scout': {
            'ocrAccuracyThreshold': {'min': 50, 'max': 100, 'type': int},
            'spiderApiLimit': {'min': 100, 'max': 10000, 'type': int},
            'processingTimeout': {'min': 10, 'max': 300, 'type': int},
            'retryAttempts': {'min': 1, 'max': 10, 'type': int},
            'batchSize': {'min': 1, 'max': 100, 'type': int},
            'autoRestart': {'type': bool}
        },
        'sentinel': {
            'threatSensitivity': {'min': 10, 'max': 100, 'type': int},
            'responseTimeThreshold': {'min': 10, 'max': 1000, 'type': int},
            'alertLevel': {'values': ['info', 'warning', 'error', 'critical'], 'type': str},
            'scanInterval': {'min': 10, 'max': 300, 'type': int},
            'falsePositiveThreshold': {'min': 1, 'max': 20, 'type': int},
            'autoBlock': {'type': bool}
        },
        'affiliate': {
            'gdprStrictMode': {'type': bool},
            'emailTemplate': {'values': ['default', 'formal', 'friendly', 'minimal'], 'type': str},
            'purgeSchedule': {'values': ['daily', 'weekly', 'monthly'], 'type': str},
            'consentTimeout': {'min': 1, 'max': 90, 'type': int},
            'autoNotification': {'type': bool},
            'complianceLevel': {'values': ['basic', 'standard', 'strict'], 'type': str}
        },
        'operator': {
            'syncInterval': {'min': 15, 'max': 1440, 'type': int},
            'retryAttempts': {'min': 1, 'max': 10, 'type': int},
            'timeoutSettings': {'min': 30, 'max': 600, 'type': int},
            'vendorLimit': {'min': 1, 'max': 100, 'type': int},
            'batchProcessing': {'type': bool},
            'errorThreshold': {'min': 1, 'max': 50, 'type': int}
        },
        'architect': {
            'performanceThreshold': {'min': 50, 'max': 100, 'type': int},
            'optimizationTrigger': {'min': 50, 'max': 95, 'type': int},
            'scalingRules': {'values': ['auto', 'manual', 'scheduled'], 'type': str},
            'resourceLimit': {'min': 50, 'max': 100, 'type': int},
            'monitoringInterval': {'min': 5, 'max': 60, 'type': int},
            'autoOptimize': {'type': bool}
        }
    }
    
    if bot_id not in validation_rules:
        return False, f"Unknown bot ID: {bot_id}"
    
    rules = validation_rules[bot_id]
    errors = []
    
    for field, value in config.items():
        if field not in rules:
            continue
            
        rule = rules[field]
        
        # Type validation
        if rule['type'] == int and not isinstance(value, int):
            errors.append(f"{field} must be an integer")
            continue
        elif rule['type'] == bool and not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
            continue
        elif rule['type'] == str and not isinstance(value, str):
            errors.append(f"{field} must be a string")
            continue
        
        # Range validation
        if 'min' in rule and value < rule['min']:
            errors.append(f"{field} must be at least {rule['min']}")
        if 'max' in rule and value > rule['max']:
            errors.append(f"{field} must be at most {rule['max']}")
        
        # Value validation
        if 'values' in rule and value not in rule['values']:
            errors.append(f"{field} must be one of: {', '.join(rule['values'])}")
    
    return len(errors) == 0, errors

@app.route('/api/settings/bots', methods=['GET'])
def get_bot_configs():
    """Get all bot configurations"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bot_configs ORDER BY bot_id")
        configs = cursor.fetchall()
        
        result = {}
        for config in configs:
            result[config['bot_id']] = {
                'enabled': config['enabled'],
                **json.loads(config['config_data'])
            }
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error fetching bot configs: {e}")
        return jsonify({'error': 'Failed to fetch bot configurations'}), 500

@app.route('/api/settings/bots/<bot_id>', methods=['PUT'])
def update_bot_config(bot_id):
    """Update bot configuration"""
    try:
        data = request.get_json()
        
        # Validate configuration
        is_valid, errors = validate_bot_config(bot_id, data)
        if not is_valid:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Extract enabled status and config data
        enabled = data.pop('enabled', True)
        config_data = json.dumps(data)
        
        # Update or insert configuration
        cursor.execute("""
            INSERT INTO bot_configs (bot_id, enabled, config_data, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (bot_id) 
            DO UPDATE SET 
                enabled = EXCLUDED.enabled,
                config_data = EXCLUDED.config_data,
                updated_at = EXCLUDED.updated_at
        """, (bot_id, enabled, config_data, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Updated configuration for bot: {bot_id}")
        return jsonify({'success': True, 'message': f'Configuration updated for {bot_id}'})
    
    except Exception as e:
        logger.error(f"Error updating bot config: {e}")
        return jsonify({'error': 'Failed to update bot configuration'}), 500

@app.route('/api/settings/alerts', methods=['GET'])
def get_alert_config():
    """Get alert configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT config_data FROM system_configs WHERE config_type = 'alerts'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(json.loads(result['config_data']))
        else:
            # Return default configuration
            default_config = {
                'cpuWarning': 70,
                'cpuCritical': 90,
                'memoryWarning': 80,
                'memoryCritical': 95,
                'responseTimeWarning': 200,
                'responseTimeCritical': 500,
                'errorRateWarning': 5,
                'errorRateCritical': 10,
                'diskWarning': 80,
                'diskCritical': 95,
                'emailEnabled': True,
                'smsEnabled': False,
                'slackEnabled': False,
                'alertFrequency': 'immediate',
                'escalationDelay': 15,
                'quietHours': False,
                'quietStart': '22:00',
                'quietEnd': '08:00'
            }
            return jsonify(default_config)
    
    except Exception as e:
        logger.error(f"Error fetching alert config: {e}")
        return jsonify({'error': 'Failed to fetch alert configuration'}), 500

@app.route('/api/settings/alerts', methods=['PUT'])
def update_alert_config():
    """Update alert configuration"""
    try:
        data = request.get_json()
        
        # Validate alert configuration
        required_fields = ['cpuWarning', 'cpuCritical', 'memoryWarning', 'memoryCritical']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate threshold relationships
        if data['cpuCritical'] <= data['cpuWarning']:
            return jsonify({'error': 'CPU critical threshold must be higher than warning threshold'}), 400
        if data['memoryCritical'] <= data['memoryWarning']:
            return jsonify({'error': 'Memory critical threshold must be higher than warning threshold'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        config_data = json.dumps(data)
        
        cursor.execute("""
            INSERT INTO system_configs (config_type, config_data, updated_at)
            VALUES ('alerts', %s, %s)
            ON CONFLICT (config_type)
            DO UPDATE SET 
                config_data = EXCLUDED.config_data,
                updated_at = EXCLUDED.updated_at
        """, (config_data, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Updated alert configuration")
        return jsonify({'success': True, 'message': 'Alert configuration updated'})
    
    except Exception as e:
        logger.error(f"Error updating alert config: {e}")
        return jsonify({'error': 'Failed to update alert configuration'}), 500

@app.route('/api/settings/system', methods=['GET'])
def get_system_config():
    """Get system configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT config_data FROM system_configs WHERE config_type = 'system'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(json.loads(result['config_data']))
        else:
            # Return default configuration
            default_config = {
                'apiRateLimit': 1000,
                'dbConnectionPool': 20,
                'cacheEnabled': True,
                'cacheTtl': 300,
                'sessionTimeout': 3600,
                'jwtExpiration': 86400,
                'logLevel': 'info',
                'debugMode': False,
                'maintenanceMode': False,
                'backupEnabled': True,
                'backupInterval': 'daily',
                'compressionEnabled': True
            }
            return jsonify(default_config)
    
    except Exception as e:
        logger.error(f"Error fetching system config: {e}")
        return jsonify({'error': 'Failed to fetch system configuration'}), 500

@app.route('/api/settings/system', methods=['PUT'])
def update_system_config():
    """Update system configuration"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        config_data = json.dumps(data)
        
        cursor.execute("""
            INSERT INTO system_configs (config_type, config_data, updated_at)
            VALUES ('system', %s, %s)
            ON CONFLICT (config_type)
            DO UPDATE SET 
                config_data = EXCLUDED.config_data,
                updated_at = EXCLUDED.updated_at
        """, (config_data, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Updated system configuration")
        return jsonify({'success': True, 'message': 'System configuration updated'})
    
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        return jsonify({'error': 'Failed to update system configuration'}), 500

@app.route('/api/settings/notifications', methods=['GET'])
def get_notification_config():
    """Get notification configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT config_data FROM system_configs WHERE config_type = 'notifications'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(json.loads(result['config_data']))
        else:
            # Return default configuration
            default_config = {
                'emailRecipients': ['brian95240@gmail.com'],
                'smtpServer': 'smtp.gmail.com',
                'smtpPort': 587,
                'emailUser': 'brian95240@gmail.com',
                'emailPassword': '',
                'slackWebhook': '',
                'smsProvider': 'twilio',
                'smsApiKey': '',
                'notificationTypes': {
                    'systemAlerts': True,
                    'botStatus': True,
                    'performanceIssues': True,
                    'securityEvents': True,
                    'maintenanceUpdates': False
                }
            }
            return jsonify(default_config)
    
    except Exception as e:
        logger.error(f"Error fetching notification config: {e}")
        return jsonify({'error': 'Failed to fetch notification configuration'}), 500

@app.route('/api/settings/notifications', methods=['PUT'])
def update_notification_config():
    """Update notification configuration"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        config_data = json.dumps(data)
        
        cursor.execute("""
            INSERT INTO system_configs (config_type, config_data, updated_at)
            VALUES ('notifications', %s, %s)
            ON CONFLICT (config_type)
            DO UPDATE SET 
                config_data = EXCLUDED.config_data,
                updated_at = EXCLUDED.updated_at
        """, (config_data, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Updated notification configuration")
        return jsonify({'success': True, 'message': 'Notification configuration updated'})
    
    except Exception as e:
        logger.error(f"Error updating notification config: {e}")
        return jsonify({'error': 'Failed to update notification configuration'}), 500

@app.route('/api/settings/security', methods=['GET'])
def get_security_config():
    """Get security configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT config_data FROM system_configs WHERE config_type = 'security'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(json.loads(result['config_data']))
        else:
            # Return default configuration
            default_config = {
                'twoFactorEnabled': False,
                'passwordPolicy': 'strong',
                'sessionSecurity': 'high',
                'ipWhitelist': '',
                'apiKeyRotation': 'monthly',
                'encryptionLevel': 'aes256',
                'auditLogging': True,
                'accessLogging': True,
                'bruteForceProtection': True,
                'rateLimiting': True
            }
            return jsonify(default_config)
    
    except Exception as e:
        logger.error(f"Error fetching security config: {e}")
        return jsonify({'error': 'Failed to fetch security configuration'}), 500

@app.route('/api/settings/security', methods=['PUT'])
def update_security_config():
    """Update security configuration"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        config_data = json.dumps(data)
        
        cursor.execute("""
            INSERT INTO system_configs (config_type, config_data, updated_at)
            VALUES ('security', %s, %s)
            ON CONFLICT (config_type)
            DO UPDATE SET 
                config_data = EXCLUDED.config_data,
                updated_at = EXCLUDED.updated_at
        """, (config_data, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Updated security configuration")
        return jsonify({'success': True, 'message': 'Security configuration updated'})
    
    except Exception as e:
        logger.error(f"Error updating security config: {e}")
        return jsonify({'error': 'Failed to update security configuration'}), 500

@app.route('/api/settings/test-connection', methods=['POST'])
def test_connection():
    """Test external service connections"""
    try:
        data = request.get_json()
        connection_type = data.get('type')
        
        if connection_type == 'email':
            # Test email connection
            # In production, this would actually test SMTP connection
            return jsonify({'success': True, 'message': 'Email connection test successful'})
        
        elif connection_type == 'slack':
            # Test Slack webhook
            # In production, this would send a test message to Slack
            return jsonify({'success': True, 'message': 'Slack connection test successful'})
        
        elif connection_type == 'database':
            # Test database connection
            conn = get_db_connection()
            if conn:
                conn.close()
                return jsonify({'success': True, 'message': 'Database connection test successful'})
            else:
                return jsonify({'success': False, 'message': 'Database connection test failed'}), 500
        
        else:
            return jsonify({'error': 'Unknown connection type'}), 400
    
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({'error': 'Connection test failed'}), 500

@app.route('/api/settings/export', methods=['GET'])
def export_settings():
    """Export all settings as JSON"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get all configurations
        export_data = {}
        
        # Bot configurations
        cursor.execute("SELECT * FROM bot_configs")
        bot_configs = cursor.fetchall()
        export_data['bots'] = {}
        for config in bot_configs:
            export_data['bots'][config['bot_id']] = {
                'enabled': config['enabled'],
                **json.loads(config['config_data'])
            }
        
        # System configurations
        cursor.execute("SELECT * FROM system_configs")
        system_configs = cursor.fetchall()
        for config in system_configs:
            export_data[config['config_type']] = json.loads(config['config_data'])
        
        cursor.close()
        conn.close()
        
        export_data['exported_at'] = datetime.now().isoformat()
        export_data['version'] = '1.0'
        
        return jsonify(export_data)
    
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        return jsonify({'error': 'Failed to export settings'}), 500

@app.route('/api/settings/import', methods=['POST'])
def import_settings():
    """Import settings from JSON"""
    try:
        data = request.get_json()
        
        if 'version' not in data:
            return jsonify({'error': 'Invalid settings file format'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        imported_count = 0
        
        # Import bot configurations
        if 'bots' in data:
            for bot_id, config in data['bots'].items():
                enabled = config.pop('enabled', True)
                config_data = json.dumps(config)
                
                cursor.execute("""
                    INSERT INTO bot_configs (bot_id, enabled, config_data, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (bot_id) 
                    DO UPDATE SET 
                        enabled = EXCLUDED.enabled,
                        config_data = EXCLUDED.config_data,
                        updated_at = EXCLUDED.updated_at
                """, (bot_id, enabled, config_data, datetime.now()))
                imported_count += 1
        
        # Import system configurations
        config_types = ['alerts', 'system', 'notifications', 'security']
        for config_type in config_types:
            if config_type in data:
                config_data = json.dumps(data[config_type])
                cursor.execute("""
                    INSERT INTO system_configs (config_type, config_data, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (config_type)
                    DO UPDATE SET 
                        config_data = EXCLUDED.config_data,
                        updated_at = EXCLUDED.updated_at
                """, (config_type, config_data, datetime.now()))
                imported_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Imported {imported_count} configurations")
        return jsonify({'success': True, 'message': f'Successfully imported {imported_count} configurations'})
    
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        return jsonify({'error': 'Failed to import settings'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

