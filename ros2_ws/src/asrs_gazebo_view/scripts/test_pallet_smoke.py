#!/usr/bin/env python3
"""Gazebo-only visual service smoke test; no WMS/WCS connection needed.

Requires a running corrected Gazebo world with UserCommands. Start the world
and run this test in another terminal to see an independent demo pallet move.
Restart Gazebo afterwards to clear the smoke-test model.
"""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asrs_gazebo_view.pallet_scene import GazeboServiceClient

pallet = GazeboServiceClient()
name = 'asrs_pallet_smoketest01'
print('Spawning pallet at inbound conveyor: x=11.4, y=0, z=0.89')
pallet.spawn(name, 'DEMO-001')
time.sleep(1.3)
print('Move pallet to the crane load platform: x=1.5, y=0, z=0.42')
pallet.set_pose(name, (1.5, 0.0, 0.42))
time.sleep(1.3)
print('Move pallet to A-01-04 shelf: x=1.5, y=3.25, z=4.92')
pallet.set_pose(name, (1.5, 3.25, 4.92))
print('Success: Gazebo /create and /set_pose services accepted requests.')
print('Restart Gazebo to clear the smoke-test pallet before automated tests.')
