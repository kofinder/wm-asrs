plugins {
    kotlin("jvm")
    application
}

kotlin { jvmToolchain(21) }

dependencies {
    // Published Milo reference server: provides endpoint setup, discovery, certificates, etc.
    implementation("org.eclipse.milo:milo-server-examples:1.1.8")
    implementation("org.eclipse.milo:milo-sdk-server:1.1.8")
    runtimeOnly("org.slf4j:slf4j-simple:2.0.20")
}

application {
    mainClass.set("com.example.asrs.simulator.SimulatorApplicationKt")
}
