package com.example.asrs.wcs

import org.slf4j.LoggerFactory
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import java.time.Instant
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

enum class TaskStatus { ACCEPTED, RUNNING, COMPLETED, UNCERTAIN }
enum class TaskOperation { PUTAWAY, RETRIEVAL }

data class PutawayRequest(val palletId: String, val targetLocation: String, val externalTaskId: String? = null)
data class RetrievalRequest(val palletId: String, val sourceLocation: String, val externalTaskId: String? = null)

data class TaskView(
    val taskId: String,
    val externalTaskId: String?,
    val palletId: String,
    // Rack address for both operations; RETRIEVAL returns to OUTBOUND.
    val targetLocation: String,
    val commandId: Int,
    val status: TaskStatus,
    val createdAt: Instant,
    val completedAt: Instant? = null,
    val operation: TaskOperation = TaskOperation.PUTAWAY,
)

@Service
class TaskService(private val opc: OpcUaClientService, private val planner: RosPlannerClient,
                  private val trace: CommunicationTraceService) {
    private val log = LoggerFactory.getLogger(javaClass)
    private val tasks = ConcurrentHashMap<String, TaskView>()
    private val byExternalId = ConcurrentHashMap<String, String>()
    private val traceByTaskId = ConcurrentHashMap<String, String>()
    private val rackPattern = Regex("A-(0[1-6])-(0[1-4])")

    private fun validate(palletId: String, rack: String, externalId: String?) {
        require(palletId.matches(Regex("[A-Za-z0-9_-]{1,40}"))) { "Invalid pallet ID" }
        require(rack.matches(rackPattern)) { "Rack must be A-01-01 through A-06-04 for Gazebo lab" }
        externalId?.let { require(it.matches(Regex("[A-Za-z0-9_-]{1,80}"))) { "Invalid externalTaskId" } }
    }

    private fun idempotent(externalId: String?, palletId: String, rack: String,
                           operation: TaskOperation): TaskView? {
        if (externalId == null) return null
        val existingId = byExternalId[externalId] ?: return null
        val existing = requireNotNull(tasks[existingId])
        require(existing.palletId == palletId && existing.targetLocation == rack &&
                existing.operation == operation) { "externalTaskId was used for another task" }
        return existing
    }

    /** In-memory demo ledger: only COMPLETED operations change stock. */
    fun storedPallets(): Map<String, String> {
        val result = linkedMapOf<String, String>()
        tasks.values.filter { it.status == TaskStatus.COMPLETED }
            .sortedBy { it.createdAt }.forEach { task ->
                if (task.operation == TaskOperation.PUTAWAY) result[task.palletId] = task.targetLocation
                else result.remove(task.palletId)
            }
        return result
    }

    private fun checkSingleCrane() {
        check(tasks.values.none { it.status in setOf(TaskStatus.ACCEPTED, TaskStatus.RUNNING,
                                                     TaskStatus.UNCERTAIN) }) {
            "Crane has an active or uncertain task. Reconcile before issuing another command"
        }
    }

    @Synchronized
    fun putaway(request: PutawayRequest, traceId: String = "DIRECT"): TaskView {
        validate(request.palletId, request.targetLocation, request.externalTaskId)
        idempotent(request.externalTaskId, request.palletId, request.targetLocation,
            TaskOperation.PUTAWAY)?.let { return it }
        checkSingleCrane()
        val stored = storedPallets()
        check(request.palletId !in stored) { "Pallet ${request.palletId} is already stored" }
        check(request.targetLocation !in stored.values) { "Rack ${request.targetLocation} is occupied" }
        // Fail closed for uncertain commands: don't reuse slot or pallet until reconciled.
        check(tasks.values.none { it.status == TaskStatus.UNCERTAIN &&
            (it.palletId == request.palletId || it.targetLocation == request.targetLocation) }) {
            "Prior uncertain task affects this pallet/rack; manual reconciliation required"
        }
        planner.validateTarget(request.targetLocation, traceId)
        val commandId = opc.requestMove(request.targetLocation, "PUTAWAY", traceId)
        return register(request.palletId, request.targetLocation, request.externalTaskId,
            commandId, TaskOperation.PUTAWAY, traceId)
    }

    @Synchronized
    fun retrieve(request: RetrievalRequest, traceId: String = "DIRECT"): TaskView {
        validate(request.palletId, request.sourceLocation, request.externalTaskId)
        idempotent(request.externalTaskId, request.palletId, request.sourceLocation,
            TaskOperation.RETRIEVAL)?.let { return it }
        checkSingleCrane()
        check(storedPallets()[request.palletId] == request.sourceLocation) {
            "No verified stored pallet ${request.palletId} at ${request.sourceLocation} in WCS memory"
        }
        check(tasks.values.none { it.status == TaskStatus.UNCERTAIN &&
            (it.palletId == request.palletId || it.targetLocation == request.sourceLocation) }) {
            "Prior uncertain task affects this pallet/rack; manual reconciliation required"
        }
        planner.validateTarget(request.sourceLocation, traceId)
        val commandId = opc.requestMove(request.sourceLocation, "RETRIEVAL", traceId)
        return register(request.palletId, request.sourceLocation, request.externalTaskId,
            commandId, TaskOperation.RETRIEVAL, traceId)
    }

    private fun register(pallet: String, rack: String, externalId: String?, commandId: Int,
                         operation: TaskOperation, traceId: String): TaskView {
        val task = TaskView(UUID.randomUUID().toString(), externalId, pallet, rack,
            commandId, TaskStatus.ACCEPTED, Instant.now(), operation = operation)
        tasks[task.taskId] = task
        traceByTaskId[task.taskId] = traceId
        trace.record(traceId, "WCS", "WCS task ledger", "INTERNAL", "Task registered", "ACCEPTED",
            mapOf("taskId" to task.taskId, "commandId" to commandId,
                "palletId" to pallet, "rack" to rack, "operation" to operation.name))
        externalId?.let { byExternalId[it] = task.taskId }
        log.info("Accepted {} task={} pallet={} rack={} command={}",
            operation, task.taskId, pallet, rack, commandId)
        return task
    }

    fun get(taskId: String): TaskView? = tasks[taskId]
    fun list(): List<TaskView> = tasks.values.sortedByDescending { it.createdAt }

    /** Match PLC command IDs, operation-specific destination and reported release. */
    @Scheduled(fixedDelay = 400L)
    fun reconcile() {
        val pending = tasks.values.filter { it.status == TaskStatus.ACCEPTED || it.status == TaskStatus.RUNNING }
        if (pending.isEmpty()) return
        try {
            val completed = opc.read("CompletedCommandId") as Int
            val accepted = opc.read("AcceptedCommandId") as Int
            val rejected = opc.read("RejectedCommandId") as Int
            val released = opc.read("ReleasedCommandId") as Int
            val fault = opc.read("FaultCode") as Int
            val busy = opc.read("Busy") as Boolean
            val position = opc.read("Position") as String
            for (task in pending) {
                val atDestination = when (task.operation) {
                    TaskOperation.PUTAWAY -> position == task.targetLocation
                    TaskOperation.RETRIEVAL -> position == "OUTBOUND" && released == task.commandId
                }
                val state = when {
                    completed == task.commandId && atDestination -> TaskStatus.COMPLETED
                    rejected == task.commandId || (accepted == task.commandId && fault != 0) -> TaskStatus.UNCERTAIN
                    completed >= task.commandId && !atDestination -> TaskStatus.UNCERTAIN
                    accepted == task.commandId && busy -> TaskStatus.RUNNING
                    else -> task.status
                }
                if (state != task.status) {
                    val next = task.copy(status = state,
                        completedAt = if (state == TaskStatus.COMPLETED) Instant.now() else null)
                    tasks.replace(task.taskId, task, next)
                    log.info("{} {} -> {}", task.operation, task.taskId, state)
                    val traceId = traceByTaskId[task.taskId] ?: task.externalTaskId ?: task.taskId
                    trace.record(traceId, "PLC simulator", "WCS", "OPC UA READ",
                        "Completion verification", if (state == TaskStatus.COMPLETED) "VERIFIED" else state.name,
                        mapOf("commandId" to task.commandId,
                            "acceptedCommandId" to accepted, "completedCommandId" to completed,
                            "rejectedCommandId" to rejected, "releasedCommandId" to released,
                            "position" to position, "faultCode" to fault, "busy" to busy,
                            "expectedRack" to task.targetLocation, "operation" to task.operation.name))
                }
            }
        } catch (e: Exception) {
            // Timeout does not mean the machine did not move.
            log.warn("PLC state unknown; do not retry automatically: {}", e.message)
        }
    }
}
