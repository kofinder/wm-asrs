package com.example.asrs.wms

import org.springframework.stereotype.Controller
import org.springframework.ui.Model
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.ResponseBody
import org.springframework.web.servlet.mvc.support.RedirectAttributes

@Controller
class WmsController(private val tasks: WmsTaskService) {
    @GetMapping("/")
    fun dashboard(model: Model): String {
        val all = tasks.list()
        model.addAttribute("tasks", all)
        model.addAttribute("inventory", tasks.inventory())
        model.addAttribute("activeCount", all.count { it.status in setOf("SUBMITTING", "ACCEPTED", "RUNNING") })
        model.addAttribute("completedCount", all.count { it.status == "COMPLETED" })
        model.addAttribute("uncertainCount", all.count { it.status == "UNCERTAIN" })
        return "index"
    }

    @PostMapping("/putaway")
    fun putaway(
        @RequestParam palletId: String,
        @RequestParam targetLocation: String,
        attributes: RedirectAttributes,
    ): String {
        try {
            val result = tasks.submit(palletId.trim(), targetLocation.trim().uppercase())
            if (result.status == "UNCERTAIN") {
                attributes.addFlashAttribute("error", result.detail)
            } else {
                attributes.addFlashAttribute("notice", "Putaway submitted: ${result.wmsTaskId}")
            }
        } catch (e: IllegalArgumentException) {
            attributes.addFlashAttribute("error", e.message ?: "Invalid input")
        }
        return "redirect:/"
    }

    @PostMapping("/retrieve")
    fun retrieve(@RequestParam palletId: String, attributes: RedirectAttributes): String {
        try {
            val task = tasks.retrieve(palletId.trim())
            if (task.status == "UNCERTAIN") attributes.addFlashAttribute("error", task.detail)
            else attributes.addFlashAttribute("notice", "Retrieval submitted: ${task.wmsTaskId}")
        } catch (e: IllegalArgumentException) {
            attributes.addFlashAttribute("error", e.message ?: "Invalid pallet")
        } catch (e: IllegalStateException) {
            attributes.addFlashAttribute("error", e.message ?: "Crane unavailable")
        }
        return "redirect:/"
    }

    @GetMapping("/api/wms/tasks")
    @ResponseBody
    fun listTasks(): List<WarehouseTask> = tasks.list()

    @GetMapping("/api/wms/inventory")
    @ResponseBody
    fun listInventory(): List<ConfirmedStock> = tasks.inventory()
}
