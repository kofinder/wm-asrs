"""Pure coordinate helpers for the visual-only ASRS forklift.

The forklift does NOT use the warehouse PLC, ROS nav or collision avoidance.
All routes stay outside the crane aisle guard in this educational SDF scene.
"""
import math

FORKLIFT_NAME = 'asrs_forklift'
HOME = (9.5, -5.6, 0.0)
GATE = (11.4, -5.6, 0.0)
GATE_TURN = (11.4, -5.6, math.pi / 2)
INBOUND_DOCK = (11.4, -1.6, math.pi / 2)
OUTBOUND_DOCK = (11.4, -4.0, math.pi / 2)
SHIPPING = (7.7, -5.6, 0.0)
FORK_REACH = 1.4
FORK_CARRY_HEIGHT = 1.08
OUTBOUND_CONVEYOR = (11.4, -2.6, 0.89)


def pallet_on_forks(vehicle_pose):
    """Pallet center on the fork tips using world x/y and yaw orientation."""
    x, y, yaw = vehicle_pose
    return (x + FORK_REACH * math.cos(yaw),
            y + FORK_REACH * math.sin(yaw),
            FORK_CARRY_HEIGHT)


def mix_pose(start, end, fraction):
    t = max(0.0, min(1.0, float(fraction)))
    return tuple(float(a) + (float(b) - float(a)) * t for a, b in zip(start, end))


def visible_route_safe(vehicle_pose):
    """Basic footprint guard for demo corridor, NOT safety-rated navigation."""
    x, y, yaw = vehicle_pose
    return (math.isfinite(x) and math.isfinite(y) and math.isfinite(yaw) and
            7.0 <= x <= 12.4 and -6.5 <= y <= -1.4 and
            (y <= -4.85 or x >= 10.75))
