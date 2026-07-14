package com.example.payments;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for PaymentWebhookController.
 *
 * These tests verify the HTTP contract:
 * - Valid webhooks return 200.
 * - Invalid signatures return 401.
 * - Malformed payloads return 400.
 * - Transient processing failures return 202.
 */
@WebMvcTest(PaymentWebhookController.class)
public class PaymentWebhookControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PaymentWebhookService paymentWebhookService;

    /**
     * AC-001: Valid webhook is accepted and processed.
     */
    @Test
    public void testValidWebhookReturns200() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_12345\",\"type\":\"charge.succeeded\",\"data\":{\"object\":{\"id\":\"ch_999\"}}}";
        String signature = "valid-signature";

        WebhookEvent event = new WebhookEvent("evt_12345", "charge.succeeded", payload);
        event.setId(1L);
        event.setStatus(WebhookEvent.Status.PROCESSED);

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(signature)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                true, 200, "Event processed successfully", event
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Webhook-Signature", signature)
                .content(payload))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.eventId").value("evt_12345"));
    }

    /**
     * AC-002: Invalid signature returns 401.
     */
    @Test
    public void testInvalidSignatureReturns401() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_12345\",\"type\":\"charge.succeeded\"}";
        String invalidSignature = "invalid-signature";

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(invalidSignature)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                false, 401, "Invalid signature", null
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Webhook-Signature", invalidSignature)
                .content(payload))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.success").value(false));
    }

    /**
     * Malformed JSON returns 400.
     */
    @Test
    public void testMalformedPayloadReturns400() throws Exception {
        // Arrange
        String malformedPayload = "{ invalid json }";
        String signature = "some-signature";

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(signature)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                false, 400, "Malformed payload: JSON parse error", null
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Webhook-Signature", signature)
                .content(malformedPayload))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.success").value(false));
    }

    /**
     * AC-003: Duplicate webhook is accepted and returns 200.
     */
    @Test
    public void testDuplicateWebhookReturns200() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_duplicate\",\"type\":\"charge.succeeded\"}";
        String signature = "valid-signature";

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(signature)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                true, 200, "Event already processed (duplicate)", null
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Webhook-Signature", signature)
                .content(payload))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.success").value(true));
    }

    /**
     * AC-006: Processing failure returns 202 Accepted.
     */
    @Test
    public void testProcessingFailureReturns202() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_fails\",\"type\":\"charge.succeeded\",\"data\":{\"object\":{\"id\":\"ch_notfound\"}}}";
        String signature = "valid-signature";

        WebhookEvent event = new WebhookEvent("evt_fails", "charge.succeeded", payload);
        event.setId(2L);
        event.setStatus(WebhookEvent.Status.FAILED);
        event.setFailureReason("Charge not found in payment system");

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(signature)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                false, 202, "Charge not found in payment system", event
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Webhook-Signature", signature)
                .content(payload))
            .andExpect(status().isAccepted())
            .andExpect(jsonPath("$.success").value(false))
            .andExpect(jsonPath("$.eventId").value("evt_fails"));
    }

    /**
     * Missing signature header is handled.
     */
    @Test
    public void testMissingSignatureHeader() throws Exception {
        // Arrange
        String payload = "{\"id\":\"evt_12345\",\"type\":\"charge.succeeded\"}";

        when(paymentWebhookService.processWebhook(any(byte[].class), eq(null)))
            .thenReturn(new PaymentWebhookService.WebhookProcessingResult(
                false, 401, "Invalid signature", null
            ));

        // Act & Assert
        mockMvc.perform(post("/webhooks/payment-provider")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
            // No signature header provided
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.success").value(false));
    }
}
