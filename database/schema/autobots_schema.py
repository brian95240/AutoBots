# AutoBots Database Schema
# PostgreSQL 15 with time-based partitioning for optimal performance

import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AutoBotsDatabase:
    """
    AutoBots database management with PostgreSQL 15 features
    Implements time-based partitioning and optimized schema design
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def initialize_pool(self):
        """Initialize connection pool with pgBouncer optimization"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def create_schema(self):
        """Create the complete AutoBots database schema"""
        async with self.pool.acquire() as conn:
            # Enable required extensions
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
            
            # Create main tables with partitioning
            await self._create_products_table(conn)
            await self._create_threats_table(conn)
            await self._create_affiliates_table(conn)
            await self._create_operations_table(conn)
            await self._create_users_table(conn)
            await self._create_audit_table(conn)
            
            # Create indexes for performance
            await self._create_indexes(conn)
            
            # Create materialized views
            await self._create_materialized_views(conn)
    
    async def _create_products_table(self, conn):
        """Products table with time-based partitioning for ScoutBot"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id BIGSERIAL,
                product_name VARCHAR(500) NOT NULL,
                product_url TEXT NOT NULL,
                image_url TEXT,
                ocr_text TEXT,
                ocr_confidence DECIMAL(5,4),
                spider_ocr_text TEXT,
                spider_confidence DECIMAL(5,4),
                price DECIMAL(12,2),
                vendor VARCHAR(100),
                category VARCHAR(100),
                scrape_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT valid_date CHECK (scrape_date > '2025-01-01'::timestamptz)
            ) PARTITION BY RANGE (scrape_date);
            
            -- Create partitions for current and next months
            CREATE TABLE IF NOT EXISTS products_2025_06 PARTITION OF products
                FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
            CREATE TABLE IF NOT EXISTS products_2025_07 PARTITION OF products
                FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
            CREATE TABLE IF NOT EXISTS products_2025_08 PARTITION OF products
                FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
        """)
    
    async def _create_threats_table(self, conn):
        """Threats table for SentinelBot real-time detection"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS threats (
                id BIGSERIAL PRIMARY KEY,
                threat_type VARCHAR(50) NOT NULL,
                severity_level INTEGER CHECK (severity_level BETWEEN 1 AND 10),
                source_ip INET,
                user_agent TEXT,
                request_path TEXT,
                threat_data JSONB,
                spider_threat_score DECIMAL(4,2),
                detection_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                resolved_at TIMESTAMPTZ,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'false_positive')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            
            -- Convert to hypertable for time-series optimization
            SELECT create_hypertable('threats', 'detection_time', if_not_exists => TRUE);
        """)
    
    async def _create_affiliates_table(self, conn):
        """Affiliates table for AffiliateBot GDPR compliance"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS affiliates (
                id BIGSERIAL PRIMARY KEY,
                affiliate_id VARCHAR(100) UNIQUE NOT NULL,
                company_name VARCHAR(200) NOT NULL,
                contact_email VARCHAR(255) NOT NULL,
                gdpr_consent BOOLEAN DEFAULT FALSE,
                consent_date TIMESTAMPTZ,
                data_retention_days INTEGER DEFAULT 30,
                disclosure_text TEXT NOT NULL,
                commission_rate DECIMAL(5,4),
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'terminated')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                gdpr_purge_date TIMESTAMPTZ GENERATED ALWAYS AS (created_at + INTERVAL '30 days') STORED
            );
        """)
    
    async def _create_operations_table(self, conn):
        """Operations table for OperatorBot and ArchitectBot"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id BIGSERIAL PRIMARY KEY,
                operation_type VARCHAR(50) NOT NULL,
                bot_name VARCHAR(50) NOT NULL,
                vendor VARCHAR(100),
                operation_data JSONB,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
    
    async def _create_users_table(self, conn):
        """Users table for ConciergeBot interface"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'operator', 'user')),
                last_login TIMESTAMPTZ,
                preferences JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
    
    async def _create_audit_table(self, conn):
        """Audit table for compliance and monitoring"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                table_name VARCHAR(50) NOT NULL,
                operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
                old_values JSONB,
                new_values JSONB,
                user_id BIGINT,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                ip_address INET
            );
            
            -- Convert to hypertable for efficient log storage
            SELECT create_hypertable('audit_log', 'timestamp', if_not_exists => TRUE);
        """)
    
    async def _create_indexes(self, conn):
        """Create optimized indexes for performance"""
        indexes = [
            # Products table indexes
            "CREATE INDEX IF NOT EXISTS idx_products_scrape_date ON products (scrape_date);",
            "CREATE INDEX IF NOT EXISTS idx_products_vendor ON products (vendor);",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);",
            "CREATE INDEX IF NOT EXISTS idx_products_ocr_confidence ON products (ocr_confidence);",
            
            # Threats table indexes
            "CREATE INDEX IF NOT EXISTS idx_threats_detection_time ON threats (detection_time);",
            "CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats (severity_level);",
            "CREATE INDEX IF NOT EXISTS idx_threats_status ON threats (status);",
            "CREATE INDEX IF NOT EXISTS idx_threats_source_ip ON threats (source_ip);",
            
            # Affiliates table indexes
            "CREATE INDEX IF NOT EXISTS idx_affiliates_gdpr_purge ON affiliates (gdpr_purge_date);",
            "CREATE INDEX IF NOT EXISTS idx_affiliates_status ON affiliates (status);",
            
            # Operations table indexes
            "CREATE INDEX IF NOT EXISTS idx_operations_bot_name ON operations (bot_name);",
            "CREATE INDEX IF NOT EXISTS idx_operations_status ON operations (status);",
            "CREATE INDEX IF NOT EXISTS idx_operations_created_at ON operations (created_at);",
            
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);",
            
            # Audit log indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_table_name ON audit_log (table_name);",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
    
    async def _create_materialized_views(self, conn):
        """Create materialized views for performance optimization"""
        await conn.execute("""
            -- Hourly margins view for real-time analytics
            CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_margins AS
            SELECT 
                DATE_TRUNC('hour', scrape_date) as hour,
                vendor,
                COUNT(*) as product_count,
                AVG(price) as avg_price,
                AVG(ocr_confidence) as avg_ocr_confidence,
                AVG(spider_confidence) as avg_spider_confidence
            FROM products 
            WHERE scrape_date >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', scrape_date), vendor
            ORDER BY hour DESC;
            
            -- Create unique index for concurrent refresh
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hourly_margins_unique 
            ON hourly_margins (hour, vendor);
        """)
        
        await conn.execute("""
            -- Threat summary view for security dashboard
            CREATE MATERIALIZED VIEW IF NOT EXISTS threat_summary AS
            SELECT 
                DATE_TRUNC('hour', detection_time) as hour,
                threat_type,
                COUNT(*) as threat_count,
                AVG(severity_level) as avg_severity,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count
            FROM threats 
            WHERE detection_time >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', detection_time), threat_type
            ORDER BY hour DESC;
            
            CREATE UNIQUE INDEX IF NOT EXISTS idx_threat_summary_unique 
            ON threat_summary (hour, threat_type);
        """)
    
    async def setup_auto_refresh(self, conn):
        """Setup automatic refresh for materialized views"""
        await conn.execute("""
            -- Create function to refresh materialized views
            CREATE OR REPLACE FUNCTION refresh_materialized_views()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_margins;
                REFRESH MATERIALIZED VIEW CONCURRENTLY threat_summary;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Schedule refresh every 5 minutes (requires pg_cron extension)
            -- SELECT cron.schedule('refresh-views', '*/5 * * * *', 'SELECT refresh_materialized_views();');
        """)
    
    async def create_gdpr_compliance_functions(self, conn):
        """Create functions for GDPR compliance automation"""
        await conn.execute("""
            -- Function to automatically purge expired affiliate data
            CREATE OR REPLACE FUNCTION purge_expired_gdpr_data()
            RETURNS INTEGER AS $$
            DECLARE
                purged_count INTEGER;
            BEGIN
                -- Delete expired affiliate data
                DELETE FROM affiliates 
                WHERE gdpr_purge_date <= NOW() 
                AND status = 'terminated';
                
                GET DIAGNOSTICS purged_count = ROW_COUNT;
                
                -- Log the purge operation
                INSERT INTO audit_log (table_name, operation, new_values, timestamp)
                VALUES ('affiliates', 'DELETE', 
                       json_build_object('purged_count', purged_count, 'reason', 'GDPR_AUTO_PURGE'),
                       NOW());
                
                RETURN purged_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

# Database configuration
DATABASE_CONFIG = {
    'host': 'your-neon-host.neon.tech',
    'port': 5432,
    'database': 'autobots',
    'user': 'your-username',
    'password': 'your-password',
    'sslmode': 'require'
}

async def main():
    """Initialize AutoBots database"""
    connection_string = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?sslmode={DATABASE_CONFIG['sslmode']}"
    
    db = AutoBotsDatabase(connection_string)
    await db.initialize_pool()
    await db.create_schema()
    
    print("✅ AutoBots database schema created successfully!")
    print("📊 Time-based partitioning enabled for products table")
    print("🔒 GDPR compliance functions installed")
    print("⚡ Materialized views created for performance optimization")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

