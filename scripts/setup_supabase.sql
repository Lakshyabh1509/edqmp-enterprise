-- =============================================================================
-- EDQMP Database Schema for Supabase
-- Run this in the Supabase SQL Editor
-- =============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. DATA QUALITY RULES
-- Stores configurable validation rules
-- =============================================================================
CREATE TABLE IF NOT EXISTS quality_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN (
        'completeness', 'accuracy', 'consistency', 
        'timeliness', 'uniqueness', 'anomaly', 'custom'
    )),
    config JSONB NOT NULL DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- =============================================================================
-- 2. DATA SOURCES (Pipelines to Monitor)
-- Stores connection and configuration for data sources
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
        'database', 'api', 'file', 'stream', 'warehouse'
    )),
    connection_config JSONB DEFAULT '{}', -- Encrypted connection details
    schema_info JSONB DEFAULT '{}', -- Expected schema definition
    sla_config JSONB DEFAULT '{
        "max_latency_ms": 300000,
        "min_freshness_hours": 24,
        "expected_records_min": 0
    }',
    schedule_cron VARCHAR(100), -- Cron expression for scheduled validation
    is_active BOOLEAN DEFAULT true,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- =============================================================================
-- 3. RULE-SOURCE MAPPINGS
-- Links rules to data sources
-- =============================================================================
CREATE TABLE IF NOT EXISTS rule_source_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES quality_rules(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    custom_config JSONB DEFAULT '{}', -- Override rule config for this source
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(rule_id, source_id)
);

-- =============================================================================
-- 4. VALIDATION RESULTS
-- Stores outcomes of validation runs
-- =============================================================================
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID REFERENCES quality_rules(id) ON DELETE SET NULL,
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    execution_time TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed', 'failed', 'warning', 'error', 'skipped')),
    score DECIMAL(5,4) CHECK (score >= 0 AND score <= 1), -- 0.0000 to 1.0000
    threshold DECIMAL(5,4),
    records_checked INTEGER DEFAULT 0,
    records_passed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    details JSONB DEFAULT '{}', -- Detailed failure information
    sample_failures JSONB DEFAULT '[]', -- Sample of failed records
    duration_ms INTEGER,
    run_id UUID, -- Group multiple validations in a single run
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- 5. PIPELINE RUNS
-- Tracks ETL/ELT workflow executions
-- =============================================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(id) ON DELETE SET NULL,
    external_run_id VARCHAR(255), -- External DAG run ID (Airflow, etc.)
    pipeline_name VARCHAR(255),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status VARCHAR(20) CHECK (status IN ('pending', 'running', 'success', 'failed', 'timeout', 'cancelled')),
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_deleted INTEGER DEFAULT 0,
    latency_ms INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 6. ALERT CONFIGURATIONS
-- Defines when and how to send alerts
-- =============================================================================
CREATE TABLE IF NOT EXISTS alert_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_id UUID REFERENCES quality_rules(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('email', 'slack', 'webhook', 'pagerduty', 'teams')),
    channel_config JSONB NOT NULL DEFAULT '{}', -- Channel-specific settings
    threshold_config JSONB DEFAULT '{
        "trigger_on_status": ["failed", "error"],
        "min_score_threshold": 0.95,
        "consecutive_failures": 1
    }',
    cooldown_minutes INTEGER DEFAULT 60, -- Minimum time between alerts
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- =============================================================================
-- 7. ALERT HISTORY
-- Records sent alerts
-- =============================================================================
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID REFERENCES alert_configs(id) ON DELETE SET NULL,
    validation_result_id UUID REFERENCES validation_results(id) ON DELETE SET NULL,
    pipeline_run_id UUID REFERENCES pipeline_runs(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('quality_failure', 'pipeline_failure', 'sla_breach', 'anomaly')),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) CHECK (status IN ('pending', 'sent', 'failed', 'acknowledged', 'resolved')),
    recipients JSONB DEFAULT '[]',
    message TEXT,
    response JSONB DEFAULT '{}',
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- =============================================================================
-- 8. AUDIT LOGS
-- Immutable record of all system actions
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    entity_name VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 9. QUALITY METRICS (Aggregated)
-- Pre-computed metrics for dashboard performance
-- =============================================================================
CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_validations INTEGER DEFAULT 0,
    passed_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    warning_validations INTEGER DEFAULT 0,
    average_score DECIMAL(5,4),
    min_score DECIMAL(5,4),
    max_score DECIMAL(5,4),
    total_records_checked BIGINT DEFAULT 0,
    total_records_failed BIGINT DEFAULT 0,
    average_latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, metric_date)
);

