"""Visual-only Gazebo pallet entity operations, using Gazebo Harmonic UserCommands.

No dependencies on ROS or Gazebo Python bindings. In the real project all
movement commands still go through the PLC simulator, not through this module.
"""
from dataclasses import dataclass
import json
import math
import os
import re
import subprocess
from xml.sax.saxutils import escape

WORLD = 'asrs_warehouse'
CONVEYOR = (11.4, 0.0, 0.89)  # center of pallet deck
NORTH_RACK_Y = 3.25
PALLET_LIFT_OFFSET_Z = 0.42  # relative to lifting-axis displacement
RACK_COLUMNS = range(1, 7)
RACK_LEVELS = range(1, 5)


def rack_coordinates(location: str):
    """Return center coordinates of a pallet deck placed in north/A rack."""
    match = re.fullmatch(r'A-(\d{2})-(\d{2})', location or '')
    if not match:
        raise ValueError(f'Unsupported visible rack location: {location!r}')
    column, level = int(match.group(1)), int(match.group(2))
    if column not in RACK_COLUMNS or level not in RACK_LEVELS:
        raise ValueError(f'Outside visible Gazebo rack: {location!r}')
    return (column * 1.5, NORTH_RACK_Y, level * 1.2 + 0.12)


def carried_coordinates(status: dict):
    """Follow simulated measured encoders (not a target or planned trajectory)."""
    x = float(status['AxisXPositionMm']) / 1000.0
    z = float(status['AxisZPositionMm']) / 1000.0
    if not (0 <= x <= 9 and 0 <= z <= 5.2):
        raise ValueError(f'Out-of-bounds measured position: {x=}, {z=}')
    return x, 0.0, z + PALLET_LIFT_OFFSET_Z


def make_entity_name(task_id: str):
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(task_id))
    if len(safe) < 8:
        raise ValueError('Invalid WCS task ID')
    return 'asrs_pallet_' + safe[:72]


def pallet_sdf(name: str, pallet_id: str):
    """Create a collision-free *static* visual pallet, movable by set_pose.

    This model deliberately cannot validate loads, forces or machine safety.
    """
    if not re.fullmatch(r'asrs_pallet_[A-Za-z0-9_]{8,72}', name):
        raise ValueError('Unsafe model name')
    # Different colors make successive WMS pallets easy to distinguish.
    palette = ('0.12 0.42 0.79 1', '0.12 0.59 0.38 1', '0.78 0.25 0.21 1')
    color = palette[sum(ord(x) for x in pallet_id) % len(palette)]
    return f'''<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{escape(name)}">
    <static>true</static>
    <pose>{CONVEYOR[0]} {CONVEYOR[1]} {CONVEYOR[2]} 0 0 0</pose>
    <link name="load">
      <visual name="wood_pallet">
        <geometry><box><size>1.10 1.00 0.16</size></box></geometry>
        <material><ambient>0.55 0.32 0.16 1</ambient><diffuse>0.55 0.32 0.16 1</diffuse></material>
      </visual>
      <visual name="cargo">
        <pose>0 0 0.34 0 0 0</pose>
        <geometry><box><size>0.95 0.90 0.56</size></box></geometry>
        <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>
      </visual>
    </link>
  </model>
</sdf>
'''


def pose_request(name: str, xyz):
    if not re.fullmatch(r'asrs_pallet_[A-Za-z0-9_]{8,72}', name):
        raise ValueError('Unsafe model name')
    x, y, z = xyz
    return (f'name: "{name}", position: '
            f'{{x: {float(x):.4f}, y: {float(y):.4f}, z: {float(z):.4f}}}, '
            f'orientation: {{w: 1.0, x: 0, y: 0, z: 0}}')


@dataclass
class GazeboServiceClient:
    world: str = WORLD

    def _request(self, service_suffix: str, reqtype: str, data: str):
        service = f'/world/{self.world}/{service_suffix}'
        # Gazebo may take several seconds to process a command in a large
        # world. 2.5 seconds was too aggressive and caused false failures.
        # Gazebo's CLI timeout is in MILLISECONDS.
        try:
            timeout_ms = int(os.getenv('ASRS_GZ_SERVICE_TIMEOUT_MS', '20000'))
        except ValueError as exc:
            raise ValueError('ASRS_GZ_SERVICE_TIMEOUT_MS must be an integer') from exc
        if not 1000 <= timeout_ms <= 60000:
            raise ValueError('ASRS_GZ_SERVICE_TIMEOUT_MS must be 1000..60000')
        argv = ['gz', 'service', '-s', service,
                '--reqtype', reqtype,
                '--reptype', 'gz.msgs.Boolean',
                '--timeout', str(timeout_ms), '--req', data]
        try:
            result = subprocess.run(argv, capture_output=True, text=True,
                                    timeout=timeout_ms / 1000.0 + 5.0, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f'{service}: Gazebo CLI did not finish. Check that the world is '
                'loaded, Gazebo is responsive, and simulation is running.'
            ) from exc
        if result.returncode != 0 or not re.search(r'\bdata\s*:\s*true\b', result.stdout, re.I):
            output = (result.stdout.strip() + ' ' + result.stderr.strip()).strip()
            raise RuntimeError(
                f'{service} failed: {output or "no response"}. '
                'Ensure Gazebo is responsive (try /world/asrs_warehouse/control), '
                'and the simulation is unpaused. A service listed by '
                '`gz service -l` is not necessarily responding.'
            )

    def spawn(self, name: str, pallet_id: str):
        # The async /create endpoint can acknowledge a request before its SDF
        # filename is consumed during Gazebo PreUpdate. A TemporaryDirectory
        # can therefore disappear before the model is loaded. Send the SDF
        # itself in the EntityFactory request (not a temporary filename).
        # json.dumps yields protobuf-text-compatible string quoting/escapes.
        # /create/blocking waits until Gazebo processes the command, making
        # any load failure observable instead of reporting a false success.
        self._request('create/blocking', 'gz.msgs.EntityFactory',
                      'sdf: ' + json.dumps(pallet_sdf(name, pallet_id)))

    def set_forklift_pose(self, x: float, y: float, yaw: float):
        """Visual-only forklift location and heading (radians about world Z)."""
        for n in (x, y, yaw):
            if not math.isfinite(float(n)):
                raise ValueError('Forklift pose must be finite')
        self._request('set_pose/blocking', 'gz.msgs.Pose',
                      f'name: "asrs_forklift", '
                      f'position: {{x: {x:.4f}, y: {y:.4f}, z: 0.0}}, '
                      f'orientation: {{w: {math.cos(yaw/2):.6f}, x: 0, y: 0, '
                      f'z: {math.sin(yaw/2):.6f}}}')

    def remove_pallet(self, name: str):
        """Remove a shipped pallet after confirmed Gazebo outbound animation."""
        if not re.fullmatch(r'asrs_pallet_[A-Za-z0-9_]{8,72}', name):
            raise ValueError('Unsafe model name')
        self._request('remove/blocking', 'gz.msgs.Entity',
                      f'name: "{name}", type: MODEL')

    def set_pose(self, name: str, xyz):
        # Avoid false success from the async pose service: /set_pose/blocking
        # waits for the update and can reject a model that was not created.
        self._request('set_pose/blocking', 'gz.msgs.Pose', pose_request(name, xyz))
