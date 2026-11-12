#!/usr/bin/env python3
"""Dependency-free tests for pallet entity geometry and Gazebo requests."""
import sys
from pathlib import Path
import unittest
import json
import re
import xml.etree.ElementTree as ET
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asrs_gazebo_view.pallet_scene import (
    pallet_sdf, rack_coordinates, carried_coordinates, make_entity_name,
    pose_request, GazeboServiceClient,
)


class TestPallet(unittest.TestCase):
    def test_rack_positions(self):
        self.assertEqual(rack_coordinates('A-01-04'), (1.5, 3.25, 4.92))
        self.assertEqual(rack_coordinates('A-03-02'), (4.5, 3.25, 2.52))
        for bad in ('B-01-04', 'A-00-01', 'A-07-01', 'A-01-05', 'a-01-04'):
            with self.assertRaises(ValueError):
                rack_coordinates(bad)

    def test_measured_positions(self):
        self.assertEqual(carried_coordinates({'AxisXPositionMm':1500,
                                              'AxisZPositionMm':4800}), (1.5, 0.0, 5.22))
        with self.assertRaises((ValueError, KeyError)):
            carried_coordinates({'Position':'HOME'})

    def test_xml_valid(self):
        name = make_entity_name('01234567-abcd-1234-abcd-9876543210ab')
        root = ET.fromstring(pallet_sdf(name, 'P0001'))
        model = root.find('model')
        self.assertEqual(model.attrib['name'], name)
        self.assertEqual(model.findtext('static'), 'true')
        self.assertEqual(len(model.findall('.//visual')), 2)
        self.assertEqual(len(model.findall('.//collision')), 0)
        self.assertIn('position: {x: 1.5000', pose_request(name, (1.5, 0, 4.92)))

    def test_gazebo_service_arguments(self):
        fake = type('Result', (), {'returncode':0, 'stdout':'data: true\n', 'stderr':''})()
        with patch('asrs_gazebo_view.pallet_scene.subprocess.run', return_value=fake) as run:
            c = GazeboServiceClient()
            c.spawn('asrs_pallet_test0001', 'P-001')
            c.set_pose('asrs_pallet_test0001', (4.5, 3.25, 2.52))
            c.set_forklift_pose(11.4, -1.6, 1.57079632679)
            c.remove_pallet('asrs_pallet_test0001')
            self.assertEqual(run.call_count, 4)
            create_args = run.call_args_list[0].args[0]
            pose_args = run.call_args_list[1].args[0]
            self.assertEqual(create_args[create_args.index('-s') + 1],
                             '/world/asrs_warehouse/create/blocking')
            self.assertEqual(pose_args[pose_args.index('-s') + 1],
                             '/world/asrs_warehouse/set_pose/blocking')
            create_req = create_args[create_args.index('--req') + 1]
            self.assertNotIn('sdf_filename', create_req)
            self.assertTrue(create_req.startswith('sdf: "'))
            embedded_sdf = json.loads(create_req[len('sdf: '):])
            self.assertEqual(ET.fromstring(embedded_sdf).find('model').get('name'),
                             'asrs_pallet_test0001')
            self.assertIn('name: "asrs_pallet_test0001"', run.call_args_list[1].args[0][-1])
            self.assertEqual(run.call_args_list[0].args[0][run.call_args_list[0].args[0].index('--timeout') + 1], '20000')
            self.assertGreaterEqual(run.call_args_list[0].kwargs['timeout'], 24)
            forklift = run.call_args_list[2].args[0]
            self.assertIn('name: "asrs_forklift"', forklift[-1])
            self.assertIn('z: 0.707107', forklift[-1])
            removal = run.call_args_list[3].args[0]
            self.assertIn('/world/asrs_warehouse/remove/blocking', removal)
            self.assertIn('type: MODEL', removal[-1])

    def test_failed_create_response_is_not_reported_as_success(self):
        fake = type('Result', (), {'returncode': 0, 'stdout': 'data: false\n', 'stderr': ''})()
        with patch('asrs_gazebo_view.pallet_scene.subprocess.run', return_value=fake):
            with self.assertRaisesRegex(RuntimeError, 'create/blocking failed'):
                GazeboServiceClient().spawn('asrs_pallet_test0001', 'P-001')


if __name__ == '__main__':
    unittest.main()
