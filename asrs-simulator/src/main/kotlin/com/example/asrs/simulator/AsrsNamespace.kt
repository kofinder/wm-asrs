package com.example.asrs.simulator

import org.eclipse.milo.opcua.sdk.core.AccessLevel
import org.eclipse.milo.opcua.sdk.core.Reference
import org.eclipse.milo.opcua.sdk.server.Lifecycle
import org.eclipse.milo.opcua.sdk.server.ManagedNamespaceWithLifecycle
import org.eclipse.milo.opcua.sdk.server.OpcUaServer
import org.eclipse.milo.opcua.sdk.server.items.DataItem
import org.eclipse.milo.opcua.sdk.server.items.MonitoredItem
import org.eclipse.milo.opcua.sdk.server.nodes.UaFolderNode
import org.eclipse.milo.opcua.sdk.server.nodes.UaVariableNode
import org.eclipse.milo.opcua.sdk.server.util.SubscriptionModel
import org.eclipse.milo.opcua.stack.core.NodeIds
import org.eclipse.milo.opcua.stack.core.types.builtin.DataValue
import org.eclipse.milo.opcua.stack.core.types.builtin.LocalizedText
import org.eclipse.milo.opcua.stack.core.types.builtin.NodeId
import org.eclipse.milo.opcua.stack.core.types.builtin.Variant
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Virtual crane OPC UA address space.
 *
 * For education ONLY: uses two separate writes (TargetLocation then CommandId).
 * An actual PLC must implement atomic/latching command semantics, validation,
 * safety interlocks, persistent reconciliation, and controlled recovery.
 */
class AsrsNamespace(server: OpcUaServer) : ManagedNamespaceWithLifecycle(server, URI) {
    companion object {
        const val URI: String = "urn:asrs:simulator"
    }

    private val variables = ConcurrentHashMap<String, UaVariableNode>()
    private val subscriptionModel = SubscriptionModel(server, this)
    private val running = AtomicBoolean(false)
    private var worker: Thread? = null

    init {
        lifecycleManager.addLifecycle(subscriptionModel)
        lifecycleManager.addStartupTask { createNodes() }
        lifecycleManager.addLifecycle(object : Lifecycle {
            override fun startup() = startWorker()
            override fun shutdown() {
                running.set(false)
                worker?.interrupt()
                worker?.join(2000)
            }
        })
    }

    private fun folder(id: String, label: String): UaFolderNode {
        val folder = UaFolderNode(nodeContext, newNodeId(id), newQualifiedName(label),
            LocalizedText.english(label))
        nodeManager.addNode(folder)
        return folder
    }

    private fun addVariable(
        parent: UaFolderNode,
        name: String,
        type: NodeId,
        initialValue: Any,
        writable: Boolean = false
    ) {
        val access = if (writable) AccessLevel.READ_WRITE else AccessLevel.READ_ONLY
        val variable = UaVariableNode.UaVariableNodeBuilder(nodeContext)
            .setNodeId(newNodeId("ASRS/Crane01/$name"))
            .setBrowseName(newQualifiedName(name))
            .setDisplayName(LocalizedText.english(name))
            .setDataType(type)
            .setTypeDefinition(NodeIds.BaseDataVariableType)
            .setAccessLevel(access)
            .setUserAccessLevel(access)
            .build()
        variable.value = DataValue.valueOnly(Variant(initialValue))
        nodeManager.addNode(variable)
        parent.addOrganizes(variable)
        variables[name] = variable
    }

