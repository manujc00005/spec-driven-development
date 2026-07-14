-- Migration: Create webhook_events table for idempotent payment webhook processing
-- This table is the source of truth for webhook idempotency.
-- The UNIQUE constraint on provider_event_id enforces single-process guarantee.

CREATE TABLE webhook_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    -- Provider's unique event identifier. This is the idempotency key.
    -- UNIQUE constraint ensures exactly one event with this ID is processed.
    provider_event_id VARCHAR(255) NOT NULL UNIQUE,

    -- Type of event (e.g., "charge.succeeded", "charge.failed", "customer.created")
    event_type VARCHAR(100) NOT NULL,

    -- Current status of the webhook event
    -- RECEIVED: Event inserted, not yet processed
    -- PROCESSED: Event processed successfully
    -- FAILED: Event processing failed (see failure_reason)
    status VARCHAR(50) NOT NULL DEFAULT 'RECEIVED',

    -- Raw JSON payload as received from the provider
    -- Stored immutably for audit and replay
    -- In production, may be compressed or archived
    payload LONGTEXT NOT NULL,

    -- SHA-256 hash of the raw payload
    -- Allows detecting if the same event_id was sent with different payloads (edge case)
    payload_hash VARCHAR(64),

    -- Cryptographic signature from the webhook header
    -- Stored for audit; not used for verification (verification happens before persistence)
    signature_header VARCHAR(500),

    -- If status=FAILED, this contains the reason why processing failed
    -- Examples: "charge_id not found in payment system", "database unavailable", "invoice creation failed"
    failure_reason TEXT,

    -- Timestamp when the webhook was received by our server
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Timestamp when processing completed (for PROCESSED or FAILED status)
    processed_at TIMESTAMP,

    -- User/service that triggered this action (for audit)
    -- Will be "webhook-receiver" for normal processing, or a username for manual replay
    created_by VARCHAR(100) DEFAULT 'webhook-receiver',
    updated_by VARCHAR(100) DEFAULT 'webhook-receiver',

    -- Ensure processed_at is not before received_at (sanity check)
    CONSTRAINT chk_webhook_timestamps CHECK (processed_at IS NULL OR processed_at >= received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for common queries

-- Find events by status (e.g., to retry failed events)
CREATE INDEX idx_webhook_status ON webhook_events (status);

-- Find recently received events (for monitoring)
CREATE INDEX idx_webhook_received_at ON webhook_events (received_at DESC);

-- Find events by type and status (e.g., all failed "charge.succeeded" events)
CREATE INDEX idx_webhook_type_status ON webhook_events (event_type, status);

-- Find events that were processed at a specific time (for reconciliation)
CREATE INDEX idx_webhook_processed_at ON webhook_events (processed_at);

-- UNIQUE constraint on provider_event_id is the heart of idempotency
-- It is created above with the column definition
-- Additional index is implicit

-- Note on PostgreSQL:
-- If using PostgreSQL instead of MySQL, change:
-- - BIGINT SERIAL -> BIGSERIAL or use an explicit sequence
-- - LONGTEXT -> TEXT
-- - AUTO_INCREMENT -> GENERATED ALWAYS AS IDENTITY
-- - ENGINE=InnoDB -> (not needed, PostgreSQL uses the default storage engine)
-- - CHARSET, COLLATE -> (PostgreSQL uses UTF-8 by default)
-- The UNIQUE constraint and CHECK constraint work identically in PostgreSQL
