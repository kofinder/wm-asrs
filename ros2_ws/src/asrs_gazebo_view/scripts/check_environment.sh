#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/jazzy/setup.bash
printf 'Gazebo CLI: '; command -v gz || true
printf 'ROS: '; command -v ros2 || true
printf 'Bridge: '; ros2 pkg list | grep -x ros_gz_bridge || echo 'MISSING ros_gz_bridge'
printf 'Rclpy: '; python3 -c 'import rclpy;print("available")' || true
if command -v gz >/dev/null; then gz sim --version; fi