    private fun createNodes() {
        val root = folder("ASRS", "ASRS")
        // Make the ASRS folder visible in UaExpert under Objects.
        root.addReference(Reference(root.nodeId, NodeIds.Organizes,
            NodeIds.ObjectsFolder.expanded(), false))
        val crane = folder("ASRS/Crane01", "Crane01")
        root.addOrganizes(crane)

        addVariable(crane, "Ready", NodeIds.Boolean, true)
        addVariable(crane, "Busy", NodeIds.Boolean, false)
        addVariable(crane, "Position", NodeIds.String, "HOME")
        addVariable(crane, "TargetLocation", NodeIds.String, "", writable = true)
        addVariable(crane, "CommandOperation", NodeIds.String, "PUTAWAY", writable = true)
        addVariable(crane, "CommandId", NodeIds.Int32, 0, writable = true)
        addVariable(crane, "AcceptedCommandId", NodeIds.Int32, 0)
        addVariable(crane, "RejectedCommandId", NodeIds.Int32, 0)
        addVariable(crane, "CompletedCommandId", NodeIds.Int32, 0)
        addVariable(crane, "PickupCommandId", NodeIds.Int32, 0)
        addVariable(crane, "ReleasedCommandId", NodeIds.Int32, 0)
        addVariable(crane, "MachineState", NodeIds.String, "IDLE")
        addVariable(crane, "FaultCode", NodeIds.Int32, 0)
        // TRAINING MODEL ONLY: these are simulated signals, NOT EtherCAT frames.
        addVariable(crane, "EthercatNetworkState", NodeIds.String, "OP")
        addVariable(crane, "AxisXPositionMm", NodeIds.Double, 0.0)
        addVariable(crane, "AxisZPositionMm", NodeIds.Double, 0.0)
        addVariable(crane, "AxisXDriveState", NodeIds.String, "READY")
        addVariable(crane, "AxisZDriveState", NodeIds.String, "READY")
        // Writable only to simulate an externally supplied guard input in the lab.
        // NOT a real safety input or certified safety function.
        addVariable(crane, "SimulatedGuardClosed", NodeIds.Boolean, true, writable = true)
        addVariable(crane, "SafetyState", NodeIds.String, "PERMISSIVE")
    }

    private fun read(name: String): Any = requireNotNull(
        requireNotNull(variables[name]) { "Unknown ASRS node: $name" }.value.value.value
    ) { "Null OPC UA value for node: $name" }
    private fun update(name: String, value: Any) {
        requireNotNull(variables[name]).value = DataValue.valueOnly(Variant(value))
    }

    /**
     * Educational motion sequence only. The virtual OPC UA server is not a real
     * PLC and the guard flag is not a safety-rated interlock.
     *
     * PUTAWAY: crane visits inbound handoff (x=9m,z=0), announces LOADING,
     * confirms a simulated pickup ID, travels to rack and completes.
     * RETRIEVAL: crane visits source rack, announces PICKING, confirms pickup,
     * returns to outbound, announces RELEASING and confirms release.
     * Delays make movements visible in Gazebo; no physical grabbing occurs.
     */
    private fun moveTo(xMm: Double, zMm: Double): Boolean {
        val originX = read("AxisXPositionMm") as Double
        val originZ = read("AxisZPositionMm") as Double
        update("AxisXDriveState", "MOVING")
        update("AxisZDriveState", "MOVING")
        for (step in 1..12) {
            Thread.sleep(250)
            if (!(read("SimulatedGuardClosed") as Boolean)) return false
            update("AxisXPositionMm", originX + (xMm - originX) * step / 12.0)
            update("AxisZPositionMm", originZ + (zMm - originZ) * step / 12.0)
        }
        update("AxisXDriveState", "READY")
        update("AxisZDriveState", "READY")
        return true
    }

    /** Hold a simulated handoff while still honoring the virtual guard input. */
    private fun waitAtStation(milliseconds: Long): Boolean {
        val iterations = (milliseconds / 100L).toInt()
        repeat(iterations) {
            Thread.sleep(100)
            if (read("SimulatedGuardClosed") != true) return false
        }
        return true
    }

