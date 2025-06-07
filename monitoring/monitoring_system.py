# AutoBots Monitoring and Alerting System
# Real-time monitoring with email/SMS alerts and dashboard integration

import asyncio
import asyncpg
import smtplib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import os
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    SYSTEM_HEALTH = "system_health"
    BOT_STATUS = "bot_status"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATABASE = "database"
    API_HEALTH = "api_health"

@dataclass
class Alert:
    id: str
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AutoBotsMonitor:
    def __init__(self, database_url: str, config: Dict[str, Any]):
        self.database_url = database_url
        self.config = config
        self.db_pool = None
        self.active_alerts = {}
        self.alert_history = []
        
        # Email configuration
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.email_user = config.get('email_user')
        self.email_password = config.get('email_password')
        self.alert_recipients = config.get('alert_recipients', [])
        
        # Monitoring thresholds
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 2000,  # milliseconds
            'error_rate': 5.0,  # percentage
            'threat_detection_rate': 10,  # per minute
            'database_connections': 80,  # percentage of max
        }
        
        # Bot health check intervals (seconds)
        self.check_intervals = {
            'system_health': 60,
            'bot_status': 30,
            'database_health': 120,
            'api_health': 45,
            'security_metrics': 180,
        }

    async def initialize(self):
        """Initialize the monitoring system"""
        try:
            # Create database connection pool
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            logger.info("✅ Database connection pool initialized")
            
            # Create monitoring tables if they don't exist
            await self.create_monitoring_tables()
            
            # Start monitoring tasks
            await self.start_monitoring_tasks()
            
            logger.info("🚀 AutoBots Monitoring System initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring system: {e}")
            raise

    async def create_monitoring_tables(self):
        """Create additional monitoring tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id VARCHAR(100) PRIMARY KEY,
                    level VARCHAR(20) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMPTZ
                );
                
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_created_at 
                ON monitoring_alerts(created_at);
                
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_level 
                ON monitoring_alerts(level);
                
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_resolved 
                ON monitoring_alerts(resolved);
            """)

    async def start_monitoring_tasks(self):
        """Start all monitoring background tasks"""
        tasks = [
            asyncio.create_task(self.monitor_system_health()),
            asyncio.create_task(self.monitor_bot_status()),
            asyncio.create_task(self.monitor_database_health()),
            asyncio.create_task(self.monitor_api_health()),
            asyncio.create_task(self.monitor_security_metrics()),
            asyncio.create_task(self.process_alert_queue()),
        ]
        
        logger.info("🔄 Started all monitoring tasks")
        return tasks

    async def monitor_system_health(self):
        """Monitor overall system health metrics"""
        while True:
            try:
                # Simulate system metrics collection
                metrics = await self.collect_system_metrics()
                
                # Check CPU usage
                if metrics['cpu_usage'] > self.thresholds['cpu_usage']:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        AlertType.SYSTEM_HEALTH,
                        "High CPU Usage",
                        f"CPU usage is {metrics['cpu_usage']:.1f}% (threshold: {self.thresholds['cpu_usage']}%)",
                        {"cpu_usage": metrics['cpu_usage']}
                    )
                
                # Check memory usage
                if metrics['memory_usage'] > self.thresholds['memory_usage']:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        AlertType.SYSTEM_HEALTH,
                        "High Memory Usage",
                        f"Memory usage is {metrics['memory_usage']:.1f}% (threshold: {self.thresholds['memory_usage']}%)",
                        {"memory_usage": metrics['memory_usage']}
                    )
                
                # Store metrics in database
                await self.store_metrics(metrics)
                
                await asyncio.sleep(self.check_intervals['system_health'])
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {e}")
                await asyncio.sleep(30)

    async def monitor_bot_status(self):
        """Monitor individual bot status and performance"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check bot configurations and activity
                    bots = await conn.fetch("""
                        SELECT bot_name, is_active, config_data, updated_at
                        FROM bot_configs
                        WHERE is_active = TRUE
                    """)
                    
                    for bot in bots:
                        # Check if bot has been updated recently (last 5 minutes)
                        last_update = bot['updated_at']
                        if datetime.now() - last_update.replace(tzinfo=None) > timedelta(minutes=5):
                            await self.create_alert(
                                AlertLevel.WARNING,
                                AlertType.BOT_STATUS,
                                f"{bot['bot_name']} Inactive",
                                f"Bot {bot['bot_name']} hasn't reported status in over 5 minutes",
                                {"bot_name": bot['bot_name'], "last_update": last_update.isoformat()}
                            )
                    
                    # Check recent bot logs for errors
                    recent_errors = await conn.fetch("""
                        SELECT bot_name, COUNT(*) as error_count
                        FROM bot_logs
                        WHERE level IN ('ERROR', 'CRITICAL')
                        AND timestamp >= NOW() - INTERVAL '10 minutes'
                        GROUP BY bot_name
                        HAVING COUNT(*) > 3
                    """)
                    
                    for error_record in recent_errors:
                        await self.create_alert(
                            AlertLevel.ERROR,
                            AlertType.BOT_STATUS,
                            f"{error_record['bot_name']} High Error Rate",
                            f"Bot {error_record['bot_name']} has {error_record['error_count']} errors in the last 10 minutes",
                            {"bot_name": error_record['bot_name'], "error_count": error_record['error_count']}
                        )
                
                await asyncio.sleep(self.check_intervals['bot_status'])
                
            except Exception as e:
                logger.error(f"Error in bot status monitoring: {e}")
                await asyncio.sleep(30)

    async def monitor_database_health(self):
        """Monitor database performance and health"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check database connection count
                    db_stats = await conn.fetchrow("""
                        SELECT 
                            numbackends as active_connections,
                            xact_commit as transactions_committed,
                            xact_rollback as transactions_rolled_back,
                            blks_read as blocks_read,
                            blks_hit as blocks_hit
                        FROM pg_stat_database 
                        WHERE datname = current_database()
                    """)
                    
                    # Calculate cache hit ratio
                    total_blocks = db_stats['blocks_read'] + db_stats['blocks_hit']
                    cache_hit_ratio = (db_stats['blocks_hit'] / total_blocks * 100) if total_blocks > 0 else 100
                    
                    # Check for low cache hit ratio
                    if cache_hit_ratio < 95:
                        await self.create_alert(
                            AlertLevel.WARNING,
                            AlertType.DATABASE,
                            "Low Database Cache Hit Ratio",
                            f"Database cache hit ratio is {cache_hit_ratio:.1f}% (should be >95%)",
                            {"cache_hit_ratio": cache_hit_ratio}
                        )
                    
                    # Check for high rollback rate
                    total_transactions = db_stats['transactions_committed'] + db_stats['transactions_rolled_back']
                    rollback_rate = (db_stats['transactions_rolled_back'] / total_transactions * 100) if total_transactions > 0 else 0
                    
                    if rollback_rate > 5:
                        await self.create_alert(
                            AlertLevel.WARNING,
                            AlertType.DATABASE,
                            "High Database Rollback Rate",
                            f"Database rollback rate is {rollback_rate:.1f}% (should be <5%)",
                            {"rollback_rate": rollback_rate}
                        )
                    
                    # Store database metrics
                    await self.store_database_metrics(db_stats, cache_hit_ratio, rollback_rate)
                
                await asyncio.sleep(self.check_intervals['database_health'])
                
            except Exception as e:
                logger.error(f"Error in database health monitoring: {e}")
                await asyncio.sleep(60)

    async def monitor_api_health(self):
        """Monitor API endpoints health and response times"""
        while True:
            try:
                # Test API endpoints
                endpoints = [
                    '/api/health',
                    '/api/bots/status',
                    '/api/metrics',
                    '/api/threats/recent'
                ]
                
                async with aiohttp.ClientSession() as session:
                    for endpoint in endpoints:
                        start_time = datetime.now()
                        try:
                            async with session.get(f"http://localhost:5000{endpoint}", timeout=10) as response:
                                response_time = (datetime.now() - start_time).total_seconds() * 1000
                                
                                if response.status != 200:
                                    await self.create_alert(
                                        AlertLevel.ERROR,
                                        AlertType.API_HEALTH,
                                        f"API Endpoint Error: {endpoint}",
                                        f"Endpoint {endpoint} returned status {response.status}",
                                        {"endpoint": endpoint, "status_code": response.status}
                                    )
                                
                                if response_time > self.thresholds['response_time']:
                                    await self.create_alert(
                                        AlertLevel.WARNING,
                                        AlertType.PERFORMANCE,
                                        f"Slow API Response: {endpoint}",
                                        f"Endpoint {endpoint} took {response_time:.0f}ms (threshold: {self.thresholds['response_time']}ms)",
                                        {"endpoint": endpoint, "response_time": response_time}
                                    )
                                
                        except asyncio.TimeoutError:
                            await self.create_alert(
                                AlertLevel.ERROR,
                                AlertType.API_HEALTH,
                                f"API Timeout: {endpoint}",
                                f"Endpoint {endpoint} timed out after 10 seconds",
                                {"endpoint": endpoint}
                            )
                        except Exception as e:
                            await self.create_alert(
                                AlertLevel.ERROR,
                                AlertType.API_HEALTH,
                                f"API Connection Error: {endpoint}",
                                f"Failed to connect to {endpoint}: {str(e)}",
                                {"endpoint": endpoint, "error": str(e)}
                            )
                
                await asyncio.sleep(self.check_intervals['api_health'])
                
            except Exception as e:
                logger.error(f"Error in API health monitoring: {e}")
                await asyncio.sleep(45)

    async def monitor_security_metrics(self):
        """Monitor security-related metrics and threats"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check recent threat detections
                    recent_threats = await conn.fetchrow("""
                        SELECT COUNT(*) as threat_count
                        FROM threat_detections
                        WHERE detected_at >= NOW() - INTERVAL '1 minute'
                        AND false_positive = FALSE
                    """)
                    
                    if recent_threats['threat_count'] > self.thresholds['threat_detection_rate']:
                        await self.create_alert(
                            AlertLevel.CRITICAL,
                            AlertType.SECURITY,
                            "High Threat Detection Rate",
                            f"Detected {recent_threats['threat_count']} threats in the last minute (threshold: {self.thresholds['threat_detection_rate']})",
                            {"threat_count": recent_threats['threat_count']}
                        )
                    
                    # Check for critical threats
                    critical_threats = await conn.fetch("""
                        SELECT threat_id, threat_type, threat_level, detected_at
                        FROM threat_detections
                        WHERE threat_level = 'CRITICAL'
                        AND detected_at >= NOW() - INTERVAL '5 minutes'
                        AND resolved_at IS NULL
                    """)
                    
                    for threat in critical_threats:
                        await self.create_alert(
                            AlertLevel.CRITICAL,
                            AlertType.SECURITY,
                            f"Critical Threat Detected: {threat['threat_type']}",
                            f"Critical threat {threat['threat_id']} detected at {threat['detected_at']}",
                            {
                                "threat_id": threat['threat_id'],
                                "threat_type": threat['threat_type'],
                                "detected_at": threat['detected_at'].isoformat()
                            }
                        )
                
                await asyncio.sleep(self.check_intervals['security_metrics'])
                
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
                await asyncio.sleep(180)

    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        # In a real implementation, this would collect actual system metrics
        # For demo purposes, we'll simulate some metrics
        import random
        
        return {
            'cpu_usage': random.uniform(20, 95),
            'memory_usage': random.uniform(30, 90),
            'disk_usage': random.uniform(40, 85),
            'network_io': random.uniform(100, 1000),
            'disk_io': random.uniform(50, 500),
            'timestamp': datetime.now()
        }

    async def store_metrics(self, metrics: Dict[str, Any]):
        """Store system metrics in database"""
        async with self.db_pool.acquire() as conn:
            for metric_name, value in metrics.items():
                if metric_name != 'timestamp' and isinstance(value, (int, float)):
                    await conn.execute("""
                        INSERT INTO system_metrics (metric_name, metric_value, timestamp)
                        VALUES ($1, $2, $3)
                    """, metric_name, value, metrics['timestamp'])

    async def store_database_metrics(self, db_stats, cache_hit_ratio, rollback_rate):
        """Store database performance metrics"""
        async with self.db_pool.acquire() as conn:
            timestamp = datetime.now()
            metrics = {
                'db_active_connections': db_stats['active_connections'],
                'db_cache_hit_ratio': cache_hit_ratio,
                'db_rollback_rate': rollback_rate,
                'db_transactions_committed': db_stats['transactions_committed'],
                'db_transactions_rolled_back': db_stats['transactions_rolled_back']
            }
            
            for metric_name, value in metrics.items():
                await conn.execute("""
                    INSERT INTO system_metrics (metric_name, metric_value, timestamp)
                    VALUES ($1, $2, $3)
                """, metric_name, value, timestamp)

    async def create_alert(self, level: AlertLevel, alert_type: AlertType, title: str, message: str, metadata: Dict[str, Any]):
        """Create and process a new alert"""
        alert_id = f"{alert_type.value}_{int(datetime.now().timestamp() * 1000000)}"  # Use microseconds for uniqueness
        
        # Check if similar alert already exists (avoid spam)
        similar_alert_key = f"{alert_type.value}_{title}"
        if similar_alert_key in self.active_alerts:
            last_alert_time = self.active_alerts[similar_alert_key]
            if datetime.now() - last_alert_time < timedelta(minutes=10):
                return  # Skip duplicate alert within 10 minutes
        
        alert = Alert(
            id=alert_id,
            level=level,
            type=alert_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Store alert in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO monitoring_alerts (id, level, type, title, message, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, alert.id, alert.level.value, alert.type.value, alert.title, 
                alert.message, json.dumps(alert.metadata), alert.timestamp)
        
        # Add to active alerts
        self.active_alerts[similar_alert_key] = alert.timestamp
        self.alert_history.append(alert)
        
        # Send notification based on alert level
        if level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            await self.send_email_alert(alert)
        
        logger.warning(f"🚨 ALERT [{level.value.upper()}] {title}: {message}")

    async def send_email_alert(self, alert: Alert):
        """Send email notification for critical alerts"""
        if not self.email_user or not self.alert_recipients:
            logger.warning("Email configuration missing, skipping email alert")
            return
        
        try:
            # Simple email without MIME
            subject = f"AutoBots Alert [{alert.level.value.upper()}]: {alert.title}"
            
            body = f"""AutoBots Monitoring Alert

