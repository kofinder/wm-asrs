package com.example.asrs.wms

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
class WmsApplication

fun main(args: Array<String>) {
    runApplication<WmsApplication>(*args)
}
