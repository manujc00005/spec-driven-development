package com.example.payments;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HexFormat;

/**
 * Verifies webhook signatures using HMAC-SHA256.
 *
 * The payment provider signs each webhook with a shared secret. We verify the signature
 * before processing the webhook to ensure it came from the provider (not forged or tampered).
 *
 * This is a generic implementation. Real integrations will use the provider's SDK
 * (Stripe's Webhook.constructEvent, Square's Webhook signature verification, etc.).
 *
 * Security note: The shared secret is retrieved from configuration/vault, not hardcoded.
 * For this example, we use a constant for simplicity.
 */
@Component
public class WebhookSignatureVerifier {

    private static final Logger log = LoggerFactory.getLogger(WebhookSignatureVerifier.class);

    // In production, this is fetched from AWS Secrets Manager, HashiCorp Vault, or similar.
    // For this example, we use a constant.
    private static final String WEBHOOK_SECRET = "webhook-secret-key-12345";

    private static final String HMAC_ALGORITHM = "HmacSHA256";

    /**
     * Verify a webhook signature.
     *
     * @param payload       The raw webhook payload (as bytes received from HTTP request body).
     * @param providedSignature The signature from the HTTP header (e.g., "t=1234567890,v1=abc...").
     * @return true if the signature is valid, false otherwise.
     */
    public boolean verify(byte[] payload, String providedSignature) {
        if (payload == null || providedSignature == null || providedSignature.isEmpty()) {
            log.warn("Webhook signature verification failed: missing payload or signature");
            return false;
        }

        try {
            // Parse the signature header. Format depends on provider; this is a generic example.
            // Stripe uses: t=timestamp,v1=hex_signature,v0=old_hex_signature
            // For simplicity, we assume providedSignature is the hex-encoded HMAC-SHA256.
            String computedSignature = computeSignature(payload);

            // Constant-time comparison to prevent timing attacks
            if (constantTimeEquals(computedSignature, providedSignature)) {
                log.debug("Webhook signature verification succeeded");
                return true;
            } else {
                log.warn("Webhook signature verification failed: signature mismatch");
                return false;
            }
        } catch (Exception e) {
            log.error("Webhook signature verification error: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Compute the HMAC-SHA256 signature for the payload.
     */
    private String computeSignature(byte[] payload) throws Exception {
        SecretKeySpec key = new SecretKeySpec(
            WEBHOOK_SECRET.getBytes(StandardCharsets.UTF_8),
            0,
            WEBHOOK_SECRET.getBytes(StandardCharsets.UTF_8).length,
            HMAC_ALGORITHM
        );

        Mac mac = Mac.getInstance(HMAC_ALGORITHM);
        mac.init(key);
        byte[] result = mac.doFinal(payload);

        // Return as hex string (or Base64, depending on provider convention)
        return HexFormat.of().formatHex(result);
    }

    /**
     * Constant-time string comparison to prevent timing attacks.
     * Even if the signature is wrong, we take the same time to compare.
     */
    private boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null) {
            return a == b;
        }

        if (a.length() != b.length()) {
            return false;
        }

        int result = 0;
        for (int i = 0; i < a.length(); i++) {
            result |= a.charAt(i) ^ b.charAt(i);
        }

        return result == 0;
    }
}
