"""ROS 2 visual-only adapter: WCS /api/crane/status -> Gazebo joint targets.

This process deliberately does NOT send commands to WCS or the PLC. It follows
read-only machine position data. It is NOT a controller or a safety component.
"""
import json
import os
import re
import time
from urllib.request import Request, urlopen

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class WcsVisualSync(Node):
    def __init__(self):
        super().__init__('asrs_wcs_visual_sync')
        self.url = os.getenv('ASRS_WCS_STATUS_URL', 'http://127.0.0.1:8080/api/crane/status')
        self.x_pub = self.create_publisher(Float64, '/asrs/crane/x_cmd', 10)
        self.z_pub = self.create_publisher(Float64, '/asrs/crane/z_cmd', 10)
        self.last = None
        self.last_warning = 0.0
        self.last_emit = 0.0
        self.timer = self.create_timer(0.25, self.tick)
        self.get_logger().info(f'Visual adapter: WCS status {self.url} -> Gazebo X/Z joints')
        self.get_logger().info('Read-only. Fork joint available for manual Gazebo visualization.')

    def get_pose(self, data):
        # Preferred: authoritative SIMULATED encoder feedback from PLC via WCS.
        if 'AxisXPositionMm' in data and 'AxisZPositionMm' in data:
            return (float(data['AxisXPositionMm']) / 1000.0,
                    float(data['AxisZPositionMm']) / 1000.0)
        # Backwards-compatible fallback: only jump to last CONFIRMED position.
        # Do not assume a target has actually been reached while RUNNING.
        position = str(data.get('Position') or '')
        match = re.fullmatch(r'A-(\d{2})-(\d{2})', position)
        if match:
            return int(match.group(1)) * 1.5, int(match.group(2)) * 1.2
        if position == 'HOME':
            return 0.0, 0.0
        return None

    def tick(self):
        try:
            request = Request(self.url, headers={'Accept': 'application/json'})
            with urlopen(request, timeout=0.65) as response:
                state = json.load(response)
            position = self.get_pose(state)
            if position is None:
                return
            x, z = position
            if not (0.0 <= x <= 9.0 and 0.0 <= z <= 5.2):
                # Rack world is deliberately small. Do not silently clamp and
                # pretend an unreachable simulated rack was visited.
                raise ValueError(f'Position outside visible crane world: x={x}, z={z}')
            now = time.monotonic()
            if self.last is None or any(abs(a-b) > 0.004 for a,b in zip(position, self.last)) or now-self.last_emit > 2:
                self.x_pub.publish(Float64(data=x))
                self.z_pub.publish(Float64(data=z))
                self.last = position
                self.last_emit = now
        except Exception as exc:
            now = time.monotonic()
            if now - self.last_warning > 5:
                self.get_logger().warning(f'WCS visual sync unavailable: {exc}')
                self.last_warning = now
            # Keep last visual target. Never infer machine stopped safely.


def main(args=None):
    rclpy.init(args=args)
    node = WcsVisualSync()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
