package com.example.payments;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;

import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Tests for PaymentWebhookService.
 *
 * These tests verify the core idempotency guarantees:
 * - First event is processed successfully.
 * - Duplicate event is detected and skipped.
 * - Invalid signature is rejected before processing.
 * - Processing failures are recorded and transient errors are returned.
 * - Concurrent duplicates are handled safely by the database constraint.
 */
@ExtendWith(MockitoExtension.class)
public class PaymentWebhookServiceTest {

    private PaymentWebhookService service;

    @Mock
    private WebhookEventRepository webhookEventRepository;

    @Mock
    private WebhookSignatureVerifier signatureVerifier;

    @Mock
    private PaymentProvider paymentProvider;

    private ObjectMapper objectMapper;

    @BeforeEach
    public void setUp() {
        objectMapper = new ObjectMapper();
        service = new PaymentWebhookService(
            webhookEventRepository,
            signatureVerifier,
            paymentProvider,
            objectMapper
        );
    }

    /**
     * AC-003: Valid, new events are processed exactly once.
     */
    @Test
    public void testProcessFirstEvent() throws Exception {
        // Arrange
        String eventId = "evt_12345";
        String eventType = "charge.succeeded";
        String payload = "{\"id\":\"" + eventId + "\",\"type\":\"" + eventType + "\",\"data\":{\"object\":{\"id\":\"ch_999\",\"amount\":10000,\"currency\":\"usd\"}}}";
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String signature = "valid-signature";

        when(signatureVerifier.verify(rawPayload, signature)).thenReturn(true);
        when(webhookEventRepository.save(any(WebhookEvent.class))).thenAnswer(invocation -> {
            WebhookEvent event = invocation.getArgument(0);
            event.setId(1L); // Simulate ID generation
            return event;
        });
        doNothing().when(paymentProvider).processEvent(any(PaymentEventPayload.class));

        // Act
        var result = service.processWebhook(rawPayload, signature);

        // Assert
        assertTrue(result.success(), "Processing should succeed");
        assertEquals(200, result.httpStatus(), "First event should return 200 OK");
        assertEquals(WebhookEvent.Status.PROCESSED, result.event().getStatus(), "Event status should be PROCESSED");
        assertNotNull(result.event().getProcessedAt(), "processed_at should be set");
        verify(paymentProvider, times(1)).processEvent(any()); // Processed exactly once
    }

    /**
     * AC-003, AC-004: Duplicate events are not processed twice.
     * When a duplicate event is received, the UNIQUE constraint violation is caught,
     * and we return 200 without processing.
     */
    @Test
    public void testDuplicateEventIsNotProcessedTwice() throws Exception {
        // Arrange
        String eventId = "evt_duplicate";
        String payload = "{\"id\":\"" + eventId + "\",\"type\":\"charge.succeeded\",\"data\":{\"object\":{\"id\":\"ch_999\"}}}";
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String signature = "valid-signature";

        when(signatureVerifier.verify(rawPayload, signature)).thenReturn(true);

        // Mock the repository to throw UNIQUE constraint violation
        when(webhookEventRepository.save(any(WebhookEvent.class)))
            .thenThrow(new DataIntegrityViolationException("Duplicate entry for provider_event_id"));

        // Act
        var result = service.processWebhook(rawPayload, signature);

        // Assert
        assertTrue(result.success(), "Duplicate should be treated as success");
        assertEquals(200, result.httpStatus(), "Duplicate should return 200 OK");
        verify(paymentProvider, never()).processEvent(any()); // Never processed
    }

    /**
     * AC-002: Invalid signatures are rejected before processing.
     */
    @Test
    public void testInvalidSignatureRejected() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_invalid\",\"type\":\"charge.succeeded\"}";
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String invalidSignature = "invalid-signature";

        when(signatureVerifier.verify(rawPayload, invalidSignature)).thenReturn(false);

        // Act
        var result = service.processWebhook(rawPayload, invalidSignature);

        // Assert
        assertFalse(result.success(), "Invalid signature should fail");
        assertEquals(401, result.httpStatus(), "Invalid signature should return 401");
        verify(webhookEventRepository, never()).save(any()); // Never persisted
        verify(paymentProvider, never()).processEvent(any()); // Never processed
    }

    /**
     * Malformed JSON payloads are rejected.
     */
    @Test
    public void testMalformedPayloadRejected() {
        // Arrange
        byte[] malformedPayload = "{ invalid json }".getBytes(StandardCharsets.UTF_8);
        String signature = "some-signature";

        when(signatureVerifier.verify(malformedPayload, signature)).thenReturn(true);

        // Act
        var result = service.processWebhook(malformedPayload, signature);

        // Assert
        assertFalse(result.success(), "Malformed payload should fail");
        assertEquals(400, result.httpStatus(), "Malformed payload should return 400");
        verify(webhookEventRepository, never()).save(any()); // Never persisted
    }

    /**
     * AC-006: Processing failures are recorded and return 202 Accepted.
     */
    @Test
    public void testProcessingFailureRecorded() throws Exception {
        // Arrange
        String eventId = "evt_fails";
        String payload = "{\"id\":\"" + eventId + "\",\"type\":\"charge.succeeded\",\"data\":{\"object\":{\"id\":\"ch_notfound\"}}}";
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String signature = "valid-signature";

        when(signatureVerifier.verify(rawPayload, signature)).thenReturn(true);
        when(webhookEventRepository.save(any(WebhookEvent.class))).thenAnswer(invocation -> {
            WebhookEvent event = invocation.getArgument(0);
            event.setId(2L);
            return event;
        });

        // PaymentProvider throws an exception during processing
        doThrow(new RuntimeException("Charge not found in payment system"))
            .when(paymentProvider).processEvent(any(PaymentEventPayload.class));

        // Act
        var result = service.processWebhook(rawPayload, signature);

        // Assert
        assertFalse(result.success(), "Processing failure should not be success");
        assertEquals(202, result.httpStatus(), "Processing failure should return 202 Accepted");
        assertEquals(WebhookEvent.Status.FAILED, result.event().getStatus(), "Event status should be FAILED");
        assertNotNull(result.event().getFailureReason(), "failure_reason should be populated");
        assertTrue(result.event().getFailureReason().contains("Charge not found"), "failure_reason should contain error details");
        verify(paymentProvider, times(1)).processEvent(any()); // Attempted once
    }

    /**
     * Missing event ID is rejected.
     */
    @Test
    public void testMissingEventIdRejected() throws Exception {
        // Arrange
        String payload = "{\"type\":\"charge.succeeded\"}"; // Missing 'id'
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String signature = "valid-signature";

        when(signatureVerifier.verify(rawPayload, signature)).thenReturn(true);

        // Act
        var result = service.processWebhook(rawPayload, signature);

        // Assert
        assertFalse(result.success(), "Missing event ID should fail");
        assertEquals(400, result.httpStatus(), "Missing event ID should return 400");
        verify(webhookEventRepository, never()).save(any());
    }

    /**
     * Missing event type is rejected.
     */
    @Test
    public void testMissingEventTypeRejected() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_12345\"}"; // Missing 'type'
        byte[] rawPayload = payload.getBytes(StandardCharsets.UTF_8);
        String signature = "valid-signature";

        when(signatureVerifier.verify(rawPayload, signature)).thenReturn(true);

        // Act
        var result = service.processWebhook(rawPayload, signature);

        // Assert
        assertFalse(result.success(), "Missing event type should fail");
        assertEquals(400, result.httpStatus(), "Missing event type should return 400");
        verify(webhookEventRepository, never()).save(any());
    }
}
