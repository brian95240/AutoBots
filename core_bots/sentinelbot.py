# SentinelBot - Real-time Threat Detection with spider.cloud Integration
# Target: <50ms threat detection response time

import asyncio
import aiohttp
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging
import json
import time
import hashlib
from dataclasses import dataclass
from enum import Enum
import ipaddress
import re

class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10

@dataclass
class ThreatDetection:
    """Threat detection result"""
    threat_type: str
    severity_level: int
    confidence: float
    source_ip: str
    user_agent: str
    request_path: str
    threat_data: Dict
    spider_score: float
    detection_time: float
    recommended_action: str

class SpiderThreatAPI:
    """Spider.cloud Threat Intelligence API integration"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.spider.cloud/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.cache = {}  # Simple in-memory cache for threat intelligence
        self.cache_ttl = 300  # 5 minutes cache TTL
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AutoBots-SentinelBot/1.0"
            },
            timeout=aiohttp.ClientTimeout(total=5)  # Fast timeout for real-time detection
        )
    
    async def analyze_threat(self, request_data: Dict) -> Dict:
        """
        Analyze potential threat using spider.cloud threat intelligence
        Fast analysis for real-time detection
        """
        # Create cache key
        cache_key = hashlib.md5(
            f"{request_data.get('ip', '')}{request_data.get('user_agent', '')}{request_data.get('path', '')}".encode()
        ).hexdigest()
        
        # Check cache first
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        payload = {
            "source_ip": request_data.get('ip'),
            "user_agent": request_data.get('user_agent'),
            "request_path": request_data.get('path'),
            "request_method": request_data.get('method', 'GET'),
            "headers": request_data.get('headers', {}),
            "analysis_type": "real_time",
            "include_reputation": True,
            "include_patterns": True
        }
        
        try:
            async with self.session.post(f"{self.base_url}/threat-intel", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Cache the result
                    self.cache[cache_key] = (result, time.time())
                    
                    return result
                else:
                    logging.warning(f"Spider threat API returned {response.status}")
                    return {"threat_score": 0.0, "threat_types": [], "reputation": "unknown"}
        
        except asyncio.TimeoutError:
            logging.warning("Spider threat API timeout")
            return {"threat_score": 0.0, "threat_types": [], "reputation": "unknown"}
        except Exception as e:
            logging.error(f"Spider threat API error: {str(e)}")
            return {"threat_score": 0.0, "threat_types": [], "reputation": "unknown"}
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

class LocalThreatDetector:
    """Local threat detection using pattern matching and heuristics"""
    
    def __init__(self):
        # Common attack patterns
        self.sql_injection_patterns = [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
            r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
            r"((\%27)|(\'))union",
            r"exec(\s|\+)+(s|x)p\w+",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
        ]
        
        self.path_traversal_patterns = [
            r"\.\.\/",
            r"\.\.\\",
            r"\%2e\%2e\%2f",
            r"\%2e\%2e\/",
            r"\.\.%2f",
        ]
        
        # Suspicious user agents
        self.suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "acunetix", "nessus", "openvas", "w3af", "skipfish"
        ]
        
        # Rate limiting tracking
        self.request_counts = {}
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_threshold = 100  # requests per minute
    
    def analyze_request(self, request_data: Dict) -> ThreatDetection:
        """
        Analyze request for threats using local patterns
        Fast local analysis for real-time detection
        """
        start_time = time.time()
        
        ip = request_data.get('ip', '')
        user_agent = request_data.get('user_agent', '')
        path = request_data.get('path', '')
        method = request_data.get('method', 'GET')
        headers = request_data.get('headers', {})
        
        threats = []
        max_severity = 0
        threat_data = {}
        
        # Check for SQL injection
        sql_threat = self._check_sql_injection(path, request_data.get('query_params', {}))
        if sql_threat:
            threats.append(sql_threat)
            max_severity = max(max_severity, sql_threat['severity'])
        
        # Check for XSS
        xss_threat = self._check_xss(path, request_data.get('query_params', {}))
        if xss_threat:
            threats.append(xss_threat)
            max_severity = max(max_severity, xss_threat['severity'])
        
        # Check for path traversal
        traversal_threat = self._check_path_traversal(path)
        if traversal_threat:
            threats.append(traversal_threat)
            max_severity = max(max_severity, traversal_threat['severity'])
        
        # Check user agent
        ua_threat = self._check_user_agent(user_agent)
        if ua_threat:
            threats.append(ua_threat)
            max_severity = max(max_severity, ua_threat['severity'])
        
        # Check rate limiting
        rate_threat = self._check_rate_limiting(ip)
        if rate_threat:
            threats.append(rate_threat)
            max_severity = max(max_severity, rate_threat['severity'])
        
        # Check for suspicious headers
        header_threat = self._check_suspicious_headers(headers)
        if header_threat:
            threats.append(header_threat)
            max_severity = max(max_severity, header_threat['severity'])
        
        detection_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Determine primary threat type
        primary_threat = threats[0]['type'] if threats else 'none'
        
        # Calculate confidence based on number and severity of threats
        confidence = min(0.95, len(threats) * 0.2 + (max_severity / 10) * 0.5)
        
        # Determine recommended action
        if max_severity >= 8:
            action = "block_immediately"
        elif max_severity >= 5:
            action = "rate_limit"
        elif max_severity >= 3:
            action = "monitor_closely"
        else:
            action = "allow"
        
        return ThreatDetection(
            threat_type=primary_threat,
            severity_level=max_severity,
            confidence=confidence,
            source_ip=ip,
            user_agent=user_agent,
            request_path=path,
            threat_data={'threats': threats, 'method': method},
            spider_score=0.0,  # Will be updated by spider.cloud
            detection_time=detection_time,
            recommended_action=action
        )
    
    def _check_sql_injection(self, path: str, params: Dict) -> Optional[Dict]:
        """Check for SQL injection patterns"""
        combined_input = path + " " + " ".join(str(v) for v in params.values())
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, combined_input, re.IGNORECASE):
                return {
                    'type': 'sql_injection',
                    'severity': 9,
                    'pattern': pattern,
                    'location': 'path_or_params'
                }
        return None
    
    def _check_xss(self, path: str, params: Dict) -> Optional[Dict]:
        """Check for XSS patterns"""
        combined_input = path + " " + " ".join(str(v) for v in params.values())
        
        for pattern in self.xss_patterns:
            if re.search(pattern, combined_input, re.IGNORECASE):
                return {
                    'type': 'xss',
                    'severity': 7,
                    'pattern': pattern,
                    'location': 'path_or_params'
                }
        return None
    
    def _check_path_traversal(self, path: str) -> Optional[Dict]:
        """Check for path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return {
                    'type': 'path_traversal',
                    'severity': 6,
                    'pattern': pattern,
                    'location': 'path'
                }
        return None
    
    def _check_user_agent(self, user_agent: str) -> Optional[Dict]:
        """Check for suspicious user agents"""
        ua_lower = user_agent.lower()
        for suspicious_ua in self.suspicious_user_agents:
            if suspicious_ua in ua_lower:
                return {
                    'type': 'suspicious_user_agent',
                    'severity': 5,
                    'user_agent': suspicious_ua,
                    'location': 'headers'
                }
        return None
    
    def _check_rate_limiting(self, ip: str) -> Optional[Dict]:
        """Check for rate limiting violations"""
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - self.rate_limit_window
        self.request_counts = {
            ip_addr: [(timestamp, count) for timestamp, count in requests 
                     if timestamp > cutoff_time]
            for ip_addr, requests in self.request_counts.items()
        }
        
        # Add current request
        if ip not in self.request_counts:
            self.request_counts[ip] = []
        self.request_counts[ip].append((current_time, 1))
        
        # Count requests in window
        total_requests = sum(count for _, count in self.request_counts[ip])
        
        if total_requests > self.rate_limit_threshold:
            return {
                'type': 'rate_limit_violation',
                'severity': 6,
                'request_count': total_requests,
                'threshold': self.rate_limit_threshold,
                'location': 'rate_limiting'
            }
        return None
    
    def _check_suspicious_headers(self, headers: Dict) -> Optional[Dict]:
        """Check for suspicious headers"""
        suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'x-originating-ip']
        
        for header_name, header_value in headers.items():
            if header_name.lower() in suspicious_headers:
                # Check for header injection
                if '\n' in header_value or '\r' in header_value:
                    return {
                        'type': 'header_injection',
                        'severity': 7,
                        'header': header_name,
                        'location': 'headers'
                    }
        return None

