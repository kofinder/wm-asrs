package com.example.asrs.wcs

import org.springframework.beans.factory.annotation.Value
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.web.client.RestClient

/**
 * Supervisory interface to the ROS 2 C++ planning node.
 * Planning is advisory; the real PLC must independently validate commands.
 */
data class RackPlan(
    val target: String = "",
    val xMm: Double = 0.0,
    val zMm: Double = 0.0,
    val valid: Boolean = false,
    val message: String = "",
)

@Service
class RosPlannerClient(
    @Value("\${asrs.planner.enabled:false}") private val enabled: Boolean,
    @Value("\${asrs.planner.url:http://127.0.0.1:8091}") private val url: String,
    private val trace: CommunicationTraceService,
) {
    private val http = RestClient.create()

    fun validateTarget(target: String, traceId: String = "SYSTEM"): RackPlan? {
        if (!enabled) {
            trace.record(traceId, "WCS", "ROS 2", "HTTP / JSON", "POST /plan", "DISABLED",
                mapOf("target" to target, "message" to "Planner disabled by configuration"))
            return null
        }
        require(target.matches(Regex("A-(0[1-6])-(0[1-4])"))) {
            "Unsupported rack location: $target"
        }
        val payload = """{"target":"$target"}"""
        trace.record(traceId, "WCS", "ROS 2", "HTTP / JSON", "POST /plan", "SENT",
            mapOf("target" to target))
        val plan = try {
            http.post().uri("${url.trimEnd('/')}/plan")
                .contentType(MediaType.APPLICATION_JSON)
                .contentLength(payload.toByteArray(Charsets.UTF_8).size.toLong())
                .body(payload)
                .retrieve().body(RackPlan::class.java)
        } catch (e: Exception) {
            trace.record(traceId, "ROS 2", "WCS", "HTTP / JSON", "POST /plan failed", "ERROR",
                mapOf("message" to (e.message ?: "ROS unavailable")))
            throw IllegalStateException("ROS planner unavailable or target rejected: ${e.message}", e)
        } ?: throw IllegalStateException("ROS planner returned no plan")

        trace.record(traceId, "ROS 2", "WCS", "HTTP / JSON", "POST /plan response", if (plan.valid) "APPROVED" else "REJECTED",
            mapOf("target" to plan.target, "xMm" to plan.xMm, "zMm" to plan.zMm,
                "valid" to plan.valid, "message" to plan.message))
        check(plan.valid && plan.target == target) {
            "ROS planner did not approve target $target"
        }
        return plan
    }
}
