#!/usr/bin/env python3
"""Offline tests for visual-only ASRS pallet lifecycles (no ROS/Gazebo)."""
from pathlib import Path
import importlib
import sys
import types
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

rclpy = types.ModuleType('rclpy')
node_module = types.ModuleType('rclpy.node')
node_module.Node = object
rclpy.node = node_module
std_msgs = types.ModuleType('std_msgs')
std_msgs_msg = types.ModuleType('std_msgs.msg')
std_msgs_msg.Float64 = lambda data: data
std_msgs.msg = std_msgs_msg
sys.modules.update({'rclpy': rclpy, 'rclpy.node': node_module,
                    'std_msgs': std_msgs, 'std_msgs.msg': std_msgs_msg})
module = importlib.import_module('asrs_gazebo_view.pallet_visual_sync')


class FakeTransport:
    def __init__(self):
        self.spawns = []
        self.moves = []
        self.should_fail = False
        self.forklift_moves = []
        self.removes = []

    def spawn(self, name, pallet_id):
        if self.should_fail:
            raise RuntimeError('Gazebo /create failed')
        self.spawns.append((name, pallet_id))

    def set_pose(self, name, xyz):
        if self.should_fail:
            raise RuntimeError('Gazebo /set_pose failed')
        self.moves.append((name, xyz))

    def set_forklift_pose(self, x, y, yaw):
        if self.should_fail:
            raise RuntimeError('Gazebo forklift /set_pose failed')
        self.forklift_moves.append((x, y, yaw))

    def remove_pallet(self, name):
        if self.should_fail:
            raise RuntimeError('Gazebo /remove failed')
        self.removes.append(name)


class FakeLogger:
    def __init__(self):
        self.lines = []

    def info(self, x, *args):
        self.lines.append(str(x))

    def warning(self, x, *args):
        self.lines.append(str(x))


def feedback(cmd=9, machine='RUNNING', pos='HOME', x=9000, z=0,
             pickup=0, completed=0, release=0):
    return dict(AcceptedCommandId=cmd, MachineState=machine, Position=pos,
                AxisXPositionMm=x, AxisZPositionMm=z, PickupCommandId=pickup,
                CompletedCommandId=completed, ReleasedCommandId=release)


def watcher(operation='PUTAWAY'):
    w = module.PalletVisualSync.__new__(module.PalletVisualSync)
    w.transport = FakeTransport()
    w.occupied = {}
    w.entity_by_location = {}
    w.seen = set()
    w.pending = []
    w.last_warn = 0.0
    w.logs = FakeLogger()
    w.forks = []
    w.get_logger = lambda: w.logs
    w.fork = lambda meters: w.forks.append(meters)
    w.active = module.ActivePallet('task-12345678', 'P003', 'A-03-02', 9,
                                   'asrs_pallet_task_12345678', operation=operation)
    return w


def finish_motion(w):
    w.active.phase_started -= 10.0