class SentinelBot:
    """
    SentinelBot - Real-time threat detection and response
    Target: <50ms threat detection response time
    """
    
    def __init__(self, database_url: str, spider_api_key: str):
        self.database_url = database_url
        self.spider_api = SpiderThreatAPI(spider_api_key)
        self.local_detector = LocalThreatDetector()
        self.db_pool = None
        self.blocked_ips = set()
        self.whitelist_ips = set()
        
        # Performance metrics
        self.detection_count = 0
        self.avg_detection_time = 0.0
        self.target_response_time = 50.0  # 50ms target
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize SentinelBot with database and API connections"""
        # Initialize database pool
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=30
        )
        
        # Initialize spider.cloud API
        await self.spider_api.initialize()
        
        # Load blocked IPs from database
        await self._load_blocked_ips()
        
        self.logger.info("SentinelBot initialized successfully")
    
    async def analyze_request(self, request_data: Dict) -> ThreatDetection:
        """
        Analyze incoming request for threats
        Implements <50ms response time target
        """
        start_time = time.time()
        
        # Quick IP whitelist/blacklist check
        source_ip = request_data.get('ip', '')
        if source_ip in self.whitelist_ips:
            return self._create_safe_detection(request_data, start_time)
        
        if source_ip in self.blocked_ips:
            return self._create_blocked_detection(request_data, start_time)
        
        # Local threat detection (fast)
        local_detection = self.local_detector.analyze_request(request_data)
        
        # If local detection is high severity, respond immediately
        if local_detection.severity_level >= 8:
            await self._store_threat_detection(local_detection)
            self._update_metrics(time.time() - start_time)
            return local_detection
        
        # For medium threats, enhance with spider.cloud (if time permits)
        if local_detection.severity_level >= 5:
            try:
                # Quick spider.cloud analysis with timeout
                spider_result = await asyncio.wait_for(
                    self.spider_api.analyze_threat(request_data),
                    timeout=0.03  # 30ms timeout to stay under 50ms total
                )
                
                # Update detection with spider.cloud data
                local_detection.spider_score = spider_result.get('threat_score', 0.0)
                
                # Adjust severity based on spider.cloud intelligence
                if spider_result.get('threat_score', 0) > 8.0:
                    local_detection.severity_level = max(local_detection.severity_level, 9)
                    local_detection.recommended_action = "block_immediately"
                
            except asyncio.TimeoutError:
                self.logger.debug("Spider.cloud analysis timed out, using local detection")
            except Exception as e:
                self.logger.warning(f"Spider.cloud analysis failed: {str(e)}")
        
        # Store threat detection
        await self._store_threat_detection(local_detection)
        
        # Update performance metrics
        detection_time = time.time() - start_time
        self._update_metrics(detection_time)
        
        return local_detection
    
    def _create_safe_detection(self, request_data: Dict, start_time: float) -> ThreatDetection:
        """Create detection result for whitelisted IP"""
        return ThreatDetection(
            threat_type='none',
            severity_level=0,
            confidence=1.0,
            source_ip=request_data.get('ip', ''),
            user_agent=request_data.get('user_agent', ''),
            request_path=request_data.get('path', ''),
            threat_data={'status': 'whitelisted'},
            spider_score=0.0,
            detection_time=(time.time() - start_time) * 1000,
            recommended_action='allow'
        )
    
    def _create_blocked_detection(self, request_data: Dict, start_time: float) -> ThreatDetection:
        """Create detection result for blocked IP"""
        return ThreatDetection(
            threat_type='blocked_ip',
            severity_level=10,
            confidence=1.0,
            source_ip=request_data.get('ip', ''),
            user_agent=request_data.get('user_agent', ''),
            request_path=request_data.get('path', ''),
            threat_data={'status': 'blocked'},
            spider_score=10.0,
            detection_time=(time.time() - start_time) * 1000,
            recommended_action='block_immediately'
        )
    
    async def _store_threat_detection(self, detection: ThreatDetection):
        """Store threat detection in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO threats (
                        threat_type, severity_level, source_ip, user_agent,
                        request_path, threat_data, spider_threat_score,
                        detection_time, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    detection.threat_type,
                    detection.severity_level,
                    detection.source_ip,
                    detection.user_agent,
                    detection.request_path,
                    json.dumps(detection.threat_data),
                    detection.spider_score,
                    datetime.now(),
                    'active' if detection.severity_level > 0 else 'resolved'
                )
        except Exception as e:
            self.logger.error(f"Failed to store threat detection: {str(e)}")
    
    async def _load_blocked_ips(self):
        """Load blocked IPs from database"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT source_ip 
                    FROM threats 
                    WHERE severity_level >= 8 
                    AND detection_time >= NOW() - INTERVAL '24 hours'
                    AND status = 'active'
                """)
                
                self.blocked_ips = {row['source_ip'] for row in rows}
                self.logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs")
        except Exception as e:
            self.logger.error(f"Failed to load blocked IPs: {str(e)}")
    
    def _update_metrics(self, detection_time: float):
        """Update performance metrics"""
        detection_time_ms = detection_time * 1000
        
        self.detection_count += 1
        self.avg_detection_time = (
            (self.avg_detection_time * (self.detection_count - 1) + detection_time_ms) 
            / self.detection_count
        )
        
        if detection_time_ms > self.target_response_time:
            self.logger.warning(f"Detection time {detection_time_ms:.2f}ms exceeded target {self.target_response_time}ms")
    
    async def get_threat_stats(self) -> Dict:
        """Get threat detection statistics"""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_threats,
                    COUNT(CASE WHEN severity_level >= 8 THEN 1 END) as critical_threats,
                    COUNT(CASE WHEN severity_level >= 5 THEN 1 END) as high_threats,
                    AVG(spider_threat_score) as avg_spider_score,
                    COUNT(DISTINCT source_ip) as unique_ips
                FROM threats 
                WHERE detection_time >= NOW() - INTERVAL '24 hours'
            """)
            
            return {
                'total_threats': stats['total_threats'],
                'critical_threats': stats['critical_threats'],
                'high_threats': stats['high_threats'],
                'avg_spider_score': float(stats['avg_spider_score'] or 0),
                'unique_threat_ips': stats['unique_ips'],
                'blocked_ips_count': len(self.blocked_ips),
                'avg_detection_time_ms': self.avg_detection_time,
                'target_met': self.avg_detection_time <= self.target_response_time,
                'detection_count': self.detection_count
            }
    
    async def block_ip(self, ip: str, reason: str = "Manual block"):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO threats (
                    threat_type, severity_level, source_ip, user_agent,
                    request_path, threat_data, detection_time, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                'manual_block',
                10,
                ip,
                'system',
                '/admin/block',
                json.dumps({'reason': reason}),
                datetime.now(),
                'active'
            )
        
        self.logger.info(f"Blocked IP {ip}: {reason}")
    
    async def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE threats 
                SET status = 'resolved', resolved_at = NOW()
                WHERE source_ip = $1 AND status = 'active'
            """, ip)
        
        self.logger.info(f"Unblocked IP {ip}")
    
    async def close(self):
        """Close all connections"""
        if self.db_pool:
            await self.db_pool.close()
        await self.spider_api.close()

