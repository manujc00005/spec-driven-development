package com.example.payments;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * HTTP endpoint for receiving payment webhooks.
 *
 * Responsibilities:
 * - Parse the HTTP request (raw body, headers).
 * - Extract the signature from headers.
 * - Delegate to the service for business logic.
 * - Return appropriate HTTP status codes based on the processing result.
 *
 * Does not contain business logic; that's in PaymentWebhookService.
 */
@RestController
@RequestMapping("/webhooks")
public class PaymentWebhookController {

    private static final Logger log = LoggerFactory.getLogger(PaymentWebhookController.class);

    private final PaymentWebhookService paymentWebhookService;

    public PaymentWebhookController(PaymentWebhookService paymentWebhookService) {
        this.paymentWebhookService = paymentWebhookService;
    }

    /**
     * POST /webhooks/payment-provider
     *
     * Receive a webhook event from the payment provider.
     *
     * Request format:
     * - Content-Type: application/json
     * - Body: JSON payload
     * - Header X-Webhook-Signature: Cryptographic signature
     *
     * Response:
     * - 200 OK: Event processed successfully or already processed (duplicate).
     * - 202 Accepted: Event received but processing failed transiently (provider should retry).
     * - 400 Bad Request: Malformed payload (provider should not retry).
     * - 401 Unauthorized: Signature verification failed (provider should not retry this event).
     * - 500 Internal Server Error: Unexpected server error (provider should retry).
     */
    @PostMapping("/payment-provider")
    public ResponseEntity<?> receiveWebhook(
            @RequestBody byte[] rawPayload,
            @RequestHeader(value = "X-Webhook-Signature", required = false) String signatureHeader
    ) {
        log.info("Received webhook: payload size={} bytes, signature present={}",
            rawPayload.length, signatureHeader != null && !signatureHeader.isEmpty());

        // Process the webhook
        PaymentWebhookService.WebhookProcessingResult result =
            paymentWebhookService.processWebhook(rawPayload, signatureHeader);

        // Return the appropriate HTTP status
        HttpStatus status = HttpStatus.valueOf(result.httpStatus());
        Map<String, Object> response = Map.of(
            "success", result.success(),
            "message", result.message(),
            "eventId", result.event() != null ? result.event().getProviderEventId() : null
        );

        log.info("Webhook response: status={}, eventId={}",
            status, result.event() != null ? result.event().getProviderEventId() : "N/A");

        return ResponseEntity.status(status).body(response);
    }

    /**
     * Health check endpoint for monitoring.
     */
    @GetMapping("/health")
    public ResponseEntity<?> health() {
        return ResponseEntity.ok(Map.of("status", "up", "service", "payment-webhook-receiver"));
    }
}
