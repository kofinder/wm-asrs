#!/usr/bin/env bash
set -u
printf '%s\n' '--- WCS crane feedback (must include AxisXPositionMm / AxisZPositionMm) ---'
curl -fsS http://127.0.0.1:8080/api/crane/status | python3 -m json.tool || true
printf '%s\n' '--- Current WCS tasks ---'
curl -fsS http://127.0.0.1:8080/api/tasks | python3 -m json.tool || true
printf '%s\n' '--- Gazebo create/pose services ---'
gz service -l | grep -E '/world/asrs_warehouse/(create|set_pose)' || true
printf '%s\n' '--- ROS visual nodes ---'
ros2 node list | grep visual_sync || true
printf '%s\n' '--- Gazebo crane command topics ---'
gz topic -l | grep /asrs/crane || true