# Example usage and testing
async def main():
    """Test SentinelBot functionality"""
    import os
    
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
    spider_api_key = os.getenv('SPIDER_API_KEY', 'your-api-key')
    
    # Initialize SentinelBot
    sentinel = SentinelBot(database_url, spider_api_key)
    await sentinel.initialize()
    
    # Test threat detection
    test_requests = [
        {
            'ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'path': '/api/users',
            'method': 'GET',
            'headers': {},
            'query_params': {}
        },
        {
            'ip': '10.0.0.1',
            'user_agent': 'sqlmap/1.0',
            'path': "/api/users?id=1' OR '1'='1",
            'method': 'GET',
            'headers': {},
            'query_params': {'id': "1' OR '1'='1"}
        }
    ]
    
    print("SentinelBot Threat Detection Test:")
    for i, request in enumerate(test_requests):
        detection = await sentinel.analyze_request(request)
        print(f"\nRequest {i+1}:")
        print(f"  Threat Type: {detection.threat_type}")
        print(f"  Severity: {detection.severity_level}")
        print(f"  Confidence: {detection.confidence:.3f}")
        print(f"  Detection Time: {detection.detection_time:.2f}ms")
        print(f"  Action: {detection.recommended_action}")
    
    # Get statistics
    stats = await sentinel.get_threat_stats()
    print(f"\nThreat Detection Statistics:")
    print(f"Average Detection Time: {stats['avg_detection_time_ms']:.2f}ms")
    print(f"Target Met (<50ms): {stats['target_met']}")
    
    await sentinel.close()

if __name__ == "__main__":
    asyncio.run(main())

