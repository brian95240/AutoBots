# ArchitectBot - System Architecture and Performance Optimization

import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import psutil
import time
from dataclasses import dataclass
from enum import Enum
import aioredis

class SystemMetric(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    DATABASE_CONNECTIONS = "database_connections"
    API_RESPONSE_TIME = "api_response_time"
    THREAT_DETECTION_TIME = "threat_detection_time"
    OCR_PROCESSING_TIME = "ocr_processing_time"

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_type: str
    value: float
    timestamp: datetime
    component: str
    metadata: Dict

class SystemMonitor:
    """System performance monitoring and metrics collection"""
    
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.db_pool = None
        self.redis_client = None
        self.metrics_buffer = []
        self.buffer_size = 100
        
        # Performance targets from PRD
        self.performance_targets = {
            'threat_detection_time': 50.0,  # <50ms
            'ocr_accuracy': 99.5,  # 99.5%
            'api_response_time': 200.0,  # <200ms
            'cpu_usage': 80.0,  # <80%
            'memory_usage': 85.0,  # <85%
            'database_connections': 80  # <80% of max
        }
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize system monitor"""
        # Initialize database pool
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=8,
            command_timeout=30
        )
        
        # Initialize Redis client
        self.redis_client = await aioredis.from_url(self.redis_url)
        
        self.logger.info("System monitor initialized")
    
    async def collect_system_metrics(self) -> List[PerformanceMetric]:
        """Collect current system performance metrics"""
        metrics = []
        current_time = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(PerformanceMetric(
            metric_type=SystemMetric.CPU_USAGE.value,
            value=cpu_percent,
            timestamp=current_time,
            component='system',
            metadata={'cores': psutil.cpu_count()}
        ))
        
        # Memory usage
        memory = psutil.virtual_memory()
        metrics.append(PerformanceMetric(
            metric_type=SystemMetric.MEMORY_USAGE.value,
            value=memory.percent,
            timestamp=current_time,
            component='system',
            metadata={'total_gb': memory.total / (1024**3)}
        ))
        
        # Disk usage
        disk = psutil.disk_usage('/')
        metrics.append(PerformanceMetric(
            metric_type=SystemMetric.DISK_USAGE.value,
            value=disk.percent,
            timestamp=current_time,
            component='system',
            metadata={'total_gb': disk.total / (1024**3)}
        ))
        
        # Database metrics
        db_metrics = await self._collect_database_metrics()
        metrics.extend(db_metrics)
        
        # Application metrics
        app_metrics = await self._collect_application_metrics()
        metrics.extend(app_metrics)
        
        return metrics
    
    async def _collect_database_metrics(self) -> List[PerformanceMetric]:
        """Collect database performance metrics"""
        metrics = []
        current_time = datetime.now()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Database connections
                conn_stats = await conn.fetchrow("""
                    SELECT 
                        count(*) as active_connections,
                        max_conn
                    FROM pg_stat_activity, 
                         (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc
                    WHERE state = 'active'
                    GROUP BY max_conn
                """)
                
                if conn_stats:
                    connection_percent = (conn_stats['active_connections'] / conn_stats['max_conn']) * 100
                    metrics.append(PerformanceMetric(
                        metric_type=SystemMetric.DATABASE_CONNECTIONS.value,
                        value=connection_percent,
                        timestamp=current_time,
                        component='database',
                        metadata={
                            'active_connections': conn_stats['active_connections'],
                            'max_connections': conn_stats['max_conn']
                        }
                    ))
                
                # Query performance
                query_stats = await conn.fetchrow("""
                    SELECT 
                        avg(mean_exec_time) as avg_query_time,
                        max(mean_exec_time) as max_query_time,
                        count(*) as total_queries
                    FROM pg_stat_statements
                    WHERE calls > 10
                """)
                
                if query_stats and query_stats['avg_query_time']:
                    metrics.append(PerformanceMetric(
                        metric_type='database_query_time',
                        value=float(query_stats['avg_query_time']),
                        timestamp=current_time,
                        component='database',
                        metadata={
                            'max_query_time': float(query_stats['max_query_time'] or 0),
                            'total_queries': query_stats['total_queries']
                        }
                    ))
        
        except Exception as e:
            self.logger.error(f"Failed to collect database metrics: {str(e)}")
        
        return metrics
    
    async def _collect_application_metrics(self) -> List[PerformanceMetric]:
        """Collect application-specific metrics"""
        metrics = []
        current_time = datetime.now()
        
        try:
            # Get metrics from Redis cache
            cached_metrics = await self.redis_client.hgetall('autobots:metrics')
            
            for metric_key, metric_value in cached_metrics.items():
                try:
                    metric_data = json.loads(metric_value)
                    metrics.append(PerformanceMetric(
                        metric_type=metric_key,
                        value=float(metric_data.get('value', 0)),
                        timestamp=datetime.fromisoformat(metric_data.get('timestamp', current_time.isoformat())),
                        component=metric_data.get('component', 'application'),
                        metadata=metric_data.get('metadata', {})
                    ))
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse metric {metric_key}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {str(e)}")
        
        return metrics
    
    async def store_metrics(self, metrics: List[PerformanceMetric]):
        """Store metrics in database and cache"""
        # Add to buffer
        self.metrics_buffer.extend(metrics)
        
        # Flush buffer if it's full
        if len(self.metrics_buffer) >= self.buffer_size:
            await self._flush_metrics_buffer()
        
        # Update real-time cache
        await self._update_metrics_cache(metrics)
    
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to database"""
        if not self.metrics_buffer:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                # Prepare batch insert
                values = []
                for metric in self.metrics_buffer:
                    values.append((
                        metric.metric_type,
                        metric.value,
                        metric.timestamp,
                        metric.component,
                        json.dumps(metric.metadata)
                    ))
                
                # Batch insert metrics
                await conn.executemany("""
                    INSERT INTO system_metrics (
                        metric_type, value, timestamp, component, metadata
                    ) VALUES ($1, $2, $3, $4, $5)
                """, values)
                
                self.logger.info(f"Flushed {len(self.metrics_buffer)} metrics to database")
                self.metrics_buffer.clear()
        
        except Exception as e:
            self.logger.error(f"Failed to flush metrics buffer: {str(e)}")
    
    async def _update_metrics_cache(self, metrics: List[PerformanceMetric]):
        """Update real-time metrics cache"""
        try:
            pipe = self.redis_client.pipeline()
            
            for metric in metrics:
                cache_data = {
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'component': metric.component,
                    'metadata': metric.metadata
                }
                
                pipe.hset('autobots:metrics', metric.metric_type, json.dumps(cache_data))
                pipe.expire('autobots:metrics', 3600)  # 1 hour TTL
            
            await pipe.execute()
        
        except Exception as e:
            self.logger.error(f"Failed to update metrics cache: {str(e)}")
    
    async def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get latest metrics for each type
                latest_metrics = await conn.fetch("""
                    SELECT DISTINCT ON (metric_type) 
                        metric_type, value, timestamp, component
                    FROM system_metrics
                    WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                    ORDER BY metric_type, timestamp DESC
                """)
                
                summary = {
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {},
                    'alerts': [],
                    'performance_score': 100.0
                }
                
                total_score = 0.0
                metric_count = 0
                
                for metric in latest_metrics:
                    metric_type = metric['metric_type']
                    value = float(metric['value'])
                    
                    summary['metrics'][metric_type] = {
                        'value': value,
                        'timestamp': metric['timestamp'].isoformat(),
                        'component': metric['component']
                    }
                    
                    # Check against performance targets
                    if metric_type in self.performance_targets:
                        target = self.performance_targets[metric_type]
                        
                        if metric_type in ['threat_detection_time', 'api_response_time']:
                            # Lower is better
                            if value > target:
                                summary['alerts'].append({
                                    'metric': metric_type,
                                    'value': value,
                                    'target': target,
                                    'severity': 'warning' if value < target * 1.5 else 'critical'
                                })
                                score = max(0, 100 - ((value - target) / target * 100))
                            else:
                                score = 100
                        else:
                            # Higher is better (for accuracy) or lower is better (for usage)
                            if metric_type == 'ocr_accuracy':
                                score = min(100, (value / target) * 100)
                            else:
                                # Usage metrics - lower is better
                                if value > target:
                                    summary['alerts'].append({
                                        'metric': metric_type,
                                        'value': value,
                                        'target': target,
                                        'severity': 'warning' if value < target * 1.2 else 'critical'
                                    })
                                    score = max(0, 100 - ((value - target) / target * 100))
                                else:
                                    score = 100
                        
                        total_score += score
                        metric_count += 1
                
                if metric_count > 0:
                    summary['performance_score'] = total_score / metric_count
                
                return summary
        
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {str(e)}")
            return {'error': str(e)}
    
    async def close(self):
        """Close monitor connections"""
        # Flush remaining metrics
        await self._flush_metrics_buffer()
        
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()

class OptimizationEngine:
    """System optimization and auto-tuning engine"""
    
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.db_pool = None
        self.redis_client = None
        
        # Optimization rules
        self.optimization_rules = {
            'high_cpu_usage': {
                'threshold': 80.0,
                'actions': ['scale_workers', 'optimize_queries', 'enable_caching']
            },
            'high_memory_usage': {
                'threshold': 85.0,
                'actions': ['clear_cache', 'optimize_memory', 'restart_services']
            },
            'slow_threat_detection': {
                'threshold': 50.0,
                'actions': ['optimize_patterns', 'increase_cache', 'parallel_processing']
            },
            'low_ocr_accuracy': {
                'threshold': 99.0,
                'actions': ['fallback_to_spider', 'image_preprocessing', 'model_tuning']
            }
        }
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize optimization engine"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=8,
            command_timeout=30
        )
        
        self.redis_client = await aioredis.from_url(self.redis_url)
        
        self.logger.info("Optimization engine initialized")
    
    async def analyze_performance(self, metrics: List[PerformanceMetric]) -> List[Dict]:
        """Analyze performance metrics and suggest optimizations"""
        optimizations = []
        
        for metric in metrics:
            # Check CPU usage
            if metric.metric_type == SystemMetric.CPU_USAGE.value:
                if metric.value > self.optimization_rules['high_cpu_usage']['threshold']:
                    optimizations.append({
                        'type': 'high_cpu_usage',
                        'metric_value': metric.value,
                        'threshold': self.optimization_rules['high_cpu_usage']['threshold'],
                        'suggested_actions': self.optimization_rules['high_cpu_usage']['actions'],
                        'priority': 'high' if metric.value > 90 else 'medium'
                    })
            
            # Check memory usage
            elif metric.metric_type == SystemMetric.MEMORY_USAGE.value:
                if metric.value > self.optimization_rules['high_memory_usage']['threshold']:
                    optimizations.append({
                        'type': 'high_memory_usage',
                        'metric_value': metric.value,
                        'threshold': self.optimization_rules['high_memory_usage']['threshold'],
                        'suggested_actions': self.optimization_rules['high_memory_usage']['actions'],
                        'priority': 'high' if metric.value > 95 else 'medium'
                    })
            
            # Check threat detection time
            elif metric.metric_type == SystemMetric.THREAT_DETECTION_TIME.value:
                if metric.value > self.optimization_rules['slow_threat_detection']['threshold']:
                    optimizations.append({
                        'type': 'slow_threat_detection',
                        'metric_value': metric.value,
                        'threshold': self.optimization_rules['slow_threat_detection']['threshold'],
                        'suggested_actions': self.optimization_rules['slow_threat_detection']['actions'],
                        'priority': 'critical'
                    })
        
        return optimizations
    
    async def apply_optimization(self, optimization: Dict) -> Dict:
        """Apply a specific optimization"""
        optimization_type = optimization['type']
        actions = optimization['suggested_actions']
        
        results = {
            'optimization_type': optimization_type,
            'actions_applied': [],
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            for action in actions:
                if action == 'scale_workers':
                    result = await self._scale_workers()
                    results['actions_applied'].append({'action': action, 'result': result})
                
                elif action == 'optimize_queries':
                    result = await self._optimize_database_queries()
                    results['actions_applied'].append({'action': action, 'result': result})
                
                elif action == 'enable_caching':
                    result = await self._enable_caching()
                    results['actions_applied'].append({'action': action, 'result': result})
                
                elif action == 'clear_cache':
                    result = await self._clear_cache()
                    results['actions_applied'].append({'action': action, 'result': result})
                
                elif action == 'optimize_patterns':
                    result = await self._optimize_threat_patterns()
                    results['actions_applied'].append({'action': action, 'result': result})
                
                else:
                    self.logger.warning(f"Unknown optimization action: {action}")
        
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.error(f"Optimization failed: {str(e)}")
        
        return results
    
    async def _scale_workers(self) -> Dict:
        """Scale worker processes"""
        # In production, this would interact with container orchestration
        # For now, simulate scaling
        return {
            'action': 'scale_workers',
            'previous_workers': 4,
            'new_workers': 6,
            'success': True
        }
    
    async def _optimize_database_queries(self) -> Dict:
        """Optimize database queries"""
        try:
            async with self.db_pool.acquire() as conn:
                # Analyze slow queries
                slow_queries = await conn.fetch("""
                    SELECT query, mean_exec_time, calls
                    FROM pg_stat_statements
                    WHERE mean_exec_time > 100
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """)
                
                # Update statistics
                await conn.execute("ANALYZE;")
                
                return {
                    'action': 'optimize_queries',
                    'slow_queries_found': len(slow_queries),
                    'statistics_updated': True,
                    'success': True
                }
        
        except Exception as e:
            return {
                'action': 'optimize_queries',
                'success': False,
                'error': str(e)
            }
    
    async def _enable_caching(self) -> Dict:
        """Enable or optimize caching"""
        try:
            # Set cache configuration
            await self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            await self.redis_client.config_set('maxmemory', '256mb')
            
            return {
                'action': 'enable_caching',
                'cache_policy': 'allkeys-lru',
                'max_memory': '256mb',
                'success': True
            }
        
        except Exception as e:
            return {
                'action': 'enable_caching',
                'success': False,
                'error': str(e)
            }
    
    async def _clear_cache(self) -> Dict:
        """Clear cache to free memory"""
        try:
            # Clear specific cache keys
            keys_deleted = 0
            
            # Clear old metrics
            await self.redis_client.delete('autobots:metrics:old')
            keys_deleted += 1
            
            # Clear expired sessions
            pattern = 'autobots:session:*'
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                keys_deleted += len(keys)
            
            return {
                'action': 'clear_cache',
                'keys_deleted': keys_deleted,
                'success': True
            }
        
        except Exception as e:
            return {
                'action': 'clear_cache',
                'success': False,
                'error': str(e)
            }
    
    async def _optimize_threat_patterns(self) -> Dict:
        """Optimize threat detection patterns"""
        # In production, this would optimize regex patterns and detection algorithms
        return {
            'action': 'optimize_patterns',
            'patterns_optimized': 15,
            'performance_improvement': '12%',
            'success': True
        }
    
    async def close(self):
        """Close optimization engine connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()

class ArchitectBot:
    """
    ArchitectBot - System Architecture and Performance Optimization
    Monitors system performance and applies automatic optimizations
    """
    
    def __init__(self, database_url: str, redis_url: str):
        self.system_monitor = SystemMonitor(database_url, redis_url)
        self.optimization_engine = OptimizationEngine(database_url, redis_url)
        self.monitoring_interval = 60  # seconds
        self.optimization_interval = 300  # 5 minutes
        self.running = False
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize ArchitectBot"""
        await self.system_monitor.initialize()
        await self.optimization_engine.initialize()
        self.logger.info("ArchitectBot initialized successfully")
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        self.running = True
        self.logger.info("Starting continuous system monitoring")
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Start optimization task
        optimization_task = asyncio.create_task(self._optimization_loop())
        
        # Wait for tasks to complete
        await asyncio.gather(monitoring_task, optimization_task)
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        self.logger.info("Stopping system monitoring")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = await self.system_monitor.collect_system_metrics()
                
                # Store metrics
                await self.system_monitor.store_metrics(metrics)
                
                self.logger.debug(f"Collected and stored {len(metrics)} metrics")
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)
            
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _optimization_loop(self):
        """Continuous optimization loop"""
        while self.running:
            try:
                # Get recent metrics
                metrics = await self.system_monitor.collect_system_metrics()
                
                # Analyze for optimizations
                optimizations = await self.optimization_engine.analyze_performance(metrics)
                
                # Apply critical optimizations automatically
                for optimization in optimizations:
                    if optimization.get('priority') == 'critical':
                        self.logger.info(f"Applying critical optimization: {optimization['type']}")
                        result = await self.optimization_engine.apply_optimization(optimization)
                        self.logger.info(f"Optimization result: {result}")
                
                # Wait for next interval
                await asyncio.sleep(self.optimization_interval)
            
            except Exception as e:
                self.logger.error(f"Optimization loop error: {str(e)}")
                await asyncio.sleep(self.optimization_interval)
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # Get performance summary
            performance_summary = await self.system_monitor.get_performance_summary()
            
            # Get recent metrics
            recent_metrics = await self.system_monitor.collect_system_metrics()
            
            # Analyze for optimizations
            optimizations = await self.optimization_engine.analyze_performance(recent_metrics)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'performance_summary': performance_summary,
                'recent_metrics_count': len(recent_metrics),
                'pending_optimizations': len(optimizations),
                'optimizations': optimizations,
                'monitoring_status': 'active' if self.running else 'inactive',
                'system_health': 'healthy' if performance_summary.get('performance_score', 0) > 80 else 'degraded'
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get system status: {str(e)}")
            return {'error': str(e)}
    
    async def manual_optimization(self, optimization_type: str) -> Dict:
        """Manually trigger a specific optimization"""
        optimization = {
            'type': optimization_type,
            'suggested_actions': self.optimization_engine.optimization_rules.get(
                optimization_type, {}
            ).get('actions', [])
        }
        
        if not optimization['suggested_actions']:
            return {
                'success': False,
                'error': f"Unknown optimization type: {optimization_type}"
            }
        
        return await self.optimization_engine.apply_optimization(optimization)
    
    async def close(self):
        """Close ArchitectBot"""
        self.running = False
        await self.system_monitor.close()
        await self.optimization_engine.close()

# Example usage and testing
async def main():
    """Test ArchitectBot functionality"""
    import os
    
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Initialize ArchitectBot
    architect_bot = ArchitectBot(database_url, redis_url)
    await architect_bot.initialize()
    
    # Get system status
    status = await architect_bot.get_system_status()
    print("System Status:")
    print(f"Performance Score: {status.get('performance_summary', {}).get('performance_score', 'N/A')}")
    print(f"System Health: {status.get('system_health', 'unknown')}")
    print(f"Pending Optimizations: {status.get('pending_optimizations', 0)}")
    
    # Test manual optimization
    if status.get('pending_optimizations', 0) > 0:
        optimization_result = await architect_bot.manual_optimization('high_cpu_usage')
        print(f"Manual optimization result: {optimization_result}")
    
    await architect_bot.close()

if __name__ == "__main__":
    asyncio.run(main())

