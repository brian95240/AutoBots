# OperatorBot - Vendor Operations and Workflow Automation

import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import aiohttp
from dataclasses import dataclass
from enum import Enum

class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OperationType(Enum):
    VENDOR_ONBOARDING = "vendor_onboarding"
    PRODUCT_SYNC = "product_sync"
    PRICE_UPDATE = "price_update"
    INVENTORY_CHECK = "inventory_check"
    COMMISSION_CALCULATION = "commission_calculation"
    PERFORMANCE_ANALYSIS = "performance_analysis"

@dataclass
class Operation:
    """Operation execution result"""
    id: int
    operation_type: str
    vendor: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    operation_data: Dict
    result_data: Dict
    error_message: Optional[str]
    retry_count: int

class VendorAPI:
    """Generic vendor API integration"""
    
    def __init__(self, vendor_config: Dict):
        self.vendor_name = vendor_config.get('name')
        self.api_base_url = vendor_config.get('api_url')
        self.api_key = vendor_config.get('api_key')
        self.rate_limit = vendor_config.get('rate_limit', 60)  # requests per minute
        self.session = None
        
        # Rate limiting
        self.request_times = []
        
    async def initialize(self):
        """Initialize vendor API session"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"AutoBots-OperatorBot/1.0 ({self.vendor_name})"
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def get_products(self, page: int = 1, limit: int = 100) -> Dict:
        """Get products from vendor API"""
        await self._rate_limit_check()
        
        params = {'page': page, 'limit': limit}
        
        try:
            async with self.session.get(f"{self.api_base_url}/products", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API error: {response.status}")
        except Exception as e:
            logging.error(f"Failed to get products from {self.vendor_name}: {str(e)}")
            raise
    
    async def get_product_details(self, product_id: str) -> Dict:
        """Get detailed product information"""
        await self._rate_limit_check()
        
        try:
            async with self.session.get(f"{self.api_base_url}/products/{product_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API error: {response.status}")
        except Exception as e:
            logging.error(f"Failed to get product {product_id} from {self.vendor_name}: {str(e)}")
            raise
    
    async def update_inventory(self, product_id: str, quantity: int) -> Dict:
        """Update product inventory"""
        await self._rate_limit_check()
        
        payload = {'quantity': quantity}
        
        try:
            async with self.session.put(f"{self.api_base_url}/products/{product_id}/inventory", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API error: {response.status}")
        except Exception as e:
            logging.error(f"Failed to update inventory for {product_id} at {self.vendor_name}: {str(e)}")
            raise
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=1)
        
        # Remove old requests
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # Check if we're at the rate limit
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (current_time - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current request
        self.request_times.append(current_time)
    
    async def close(self):
        """Close API session"""
        if self.session:
            await self.session.close()

class WorkflowEngine:
    """Workflow automation engine for vendor operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_pool = None
        self.vendor_apis = {}
        self.active_operations = {}
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize workflow engine"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=3,
            max_size=15,
            command_timeout=60
        )
        
        # Load vendor configurations
        await self._load_vendor_configs()
        
        self.logger.info("Workflow engine initialized")
    
    async def _load_vendor_configs(self):
        """Load vendor API configurations"""
        # In production, this would load from database or config file
        vendor_configs = [
            {
                'name': 'amazon',
                'api_url': 'https://api.amazon.com/v1',
                'api_key': 'amazon-api-key',
                'rate_limit': 100
            },
            {
                'name': 'shopify',
                'api_url': 'https://api.shopify.com/v1',
                'api_key': 'shopify-api-key',
                'rate_limit': 80
            }
        ]
        
        for config in vendor_configs:
            vendor_api = VendorAPI(config)
            await vendor_api.initialize()
            self.vendor_apis[config['name']] = vendor_api
    
    async def create_operation(self, operation_type: str, vendor: str, operation_data: Dict) -> int:
        """Create a new operation"""
        async with self.db_pool.acquire() as conn:
            operation_id = await conn.fetchval("""
                INSERT INTO operations (
                    operation_type, bot_name, vendor, operation_data, 
                    status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """,
                operation_type,
                'OperatorBot',
                vendor,
                json.dumps(operation_data),
                OperationStatus.PENDING.value,
                datetime.now()
            )
            
            self.logger.info(f"Created operation {operation_id}: {operation_type} for {vendor}")
            return operation_id
    
    async def execute_operation(self, operation_id: int) -> Operation:
        """Execute a specific operation"""
        async with self.db_pool.acquire() as conn:
            # Get operation details
            op_row = await conn.fetchrow(
                "SELECT * FROM operations WHERE id = $1",
                operation_id
            )
            
            if not op_row:
                raise ValueError(f"Operation {operation_id} not found")
            
            operation = Operation(
                id=op_row['id'],
                operation_type=op_row['operation_type'],
                vendor=op_row['vendor'],
                status=op_row['status'],
                started_at=op_row['started_at'] or datetime.now(),
                completed_at=op_row['completed_at'],
                operation_data=json.loads(op_row['operation_data'] or '{}'),
                result_data={},
                error_message=op_row['error_message'],
                retry_count=op_row['retry_count']
            )
            
            # Update status to running
            await conn.execute("""
                UPDATE operations SET 
                    status = $1, started_at = $2
                WHERE id = $3
            """, OperationStatus.RUNNING.value, datetime.now(), operation_id)
        
        try:
            # Execute the operation based on type
            if operation.operation_type == OperationType.VENDOR_ONBOARDING.value:
                result = await self._execute_vendor_onboarding(operation)
            elif operation.operation_type == OperationType.PRODUCT_SYNC.value:
                result = await self._execute_product_sync(operation)
            elif operation.operation_type == OperationType.PRICE_UPDATE.value:
                result = await self._execute_price_update(operation)
            elif operation.operation_type == OperationType.INVENTORY_CHECK.value:
                result = await self._execute_inventory_check(operation)
            elif operation.operation_type == OperationType.COMMISSION_CALCULATION.value:
                result = await self._execute_commission_calculation(operation)
            elif operation.operation_type == OperationType.PERFORMANCE_ANALYSIS.value:
                result = await self._execute_performance_analysis(operation)
            else:
                raise ValueError(f"Unknown operation type: {operation.operation_type}")
            
            # Update operation as completed
            operation.status = OperationStatus.COMPLETED.value
            operation.completed_at = datetime.now()
            operation.result_data = result
            
            await self._update_operation_status(operation)
            
            self.logger.info(f"Operation {operation_id} completed successfully")
            
        except Exception as e:
            # Update operation as failed
            operation.status = OperationStatus.FAILED.value
            operation.completed_at = datetime.now()
            operation.error_message = str(e)
            operation.retry_count += 1
            
            await self._update_operation_status(operation)
            
            self.logger.error(f"Operation {operation_id} failed: {str(e)}")
        
        return operation
    
    async def _execute_vendor_onboarding(self, operation: Operation) -> Dict:
        """Execute vendor onboarding workflow"""
        vendor_data = operation.operation_data
        vendor_name = operation.vendor
        
        steps_completed = []
        
        # Step 1: Validate vendor API connectivity
        if vendor_name in self.vendor_apis:
            vendor_api = self.vendor_apis[vendor_name]
            try:
                # Test API connection
                test_products = await vendor_api.get_products(page=1, limit=1)
                steps_completed.append("api_connectivity_verified")
            except Exception as e:
                raise Exception(f"API connectivity test failed: {str(e)}")
        else:
            raise Exception(f"Vendor API not configured: {vendor_name}")
        
        # Step 2: Create vendor record in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO vendors (name, api_config, status, onboarded_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET
                    api_config = EXCLUDED.api_config,
                    status = EXCLUDED.status,
                    onboarded_at = EXCLUDED.onboarded_at
            """,
                vendor_name,
                json.dumps(vendor_data.get('api_config', {})),
                'active',
                datetime.now()
            )
            steps_completed.append("vendor_record_created")
        
        # Step 3: Initial product sync
        sync_result = await self._execute_product_sync(Operation(
            id=0,
            operation_type=OperationType.PRODUCT_SYNC.value,
            vendor=vendor_name,
            status=OperationStatus.RUNNING.value,
            started_at=datetime.now(),
            completed_at=None,
            operation_data={'initial_sync': True, 'limit': 100},
            result_data={},
            error_message=None,
            retry_count=0
        ))
        steps_completed.append("initial_product_sync")
        
        return {
            'vendor_name': vendor_name,
            'steps_completed': steps_completed,
            'products_synced': sync_result.get('products_synced', 0),
            'onboarding_date': datetime.now().isoformat()
        }
    
    async def _execute_product_sync(self, operation: Operation) -> Dict:
        """Execute product synchronization"""
        vendor_name = operation.vendor
        sync_config = operation.operation_data
        
        if vendor_name not in self.vendor_apis:
            raise Exception(f"Vendor API not available: {vendor_name}")
        
        vendor_api = self.vendor_apis[vendor_name]
        products_synced = 0
        products_updated = 0
        products_created = 0
        
        # Get products from vendor API
        page = 1
        limit = sync_config.get('limit', 100)
        
        while True:
            try:
                products_response = await vendor_api.get_products(page=page, limit=limit)
                products = products_response.get('products', [])
                
                if not products:
                    break
                
                # Process each product
                for product_data in products:
                    try:
                        result = await self._sync_single_product(vendor_name, product_data)
                        products_synced += 1
                        
                        if result == 'created':
                            products_created += 1
                        elif result == 'updated':
                            products_updated += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to sync product {product_data.get('id')}: {str(e)}")
                
                page += 1
                
                # Limit pages for initial sync
                if sync_config.get('initial_sync') and page > 10:
                    break
                
            except Exception as e:
                self.logger.error(f"Failed to get products page {page}: {str(e)}")
                break
        
        return {
            'vendor_name': vendor_name,
            'products_synced': products_synced,
            'products_created': products_created,
            'products_updated': products_updated,
            'sync_date': datetime.now().isoformat()
        }
    
    async def _sync_single_product(self, vendor_name: str, product_data: Dict) -> str:
        """Sync a single product to database"""
        async with self.db_pool.acquire() as conn:
            # Check if product exists
            existing = await conn.fetchrow("""
                SELECT id FROM products 
                WHERE vendor = $1 AND product_url = $2
            """, vendor_name, product_data.get('url', ''))
            
            if existing:
                # Update existing product
                await conn.execute("""
                    UPDATE products SET
                        product_name = $3,
                        price = $4,
                        category = $5,
                        updated_at = NOW()
                    WHERE vendor = $1 AND product_url = $2
                """,
                    vendor_name,
                    product_data.get('url', ''),
                    product_data.get('name', ''),
                    product_data.get('price', 0.0),
                    product_data.get('category', '')
                )
                return 'updated'
            else:
                # Create new product
                await conn.execute("""
                    INSERT INTO products (
                        product_name, product_url, price, vendor, 
                        category, scrape_date, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    product_data.get('name', ''),
                    product_data.get('url', ''),
                    product_data.get('price', 0.0),
                    vendor_name,
                    product_data.get('category', ''),
                    datetime.now(),
                    datetime.now()
                )
                return 'created'
    
    async def _execute_price_update(self, operation: Operation) -> Dict:
        """Execute price update operation"""
        vendor_name = operation.vendor
        update_config = operation.operation_data
        
        products_updated = 0
        
        async with self.db_pool.acquire() as conn:
            # Get products that need price updates
            products = await conn.fetch("""
                SELECT product_url, price FROM products
                WHERE vendor = $1
                AND updated_at < NOW() - INTERVAL '1 hour'
                LIMIT $2
            """, vendor_name, update_config.get('limit', 100))
            
            if vendor_name in self.vendor_apis:
                vendor_api = self.vendor_apis[vendor_name]
                
                for product in products:
                    try:
                        # Get current price from vendor
                        product_details = await vendor_api.get_product_details(
                            product['product_url'].split('/')[-1]  # Extract product ID
                        )
                        
                        new_price = product_details.get('price', 0.0)
                        
                        # Update price if changed
                        if abs(new_price - product['price']) > 0.01:
                            await conn.execute("""
                                UPDATE products SET
                                    price = $1,
                                    updated_at = NOW()
                                WHERE product_url = $2 AND vendor = $3
                            """, new_price, product['product_url'], vendor_name)
                            
                            products_updated += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Failed to update price for {product['product_url']}: {str(e)}")
        
        return {
            'vendor_name': vendor_name,
            'products_updated': products_updated,
            'update_date': datetime.now().isoformat()
        }
    
    async def _execute_inventory_check(self, operation: Operation) -> Dict:
        """Execute inventory check operation"""
        vendor_name = operation.vendor
        
        # Placeholder for inventory check logic
        # In production, this would check stock levels and update database
        
        return {
            'vendor_name': vendor_name,
            'inventory_checked': True,
            'check_date': datetime.now().isoformat()
        }
    
    async def _execute_commission_calculation(self, operation: Operation) -> Dict:
        """Execute commission calculation"""
        vendor_name = operation.vendor
        calc_config = operation.operation_data
        
        total_commission = 0.0
        transactions_processed = 0
        
        async with self.db_pool.acquire() as conn:
            # Get affiliate transactions for commission calculation
            transactions = await conn.fetch("""
                SELECT a.commission_rate, p.price, COUNT(*) as transaction_count
                FROM affiliates a
                JOIN products p ON p.vendor = $1
                WHERE a.status = 'active'
                AND p.scrape_date >= NOW() - INTERVAL '30 days'
                GROUP BY a.commission_rate, p.price
            """, vendor_name)
            
            for transaction in transactions:
                commission = transaction['price'] * transaction['commission_rate'] * transaction['transaction_count']
                total_commission += commission
                transactions_processed += transaction['transaction_count']
        
        return {
            'vendor_name': vendor_name,
            'total_commission': total_commission,
            'transactions_processed': transactions_processed,
            'calculation_date': datetime.now().isoformat()
        }
    
    async def _execute_performance_analysis(self, operation: Operation) -> Dict:
        """Execute performance analysis"""
        vendor_name = operation.vendor
        
        async with self.db_pool.acquire() as conn:
            # Get performance metrics
            metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_products,
                    AVG(price) as avg_price,
                    MAX(price) as max_price,
                    MIN(price) as min_price,
                    COUNT(DISTINCT category) as categories
                FROM products
                WHERE vendor = $1
                AND scrape_date >= NOW() - INTERVAL '30 days'
            """, vendor_name)
            
            return {
                'vendor_name': vendor_name,
                'total_products': metrics['total_products'],
                'avg_price': float(metrics['avg_price'] or 0),
                'max_price': float(metrics['max_price'] or 0),
                'min_price': float(metrics['min_price'] or 0),
                'categories': metrics['categories'],
                'analysis_date': datetime.now().isoformat()
            }
    
    async def _update_operation_status(self, operation: Operation):
        """Update operation status in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE operations SET
                    status = $1,
                    completed_at = $2,
                    error_message = $3,
                    retry_count = $4
                WHERE id = $5
            """,
                operation.status,
                operation.completed_at,
                operation.error_message,
                operation.retry_count,
                operation.id
            )
    
    async def get_operation_status(self, operation_id: int) -> Optional[Operation]:
        """Get operation status"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM operations WHERE id = $1",
                operation_id
            )
            
            if row:
                return Operation(
                    id=row['id'],
                    operation_type=row['operation_type'],
                    vendor=row['vendor'],
                    status=row['status'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    operation_data=json.loads(row['operation_data'] or '{}'),
                    result_data={},
                    error_message=row['error_message'],
                    retry_count=row['retry_count']
                )
        return None
    
    async def close(self):
        """Close all connections"""
        if self.db_pool:
            await self.db_pool.close()
        
        for vendor_api in self.vendor_apis.values():
            await vendor_api.close()

class OperatorBot:
    """
    OperatorBot - Vendor Operations and Workflow Automation
    Manages vendor integrations and automates operational workflows
    """
    
    def __init__(self, database_url: str):
        self.workflow_engine = WorkflowEngine(database_url)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize OperatorBot"""
        await self.workflow_engine.initialize()
        self.logger.info("OperatorBot initialized successfully")
    
    async def onboard_vendor(self, vendor_name: str, vendor_config: Dict) -> int:
        """Onboard a new vendor"""
        operation_id = await self.workflow_engine.create_operation(
            OperationType.VENDOR_ONBOARDING.value,
            vendor_name,
            vendor_config
        )
        
        # Execute onboarding workflow
        operation = await self.workflow_engine.execute_operation(operation_id)
        
        return operation_id
    
    async def sync_vendor_products(self, vendor_name: str, sync_config: Dict = None) -> int:
        """Sync products from vendor"""
        if sync_config is None:
            sync_config = {'limit': 100}
        
        operation_id = await self.workflow_engine.create_operation(
            OperationType.PRODUCT_SYNC.value,
            vendor_name,
            sync_config
        )
        
        # Execute sync workflow
        operation = await self.workflow_engine.execute_operation(operation_id)
        
        return operation_id
    
    async def update_prices(self, vendor_name: str, update_config: Dict = None) -> int:
        """Update product prices from vendor"""
        if update_config is None:
            update_config = {'limit': 100}
        
        operation_id = await self.workflow_engine.create_operation(
            OperationType.PRICE_UPDATE.value,
            vendor_name,
            update_config
        )
        
        # Execute price update workflow
        operation = await self.workflow_engine.execute_operation(operation_id)
        
        return operation_id
    
    async def get_operation_status(self, operation_id: int) -> Optional[Operation]:
        """Get status of an operation"""
        return await self.workflow_engine.get_operation_status(operation_id)
    
    async def close(self):
        """Close OperatorBot"""
        await self.workflow_engine.close()

# Example usage and testing
async def main():
    """Test OperatorBot functionality"""
    import os
    
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
    
    # Initialize OperatorBot
    operator_bot = OperatorBot(database_url)
    await operator_bot.initialize()
    
    # Test vendor onboarding
    vendor_config = {
        'api_config': {
            'api_url': 'https://api.example.com/v1',
            'api_key': 'test-key',
            'rate_limit': 60
        }
    }
    
    onboard_op_id = await operator_bot.onboard_vendor('test_vendor', vendor_config)
    print(f"Vendor onboarding operation created: {onboard_op_id}")
    
    # Test product sync
    sync_op_id = await operator_bot.sync_vendor_products('test_vendor', {'limit': 50})
    print(f"Product sync operation created: {sync_op_id}")
    
    # Check operation status
    operation = await operator_bot.get_operation_status(onboard_op_id)
    if operation:
        print(f"Operation {onboard_op_id} status: {operation.status}")
    
    await operator_bot.close()

if __name__ == "__main__":
    asyncio.run(main())

