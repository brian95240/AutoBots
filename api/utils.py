# AutoBots API Utilities

import asyncio
import asyncpg
import aioredis
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import hashlib
import secrets
from functools import wraps
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and query management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database pool initialized")
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_single(self, query: str, *args) -> Any:
        """Execute a query and return single result"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_command(self, query: str, *args) -> str:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()

class CacheManager:
    """Redis cache management"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
    
    async def initialize(self):
        """Initialize Redis client"""
        self.client = await aioredis.from_url(self.redis_url)
        logger.info("Redis client initialized")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        try:
            await self.client.setex(key, expire, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis client"""
        if self.client:
            await self.client.close()

class RateLimiter:
    """API rate limiting"""
    
    def __init__(self, cache_manager: CacheManager, default_limit: int = 100):
        self.cache = cache_manager
        self.default_limit = default_limit
    
    async def is_allowed(self, identifier: str, limit: int = None) -> bool:
        """Check if request is allowed based on rate limit"""
        if limit is None:
            limit = self.default_limit
        
        key = f"rate_limit:{identifier}"
        
        try:
            # Get current count
            current = await self.cache.get(key)
            
            if current is None:
                # First request in this window
                await self.cache.set(key, "1", 60)  # 1 minute window
                return True
            
            count = int(current)
            if count >= limit:
                return False
            
            # Increment count
            await self.cache.client.incr(key)
            return True
        
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return True  # Allow on error

def rate_limit(limit: int = 100):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # This would be implemented with the actual rate limiter
            # For now, just pass through
            return await f(*args, **kwargs)
        return decorated_function
    return decorator

class SecurityUtils:
    """Security utilities"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = input_str
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def validate_affiliate_id(affiliate_id: str) -> bool:
        """Validate affiliate ID format"""
        import re
        # Alphanumeric, 3-20 characters
        pattern = r'^[a-zA-Z0-9]{3,20}$'
        return re.match(pattern, affiliate_id) is not None

class ResponseFormatter:
    """API response formatting utilities"""
    
    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict:
        """Format successful response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def error_response(error: str, code: int = 400) -> Dict:
        """Format error response"""
        return {
            'success': False,
            'error': error,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def paginated_response(data: List, page: int, limit: int, total: int) -> Dict:
        """Format paginated response"""
        return {
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            },
            'timestamp': datetime.now().isoformat()
        }

class MetricsCollector:
    """API metrics collection"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request metrics"""
        try:
            # Record in cache for real-time metrics
            metrics_key = f"metrics:{endpoint}:{method}"
            
            # Get existing metrics
            existing = await self.cache.get(metrics_key)
            
            if existing:
                metrics = json.loads(existing)
            else:
                metrics = {
                    'total_requests': 0,
                    'success_requests': 0,
                    'error_requests': 0,
                    'avg_response_time': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            
            # Update metrics
            metrics['total_requests'] += 1
            
            if 200 <= status_code < 400:
                metrics['success_requests'] += 1
            else:
                metrics['error_requests'] += 1
            
            # Update average response time
            current_avg = metrics['avg_response_time']
            total_requests = metrics['total_requests']
            metrics['avg_response_time'] = ((current_avg * (total_requests - 1)) + response_time) / total_requests
            
            metrics['last_updated'] = datetime.now().isoformat()
            
            # Store updated metrics
            await self.cache.set(metrics_key, json.dumps(metrics), 3600)
            
        except Exception as e:
            logger.error(f"Metrics recording error: {str(e)}")
    
    async def get_endpoint_metrics(self, endpoint: str, method: str) -> Dict:
        """Get metrics for specific endpoint"""
        try:
            metrics_key = f"metrics:{endpoint}:{method}"
            existing = await self.cache.get(metrics_key)
            
            if existing:
                return json.loads(existing)
            else:
                return {
                    'total_requests': 0,
                    'success_requests': 0,
                    'error_requests': 0,
                    'avg_response_time': 0.0,
                    'last_updated': None
                }
        
        except Exception as e:
            logger.error(f"Metrics retrieval error: {str(e)}")
            return {}

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def log_performance(f):
    """Decorator to log function performance"""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await f(*args, **kwargs)
            end_time = time.time()
            logger.info(f"{f.__name__} completed in {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            end_time = time.time()
            logger.error(f"{f.__name__} failed in {end_time - start_time:.3f}s: {str(e)}")
            raise
    return wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{f.__name__} attempt {attempt + 1} failed: {str(e)}, retrying...")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"{f.__name__} failed after {max_retries} attempts")
            
            raise last_exception
        return wrapper
    return decorator

