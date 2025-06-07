# AutoBots API - Main Application Entry Point

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import asyncpg
import aioredis
import os
import logging
from datetime import datetime
import json
from typing import Dict, List, Optional

# Import bot modules
import sys
sys.path.append('/home/ubuntu/autobots_project/core_bots')

from scoutbot import ScoutBot
from sentinelbot import SentinelBot
from affiliatebot import AffiliateBot
from operatorbot import OperatorBot
from architectbot import ArchitectBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoBotsAPI:
    """Main AutoBots API application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, origins="*")  # Allow all origins for development
        
        # Configuration
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.spider_api_key = os.getenv('SPIDER_API_KEY', 'your-spider-api-key')
        
        # Bot instances
        self.scout_bot = None
        self.sentinel_bot = None
        self.affiliate_bot = None
        self.operator_bot = None
        self.architect_bot = None
        
        # Database pool
        self.db_pool = None
        self.redis_client = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'bots_initialized': all([
                    self.scout_bot is not None,
                    self.sentinel_bot is not None,
                    self.affiliate_bot is not None,
                    self.operator_bot is not None,
                    self.architect_bot is not None
                ])
            })
        
        @self.app.route('/api/scout/ocr', methods=['POST'])
        def scout_ocr():
            """ScoutBot OCR processing endpoint"""
            try:
                data = request.get_json()
                image_url = data.get('image_url')
                
                if not image_url:
                    return jsonify({'error': 'image_url is required'}), 400
                
                # Process OCR asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.scout_bot.process_image_ocr(image_url)
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"OCR processing error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scout/scrape', methods=['POST'])
        def scout_scrape():
            """ScoutBot web scraping endpoint"""
            try:
                data = request.get_json()
                url = data.get('url')
                scrape_type = data.get('type', 'product')
                
                if not url:
                    return jsonify({'error': 'url is required'}), 400
                
                # Process scraping asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                if scrape_type == 'product':
                    result = loop.run_until_complete(
                        self.scout_bot.scrape_product_data(url)
                    )
                else:
                    result = loop.run_until_complete(
                        self.scout_bot.scrape_general_content(url)
                    )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"Scraping error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sentinel/analyze', methods=['POST'])
        def sentinel_analyze():
            """SentinelBot threat analysis endpoint"""
            try:
                data = request.get_json()
                content = data.get('content')
                content_type = data.get('type', 'text')
                
                if not content:
                    return jsonify({'error': 'content is required'}), 400
                
                # Process threat analysis asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.sentinel_bot.analyze_content(content, content_type)
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"Threat analysis error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/affiliate/consent', methods=['POST'])
        def affiliate_consent():
            """AffiliateBot GDPR consent processing endpoint"""
            try:
                data = request.get_json()
                
                # Process consent asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.affiliate_bot.process_affiliate_request('consent', data)
                )
                
                loop.close()
                
                return jsonify({
                    'success': result.success,
                    'action_type': result.action_type,
                    'affiliate_id': result.affiliate_id,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat()
                })
            
            except Exception as e:
                logger.error(f"Consent processing error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/affiliate/withdrawal', methods=['POST'])
        def affiliate_withdrawal():
            """AffiliateBot GDPR withdrawal processing endpoint"""
            try:
                data = request.get_json()
                
                # Process withdrawal asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.affiliate_bot.process_affiliate_request('withdrawal', data)
                )
                
                loop.close()
                
                return jsonify({
                    'success': result.success,
                    'action_type': result.action_type,
                    'affiliate_id': result.affiliate_id,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat()
                })
            
            except Exception as e:
                logger.error(f"Withdrawal processing error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/operator/onboard', methods=['POST'])
        def operator_onboard():
            """OperatorBot vendor onboarding endpoint"""
            try:
                data = request.get_json()
                vendor_name = data.get('vendor_name')
                vendor_config = data.get('vendor_config', {})
                
                if not vendor_name:
                    return jsonify({'error': 'vendor_name is required'}), 400
                
                # Process onboarding asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                operation_id = loop.run_until_complete(
                    self.operator_bot.onboard_vendor(vendor_name, vendor_config)
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'operation_id': operation_id,
                    'vendor_name': vendor_name,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"Vendor onboarding error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/operator/sync', methods=['POST'])
        def operator_sync():
            """OperatorBot product sync endpoint"""
            try:
                data = request.get_json()
                vendor_name = data.get('vendor_name')
                sync_config = data.get('sync_config', {})
                
                if not vendor_name:
                    return jsonify({'error': 'vendor_name is required'}), 400
                
                # Process sync asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                operation_id = loop.run_until_complete(
                    self.operator_bot.sync_vendor_products(vendor_name, sync_config)
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'operation_id': operation_id,
                    'vendor_name': vendor_name,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"Product sync error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/architect/status', methods=['GET'])
        def architect_status():
            """ArchitectBot system status endpoint"""
            try:
                # Get system status asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                status = loop.run_until_complete(
                    self.architect_bot.get_system_status()
                )
                
                loop.close()
                
                return jsonify(status)
            
            except Exception as e:
                logger.error(f"System status error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/architect/optimize', methods=['POST'])
        def architect_optimize():
            """ArchitectBot manual optimization endpoint"""
            try:
                data = request.get_json()
                optimization_type = data.get('optimization_type')
                
                if not optimization_type:
                    return jsonify({'error': 'optimization_type is required'}), 400
                
                # Process optimization asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.architect_bot.manual_optimization(optimization_type)
                )
                
                loop.close()
                
                return jsonify(result)
            
            except Exception as e:
                logger.error(f"Manual optimization error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/dashboard/metrics', methods=['GET'])
        def dashboard_metrics():
            """Dashboard metrics endpoint"""
            try:
                # Get comprehensive metrics
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Get system status
                system_status = loop.run_until_complete(
                    self.architect_bot.get_system_status()
                )
                
                # Get recent operations
                recent_ops = loop.run_until_complete(
                    self._get_recent_operations()
                )
                
                # Get affiliate stats
                affiliate_stats = loop.run_until_complete(
                    self._get_affiliate_stats()
                )
                
                loop.close()
                
                return jsonify({
                    'system_status': system_status,
                    'recent_operations': recent_ops,
                    'affiliate_stats': affiliate_stats,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                logger.error(f"Dashboard metrics error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    async def _get_recent_operations(self) -> List[Dict]:
        """Get recent operations from database"""
        try:
            async with self.db_pool.acquire() as conn:
                operations = await conn.fetch("""
                    SELECT id, operation_type, bot_name, vendor, status, created_at
                    FROM operations
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                
                return [
                    {
                        'id': op['id'],
                        'operation_type': op['operation_type'],
                        'bot_name': op['bot_name'],
                        'vendor': op['vendor'],
                        'status': op['status'],
                        'created_at': op['created_at'].isoformat()
                    }
                    for op in operations
                ]
        except Exception as e:
            logger.error(f"Failed to get recent operations: {str(e)}")
            return []
    
    async def _get_affiliate_stats(self) -> Dict:
        """Get affiliate statistics"""
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_affiliates,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_affiliates,
                        COUNT(CASE WHEN gdpr_consent = TRUE THEN 1 END) as consented_affiliates
                    FROM affiliates
                """)
                
                return {
                    'total_affiliates': stats['total_affiliates'],
                    'active_affiliates': stats['active_affiliates'],
                    'consented_affiliates': stats['consented_affiliates'],
                    'compliance_rate': (stats['consented_affiliates'] / stats['total_affiliates'] * 100) if stats['total_affiliates'] > 0 else 100
                }
        except Exception as e:
            logger.error(f"Failed to get affiliate stats: {str(e)}")
            return {
                'total_affiliates': 0,
                'active_affiliates': 0,
                'consented_affiliates': 0,
                'compliance_rate': 100
            }
    
    async def initialize_bots(self):
        """Initialize all bot instances"""
        try:
            # Initialize database pool
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Initialize Redis client
            self.redis_client = await aioredis.from_url(self.redis_url)
            
            # Initialize bots
            self.scout_bot = ScoutBot(self.spider_api_key, self.database_url)
            await self.scout_bot.initialize()
            
            self.sentinel_bot = SentinelBot(self.database_url, self.redis_url)
            await self.sentinel_bot.initialize()
            
            email_config = {
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'your-email@gmail.com',
                'password': 'your-password',
                'from_email': 'noreply@autobots.com'
            }
            self.affiliate_bot = AffiliateBot(self.database_url, email_config)
            await self.affiliate_bot.initialize()
            
            self.operator_bot = OperatorBot(self.database_url)
            await self.operator_bot.initialize()
            
            self.architect_bot = ArchitectBot(self.database_url, self.redis_url)
            await self.architect_bot.initialize()
            
            logger.info("All bots initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bots: {str(e)}")
            raise
    
    async def close_bots(self):
        """Close all bot instances"""
        try:
            if self.scout_bot:
                await self.scout_bot.close()
            if self.sentinel_bot:
                await self.sentinel_bot.close()
            if self.affiliate_bot:
                await self.affiliate_bot.close()
            if self.operator_bot:
                await self.operator_bot.close()
            if self.architect_bot:
                await self.architect_bot.close()
            
            if self.db_pool:
                await self.db_pool.close()
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("All bots closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing bots: {str(e)}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        # Initialize bots before starting the server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.initialize_bots())
        loop.close()
        
        logger.info(f"Starting AutoBots API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Create the application instance
autobots_api = AutoBotsAPI()

# Flask app instance for deployment
app = autobots_api.app

if __name__ == '__main__':
    # Run the application
    autobots_api.run(debug=True)