class TestPalletChoreography(unittest.TestCase):
    def test_putaway_full_conveyor_crane_rack_path(self):
        w = watcher()
        task = {'taskId': w.active.task_id, 'status':'ACCEPTED',
                'targetLocation':'A-03-02','commandId':9}
        s = feedback()
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'FORK_IN_APPROACH')
        self.assertEqual(len(w.transport.spawns), 1)
        # Exercise forklift inbound delivery before the normal conveyor stage.
        for phase in ['FORK_IN_APPROACH','FORK_IN_TURN','FORK_IN_DOCK',
                      'FORK_IN_UNLOAD','FORK_IN_CLEAR','FORK_IN_FACE_HOME',
                      'FORK_IN_HOME']:
            self.assertEqual(w.active.phase, phase)
            finish_motion(w)
            w.putaway(task, s)
        self.assertEqual(w.active.phase, 'INFEED')
        self.assertGreaterEqual(len(w.transport.forklift_moves), 6)
        self.assertEqual(w.transport.moves[-1][1], module.CONVEYOR)
        finish_motion(w)
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'WAIT_LOADING')
        self.assertEqual(w.transport.moves[-1][1], module.INFEED_END)
        s['MachineState'] = 'LOADING'
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'LOADING')
        finish_motion(w)
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'WAIT_PICKUP_ACK')
        self.assertEqual(w.transport.moves[-1][1], module.HANDOFF)
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'WAIT_PICKUP_ACK')  # no forged pickup
        s['PickupCommandId'] = 9
        s['MachineState'] = 'TRANSPORTING'
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'CARRYING')
        s.update(AxisXPositionMm=4500, AxisZPositionMm=2400)
        task['status'] = 'RUNNING'
        w.putaway(task, s)
        self.assertEqual(w.transport.moves[-1][1], (4.5, 0.0, 2.82))
        task['status'] = 'COMPLETED'
        s.update(CompletedCommandId=9, Position='A-03-02', MachineState='COMPLETED')
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'DEPOSITING')
        self.assertEqual(w.occupied, {})
        self.assertIn(module.FORK_EXTENSION, w.forks)
        finish_motion(w)
        w.putaway(task, s)
        self.assertIsNone(w.active)
        self.assertEqual(w.occupied, {'A-03-02':'P003'})
        self.assertEqual(w.transport.moves[-1][1], (4.5, 3.25, 2.52))
        self.assertEqual(w.forks[-1], 0.0)

    def test_no_placement_for_wrong_completed_command_or_location(self):
        w = watcher()
        w.active.phase = 'CARRYING'
        task = {'status':'COMPLETED','targetLocation':'A-03-02','commandId':9}
        s = feedback(pickup=9, completed=8, pos='A-03-02',x=4500,z=2400)
        w.putaway(task, s)
        self.assertEqual(w.occupied, {})
        self.assertEqual(w.active.phase, 'CARRYING')
        s['CompletedCommandId'] = 9
        s['Position'] = 'A-02-02'
        w.putaway(task, s)
        self.assertEqual(w.occupied, {})
        self.assertEqual(w.active.phase, 'CARRYING')
        s['Position'] = 'A-03-02'
        w.putaway(task, s)
        self.assertEqual(w.active.phase, 'DEPOSITING')

    def test_no_success_if_gazebo_pose_service_fails(self):
        w = watcher()
        w.active.phase = 'DEPOSITING'
        w.transport.should_fail = True
        task = {'status':'COMPLETED','targetLocation':'A-03-02','commandId':9}
        with self.assertRaisesRegex(RuntimeError, 'set_pose failed'):
            w.putaway(task, feedback())
        self.assertEqual(w.occupied, {})
        self.assertIsNotNone(w.active)

    def test_retrieval_rack_to_crane_to_outbound(self):
        w = watcher('RETRIEVAL')
        w.occupied = {'A-03-02': 'P003'}
        w.entity_by_location = {'A-03-02': 'asrs_pallet_stored0001'}
        task = {'status':'RUNNING', 'targetLocation':'A-03-02', 'commandId':9}
        s = feedback(machine='RUNNING',pos='HOME',x=1000,z=1000)
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'WAIT_RACK')
        self.assertEqual(w.active.entity_name, 'asrs_pallet_stored0001')
        self.assertEqual(w.transport.spawns, [])
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'WAIT_RACK')
        s.update(MachineState='PICKING',Position='A-03-02',AxisXPositionMm=4500,AxisZPositionMm=2400)
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'RACK_PICKUP')
        self.assertIn(module.FORK_EXTENSION, w.forks)
        finish_motion(w)
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'WAIT_PICKUP_ACK')
        self.assertEqual(w.transport.moves[-1][1], (4.5, 0.0, 2.82))
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'WAIT_PICKUP_ACK')
        s['PickupCommandId'] = 9
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'RETURNING')
        s.update(AxisXPositionMm=9000,AxisZPositionMm=0,Position='OUTBOUND',
                 CompletedCommandId=9,ReleasedCommandId=8)
        task['status'] = 'COMPLETED'
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'RETURNING')  # stale release ID
        self.assertEqual(w.occupied, {'A-03-02': 'P003'})
        s['ReleasedCommandId'] = 9
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'OUTFEED')
        finish_motion(w)
        w.retrieval(task, s)
        self.assertEqual(w.active.phase, 'FORK_OUT_APPROACH')
        self.assertEqual(w.occupied, {})
        self.assertEqual(w.transport.moves[-1][1], module.OUTBOUND_CONVEYOR)
        for phase in ['FORK_OUT_APPROACH','FORK_OUT_TURN','FORK_OUT_DOCK',
                      'FORK_OUT_PICKUP','FORK_OUT_CLEAR','FORK_OUT_FACE_HOME',
                      'FORK_OUT_SHIPPING','FORK_OUT_REMOVE','FORK_OUT_HOME']:
            self.assertEqual(w.active.phase, phase)
            finish_motion(w)
            w.retrieval(task, s)
        self.assertIsNone(w.active)
        self.assertEqual(w.transport.removes, ['asrs_pallet_stored0001'])
        self.assertGreaterEqual(len(w.transport.forklift_moves), 6)

    def test_retrieval_restores_model_when_gazebo_restarted(self):
        w = watcher('RETRIEVAL')
        task = {'status':'ACCEPTED', 'targetLocation':'A-03-02','commandId':9}
        w.retrieval(task, feedback())
        self.assertEqual(w.active.phase, 'WAIT_RACK')
        self.assertEqual(w.occupied, {'A-03-02':'P003'})
        self.assertEqual(w.transport.moves[-1][1], (4.5,3.25,2.52))

    def test_conflicting_pallet_does_not_replace_existing_rack_visual(self):
        w = watcher('RETRIEVAL')
        w.occupied = {'A-03-02':'OTHER'}
        w.retrieval({'status':'RUNNING'}, feedback())
        self.assertIsNone(w.active)
        self.assertEqual(w.occupied, {'A-03-02':'OTHER'})

    def test_uncertain_no_placement_or_retrieval_success(self):
        for operation in ('PUTAWAY','RETRIEVAL'):
            w = watcher(operation)
            w.active.phase = 'CARRYING' if operation == 'PUTAWAY' else 'RETURNING'
            w.status_url = 'status'
            w.tasks_url = 'tasks'
            w.get_json = lambda url, w=w: (
                [{'taskId': w.active.task_id, 'status':'UNCERTAIN'}] if url == 'tasks'
                else feedback())
            w.tick()
            self.assertIsNone(w.active)
            self.assertEqual(w.occupied,{})
            self.assertEqual(w.forks[-1],0)

    def test_newly_finished_task_is_not_silently_dropped(self):
        w = watcher()
        w.active = None
        w.status_url = 'status'; w.tasks_url = 'tasks'
        w.seen = {'old-task'}
        task = {'taskId':'new-task-12345678','palletId':'P005','targetLocation':'A-02-01',
                'commandId':15,'status':'COMPLETED','operation':'PUTAWAY'}
        w.get_json = lambda url: [task] if url=='tasks' else feedback(cmd=15,completed=15,pos='A-02-01')
        w.tick()
        self.assertEqual(len(w.transport.spawns),1)
        self.assertTrue(w.active.replay)
        self.assertEqual(w.active.phase,'FORK_IN_APPROACH')
        self.assertTrue(any('VISUAL REPLAY' in s for s in w.logs.lines))

    def test_historical_completed_task_on_startup_is_ignored(self):
        w = watcher()
        w.active = None
        w.seen = None
        w.status_url = 'status'; w.tasks_url = 'tasks'
        w.get_json = lambda url: [{'taskId':'old-task','status':'COMPLETED'}]
        w.tick()
        self.assertIsNone(w.active)
        self.assertEqual(w.transport.spawns, [])

    def test_forklift_pickup_requires_gazebo_service_success(self):
        w = watcher('RETRIEVAL')
        w.active.phase = 'FORK_OUT_REMOVE'
        w.transport.should_fail = True
        with self.assertRaisesRegex(RuntimeError, 'remove failed'):
            w.retrieval({'status': 'COMPLETED'}, feedback())
        self.assertEqual(w.active.phase, 'FORK_OUT_REMOVE')
        self.assertIsNotNone(w.active)

    def test_forklift_route_does_not_enter_guarded_aisle(self):
        from asrs_gazebo_view.forklift_scene import HOME, GATE, GATE_TURN, INBOUND_DOCK, OUTBOUND_DOCK, visible_route_safe, pallet_on_forks
        for pos in (HOME, GATE, GATE_TURN, INBOUND_DOCK, OUTBOUND_DOCK):
            self.assertTrue(visible_route_safe(pos))
        self.assertFalse(visible_route_safe((5.0, 0.0, 0.0)))
        self.assertAlmostEqual(pallet_on_forks(INBOUND_DOCK)[1], -0.2)
        self.assertAlmostEqual(pallet_on_forks(OUTBOUND_DOCK)[1], -2.6)

    def test_interpolation_is_bounded(self):
        self.assertEqual(module.interpolate((0,0,0),(9,0,1),-4), (0,0,0))
        self.assertEqual(module.interpolate((0,0,0),(9,0,1),1.5), (9,0,1))
        self.assertEqual(module.interpolate((0,0,0),(9,0,1),.5), (4.5,0,.5))


if __name__=='__main__':
    unittest.main()
