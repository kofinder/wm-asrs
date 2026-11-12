#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for p in \
  settings.gradle.kts build.gradle.kts gradlew \
  asrs-simulator/build.gradle.kts \
  asrs-wcs/build.gradle.kts \
  asrs-simulator/src/main/kotlin/com/example/asrs/simulator/SimulatorApplication.kt \
  asrs-simulator/src/main/kotlin/com/example/asrs/simulator/AsrsNamespace.kt \
  asrs-wcs/src/main/kotlin/com/example/asrs/wcs/WcsApplication.kt \
  asrs-wcs/src/main/kotlin/com/example/asrs/wcs/OpcUaClientService.kt \
  asrs-wcs/src/main/kotlin/com/example/asrs/wcs/TaskService.kt \
  asrs-wcs/src/main/kotlin/com/example/asrs/wcs/CraneController.kt \
  asrs-wcs/src/main/resources/application.yaml; do
  test -s "$p" || { echo "Missing or empty $p" >&2; exit 1; }
done
bash -n gradlew scripts/*.sh
echo 'Source layout and shell script syntax: OK'
