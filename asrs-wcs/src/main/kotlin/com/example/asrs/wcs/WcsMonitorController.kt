package com.example.asrs.wcs

import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.ResponseBody

@Controller
class WcsMonitorController(
    private val trace: CommunicationTraceService,
    private val tasks: TaskService,
    private val opc: OpcUaClientService,
) {
    @GetMapping("/", "/monitor")
    fun dashboard(): String = "wcs-monitor"

    @GetMapping("/api/monitor/snapshot")
    @ResponseBody
    fun snapshot(): Map<String, Any?> {
        val plc = runCatching { opc.status() }
        return mapOf(
            "generatedAt" to java.time.Instant.now().toString(),
            "events" to trace.recent(),
            "tasks" to tasks.list(),
            "plcOnline" to plc.isSuccess,
            "plcStatus" to plc.getOrNull(),
            "plcError" to plc.exceptionOrNull()?.message,
            "note" to "Application-level events in memory, not raw network packets or a safety audit log",
        )
    }
}
