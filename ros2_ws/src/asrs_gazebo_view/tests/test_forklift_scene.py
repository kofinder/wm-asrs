#!/usr/bin/env python3
"""Unit tests for visual-only forklift paths and coordinates."""
from pathlib import Path
import math
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asrs_gazebo_view.forklift_scene import (
    HOME, GATE, GATE_TURN, INBOUND_DOCK, OUTBOUND_DOCK,
    SHIPPING, OUTBOUND_CONVEYOR, pallet_on_forks, mix_pose, visible_route_safe,
)


class TestForkliftScene(unittest.TestCase):
    def test_cargo_follows_heading(self):
        x, y, z = pallet_on_forks(HOME)
        self.assertAlmostEqual(x, 10.9)
        self.assertAlmostEqual(y, -5.6)
        self.assertAlmostEqual(z, 1.08)
        x, y, z = pallet_on_forks(INBOUND_DOCK)
        self.assertAlmostEqual(x, 11.4)
        self.assertAlmostEqual(y, -0.2)
        self.assertAlmostEqual(z, 1.08)
        x, y, z = pallet_on_forks(OUTBOUND_DOCK)
        self.assertAlmostEqual(x, OUTBOUND_CONVEYOR[0])
        self.assertAlmostEqual(y, OUTBOUND_CONVEYOR[1])

    def test_route_samples_clear_crane_aisle(self):
        waypoints = [HOME, GATE, GATE_TURN, INBOUND_DOCK,
                     GATE_TURN, GATE, HOME, GATE, GATE_TURN,
                     OUTBOUND_DOCK, GATE_TURN, GATE, SHIPPING, HOME]
        for start, end in zip(waypoints, waypoints[1:]):
            for i in range(21):
                self.assertTrue(visible_route_safe(mix_pose(start, end, i / 20)),
                                f'Route not in demo corridor: {start} -> {end}')
        self.assertFalse(visible_route_safe((5, 0, 0)))

    def test_world_has_local_movable_forklift_geometry(self):
        world = Path(__file__).resolve().parents[1] / 'worlds/asrs_warehouse.sdf'
        root = ET.parse(world).getroot()
        model = root.find(".//model[@name='asrs_forklift']")
        self.assertIsNotNone(model)
        self.assertEqual(model.findtext('static'), 'true')
        self.assertEqual(model.findtext('pose'), '9.5 -5.6 0 0 0 0')
        chassis = model.find("link/visual[@name='chassis']")
        self.assertIsNotNone(chassis)
        self.assertEqual(chassis.findtext('pose'), '0 0 0.55 0 0 0')
        self.assertIsNotNone(root.find(".//model[@name='outbound_conveyor']"))


if __name__ == '__main__':
    unittest.main()
