package com.example.asrs.wcs

import org.springframework.stereotype.Service
import java.time.Instant
import java.util.ArrayDeque
import java.util.concurrent.atomic.AtomicLong

/**
 * Live application-level communication journal for the educational ASRS lab.
 * This is not a packet capture, durable audit log, or certified machine log.
 * We retain at most [maximumEvents] recent events in memory, without secrets.
 */
data class CommunicationEvent(
    val id: Long,
    val time: String,
    val correlationId: String,
    val from: String,
    val to: String,
    val protocol: String,
    val action: String,
    val outcome: String,
    val payload: Map<String, Any?>,
)

@Service
class CommunicationTraceService {
    private val sequence = AtomicLong(0)
    private val events = ArrayDeque<CommunicationEvent>()
    private val maximumEvents = 350

    @Synchronized
    fun record(
        correlationId: String,
        from: String,
        to: String,
        protocol: String,
        action: String,
        outcome: String,
        payload: Map<String, Any?> = emptyMap(),
    ): CommunicationEvent {
        val event = CommunicationEvent(sequence.incrementAndGet(), Instant.now().toString(),
            correlationId, from, to, protocol, action, outcome, payload.toMap())
        events.addLast(event)
        while (events.size > maximumEvents) events.removeFirst()
        return event
    }

    @Synchronized
    fun recent(): List<CommunicationEvent> = events.toList().asReversed()
}
