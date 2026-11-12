"""Live, read-only WCS/PLC -> Gazebo visual pallet choreography.

An ASRS is not just an X/Z crane: the visible load must pass through the
inbound station, loading platform, rack fork, and (on retrieval) outbound
station. WCS/PLC reports are authoritative. This module does NOT issue PLC
commands and its simplified kinematic motions are NOT contact physics.

All Gazebo entity operations use confirmed, blocking UserCommands services.
When a command is first observed after PLC completion, a visual demonstration
may play late and is explicitly logged as a REPLAY, not live machine feedback.
"""
import json
import os
import time
from dataclasses import dataclass
from urllib.request import Request, urlopen

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from .pallet_scene import (
    GazeboServiceClient, CONVEYOR, carried_coordinates, make_entity_name,
    rack_coordinates,
)
from .forklift_scene import (
    HOME, GATE, GATE_TURN, INBOUND_DOCK, OUTBOUND_DOCK, SHIPPING,
    OUTBOUND_CONVEYOR, pallet_on_forks, mix_pose, visible_route_safe,
)

# Physical-looking movements, intentionally slowed for teaching and visibility.
INFEED_END = (9.4, 0.0, 0.89)
HANDOFF = (9.0, 0.0, 0.42)
FORK_EXTENSION = 2.2  # meters; +Y towards north rack A
INFEED_SECONDS = 1.8
LOADING_SECONDS = 1.6
RACK_TRANSFER_SECONDS = 2.6
RACK_PICKUP_SECONDS = 2.4
OUTFEED_SECONDS = 2.6
FORKLIFT_DRIVE_SECONDS = 2.8
FORKLIFT_TURN_SECONDS = 1.1
FORKLIFT_DOCK_SECONDS = 2.5
FORKLIFT_HANDOFF_SECONDS = 1.1


def interpolate(start, end, fraction):
    f = min(1.0, max(0.0, float(fraction)))
    return tuple(float(s) + (float(e) - float(s)) * f for s, e in zip(start, end))


def matches_putaway_completion(task, feedback):
    """Require the WCS task AND the matching PLC command/destination."""
    try:
        return (task.get('status') == 'COMPLETED' and
                int(task['commandId']) == int(feedback['CompletedCommandId']) and
                feedback.get('Position') == task.get('targetLocation'))
    except (ValueError, TypeError, KeyError):
        return False


def matches_retrieval_completion(task, feedback):
    """Rack pickup and release must belong to this exact retrieval command."""
    try:
        cmd = int(task['commandId'])
        return (task.get('status') == 'COMPLETED' and
                cmd == int(feedback['CompletedCommandId']) ==
                int(feedback['PickupCommandId']) == int(feedback['ReleasedCommandId']) and
                feedback.get('Position') == 'OUTBOUND')
    except (ValueError, TypeError, KeyError):
        return False


@dataclass
class ActivePallet:
    task_id: str
    pallet_id: str
    target: str
    command_id: int
    entity_name: str
    operation: str = 'PUTAWAY'
    phase: str = 'NEW'
    phase_started: float = 0.0
    last_xyz: tuple | None = None
    replay: bool = False


