#!/usr/bin/env python3
"""Standalone visual test for forklift inbound delivery and outbound collection.

Start only Gazebo with worlds/asrs_warehouse.sdf. Do NOT run the ROS visual
sync nodes or a WMS task while this demo is using the same world. No WCS/PLC.
"""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asrs_gazebo_view.pallet_scene import GazeboServiceClient, CONVEYOR
from asrs_gazebo_view.forklift_scene import (
    HOME, GATE, GATE_TURN, INBOUND_DOCK, OUTBOUND_DOCK, SHIPPING,
    OUTBOUND_CONVEYOR, pallet_on_forks, mix_pose, visible_route_safe,
)


def drive(client, start, end, seconds, pallet=None, steps=12):
    for n in range(1, steps + 1):
        v = mix_pose(start, end, n / steps)
        if not visible_route_safe(v):
            raise RuntimeError(f'Unsafe demo visual route: {v}')
        client.set_forklift_pose(*v)
        if pallet:
            client.set_pose(pallet, pallet_on_forks(v))
        time.sleep(seconds / steps)


def slide(client, pallet, start, end, seconds, steps=8):
    for n in range(1, steps+1):
        client.set_pose(pallet, mix_pose(start, end, n / steps))
        time.sleep(seconds / steps)


def main():
    g = GazeboServiceClient()
    name = 'asrs_pallet_forkliftdemo0001'
    print('Visual forklift-only demonstration: no WMS/PLC commands.', flush=True)
    g.spawn(name, 'FORKLIFT-DEMO')
    g.set_pose(name, pallet_on_forks(HOME))
    print('[1/7] Forklift delivers pallet from receiving to inbound conveyor', flush=True)
    drive(g, HOME, GATE, 2.0, name)
    drive(g, GATE, GATE_TURN, 1.0, name)
    drive(g, GATE_TURN, INBOUND_DOCK, 2.0, name)
    slide(g, name, pallet_on_forks(INBOUND_DOCK), CONVEYOR, 1.2)
    print('[2/7] Forklift leaves pallet on inbound conveyor', flush=True)
    drive(g, INBOUND_DOCK, GATE_TURN, 2.0)
    drive(g, GATE_TURN, GATE, 1.0)
    drive(g, GATE, HOME, 2.0)
    time.sleep(1.3)
    print('[3/7] For demo only, move same pallet to outbound conveyor', flush=True)
    slide(g, name, CONVEYOR, OUTBOUND_CONVEYOR, 1.6)
    print('[4/7] Forklift approaches outbound conveyor', flush=True)
    drive(g, HOME, GATE, 2.0)
    drive(g, GATE, GATE_TURN, 1.0)
    drive(g, GATE_TURN, OUTBOUND_DOCK, 1.6)
    print('[5/7] Forklift lifts pallet at outbound conveyor', flush=True)
    slide(g, name, OUTBOUND_CONVEYOR, pallet_on_forks(OUTBOUND_DOCK), 1.2)
    print('[6/7] Forklift carries pallet to shipping', flush=True)
    drive(g, OUTBOUND_DOCK, GATE_TURN, 1.6, name)
    drive(g, GATE_TURN, GATE, 1.0, name)
    drive(g, GATE, SHIPPING, 2.0, name)
    g.remove_pallet(name)
    print('[7/7] Pallet departed shipping; forklift returns home', flush=True)
    drive(g, SHIPPING, HOME, 1.5)
    print('SUCCESS: forklift create, drive, carry, handoff and remove service calls worked.\n'
          'This is a visual kinematic demo, not real forklift autonomy.', flush=True)


if __name__ == '__main__':
    main()
