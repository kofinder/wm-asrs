package com.example.asrs.wcs

import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.bind.annotation.RestControllerAdvice
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

@RestController
@RequestMapping("/api")
class CraneController(
    private val opc: OpcUaClientService,
    private val tasks: TaskService,
    private val planner: RosPlannerClient,
    private val trace: CommunicationTraceService,
) {
    private val lastReportedStatus = ConcurrentHashMap<String, TaskStatus>()

    @GetMapping("/crane/status")
    fun craneStatus(): Map<String, Any> = opc.status()

    @PostMapping("/tasks/putaway")
    fun putaway(@RequestBody request: PutawayRequest): ResponseEntity<TaskView> {
        val correlation = request.externalTaskId ?: "WCS-${UUID.randomUUID()}"
        trace.record(correlation, "WMS", "WCS", "REST / JSON", "POST /api/tasks/putaway", "RECEIVED",
            mapOf("palletId" to request.palletId, "targetLocation" to request.targetLocation,
                "externalTaskId" to request.externalTaskId))
        return try {
            val result = tasks.putaway(request, correlation)
            trace.record(correlation, "WCS", "WMS", "REST / JSON", "HTTP 202 Accepted", "RESPONSE",
                mapOf("taskId" to result.taskId, "commandId" to result.commandId,
                    "operation" to result.operation.name, "status" to result.status.name))
            ResponseEntity.status(HttpStatus.ACCEPTED).body(result)
        } catch (e: RuntimeException) {
            trace.record(correlation, "WCS", "WMS", "REST / JSON", "Task request failed", "ERROR",
                mapOf("message" to (e.message ?: "Unknown failure")))
            throw e
        }
    }

    @PostMapping("/tasks/retrieval")
    fun retrieval(@RequestBody request: RetrievalRequest): ResponseEntity<TaskView> {
        val correlation = request.externalTaskId ?: "WCS-${UUID.randomUUID()}"
        trace.record(correlation, "WMS", "WCS", "REST / JSON", "POST /api/tasks/retrieval", "RECEIVED",
            mapOf("palletId" to request.palletId, "sourceLocation" to request.sourceLocation,
                "externalTaskId" to request.externalTaskId))
        return try {
            val result = tasks.retrieve(request, correlation)
            trace.record(correlation, "WCS", "WMS", "REST / JSON", "HTTP 202 Accepted", "RESPONSE",
                mapOf("taskId" to result.taskId, "commandId" to result.commandId,
                    "operation" to result.operation.name, "status" to result.status.name))
            ResponseEntity.status(HttpStatus.ACCEPTED).body(result)
        } catch (e: RuntimeException) {
            trace.record(correlation, "WCS", "WMS", "REST / JSON", "Task request failed", "ERROR",
                mapOf("message" to (e.message ?: "Unknown failure")))
            throw e
        }
    }

    @GetMapping("/tasks")
    fun listTasks(): List<TaskView> = tasks.list()

    @GetMapping("/tasks/{taskId}")
    fun task(@PathVariable taskId: String): ResponseEntity<TaskView> =
        tasks.get(taskId)?.let { view ->
            // WMS polls every ~800 ms. Journal the *actual* GET and response only
            // once per task state, avoiding hundreds of duplicate events.
            if (lastReportedStatus.put(taskId, view.status) != view.status) {
                val correlation = view.externalTaskId ?: view.taskId
                trace.record(correlation, "WMS / API client", "WCS", "REST / JSON",
                    "GET /api/tasks/{taskId}", "RECEIVED", mapOf("taskId" to taskId))
                trace.record(correlation, "WCS", "WMS / API client", "REST / JSON",
                    "HTTP 200 task status", "RESPONSE",
                    mapOf("taskId" to view.taskId, "commandId" to view.commandId,
                        "status" to view.status.name, "operation" to view.operation.name,
                        "targetLocation" to view.targetLocation))
            }
            ResponseEntity.ok(view)
        } ?: ResponseEntity.notFound().build()

    // Compatibility with the previous Java project.
    data class MoveRequest(val target: String)

    @PostMapping("/crane/move")
    fun move(@RequestBody request: MoveRequest): ResponseEntity<Map<String, Any>> {
        val correlation = "DIRECT-${UUID.randomUUID()}"
        trace.record(correlation, "API CLIENT", "WCS", "REST / JSON", "POST /api/crane/move", "RECEIVED",
            mapOf("target" to request.target))
        planner.validateTarget(request.target, correlation)
        val commandId = opc.requestMove(request.target, traceId = correlation)
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(
            mapOf("commandId" to commandId, "target" to request.target, "status" to "ACCEPTED")
        )
    }
}

@RestControllerAdvice
class ApiErrorHandler {
    @ExceptionHandler(IllegalArgumentException::class)
    fun badRequest(e: IllegalArgumentException): ResponseEntity<Map<String, String>> =
        ResponseEntity.badRequest().body(mapOf("error" to (e.message ?: "Invalid request")))

    @ExceptionHandler(IllegalStateException::class)
    fun conflict(e: IllegalStateException): ResponseEntity<Map<String, String>> =
        ResponseEntity.status(HttpStatus.CONFLICT)
            .body(mapOf("error" to (e.message ?: "Equipment unavailable")))
}
