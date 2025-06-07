# AutoBots Monitoring API
# Flask API for monitoring dashboard integration

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import asyncpg
import json
import os
from datetime import datetime, timedelta
from monitoring_system import AutoBotsMonitor, MONITORING_CONFIG

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global monitoring instance
monitor = None
db_pool = None

DATABASE_URL = "postgresql://neondb_owner:npg_MdRXSxVkq46T@ep-white-leaf-a87kfssa-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

async def init_monitoring():
    """Initialize monitoring system"""
    global monitor, db_pool
    
    # Create database pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30
    )
    
    # Initialize monitor
    monitor = AutoBotsMonitor(DATABASE_URL, MONITORING_CONFIG)
    await monitor.initialize()

@app.route('/api/monitoring/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'autobots-monitoring'
    })

@app.route('/api/monitoring/alerts', methods=['GET'])
def get_alerts():
    """Get current alerts"""
    try:
        # Get query parameters
        level = request.args.get('level')
        limit = int(request.args.get('limit', 50))
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        
        # Run async query in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch_alerts():
            async with db_pool.acquire() as conn:
                query = """
                    SELECT id, level, type, title, message, metadata, 
                           created_at, resolved, resolved_at
                    FROM monitoring_alerts
                    WHERE 1=1
                """
                params = []
                
                if level:
                    query += " AND level = $" + str(len(params) + 1)
                    params.append(level)
                
                if not resolved:
                    query += " AND resolved = FALSE"
                
                query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                return await conn.fetch(query, *params)
        
        alerts = loop.run_until_complete(fetch_alerts())
        loop.close()
        
        # Convert to JSON-serializable format
        result = []
        for alert in alerts:
            result.append({
                'id': alert['id'],
                'level': alert['level'],
                'type': alert['type'],
                'title': alert['title'],
                'message': alert['message'],
                'metadata': alert['metadata'],
                'created_at': alert['created_at'].isoformat(),
                'resolved': alert['resolved'],
                'resolved_at': alert['resolved_at'].isoformat() if alert['resolved_at'] else None
            })
        
        return jsonify({
            'alerts': result,
            'count': len(result),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/alerts/summary', methods=['GET'])
def get_alert_summary():
    """Get alert summary statistics"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch_summary():
            async with db_pool.acquire() as conn:
                # Get counts by level for last 24 hours
                level_counts = await conn.fetch("""
                    SELECT level, COUNT(*) as count
                    FROM monitoring_alerts
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND resolved = FALSE
                    GROUP BY level
                """)
                
                # Get total counts
                total_active = await conn.fetchval("""
                    SELECT COUNT(*) FROM monitoring_alerts
                    WHERE resolved = FALSE
                """)
                
                total_24h = await conn.fetchval("""
                    SELECT COUNT(*) FROM monitoring_alerts
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                # Get recent critical alerts
                critical_alerts = await conn.fetch("""
                    SELECT id, title, created_at
                    FROM monitoring_alerts
                    WHERE level = 'critical'
                    AND created_at >= NOW() - INTERVAL '1 hour'
                    AND resolved = FALSE
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                return {
                    'level_counts': {row['level']: row['count'] for row in level_counts},
                    'total_active': total_active,
                    'total_24h': total_24h,
                    'critical_alerts': [
                        {
                            'id': alert['id'],
                            'title': alert['title'],
                            'created_at': alert['created_at'].isoformat()
                        } for alert in critical_alerts
                    ]
                }
        
        summary = loop.run_until_complete(fetch_summary())
        loop.close()
        
        return jsonify({
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        # Get query parameters
        metric_name = request.args.get('metric')
        hours = int(request.args.get('hours', 24))
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch_metrics():
            async with db_pool.acquire() as conn:
                query = """
                    SELECT metric_name, metric_value, metric_unit, timestamp
                    FROM system_metrics
                    WHERE timestamp >= NOW() - INTERVAL '%s hours'
                """ % hours
                
                params = []
                if metric_name:
                    query += " AND metric_name = $1"
                    params.append(metric_name)
                
                query += " ORDER BY timestamp DESC LIMIT 1000"
                
                return await conn.fetch(query, *params)
        
        metrics = loop.run_until_complete(fetch_metrics())
        loop.close()
        
        # Group metrics by name
        grouped_metrics = {}
        for metric in metrics:
            name = metric['metric_name']
            if name not in grouped_metrics:
                grouped_metrics[name] = []
            
            grouped_metrics[name].append({
                'value': float(metric['metric_value']),
                'unit': metric['metric_unit'],
                'timestamp': metric['timestamp'].isoformat()
            })
        
        return jsonify({
            'metrics': grouped_metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/bots/status', methods=['GET'])
def get_bot_status():
    """Get bot status information"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch_bot_status():
            async with db_pool.acquire() as conn:
                # Get bot configurations
                bots = await conn.fetch("""
                    SELECT bot_name, is_active, config_data, updated_at
                    FROM bot_configs
                    ORDER BY bot_name
                """)
                
                # Get recent bot logs
                recent_logs = await conn.fetch("""
                    SELECT bot_name, level, COUNT(*) as count
                    FROM bot_logs
                    WHERE timestamp >= NOW() - INTERVAL '1 hour'
                    GROUP BY bot_name, level
                """)
                
                # Get bot performance metrics
                bot_metrics = await conn.fetch("""
                    SELECT 
                        bot_name,
                        COUNT(*) as total_operations,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration
                    FROM operations
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY bot_name
                """)
                
                return {
                    'bots': [dict(bot) for bot in bots],
                    'recent_logs': [dict(log) for log in recent_logs],
                    'performance': [dict(metric) for metric in bot_metrics]
                }
        
        status = loop.run_until_complete(fetch_bot_status())
        loop.close()
        
        # Process bot status
        bot_status = {}
        for bot in status['bots']:
            bot_name = bot['bot_name']
            bot_status[bot_name] = {
                'name': bot_name,
                'active': bot['is_active'],
                'last_update': bot['updated_at'].isoformat(),
                'config': bot['config_data'],
                'logs': {},
                'performance': {}
            }
        
        # Add log counts
        for log in status['recent_logs']:
            bot_name = log['bot_name']
            if bot_name in bot_status:
                bot_status[bot_name]['logs'][log['level']] = log['count']
        
        # Add performance metrics
        for metric in status['performance']:
            bot_name = metric['bot_name']
            if bot_name in bot_status:
                bot_status[bot_name]['performance'] = {
                    'total_operations': metric['total_operations'],
                    'completed': metric['completed'],
                    'failed': metric['failed'],
                    'success_rate': (metric['completed'] / metric['total_operations'] * 100) if metric['total_operations'] > 0 else 0,
                    'avg_duration': float(metric['avg_duration']) if metric['avg_duration'] else 0
                }
        
        return jsonify({
            'bots': list(bot_status.values()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def resolve():
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE monitoring_alerts
                    SET resolved = TRUE, resolved_at = NOW()
                    WHERE id = $1
                """, alert_id)
                
                return await conn.fetchrow("""
                    SELECT * FROM monitoring_alerts WHERE id = $1
                """, alert_id)
        
        alert = loop.run_until_complete(resolve())
        loop.close()
        
        if alert:
            return jsonify({
                'message': 'Alert resolved successfully',
                'alert_id': alert_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/test-alert', methods=['POST'])
def test_alert():
    """Create a test alert for testing purposes"""
    try:
        data = request.get_json() or {}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def create_test_alert():
            if monitor:
                from monitoring_system import AlertLevel, AlertType
                await monitor.create_alert(
                    AlertLevel.INFO,
                    AlertType.SYSTEM_HEALTH,
                    data.get('title', 'Test Alert'),
                    data.get('message', 'This is a test alert from the monitoring API'),
                    {'test': True, 'source': 'api'}
                )
        
        loop.run_until_complete(create_test_alert())
        loop.close()
        
        return jsonify({
            'message': 'Test alert created successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize monitoring system
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_monitoring())
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)

