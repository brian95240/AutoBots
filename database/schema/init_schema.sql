-- AutoBots Database Schema SQL
-- PostgreSQL 15 with TimescaleDB for time-series optimization
-- Implements time-based partitioning and GDPR compliance

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Products table with time-based partitioning for ScoutBot
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

-- Threats table for SentinelBot real-time detection
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

-- Affiliates table for AffiliateBot GDPR compliance
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

-- Operations table for OperatorBot and ArchitectBot
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

-- Users table for ConciergeBot interface
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

-- Audit table for compliance and monitoring
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

-- Create optimized indexes for performance
-- Products table indexes
CREATE INDEX IF NOT EXISTS idx_products_scrape_date ON products (scrape_date);
CREATE INDEX IF NOT EXISTS idx_products_vendor ON products (vendor);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_ocr_confidence ON products (ocr_confidence);

-- Threats table indexes
CREATE INDEX IF NOT EXISTS idx_threats_detection_time ON threats (detection_time);
CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats (severity_level);
CREATE INDEX IF NOT EXISTS idx_threats_status ON threats (status);
CREATE INDEX IF NOT EXISTS idx_threats_source_ip ON threats (source_ip);

-- Affiliates table indexes
CREATE INDEX IF NOT EXISTS idx_affiliates_gdpr_purge ON affiliates (gdpr_purge_date);
CREATE INDEX IF NOT EXISTS idx_affiliates_status ON affiliates (status);

-- Operations table indexes
CREATE INDEX IF NOT EXISTS idx_operations_bot_name ON operations (bot_name);
CREATE INDEX IF NOT EXISTS idx_operations_status ON operations (status);
CREATE INDEX IF NOT EXISTS idx_operations_created_at ON operations (created_at);

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_table_name ON audit_log (table_name);

-- Materialized views for performance optimization
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

-- Functions for automation and GDPR compliance
-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_margins;
    REFRESH MATERIALIZED VIEW CONCURRENTLY threat_summary;
END;
$$ LANGUAGE plpgsql;

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

-- Schedule automatic tasks (requires pg_cron extension)
-- Refresh materialized views every 5 minutes
SELECT cron.schedule('refresh-views', '*/5 * * * *', 'SELECT refresh_materialized_views();');

-- GDPR data purge daily at 2 AM
SELECT cron.schedule('gdpr-purge', '0 2 * * *', 'SELECT purge_expired_gdpr_data();');

-- Create partition maintenance function
CREATE OR REPLACE FUNCTION maintain_partitions()
RETURNS void AS $$
DECLARE
    next_month_start DATE;
    next_month_end DATE;
    partition_name TEXT;
BEGIN
    -- Calculate next month dates
    next_month_start := DATE_TRUNC('month', NOW() + INTERVAL '2 months');
    next_month_end := next_month_start + INTERVAL '1 month';
    
    -- Generate partition name
    partition_name := 'products_' || TO_CHAR(next_month_start, 'YYYY_MM');
    
    -- Create partition if it doesn't exist
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF products FOR VALUES FROM (%L) TO (%L)',
                   partition_name, next_month_start, next_month_end);
END;
$$ LANGUAGE plpgsql;

-- Schedule partition maintenance monthly
SELECT cron.schedule('partition-maintenance', '0 0 1 * *', 'SELECT maintain_partitions();');

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@autobots.com', '$2b$12$example_hash', 'admin'),
('operator', 'operator@autobots.com', '$2b$12$example_hash', 'operator')
ON CONFLICT (username) DO NOTHING;

INSERT INTO affiliates (affiliate_id, company_name, contact_email, disclosure_text, commission_rate) VALUES
('AFF001', 'Example Affiliate Corp', 'contact@example.com', 'Disclosure: We earn commissions from qualifying purchases.', 0.05),
('AFF002', 'Test Marketing LLC', 'info@testmarketing.com', 'Disclosure: We earn commissions from qualifying purchases.', 0.03)
ON CONFLICT (affiliate_id) DO NOTHING;

-- Performance optimization settings
-- Enable parallel query execution
SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 8;

-- Optimize for time-series workloads
SET shared_preload_libraries = 'timescaledb, pg_stat_statements';
SET timescaledb.max_background_workers = 8;

