package com.example.asrs.wcs

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
class WcsApplication

fun main(args: Array<String>) {
    runApplication<WcsApplication>(*args)
}