class PalletVisualSync(Node):
    def __init__(self):
        super().__init__('asrs_pallet_visual_sync')
        base = os.getenv('ASRS_WCS_URL', 'http://127.0.0.1:8080').rstrip('/')
        self.tasks_url = f'{base}/api/tasks'
        self.status_url = f'{base}/api/crane/status'
        self.transport = GazeboServiceClient()
        self.seen = None
        self.pending = []
        self.active = None
        self.occupied = {}  # rack -> pallet ID, only after verified placement
        self.entity_by_location = {}  # rack -> spawned entity to reuse for retrieval
        self.last_warn = 0.0
        self.last_forklift_pose = HOME
        self.fork_pub = self.create_publisher(Float64, '/asrs/crane/fork_cmd', 10)
        self.timer = self.create_timer(0.30, self.tick)
        self.get_logger().info('ASRS pallet lifecycle: %s' % self.tasks_url)
        self.get_logger().info('Visual-only: FORKLIFT INBOUND -> LOAD -> CARRY -> RACK / RACK -> OUTBOUND -> FORKLIFT SHIPPING')
        self.get_logger().info('Start this node before new WMS tasks; already completed tasks at startup are ignored.')

    def get_json(self, url):
        request = Request(url, headers={'Accept': 'application/json'})
        with urlopen(request, timeout=1.5) as response:
            return json.load(response)

    def fork(self, meters):
        self.fork_pub.publish(Float64(data=float(meters)))

    def phase(self, a, name):
        a.phase = name
        a.phase_started = time.monotonic()

    def pose(self, a, xyz):
        position = tuple(float(n) for n in xyz)
        if a.last_xyz is None or any(abs(x - y) > 0.005 for x, y in zip(a.last_xyz, position)):
            self.transport.set_pose(a.entity_name, position)
            a.last_xyz = position

    def tween(self, a, start, end, duration):
        fraction = min(1.0, (time.monotonic() - a.phase_started) / duration)
        self.pose(a, interpolate(start, end, fraction))
        return fraction >= 1.0

    def drive_forklift(self, a, start, end, duration, carry=False):
        """Animate an idealized vehicle pose, optionally moving the same pallet.

        Successful Gazebo UserCommands service replies are required before
        advancing the phase. No PLC machine completion is inferred here.
        """
        fraction = min(1.0, (time.monotonic() - a.phase_started) / duration)
        vehicle = mix_pose(start, end, fraction)
        if not visible_route_safe(vehicle):
            raise ValueError(f'Forklift route leaves demo travel corridor: {vehicle}')
        previous = getattr(self, 'last_forklift_pose', None)
        if previous is None or any(abs(t - p) > 0.005 for t, p in zip(vehicle, previous)):
            self.transport.set_forklift_pose(*vehicle)
            self.last_forklift_pose = vehicle
        if carry:
            self.pose(a, pallet_on_forks(vehicle))
        return fraction >= 1.0

    def advance_inbound_forklift(self, a):
        """Returns True if the active task was handled by the forklift phase."""
        if a.phase == 'FORK_IN_APPROACH':
            if self.drive_forklift(a, HOME, GATE, FORKLIFT_DRIVE_SECONDS, carry=True):
                self.phase(a, 'FORK_IN_TURN')
            return True
        if a.phase == 'FORK_IN_TURN':
            if self.drive_forklift(a, GATE, GATE_TURN, FORKLIFT_TURN_SECONDS, carry=True):
                self.phase(a, 'FORK_IN_DOCK')
            return True
        if a.phase == 'FORK_IN_DOCK':
            if self.drive_forklift(a, GATE_TURN, INBOUND_DOCK, FORKLIFT_DOCK_SECONDS, carry=True):
                self.phase(a, 'FORK_IN_UNLOAD')
                self.get_logger().info('FORKLIFT AT INBOUND: %s' % a.pallet_id)
            return True
        if a.phase == 'FORK_IN_UNLOAD':
            if self.tween(a, pallet_on_forks(INBOUND_DOCK), CONVEYOR, FORKLIFT_HANDOFF_SECONDS):
                self.phase(a, 'FORK_IN_CLEAR')
                self.get_logger().info('FORKLIFT RELEASED INBOUND PALLET: %s' % a.pallet_id)
            return True
        if a.phase == 'FORK_IN_CLEAR':
            if self.drive_forklift(a, INBOUND_DOCK, GATE_TURN, FORKLIFT_DOCK_SECONDS):
                self.phase(a, 'FORK_IN_FACE_HOME')
            return True
        if a.phase == 'FORK_IN_FACE_HOME':
            if self.drive_forklift(a, GATE_TURN, GATE, FORKLIFT_TURN_SECONDS):
                self.phase(a, 'FORK_IN_HOME')
            return True
        if a.phase == 'FORK_IN_HOME':
            if self.drive_forklift(a, GATE, HOME, FORKLIFT_DRIVE_SECONDS):
                self.phase(a, 'INFEED')
                self.get_logger().info('CONVEYOR RECEIVED FORKLIFT PALLET: %s' % a.pallet_id)
            return True
        return False

    def advance_outbound_forklift(self, a):
        if a.phase == 'FORK_OUT_APPROACH':
            if self.drive_forklift(a, HOME, GATE, FORKLIFT_DRIVE_SECONDS):
                self.phase(a, 'FORK_OUT_TURN')
            return True
        if a.phase == 'FORK_OUT_TURN':
            if self.drive_forklift(a, GATE, GATE_TURN, FORKLIFT_TURN_SECONDS):
                self.phase(a, 'FORK_OUT_DOCK')
            return True
        if a.phase == 'FORK_OUT_DOCK':
            if self.drive_forklift(a, GATE_TURN, OUTBOUND_DOCK, FORKLIFT_DOCK_SECONDS):
                self.phase(a, 'FORK_OUT_PICKUP')
                self.get_logger().info('FORKLIFT AT OUTBOUND: %s' % a.pallet_id)
            return True
        if a.phase == 'FORK_OUT_PICKUP':
            if self.tween(a, OUTBOUND_CONVEYOR, pallet_on_forks(OUTBOUND_DOCK), FORKLIFT_HANDOFF_SECONDS):
                self.phase(a, 'FORK_OUT_CLEAR')
                self.get_logger().info('FORKLIFT PICKED OUTBOUND PALLET: %s' % a.pallet_id)
            return True
        if a.phase == 'FORK_OUT_CLEAR':
            if self.drive_forklift(a, OUTBOUND_DOCK, GATE_TURN, FORKLIFT_DOCK_SECONDS, carry=True):
                self.phase(a, 'FORK_OUT_FACE_HOME')
            return True
        if a.phase == 'FORK_OUT_FACE_HOME':
            if self.drive_forklift(a, GATE_TURN, GATE, FORKLIFT_TURN_SECONDS, carry=True):
                self.phase(a, 'FORK_OUT_SHIPPING')
            return True
        if a.phase == 'FORK_OUT_SHIPPING':
            if self.drive_forklift(a, GATE, SHIPPING, FORKLIFT_DRIVE_SECONDS, carry=True):
                self.phase(a, 'FORK_OUT_REMOVE')
            return True
        if a.phase == 'FORK_OUT_REMOVE':
            # Do not claim successful visual dispatch if Gazebo remove fails.
            self.transport.remove_pallet(a.entity_name)
            self.phase(a, 'FORK_OUT_HOME')
            self.get_logger().info('FORKLIFT DISPATCHED TO SHIPPING: %s' % a.pallet_id)
            return True
        if a.phase == 'FORK_OUT_HOME':
            if self.drive_forklift(a, SHIPPING, HOME, FORKLIFT_DRIVE_SECONDS):
                self.active = None
                self.get_logger().info('FORKLIFT READY FOR NEXT TASK')
            return True
        return False

    def tick(self):
        try:
            tasks = self.get_json(self.tasks_url)
            if not isinstance(tasks, list):
                raise ValueError('WCS /api/tasks did not return an array')
            if self.seen is None:
                # Never fabricate a new placement for historical tasks that
                # completed before this Gazebo session started.
                self.seen = {t.get('taskId') for t in tasks
                             if t.get('status') in ('COMPLETED', 'UNCERTAIN')}
            for task in reversed(tasks):  # endpoint is newest-first
                task_id = task.get('taskId')
                if not task_id or task_id in self.seen:
                    continue
                if task.get('status') not in ('ACCEPTED', 'RUNNING', 'COMPLETED', 'UNCERTAIN'):
                    continue
                self.seen.add(task_id)
                if task.get('status') == 'UNCERTAIN':
                    self.get_logger().warning('Ignoring already uncertain task %s' % task_id)
                    continue
                try:
                    rack_coordinates(task['targetLocation'])
                    operation = task.get('operation', 'PUTAWAY')
                    if operation not in ('PUTAWAY', 'RETRIEVAL'):
                        raise ValueError('Unknown operation: %r' % operation)
                    self.pending.append(ActivePallet(
                        task_id=task_id, pallet_id=task['palletId'],
                        target=task['targetLocation'], command_id=int(task['commandId']),
                        entity_name=make_entity_name(task_id), operation=operation,
                        replay=task['status'] == 'COMPLETED'))
                except (KeyError, ValueError, TypeError) as exc:
                    self.get_logger().warning('Unsupported task for Gazebo: %s' % exc)
            if self.active is None and self.pending:
                self.active = self.pending.pop(0)
                if self.active.replay:
                    self.get_logger().warning(
                        'VISUAL REPLAY: %s was completed before the monitor observed it. '
                        'This is a demonstration, not live machine motion.' % self.active.task_id)
            if self.active is None:
                return
            task = next((t for t in tasks if t.get('taskId') == self.active.task_id), None)
            if not task:
                return
            if task.get('status') == 'UNCERTAIN':
                self.fork(0)
                self.get_logger().warning(
                    'PLC TASK UNCERTAIN: %s; NOT showing successful pallet delivery.' %
                    self.active.pallet_id)
                self.active = None
                return
            feedback = self.get_json(self.status_url)
            if self.active.operation == 'PUTAWAY':
                self.putaway(task, feedback)
            else:
                self.retrieval(task, feedback)
        except Exception as exc:
            now = time.monotonic()
            if now - self.last_warn >= 5.0:
                self.get_logger().warning('Pallet visualization waiting: %s' % exc)
                self.last_warn = now

    def putaway(self, task, feedback):
        a = self.active
        if a.phase == 'NEW':
            if a.target in self.occupied:
                self.get_logger().warning('Visual rack %s is already occupied; skipping %s' %
                                          (a.target, a.pallet_id))
                self.active = None
                return
            self.transport.spawn(a.entity_name, a.pallet_id)
            # Pallet and forklift form one visual load until the conveyor dock.
            self.pose(a, pallet_on_forks(HOME))
            self.phase(a, 'FORK_IN_APPROACH')
            self.get_logger().info('FORKLIFT LOADED: %s from receiving area' % a.pallet_id)
            return

        if self.advance_inbound_forklift(a):
            return

        if a.phase == 'INFEED':
            if self.tween(a, CONVEYOR, INFEED_END, INFEED_SECONDS):
                self.phase(a, 'WAIT_LOADING')
                self.get_logger().info('CONVEYOR ARRIVAL: %s at crane loading station' % a.pallet_id)
            return

        if a.phase == 'WAIT_LOADING':
            if (feedback.get('MachineState') == 'LOADING' and
                    int(feedback.get('AcceptedCommandId', -1)) == a.command_id) or \
                    int(feedback.get('PickupCommandId', -1)) == a.command_id or \
                    matches_putaway_completion(task, feedback):
                self.phase(a, 'LOADING')
                self.get_logger().info('LOADING PLATFORM: %s moving onto crane' % a.pallet_id)
            return

        if a.phase == 'LOADING':
            if self.tween(a, INFEED_END, HANDOFF, LOADING_SECONDS):
                self.phase(a, 'WAIT_PICKUP_ACK')
            return

        if a.phase == 'WAIT_PICKUP_ACK':
            if int(feedback.get('PickupCommandId', -1)) == a.command_id or \
                    matches_putaway_completion(task, feedback):
                self.phase(a, 'CARRYING')
                self.get_logger().info('CRANE LOADED: %s, command %d' % (a.pallet_id, a.command_id))
            return

        if a.phase == 'CARRYING':
            if matches_putaway_completion(task, feedback):
                self.pose(a, carried_coordinates(feedback))
                self.fork(FORK_EXTENSION)
                self.phase(a, 'DEPOSITING')
                self.get_logger().info('FORK EXTENDING: %s to %s' % (a.pallet_id, a.target))
            elif (task.get('status') in ('ACCEPTED', 'RUNNING') and
                  int(feedback.get('PickupCommandId', -1)) == a.command_id and
                  int(feedback.get('AcceptedCommandId', -1)) == a.command_id):
                self.pose(a, carried_coordinates(feedback))
            return

        if a.phase == 'DEPOSITING':
            # Start on the lift and transfer into north rack, including a small
            # change in pallet elevation. This is visually synchronized to the
            # fork, but there is no collision-based load attachment.
            x, y, z = rack_coordinates(a.target)
            if self.tween(a, (x, 0.0, z + 0.30), (x, y, z), RACK_TRANSFER_SECONDS):
                # Only record placement after the blocking Gazebo pose was accepted
                # AND the WCS + PLC command had previously been verified.
                self.occupied[a.target] = a.pallet_id
                self.entity_by_location[a.target] = a.entity_name
                self.fork(0.0)
                self.get_logger().info('PALLET VISIBLE ON SHELF: %s -> %s' %
                                       (a.pallet_id, a.target))
                self.active = None
            return

    def retrieval(self, task, feedback):
        a = self.active
        if a.phase == 'NEW':
            previous = self.entity_by_location.get(a.target)
            known = self.occupied.get(a.target)
            if known is not None and known != a.pallet_id:
                self.get_logger().warning('VISUAL CONFLICT: shelf %s contains %s, not %s' %
                                          (a.target, known, a.pallet_id))
                self.active = None
                return
            if previous:
                a.entity_name = previous
                a.last_xyz = rack_coordinates(a.target)
            else:
                # WCS retrieval acceptance implies it had previously verified
                # stored stock. Restore that model if Gazebo was restarted.
                self.transport.spawn(a.entity_name, a.pallet_id)
                self.pose(a, rack_coordinates(a.target))
                self.occupied[a.target] = a.pallet_id
                self.entity_by_location[a.target] = a.entity_name
                self.get_logger().info('RESTORED RACK PALLET: %s -> %s' %
                                       (a.pallet_id, a.target))
            self.phase(a, 'WAIT_RACK')
            return

        if a.phase == 'WAIT_RACK':
            if ((feedback.get('MachineState') == 'PICKING' and
                 feedback.get('Position') == a.target and
                 int(feedback.get('AcceptedCommandId', -1)) == a.command_id) or
                    int(feedback.get('PickupCommandId', -1)) == a.command_id or
                    matches_retrieval_completion(task, feedback)):
                self.fork(FORK_EXTENSION)
                self.phase(a, 'RACK_PICKUP')
                self.get_logger().info('FORK PICKUP: %s from %s' % (a.pallet_id, a.target))
            return

        if a.phase == 'RACK_PICKUP':
            x, _, z = rack_coordinates(a.target)
            if self.tween(a, (x, 3.25, z), (x, 0.0, z + 0.30), RACK_PICKUP_SECONDS):
                self.phase(a, 'WAIT_PICKUP_ACK')
            return

        if a.phase == 'WAIT_PICKUP_ACK':
            if int(feedback.get('PickupCommandId', -1)) == a.command_id:
                self.fork(0.0)
                self.phase(a, 'RETURNING')
                self.get_logger().info('RETRIEVAL LOADED: %s returning to outbound' % a.pallet_id)
            return

        if a.phase == 'RETURNING':
            if matches_retrieval_completion(task, feedback):
                self.pose(a, HANDOFF)
                self.phase(a, 'OUTFEED')
                self.get_logger().info('OUTBOUND HANDOFF: %s' % a.pallet_id)
            elif (task.get('status') in ('ACCEPTED', 'RUNNING') and
                  int(feedback.get('PickupCommandId', -1)) == a.command_id and
                  int(feedback.get('AcceptedCommandId', -1)) == a.command_id):
                self.pose(a, carried_coordinates(feedback))
            return

        if a.phase == 'OUTFEED':
            if self.tween(a, HANDOFF, OUTBOUND_CONVEYOR, OUTFEED_SECONDS):
                # The PLC/WCS completion was verified before outfeed started.
                # Inventory is owned by WMS; this is read-only visualization.
                self.occupied.pop(a.target, None)
                self.entity_by_location.pop(a.target, None)
                self.phase(a, 'FORK_OUT_APPROACH')
                self.get_logger().info('PALLET ON OUTBOUND CONVEYOR: %s' % a.pallet_id)
            return

        if self.advance_outbound_forklift(a):
            return


def main(args=None):
    rclpy.init(args=args)
    node = PalletVisualSync()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
