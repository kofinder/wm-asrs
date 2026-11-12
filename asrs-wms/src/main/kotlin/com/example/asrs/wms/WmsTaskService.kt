package com.example.asrs.wms

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.client.SimpleClientHttpRequestFactory
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import org.springframework.web.client.RestClient
import java.time.Instant
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

data class WarehouseTask(
    val wmsTaskId: String,
    val palletId: String,
    val targetLocation: String, // rack for both operations
    val createdAt: String,
    val wcsTaskId: String? = null,
    val commandId: Int? = null,
    val status: String = "SUBMITTING",
    val storedLocation: String? = null,
    val detail: String = "",
    val completedAt: String? = null,
    val operation: String = "PUTAWAY",
)

data class ConfirmedStock(
    val palletId: String,
    val location: String,
    val sourceTaskId: String,
    val confirmedAt: String,
)

@Service
class WmsTaskService(@Value("\${asrs.wcs.base-url}") wcsUrl: String) {
    private val log = LoggerFactory.getLogger(javaClass)
    private val http = RestClient.builder().baseUrl(wcsUrl)
        .requestFactory(SimpleClientHttpRequestFactory().apply {
            setConnectTimeout(3_000)
            setReadTimeout(5_000)
        }).build()
    private val tasks = ConcurrentHashMap<String, WarehouseTask>()
    private val reservedStates = setOf("SUBMITTING", "ACCEPTED", "RUNNING", "UNCERTAIN")

    private fun checkNoOpenTask() {
        require(tasks.values.none { it.status in reservedStates }) {
            "A WMS task is active or uncertain. Wait for completion or reconcile before continuing"
        }
    }

    /**
     * In-memory event ledger: only verified COMPLETED tasks change inventory.
     * A pending / uncertain retrieval keeps the pallet in stock but RESERVED.
     */
    @Synchronized
    fun inventory(): List<ConfirmedStock> {
        val stock = linkedMapOf<String, ConfirmedStock>()
        tasks.values.filter { it.status == "COMPLETED" }
            .sortedBy { it.createdAt }.forEach { event ->
                if (event.operation == "PUTAWAY" && event.storedLocation == event.targetLocation) {
                    stock[event.palletId] = ConfirmedStock(event.palletId, event.targetLocation,
                        event.wmsTaskId, event.completedAt ?: event.createdAt)
                } else if (event.operation == "RETRIEVAL") {
                    stock.remove(event.palletId)
                }
            }
        return stock.values.sortedBy { it.location }
    }

    @Synchronized
    fun submit(palletId: String, targetLocation: String): WarehouseTask {
        validatePallet(palletId)
        validateRack(targetLocation)
        checkNoOpenTask()
        val stock = inventory()
        require(stock.none { it.palletId == palletId }) { "Pallet $palletId is already stored" }
        require(stock.none { it.location == targetLocation }) { "Rack $targetLocation is occupied" }
        require(tasks.values.none { it.palletId == palletId && it.status in reservedStates }) {
            "Pallet $palletId has an active or uncertain task; reconcile first"
        }
        require(tasks.values.none { it.operation == "PUTAWAY" &&
            it.targetLocation == targetLocation && it.status in reservedStates }) {
            "Rack $targetLocation is reserved by an active or uncertain task"
        }
        return issue("PUTAWAY", palletId, targetLocation)
    }

    @Synchronized
    fun retrieve(palletId: String): WarehouseTask {
        validatePallet(palletId)
        checkNoOpenTask()
        val stock = inventory().find { it.palletId == palletId }
            ?: throw IllegalArgumentException("No verified stored pallet $palletId in WMS inventory")
        require(tasks.values.none { it.palletId == palletId && it.status in reservedStates }) {
            "Pallet $palletId has an active or uncertain task; reconcile first"
        }
        return issue("RETRIEVAL", palletId, stock.location)
    }

    private fun validatePallet(value: String) {
        require(value.matches(Regex("[A-Za-z0-9_-]{1,40}"))) { "Invalid pallet ID" }
    }

    private fun validateRack(value: String) {
        require(value.matches(Regex("A-(0[1-6])-(0[1-4])"))) {
            "For this Gazebo demo use A-01-01 through A-06-04"
        }
    }

    private fun issue(operation: String, pallet: String, rack: String): WarehouseTask {
        val id = "WMS-${UUID.randomUUID()}"
        val entry = WarehouseTask(id, pallet, rack, Instant.now().toString(), operation = operation)
        tasks[id] = entry // reserve before network call
        try {
            val endpoint = if (operation == "RETRIEVAL") "/api/tasks/retrieval" else "/api/tasks/putaway"
            val body = if (operation == "RETRIEVAL")
                mapOf("palletId" to pallet, "sourceLocation" to rack, "externalTaskId" to id)
            else
                mapOf("palletId" to pallet, "targetLocation" to rack, "externalTaskId" to id)
            val reply = http.post().uri(endpoint).body(body)
                .retrieve().body(Map::class.java) ?: error("WCS returned no response")
            val wcsId = reply["taskId"]?.toString() ?: error("WCS returned no taskId")
            val updated = entry.copy(wcsTaskId = wcsId,
                commandId = (reply["commandId"] as? Number)?.toInt(),
                status = reply["status"]?.toString() ?: "UNCERTAIN",
                detail = "WCS accepted $operation request")
            tasks[id] = updated
            return updated
        } catch (e: Exception) {
            // A timeout is not proof that the PLC did not execute the command.
            val uncertain = entry.copy(status = "UNCERTAIN",
                detail = "WCS response uncertain: ${e.message}. Check PLC IDs before retrying.")
            tasks[id] = uncertain
            log.warn("{} submit uncertain {}: {}", operation, id, e.message)
            return uncertain
        }
    }

    fun list(): List<WarehouseTask> = tasks.values.sortedByDescending { it.createdAt }

    @Scheduled(fixedDelay = 800L)
    fun refresh() {
        tasks.values.filter { it.wcsTaskId != null && it.status !in setOf("COMPLETED", "UNCERTAIN") }
            .forEach { task ->
                try {
                    val reply = http.get().uri("/api/tasks/{id}", task.wcsTaskId!!)
                        .retrieve().body(Map::class.java) ?: return@forEach
                    val status = reply["status"]?.toString() ?: return@forEach
                    val complete = status == "COMPLETED"
                    val latest = task.copy(status = status,
                        storedLocation = if (complete && task.operation == "PUTAWAY")
                            task.targetLocation else null,
                        completedAt = if (complete) Instant.now().toString() else null,
                        detail = when (status) {
                            "COMPLETED" -> if (task.operation == "RETRIEVAL")
                                "Verified outbound release; pallet removed from WMS inventory"
                                else "Verified rack position and command ID"
                            "UNCERTAIN" -> "Result uncertain; manually reconcile PLC and WCS"
                            else -> "Waiting for virtual PLC confirmation"
                        })
                    tasks.replace(task.wmsTaskId, task, latest)
                } catch (e: Exception) {
                    log.warn("Cannot refresh WCS task {}: {}", task.wcsTaskId, e.message)
                }
            }
    }
}
