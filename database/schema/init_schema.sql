-- AutoBots Database Schema SQL
-- PostgreSQL 17 optimized for Neon serverless
-- Implements GDPR compliance and performance optimization

-- Enable required extensions (compatible with Neon)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Bot configurations table for system settings
CREATE TABLE IF NOT EXISTS bot_configs (
    id BIGSERIAL PRIMARY KEY,
    bot_name VARCHAR(50) UNIQUE NOT NULL,
    config_data JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System settings table for global configuration
CREATE TABLE IF NOT EXISTS system_settings (
    id BIGSERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bot logs table for monitoring and debugging
CREATE TABLE IF NOT EXISTS bot_logs (
    id BIGSERIAL PRIMARY KEY,
    bot_name VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System metrics table for performance monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Threat detections table for SentinelBot
CREATE TABLE IF NOT EXISTS threat_detections (
    id BIGSERIAL PRIMARY KEY,
    threat_id VARCHAR(100) UNIQUE NOT NULL,
    threat_type VARCHAR(50) NOT NULL,
    threat_level VARCHAR(20) NOT NULL CHECK (threat_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    source_data JSONB NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    false_positive BOOLEAN DEFAULT FALSE
);

-- Vendor operations table for OperatorBot
CREATE TABLE IF NOT EXISTS vendor_operations (
    id BIGSERIAL PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    operation_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_details TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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
    threat_type VARCHAR(100) NOT NULL,
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
    gdpr_purge_date TIMESTAMPTZ
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

-- Create indexes for audit log performance
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);

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

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@autobots.com', '$2b$12$example_hash', 'admin'),
('operator', 'operator@autobots.com', '$2b$12$example_hash', 'operator')
ON CONFLICT (username) DO NOTHING;

INSERT INTO affiliates (affiliate_id, company_name, contact_email, disclosure_text, commission_rate) VALUES
('AFF001', 'Example Affiliate Corp', 'contact@example.com', 'Disclosure: We earn commissions from qualifying purchases.', 0.05),
('AFF002', 'Test Marketing LLC', 'info@testmarketing.com', 'Disclosure: We earn commissions from qualifying purchases.', 0.03)
ON CONFLICT (affiliate_id) DO NOTHING;

-- Performance optimization settings (Neon managed)
-- Note: Many settings are automatically optimized by Neon

