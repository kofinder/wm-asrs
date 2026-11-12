#!/usr/bin/env bash
# Read-only health checks, does not issue any equipment commands.
set -u
ok=0
check() {
  local label="$1" url="$2"
  if curl --max-time 3 --silent --fail "$url" >/dev/null; then
    printf 'OK   %s  %s\n' "$label" "$url"
  else
    printf 'FAIL %s  %s\n' "$label" "$url"
    ok=1
  fi
}
check 'ROS planner' http://127.0.0.1:8091/health
check 'WCS status' http://127.0.0.1:8080/api/crane/status
check 'WCS tasks' http://127.0.0.1:8080/api/tasks
check 'WMS inventory' http://127.0.0.1:8081/api/wms/inventory
if command -v ros2 >/dev/null 2>&1; then
  echo 'ROS visual nodes:'
  ros2 node list 2>/dev/null | grep 'visual_sync' || { echo '  no visual_sync nodes'; ok=1; }
fi
if command -v gz >/dev/null 2>&1; then
  echo 'Gazebo palette services:'
  gz service -l 2>/dev/null | grep -E '/world/asrs_warehouse/(create|set_pose)$' || { echo '  no expected world services'; ok=1; }
fi
exit "$ok"
