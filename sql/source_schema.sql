-- Schema definition for raw ingestion database (Bronze / Landing Layer)

CREATE TABLE IF NOT EXISTS raw_requests (
    request_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    request_parameters JSONB NOT NULL,
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status_code INT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE
);

-- Performance Index to optimize transformer read queries filtering for un-processed records
CREATE INDEX IF NOT EXISTS idx_raw_processed ON raw_requests(processed);
