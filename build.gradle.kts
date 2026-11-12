plugins {
    kotlin("jvm") version "2.4.21" apply false
    kotlin("plugin.spring") version "2.4.21" apply false
    id("org.springframework.boot") version "4.1.2" apply false
}

allprojects {
    group = "com.example.asrs"
    version = "1.0.0"
    repositories { mavenCentral() }
}
