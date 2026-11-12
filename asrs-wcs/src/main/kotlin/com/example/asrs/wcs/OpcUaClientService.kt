package com.example.asrs.wcs

import jakarta.annotation.PostConstruct
import jakarta.annotation.PreDestroy
import org.eclipse.milo.opcua.sdk.client.OpcUaClient
import org.eclipse.milo.opcua.sdk.client.subscriptions.OpcUaMonitoredItem
import org.eclipse.milo.opcua.sdk.client.subscriptions.OpcUaSubscription
import org.eclipse.milo.opcua.stack.core.NodeIds
import org.eclipse.milo.opcua.stack.core.security.SecurityPolicy
import org.eclipse.milo.opcua.stack.core.types.builtin.DataValue
import org.eclipse.milo.opcua.stack.core.types.builtin.LocalizedText
import org.eclipse.milo.opcua.stack.core.types.builtin.NodeId
import org.eclipse.milo.opcua.stack.core.types.builtin.Variant
import org.eclipse.milo.opcua.stack.core.types.enumerated.TimestampsToReturn
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import java.util.concurrent.atomic.AtomicInteger

/** OPC UA client adapter. One WCS process and one virtual crane only. */
@Service
class OpcUaClientService(
    @Value("\${asrs.opcua.endpoint}") private val endpoint: String,
    @Value("\${asrs.opcua.namespace}") private val namespaceUri: String,
    private val trace: CommunicationTraceService,
) {
    private val log = LoggerFactory.getLogger(javaClass)
    private lateinit var client: OpcUaClient
    private var subscription: OpcUaSubscription? = null
    private var namespaceIndex: Int = -1
    private val sequence = AtomicInteger(0)

    @PostConstruct
    fun connect() {
        client = OpcUaClient.create(
            endpoint,
            { endpoints ->
                endpoints.stream()
                    .filter { it.securityPolicyUri == SecurityPolicy.None.uri }
                    .filter { it.endpointUrl?.contains("/milo") == true }
                    .findFirst()
            },
            { /* default TCP transport config */ },
            { config ->
                config.setApplicationName(LocalizedText.english("ASRS Kotlin WCS"))
                    .setApplicationUri("urn:asrs:wcs:kotlin")
            },
        )

        client.connect()
        val namespaceData = readDataValue(NodeIds.Server_NamespaceArray)
        val namespaceUris = requireNotNull(namespaceData.value.value) as Array<*>
        namespaceIndex = namespaceUris.indexOf(namespaceUri)
        check(namespaceIndex >= 0) { "Namespace not found: $namespaceUri" }
        sequence.set(read("CommandId") as Int)
        subscribe()
        log.info("Connected to {} (namespaceIndex={})", endpoint, namespaceIndex)
        trace.record("SYSTEM", "WCS", "PLC simulator", "OPC UA", "Client connected", "CONNECTED",
            mapOf("endpoint" to endpoint, "namespaceUri" to namespaceUri, "namespaceIndex" to namespaceIndex))
    }

    private fun node(name: String): NodeId = NodeId(namespaceIndex, "ASRS/Crane01/$name")

    private fun readDataValue(nodeId: NodeId): DataValue {
        val result = client.readValuesAsync(
            0.0, TimestampsToReturn.Both, listOf(nodeId),
        ).get().single()
        check(result.statusCode.isGood) { "OPC UA read error: ${result.statusCode} for $nodeId" }
        return result
    }

    fun read(name: String): Any = requireNotNull(readDataValue(node(name)).value.value) {
        "Null value from $name"
    }

    private fun write(name: String, value: Any, traceId: String) {
        val result = client.writeValues(
            listOf(node(name)),
            listOf(DataValue.valueOnly(Variant(value))),
        )
        check(result.size == 1 && result.single().isGood) {
            "OPC UA write error for $name: $result"
        }
        trace.record(traceId, "WCS", "PLC simulator", "OPC UA WRITE",
            "Write ASRS/Crane01/$name", "GOOD",
            mapOf("nodeId" to node(name).toString(), "namespaceUri" to namespaceUri,
                "value" to value, "valueType" to value.javaClass.simpleName,
                "statusCode" to result.single().toString()))
    }

    private fun subscribe() {
        val sub = OpcUaSubscription(client)
        sub.create()
        listOf("MachineState", "AcceptedCommandId", "RejectedCommandId",
            "CompletedCommandId", "Position", "FaultCode").forEach { name ->
            val item = OpcUaMonitoredItem.newDataItem(node(name))
            item.setDataValueListener { _, value ->
                log.info("OPC UA subscription: {}={} status={}",
                    name, value.value.value, value.statusCode)
                trace.record("PLC-LIVE", "PLC simulator", "WCS", "OPC UA SUBSCRIPTION",
                    "Data change: $name", if (value.statusCode.isGood) "GOOD" else "BAD",
                    mapOf("nodeId" to node(name).toString(), "namespaceUri" to namespaceUri,
                        "value" to value.value.value, "statusCode" to value.statusCode.toString()))
            }
            sub.addMonitoredItem(item)
        }
        sub.synchronizeMonitoredItems()
        subscription = sub
    }

    /** Returns ONLY when the virtual PLC has acknowledged acceptance. */
    @Synchronized
    fun requestMove(target: String, operation: String = "PUTAWAY", traceId: String = "DIRECT"): Int {
        require(target.matches(Regex("[A-Za-z0-9_-]{1,40}"))) {
            "Target must contain 1-40 letters, digits, underscores, or hyphens"
        }
        require(operation in setOf("PUTAWAY", "RETRIEVAL")) { "Unknown operation" }
        check(read("Ready") == true && read("Busy") == false) { "Crane is busy or not ready" }
        check((read("FaultCode") as Int) == 0) { "Crane has a fault" }

        val commandId = maxOf(sequence.get(), read("CommandId") as Int) + 1
        sequence.set(commandId)

        // NOTE: For learning only. These are two separate, non-atomic writes.
        write("TargetLocation", target, traceId)
        write("CommandOperation", operation, traceId)
        write("CommandId", commandId, traceId) // the virtual PLC treats this as the trigger

        val deadline = System.nanoTime() + 5_000_000_000L
        while (System.nanoTime() < deadline) {
            if ((read("RejectedCommandId") as Int) == commandId) {
                trace.record(traceId, "PLC simulator", "WCS", "OPC UA READ", "RejectedCommandId", "REJECTED",
                    mapOf("commandId" to commandId, "faultCode" to read("FaultCode")))
                error("PLC rejected command $commandId (FaultCode=${read("FaultCode")})")
            }
            if ((read("AcceptedCommandId") as Int) == commandId) {
                trace.record(traceId, "PLC simulator", "WCS", "OPC UA READ", "AcceptedCommandId", "ACKNOWLEDGED",
                    mapOf("commandId" to commandId, "acceptedCommandId" to commandId))
                return commandId
            }
            Thread.sleep(100)
        }
        trace.record(traceId, "PLC simulator", "WCS", "OPC UA READ", "Acknowledgment timeout", "UNCERTAIN",
            mapOf("commandId" to commandId, "message" to "Reconcile PLC state; do not retry blindly"))
        error("UNCERTAIN acknowledgment for command $commandId. Reconcile PLC state; do not retry blindly.")
    }

    fun status(): Map<String, Any> = linkedMapOf(
        "Ready" to read("Ready"),
        "Busy" to read("Busy"),
        "Position" to read("Position"),
        "TargetLocation" to read("TargetLocation"),
        "MachineState" to read("MachineState"),
        "CommandId" to read("CommandId"),
        "AcceptedCommandId" to read("AcceptedCommandId"),
        "RejectedCommandId" to read("RejectedCommandId"),
        "CompletedCommandId" to read("CompletedCommandId"),
        "FaultCode" to read("FaultCode"),
        "CommandOperation" to read("CommandOperation"),
        "PickupCommandId" to read("PickupCommandId"),
        "ReleasedCommandId" to read("ReleasedCommandId"),
        "AxisXPositionMm" to read("AxisXPositionMm"),
        "AxisZPositionMm" to read("AxisZPositionMm"),
        "SafetyState" to read("SafetyState"),
        "SimulatedGuardClosed" to read("SimulatedGuardClosed"),
    )

    @PreDestroy
    fun disconnect() {
        runCatching { subscription?.delete() }
            .onFailure { log.warn("Subscription shutdown failed", it) }
        if (::client.isInitialized) {
            runCatching { client.disconnect() }
                .onFailure { log.warn("OPC UA disconnect failed", it) }
        }
    }
}
