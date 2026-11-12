pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}
rootProject.name = "wm-asrs"
include("asrs-wms", "asrs-wcs", "asrs-simulator")