-- =============================================================================
-- INDEXES for Performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_validation_results_rule ON validation_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_source ON validation_results(source_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_time ON validation_results(execution_time DESC);
CREATE INDEX IF NOT EXISTS idx_validation_results_status ON validation_results(status);
CREATE INDEX IF NOT EXISTS idx_validation_results_run ON validation_results(run_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_source ON pipeline_runs(source_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_time ON pipeline_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);

CREATE INDEX IF NOT EXISTS idx_alert_history_time ON alert_history(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON alert_history(status);

CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_quality_metrics_date ON quality_metrics(metric_date DESC);

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_quality_rules_updated_at
    BEFORE UPDATE ON quality_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_configs_updated_at
    BEFORE UPDATE ON alert_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================
ALTER TABLE quality_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE rule_source_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_metrics ENABLE ROW LEVEL SECURITY;

-- Policies: Allow authenticated users to read all, write own
CREATE POLICY "Allow authenticated read" ON quality_rules
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated insert" ON quality_rules
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Allow owner update" ON quality_rules
    FOR UPDATE TO authenticated USING (auth.uid() = created_by);

-- Similar policies for other tables (simplified for dev)
CREATE POLICY "Allow authenticated read" ON data_sources FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON data_sources FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON validation_results FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON validation_results FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON pipeline_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON pipeline_runs FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON alert_configs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON alert_configs FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON alert_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON alert_history FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON audit_logs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated insert" ON audit_logs FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Allow authenticated read" ON quality_metrics FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON quality_metrics FOR ALL TO authenticated USING (true);

CREATE POLICY "Allow authenticated read" ON rule_source_mappings FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated write" ON rule_source_mappings FOR ALL TO authenticated USING (true);

-- =============================================================================
-- SEED DATA (Sample rules for testing)
-- =============================================================================
INSERT INTO quality_rules (name, description, rule_type, config, severity, tags) VALUES
(
    'trade_completeness',
    'Ensure all required trade fields are populated',
    'completeness',
    '{"columns": ["trade_id", "symbol", "quantity", "price", "execution_time"], "threshold": 0.99}',
    'critical',
    ARRAY['trading', 'compliance']
),
(
    'account_format_validation',
    'Validate account numbers match expected format',
    'accuracy',
    '{"column": "account_number", "pattern": "^[A-Z]{2}[0-9]{10}$", "threshold": 1.0}',
    'critical',
    ARRAY['kyc', 'compliance']
),
(
    'price_anomaly_detection',
    'Detect unusual price movements using z-score',
    'anomaly',
    '{"column": "price", "method": "zscore", "z_threshold": 3.0}',
    'warning',
    ARRAY['trading', 'risk']
),
(
    'customer_uniqueness',
    'Ensure no duplicate customer records',
    'uniqueness',
    '{"columns": ["customer_id", "document_number"]}',
    'critical',
    ARRAY['kyc', 'compliance']
),
(
    'data_freshness_check',
    'Validate data is updated within SLA window',
    'timeliness',
    '{"timestamp_column": "updated_at", "max_age_hours": 24}',
    'warning',
    ARRAY['sla', 'monitoring']
)
ON CONFLICT (name) DO NOTHING;

-- Sample data source
INSERT INTO data_sources (name, description, source_type, sla_config, tags) VALUES
(
    'trade_settlement_db',
    'Primary trade settlement database',
    'database',
    '{"max_latency_ms": 300000, "min_freshness_hours": 1, "expected_records_min": 1000}',
    ARRAY['trading', 'tier1']
),
(
    'kyc_customer_api',
    'Customer KYC data API',
    'api',
    '{"max_latency_ms": 60000, "min_freshness_hours": 24, "expected_records_min": 100}',
    ARRAY['kyc', 'compliance']
),
(
    'fx_rates_stream',
    'Real-time FX rates data stream',
    'stream',
    '{"max_latency_ms": 5000, "min_freshness_hours": 0.1, "expected_records_min": 10000}',
    ARRAY['trading', 'market-data']
)
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- VIEWS for Dashboard
-- =============================================================================
CREATE OR REPLACE VIEW v_quality_summary AS
SELECT 
    ds.id as source_id,
    ds.name as source_name,
    COUNT(vr.id) as total_validations,
    COUNT(CASE WHEN vr.status = 'passed' THEN 1 END) as passed_count,
    COUNT(CASE WHEN vr.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN vr.status = 'warning' THEN 1 END) as warning_count,
    ROUND(AVG(vr.score)::numeric, 4) as avg_score,
    MAX(vr.execution_time) as last_validation
FROM data_sources ds
LEFT JOIN validation_results vr ON ds.id = vr.source_id
GROUP BY ds.id, ds.name;

CREATE OR REPLACE VIEW v_pipeline_health AS
SELECT 
    ds.id as source_id,
    ds.name as source_name,
    COUNT(pr.id) as total_runs,
    COUNT(CASE WHEN pr.status = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN pr.status = 'failed' THEN 1 END) as failed_count,
    ROUND(AVG(pr.latency_ms)::numeric, 0) as avg_latency_ms,
    MAX(pr.ended_at) as last_run
FROM data_sources ds
LEFT JOIN pipeline_runs pr ON ds.id = pr.source_id
GROUP BY ds.id, ds.name;

SELECT 'EDQMP Database Schema Created Successfully!' as status;