Level: {alert.level.value.upper()}
Type: {alert.type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Title: {alert.title}
Message: {alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2)}

---
AutoBots Monitoring System
            """
            
            message = f"Subject: {subject}\n\n{body}"
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, self.alert_recipients, message)
            server.quit()
            
            logger.info(f"📧 Email alert sent for: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def process_alert_queue(self):
        """Process and manage alert lifecycle"""
        while True:
            try:
                # Auto-resolve old alerts
                cutoff_time = datetime.now() - timedelta(hours=24)
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE monitoring_alerts 
                        SET resolved = TRUE, resolved_at = NOW()
                        WHERE created_at < $1 AND resolved = FALSE
                    """, cutoff_time)
                
                # Clean up active alerts cache
                current_time = datetime.now()
                expired_keys = [
                    key for key, timestamp in self.active_alerts.items()
                    if current_time - timestamp > timedelta(hours=1)
                ]
                for key in expired_keys:
                    del self.active_alerts[key]
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in alert queue processing: {e}")
                await asyncio.sleep(300)

    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get current alert summary for dashboard"""
        async with self.db_pool.acquire() as conn:
            # Get alert counts by level
            alert_counts = await conn.fetch("""
                SELECT level, COUNT(*) as count
                FROM monitoring_alerts
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                AND resolved = FALSE
                GROUP BY level
            """)
            
            # Get recent alerts
            recent_alerts = await conn.fetch("""
                SELECT id, level, type, title, message, created_at
                FROM monitoring_alerts
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            return {
                'alert_counts': {row['level']: row['count'] for row in alert_counts},
                'recent_alerts': [dict(row) for row in recent_alerts],
                'total_active': sum(row['count'] for row in alert_counts),
                'last_updated': datetime.now().isoformat()
            }

    async def close(self):
        """Clean shutdown of monitoring system"""
        if self.db_pool:
            await self.db_pool.close()
        logger.info("🔌 AutoBots Monitoring System shut down")

# Configuration for production deployment
MONITORING_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_user': os.getenv('ALERT_EMAIL_USER'),
    'email_password': os.getenv('ALERT_EMAIL_PASSWORD'),
    'alert_recipients': [
        'brian95240@gmail.com',  # Primary admin
        # Add more recipients as needed
    ]
}

async def main():
    """Main function to run the monitoring system"""
    database_url = "postgresql://neondb_owner:npg_MdRXSxVkq46T@ep-white-leaf-a87kfssa-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
    
    monitor = AutoBotsMonitor(database_url, MONITORING_CONFIG)
    
    try:
        await monitor.initialize()
        
        # Keep the monitoring system running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring system...")
    finally:
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main())

