package com.example.payments;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * Domain model: A webhook event from a payment provider.
 *
 * This is the source of truth for webhook idempotency. The UNIQUE constraint on
 * provider_event_id at the database level is the actual enforcement; this entity
 * is the application representation.
 *
 * The lifecycle is: RECEIVED -> PROCESSED or RECEIVED -> FAILED.
 * Once set, status never goes backward.
 */
@Entity
@Table(name = "webhook_events", indexes = {
    @Index(name = "idx_webhook_status", columnList = "status"),
    @Index(name = "idx_webhook_received_at", columnList = "received_at"),
    @Index(name = "idx_webhook_type_status", columnList = "event_type, status")
})
public class WebhookEvent {

    public enum Status {
        RECEIVED,     // Event inserted, not yet processed
        PROCESSED,    // Processing succeeded
        FAILED        // Processing failed (check failure_reason)
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Provider's unique event identifier (e.g., "evt_abc123" or "ch_xyz789").
     * This is the idempotency key. UNIQUE constraint at database level.
     */
    @Column(name = "provider_event_id", nullable = false, unique = true, length = 255)
    private String providerEventId;

    /**
     * Event type (e.g., "charge.succeeded", "charge.failed", "customer.created").
     */
    @Column(name = "event_type", nullable = false, length = 100)
    private String eventType;

    /**
     * Current status of the event.
     */
    @Column(name = "status", nullable = false, length = 50)
    @Enumerated(EnumType.STRING)
    private Status status;

    /**
     * Raw JSON payload as received from the provider.
     * Stored immutably for audit and replay.
     */
    @Column(name = "payload", nullable = false, columnDefinition = "LONGTEXT")
    private String payload;

    /**
     * SHA-256 hash of the raw payload for integrity verification.
     */
    @Column(name = "payload_hash", length = 64)
    private String payloadHash;

    /**
     * Cryptographic signature from the webhook HTTP header.
     * Stored for audit; the actual signature verification happens in the controller
     * before this entity is ever persisted.
     */
    @Column(name = "signature_header", length = 500)
    private String signatureHeader;

    /**
     * Failure reason, populated if status = FAILED.
     * Examples: "charge_id not found", "database unavailable", "invoice creation failed".
     */
    @Column(name = "failure_reason", columnDefinition = "TEXT")
    private String failureReason;

    /**
     * Timestamp when the webhook was received.
     * Set at INSERT time, never changed.
     */
    @Column(name = "received_at", nullable = false, updatable = false)
    private LocalDateTime receivedAt;

    /**
     * Timestamp when processing completed (for PROCESSED or FAILED status).
     * Null if status = RECEIVED.
     */
    @Column(name = "processed_at")
    private LocalDateTime processedAt;

    /**
     * User or service that created this record (audit).
     */
    @Column(name = "created_by", length = 100)
    private String createdBy;

    /**
     * User or service that last updated this record (audit).
     */
    @Column(name = "updated_by", length = 100)
    private String updatedBy;

    // Constructors

    public WebhookEvent() {
    }

    public WebhookEvent(String providerEventId, String eventType, String payload) {
        this.providerEventId = providerEventId;
        this.eventType = eventType;
        this.payload = payload;
        this.status = Status.RECEIVED;
        this.receivedAt = LocalDateTime.now();
        this.createdBy = "webhook-receiver";
        this.updatedBy = "webhook-receiver";
    }

    // Getters and setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getProviderEventId() {
        return providerEventId;
    }

    public void setProviderEventId(String providerEventId) {
        this.providerEventId = providerEventId;
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public String getPayload() {
        return payload;
    }

    public void setPayload(String payload) {
        this.payload = payload;
    }

    public String getPayloadHash() {
        return payloadHash;
    }

    public void setPayloadHash(String payloadHash) {
        this.payloadHash = payloadHash;
    }

    public String getSignatureHeader() {
        return signatureHeader;
    }

    public void setSignatureHeader(String signatureHeader) {
        this.signatureHeader = signatureHeader;
    }

    public String getFailureReason() {
        return failureReason;
    }

    public void setFailureReason(String failureReason) {
        this.failureReason = failureReason;
    }

    public LocalDateTime getReceivedAt() {
        return receivedAt;
    }

    public void setReceivedAt(LocalDateTime receivedAt) {
        this.receivedAt = receivedAt;
    }

    public LocalDateTime getProcessedAt() {
        return processedAt;
    }

    public void setProcessedAt(LocalDateTime processedAt) {
        this.processedAt = processedAt;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(String createdBy) {
        this.createdBy = createdBy;
    }

    public String getUpdatedBy() {
        return updatedBy;
    }

    public void setUpdatedBy(String updatedBy) {
        this.updatedBy = updatedBy;
    }

    @Override
    public String toString() {
        return "WebhookEvent{" +
                "id=" + id +
                ", providerEventId='" + providerEventId + '\'' +
                ", eventType='" + eventType + '\'' +
                ", status=" + status +
                ", receivedAt=" + receivedAt +
                ", processedAt=" + processedAt +
                ", failureReason='" + failureReason + '\'' +
                '}';
    }
}
