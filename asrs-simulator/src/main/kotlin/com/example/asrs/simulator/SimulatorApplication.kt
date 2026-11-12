package com.example.asrs.simulator

import org.eclipse.milo.examples.server.ExampleServer
import java.util.concurrent.CountDownLatch

/** Training-only virtual crane. Run this BEFORE starting the WCS. */
fun main() {
    val exampleServer = ExampleServer()
    val asrs = AsrsNamespace(exampleServer.server)

    asrs.startup()
    exampleServer.startup().get()

    println("\n=== ASRS Virtual PLC / OPC UA Server ===")
    println("Endpoint: opc.tcp://localhost:12686/milo")
    println("Namespace URI: ${AsrsNamespace.URI}")
    println("Browse in UaExpert: Objects / ASRS / Crane01")
    println("Press Ctrl+C to stop.\n")

    Runtime.getRuntime().addShutdownHook(Thread {
        runCatching { asrs.shutdown() }.onFailure { it.printStackTrace() }
        runCatching { exampleServer.shutdown().get() }.onFailure { it.printStackTrace() }
    })

    CountDownLatch(1).await()
}