    private fun startWorker() {
        running.set(true)
        worker = Thread({
            while (running.get()) {
                try {
                    val guardClosed = read("SimulatedGuardClosed") as Boolean
                    update("SafetyState", if (guardClosed) "PERMISSIVE" else "INHIBITED")
                    val command = read("CommandId") as Int
                    val lastAccepted = read("AcceptedCommandId") as Int
                    val lastRejected = read("RejectedCommandId") as Int
                    if (read("MachineState") != "FAULT" && command > maxOf(lastAccepted, lastRejected)) {
                        val rack = read("TargetLocation") as String
                        val operation = read("CommandOperation") as String
                        val coordinate = Regex("A-(0[1-6])-(0[1-4])").matchEntire(rack)
                        val errorCode = when {
                            !guardClosed -> 301
                            coordinate == null -> 101
                            operation !in setOf("PUTAWAY", "RETRIEVAL") -> 102
                            else -> 0
                        }
                        if (errorCode != 0) {
                            update("RejectedCommandId", command)
                            update("FaultCode", errorCode)
                            update("MachineState", "REJECTED")
                            println("Rejected command #$command op=$operation rack=$rack code=$errorCode")
                        } else {
                            val targetX = coordinate!!.groupValues[1].toInt() * 1500.0
                            val targetZ = coordinate.groupValues[2].toInt() * 1200.0
                            update("Ready", false)
                            update("Busy", true)
                            update("AcceptedCommandId", command)
                            update("FaultCode", 0)
                            update("MachineState", "RUNNING")
                            println("Accepted $operation #$command -> $rack")

                            var completedPath: Boolean
                            if (operation == "PUTAWAY") {
                                // A real ASRS must obtain a pallet at an input station
                                // before traveling to the rack. This training handoff
                                // provides a visible cue for the Gazebo animation.
                                completedPath = moveTo(9000.0, 0.0)
                                if (completedPath) {
                                    update("MachineState", "LOADING")
                                    update("Position", "INBOUND")
                                    completedPath = waitAtStation(4500)
                                }
                                if (completedPath) {
                                    update("PickupCommandId", command)
                                    update("MachineState", "TRANSPORTING")
                                    completedPath = moveTo(targetX, targetZ)
                                }
                            } else {
                                completedPath = moveTo(targetX, targetZ)
                                if (completedPath) {
                                    update("MachineState", "PICKING")
                                    update("Position", rack) // at rack, not yet picked
                                    completedPath = waitAtStation(3500)
                                }
                                if (completedPath) {
                                    update("PickupCommandId", command)
                                    update("MachineState", "RETURNING")
                                    completedPath = moveTo(9000.0, 0.0)
                                }
                                if (completedPath) {
                                    update("MachineState", "RELEASING")
                                    completedPath = waitAtStation(1800)
                                }
                            }
                            update("AxisXDriveState", "READY")
                            update("AxisZDriveState", "READY")
                            update("Busy", false)
                            if (!completedPath) {
                                update("SafetyState", "INHIBITED")
                                update("MachineState", "FAULT")
                                update("FaultCode", 302)
                                update("Ready", false)
                                println("Command #$command stopped: simulated guard opened")
                            } else {
                                if (operation == "RETRIEVAL") {
                                    update("Position", "OUTBOUND")
                                    update("ReleasedCommandId", command)
                                } else {
                                    update("Position", rack)
                                }
                                update("CompletedCommandId", command)
                                update("MachineState", "COMPLETED")
                                update("Ready", true)
                                println("Completed $operation #$command at ${read("Position")}")
                            }
                        }
                    }
                    Thread.sleep(100)
                } catch (_: InterruptedException) {
                    Thread.currentThread().interrupt()
                    break
                } catch (e: Exception) {
                    e.printStackTrace()
                    update("MachineState", "FAULT")
                    update("FaultCode", 999)
                    running.set(false)
                }
            }
        }, "virtual-asrs-motion-controller").also {
            it.isDaemon = true
            it.start()
        }
    }

    // These callbacks are REQUIRED by the Milo 1.1.x AddressSpace interface.
    // The previous ZIP was missing them; this project includes all four.
    override fun onDataItemsCreated(items: MutableList<DataItem>) {
        subscriptionModel.onDataItemsCreated(items)
    }

    override fun onDataItemsModified(items: MutableList<DataItem>) {
        subscriptionModel.onDataItemsModified(items)
    }

    override fun onDataItemsDeleted(items: MutableList<DataItem>) {
        subscriptionModel.onDataItemsDeleted(items)
    }

    override fun onMonitoringModeChanged(items: MutableList<MonitoredItem>) {
        subscriptionModel.onMonitoringModeChanged(items)
    }
}
