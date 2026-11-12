#!/usr/bin/env python3
"""Stand-alone Gazebo pallet-handling visual demo (NO WMS/PLC control).

Launch ONLY Gazebo with asrs_warehouse.sdf (without visual sync nodes).
This publishes idealized joint targets and animates a static pallet with Gazebo
UserCommands; it demonstrates geometry but NOT physical fork/pallet contact.
"""
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asrs_gazebo_view.pallet_scene import GazeboServiceClient, CONVEYOR, rack_coordinates
INFEED_END = (9.4, 0.0, 0.89)
HANDOFF = (9.0, 0.0, 0.42)
FORK_EXTENSION = 2.2


def interpolate(start, end, fraction):
    return tuple(float(a) + (float(b) - float(a)) * fraction
                 for a, b in zip(start, end))

def joint(name, value):
    subprocess.run(['gz', 'topic', '-t', '/asrs/crane/' + name + '_cmd',
                    '-m', 'gz.msgs.Double', '-p', 'data: %.4f' % value],
                   check=True, capture_output=True, text=True, timeout=15)


def slide(pallet, name, start, end, seconds=3.0, steps=12):
    for i in range(1, steps+1):
        pallet.set_pose(name, interpolate(start, end, i / steps))
        time.sleep(seconds / steps)


def main():
    name = 'asrs_pallet_demo_' + format(time.time_ns(), 'x')
    transport = GazeboServiceClient()
    target = rack_coordinates('A-03-02')
    print('STANDALONE DEMO only: no PLC command, no WMS stock update.', flush=True)
    joint('x', 9.0)
    joint('z', 0.0)
    joint('fork', 0.0)
    time.sleep(3.0)
    print('[1/5] Pallet appears at inbound roller conveyor', flush=True)
    transport.spawn(name, 'PALLET-DEMO')
    time.sleep(1.3)
    print('[2/5] Conveyor moves pallet toward crane loading platform', flush=True)
    slide(transport, name, CONVEYOR, INFEED_END, 2.0)
    slide(transport, name, INFEED_END, HANDOFF, 1.8)
    print('[3/5] Crane carries pallet to A-03-02', flush=True)
    joint('x', 4.5)
    joint('z', 2.4)
    slide(transport, name, HANDOFF, (4.5, 0, 2.82), 4.5, 18)
    time.sleep(1.0)
    print('[4/5] Telescopic fork extends into north rack; pallet is placed', flush=True)
    joint('fork', FORK_EXTENSION)
    time.sleep(1.1)
    slide(transport, name, (4.5, 0, 2.82), target, 3.3, 16)
    joint('fork', 0.0)
    print('[5/5] Pallet remains visible on shelf A-03-02', flush=True)
    print('Restart Gazebo to clear the demonstration pallet.', flush=True)


if __name__ == '__main__':
    main()
