package com.example.payments;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Data access for webhook events.
 *
 * The UNIQUE constraint on provider_event_id is the source of truth.
 * When a duplicate event is inserted, this repository catches the constraint violation
 * and treats it as idempotency, not as an error.
 */
@Repository
public interface WebhookEventRepository extends JpaRepository<WebhookEvent, Long> {

    /**
     * Find an existing webhook event by its provider event ID.
     * Used to check if an event has already been processed.
     */
    Optional<WebhookEvent> findByProviderEventId(String providerEventId);

    /**
     * Find all failed events so they can be retried manually.
     */
    List<WebhookEvent> findByStatus(WebhookEvent.Status status);

    /**
     * Find failed events of a specific type for targeted retry.
     */
    List<WebhookEvent> findByEventTypeAndStatus(String eventType, WebhookEvent.Status status);

    /**
     * Find recently received events (for monitoring).
     */
    @Query("SELECT w FROM WebhookEvent w WHERE w.receivedAt >= ?1 ORDER BY w.receivedAt DESC")
    List<WebhookEvent> findRecentEvents(LocalDateTime since);

    /**
     * Count events by status (for metrics).
     */
    long countByStatus(WebhookEvent.Status status);

    /**
     * Count events by type and status (for dashboards).
     */
    long countByEventTypeAndStatus(String eventType, WebhookEvent.Status status);
}
