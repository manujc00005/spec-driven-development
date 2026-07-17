package com.example.payments;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * DTO for a payment provider webhook payload.
 *
 * This is a generic model; real integrations will use the provider's SDK types
 * (Stripe Event, Square Event, PayPal WebhookEvent, etc.).
 *
 * Example (generic):
 * {
 *   "id": "evt_12345",
 *   "type": "charge.succeeded",
 *   "created": 1234567890,
 *   "data": {
 *     "object": {
 *       "id": "ch_67890",
 *       "amount": 10000,
 *       "currency": "usd",
 *       "customer": "cus_xyz"
 *     }
 *   }
 * }
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PaymentEventPayload {

    /**
     * Unique event identifier from the provider (the idempotency key).
     */
    @JsonProperty("id")
    private String id;

    /**
     * Type of event (e.g., "charge.succeeded", "charge.failed").
     */
    @JsonProperty("type")
    private String type;

    /**
     * Unix timestamp when the event was created at the provider.
     */
    @JsonProperty("created")
    private Long created;

    /**
     * Event data (provider-specific structure).
     */
    @JsonProperty("data")
    private EventData data;

    // Getters and setters

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Long getCreated() {
        return created;
    }

    public void setCreated(Long created) {
        this.created = created;
    }

    public EventData getData() {
        return data;
    }

    public void setData(EventData data) {
        this.data = data;
    }

    /**
     * Inner DTO for event data object.
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class EventData {
        @JsonProperty("object")
        private ChargeObject object;

        public ChargeObject getObject() {
            return object;
        }

        public void setObject(ChargeObject object) {
            this.object = object;
        }
    }

    /**
     * Inner DTO for charge/payment object.
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ChargeObject {
        @JsonProperty("id")
        private String id;

        @JsonProperty("amount")
        private Long amount;

        @JsonProperty("currency")
        private String currency;

        @JsonProperty("customer")
        private String customer;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public Long getAmount() {
            return amount;
        }

        public void setAmount(Long amount) {
            this.amount = amount;
        }

        public String getCurrency() {
            return currency;
        }

        public void setCurrency(String currency) {
            this.currency = currency;
        }

        public String getCustomer() {
            return customer;
        }

        public void setCustomer(String customer) {
            this.customer = customer;
        }
    }

    @Override
    public String toString() {
        return "PaymentEventPayload{" +
                "id='" + id + '\'' +
                ", type='" + type + '\'' +
                ", created=" + created +
                '}';
    }
}
