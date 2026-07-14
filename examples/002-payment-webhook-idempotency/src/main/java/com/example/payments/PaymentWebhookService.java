package com.example.payments;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.HexFormat;

/**
 * Service for processing payment webhooks idempotently.
 *
 * Core responsibilities:
 * 1. Verify the webhook signature (delegated to WebhookSignatureVerifier).
 * 2. Extract the provider event ID (idempotency key) from the payload.
 * 3. Store the event in the database with UNIQUE constraint idempotency.
 * 4. Process the event if it's new, or return success if it's a duplicate.
 * 5. Handle processing errors gracefully, recording the failure reason.
 *
 * The flow is:
 * - INSERT webhook_events with provider_event_id
 *   → If UNIQUE constraint violated: duplicate detected, return success
 *   → If INSERT succeeds: process the event in a transaction
 * - If processing fails: record failure reason, return transient error (202)
 * - If processing succeeds: update status to PROCESSED, return success (200)
 */
@Service
public class PaymentWebhookService {

    private static final Logger log = LoggerFactory.getLogger(PaymentWebhookService.class);

    private final WebhookEventRepository webhookEventRepository;
    private final WebhookSignatureVerifier signatureVerifier;
    private final PaymentProvider paymentProvider;
    private final ObjectMapper objectMapper;

    public PaymentWebhookService(
            WebhookEventRepository webhookEventRepository,
            WebhookSignatureVerifier signatureVerifier,
            PaymentProvider paymentProvider,
            ObjectMapper objectMapper
    ) {
        this.webhookEventRepository = webhookEventRepository;
        this.signatureVerifier = signatureVerifier;
        this.paymentProvider = paymentProvider;
        this.objectMapper = objectMapper;
    }

    /**
     * Result of processing a webhook.
     */
    public record WebhookProcessingResult(
        boolean success,
        int httpStatus,
        String message,
        WebhookEvent event
    ) {}

    /**
     * Process a webhook from the payment provider.
     *
     * @param rawPayload    Raw request body (bytes).
     * @param signatureHeader Signature from HTTP header.
     * @return WebhookProcessingResult with HTTP status code and message.
     */
    public WebhookProcessingResult processWebhook(byte[] rawPayload, String signatureHeader) {
        // Step 1: Verify signature (before persisting anything)
        if (!signatureVerifier.verify(rawPayload, signatureHeader)) {
            log.warn("Rejecting webhook: signature verification failed");
            return new WebhookProcessingResult(
                false, 401, "Invalid signature", null
            );
        }

        // Step 2: Deserialize payload
        PaymentEventPayload payload;
        try {
            payload = objectMapper.readValue(rawPayload, PaymentEventPayload.class);
        } catch (Exception e) {
            log.warn("Rejecting webhook: malformed payload - {}", e.getMessage());
            return new WebhookProcessingResult(
                false, 400, "Malformed payload: " + e.getMessage(), null
            );
        }

        // Step 3: Validate required fields
        if (payload.getId() == null || payload.getId().isEmpty()) {
            log.warn("Rejecting webhook: missing provider event ID");
            return new WebhookProcessingResult(
                false, 400, "Missing provider event ID", null
            );
        }

        if (payload.getType() == null || payload.getType().isEmpty()) {
            log.warn("Rejecting webhook: missing event type");
            return new WebhookProcessingResult(
                false, 400, "Missing event type", null
            );
        }

        // Step 4: Create WebhookEvent entity and insert it (UNIQUE constraint idempotency)
        WebhookEvent event = new WebhookEvent(
            payload.getId(),
            payload.getType(),
            new String(rawPayload, StandardCharsets.UTF_8)
        );
        event.setSignatureHeader(signatureHeader);
        event.setPayloadHash(computePayloadHash(rawPayload));

        try {
            webhookEventRepository.save(event);
            log.info("Webhook event {} received and stored", event.getProviderEventId());
        } catch (DataIntegrityViolationException e) {
            // UNIQUE constraint violation: duplicate event
            log.info("Webhook event {} is a duplicate, skipping processing", payload.getId());
            return new WebhookProcessingResult(
                true, 200, "Event already processed (duplicate)", null
            );
        }

        // Step 5: Process the event in a transaction
        return processEventInTransaction(event, payload);
    }

    /**
     * Process the webhook event after successful storage.
     * Runs in a separate transaction so that processing failures are recorded separately.
     */
    @Transactional
    protected WebhookProcessingResult processEventInTransaction(
            WebhookEvent event,
            PaymentEventPayload payload
    ) {
        try {
            // Delegate to the payment provider abstraction
            paymentProvider.processEvent(payload);

            // Mark as processed
            event.setStatus(WebhookEvent.Status.PROCESSED);
            event.setProcessedAt(LocalDateTime.now());
            event.setUpdatedBy("webhook-receiver");
            webhookEventRepository.save(event);

            log.info("Webhook event {} processed successfully", event.getProviderEventId());
            return new WebhookProcessingResult(
                true, 200, "Event processed successfully", event
            );
        } catch (Exception e) {
            // Mark as failed with reason
            String failureReason = "Processing failed: " + e.getClass().getSimpleName() + " - " + e.getMessage();
            log.warn("Webhook event {} processing failed: {}", event.getProviderEventId(), failureReason, e);

            event.setStatus(WebhookEvent.Status.FAILED);
            event.setProcessedAt(LocalDateTime.now());
            event.setFailureReason(failureReason);
            event.setUpdatedBy("webhook-receiver");
            webhookEventRepository.save(event);

            // Return 202 Accepted so the provider retries
            return new WebhookProcessingResult(
                false, 202, failureReason, event
            );
        }
    }

    /**
     * Compute SHA-256 hash of the payload for integrity verification.
     */
    private String computePayloadHash(byte[] payload) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(payload);
            return HexFormat.of().formatHex(hash);
        } catch (Exception e) {
            log.warn("Failed to compute payload hash: {}", e.getMessage());
            return null;
        }
    }
}

/**
 * Abstraction for processing payment events.
 * This is implemented by a real payment provider integration.
 * For testing, this can be mocked to succeed or fail on demand.
 */
interface PaymentProvider {
    void processEvent(PaymentEventPayload payload) throws Exception;
}

/**
 * Stub/mock implementation of PaymentProvider.
 * In a real system, this would call the payment system to look up the charge,
 * create an invoice, emit emails, update accounting records, etc.
 */
@Component
class PaymentProviderStub implements PaymentProvider {
    private static final Logger log = LoggerFactory.getLogger(PaymentProviderStub.class);

    @Override
    public void processEvent(PaymentEventPayload payload) throws Exception {
        if (payload.getType() == null) {
            throw new IllegalArgumentException("Event type is required");
        }

        // Simulate processing
        log.info("Processing event type: {}, charge ID: {}",
            payload.getType(),
            payload.getData() != null && payload.getData().getObject() != null
                ? payload.getData().getObject().getId()
                : "N/A"
        );

        // In a real implementation:
        // - Lookup the charge in the payment system
        // - Create an invoice in the accounting system
        // - Emit customer notification emails
        // - Update reconciliation records
        // - Trigger downstream workflows
    }
}
