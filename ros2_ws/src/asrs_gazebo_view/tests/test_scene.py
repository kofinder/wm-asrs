#!/usr/bin/env python3
"""Static offline scene checks (does not require Gazebo or ROS)."""
import ast
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
world=ET.parse(root/'worlds/asrs_warehouse.sdf').getroot()
assert world.tag=='sdf'
w=world.find('world')
assert w is not None
models={m.attrib['name']:m for m in w.findall('model')}
for name in ['factory_building','rack_north','rack_south','asrs_crane','inbound_conveyor', 'asrs_forklift', 'outbound_conveyor', 'worker_1_outside_guard','worker_2_outside_guard','worker_3_outside_guard']:
    assert name in models, name
# Moving forklift geometry must be model-local, and the model must be movable.
assert models['asrs_forklift'].findtext('static') == 'true'
assert models['asrs_forklift'].findtext('pose').split()[:2] == ['9.5', '-5.6']
assert models['asrs_forklift'].find("link/visual[@name='chassis']") is not None
crane=models['asrs_crane']
for joint in ['x_travel','z_lift','fork_extension','world_anchor']:
    assert crane.find(f"joint[@name='{joint}']") is not None, joint
# A rack-reaching fork must extend towards +Y, not sideways across X.
fork_joint = crane.find("joint[@name='fork_extension']")
assert fork_joint.findtext('axis/xyz') == '0 1 0'
assert float(fork_joint.findtext('axis/limit/upper')) >= 2.2
fork_link = crane.find("link[@name='y_fork']")
tines = [v for v in fork_link.findall('visual') if v.attrib['name'].startswith('fork_tine_')]
assert len(tines) == 2
assert all(float(v.findtext('geometry/box/size').split()[1]) >
           float(v.findtext('geometry/box/size').split()[0]) for v in tines)
# SDFormat requires link/joint/frame names to be unique within a model.
for model in models.values():
    names = [item.attrib['name'] for item in model if item.tag in {'link', 'joint', 'frame'}]
    assert len(names) == len(set(names)), f"Duplicate link/joint/frame name in {model.attrib['name']}: {names}"
    for j in model.findall('joint'):
        assert j.attrib['name'] != j.findtext('child'), f"Joint named like its own child link: {j.attrib['name']}"

plugins={p.attrib['filename']:p for p in crane.findall('plugin')}
# A custom <gui> must include separate plugins for mouse camera controls.
gui = w.find('gui')
assert gui is not None
gui_plugins = {p.attrib['filename'] for p in gui.findall('plugin')}
assert {'MinimalScene', 'GzSceneManager', 'InteractiveViewControl', 'CameraTracking',
        'EntityContextMenuPlugin', 'SelectEntities'} <= gui_plugins, gui_plugins
assert 'gz-sim-joint-position-controller-system' in plugins
joint_topics=[p.findtext('topic') for p in crane.findall('plugin')]
assert set(joint_topics)=={'/asrs/crane/x_cmd','/asrs/crane/z_cmd','/asrs/crane/fork_cmd'}
wplugins={p.attrib['filename'] for p in w.findall('plugin')}
assert {'gz-sim-physics-system','gz-sim-user-commands-system','gz-sim-scene-broadcaster-system'} <= wplugins
for file in ['asrs_gazebo_view/wcs_visual_sync.py','launch/asrs_warehouse.launch.py','worlds/generate_world.py', 'asrs_gazebo_view/pallet_scene.py', 'asrs_gazebo_view/pallet_visual_sync.py', 'asrs_gazebo_view/forklift_scene.py', 'scripts/demo_forklift_sequence.py', 'scripts/test_pallet_smoke.py', 'scripts/demo_pallet_sequence.py']:
    ast.parse((root/file).read_text())
assert not models['inbound_conveyor'].findall(".//visual[@name='pallet']")
assert not models['asrs_crane'].findall(".//visual[@name='pallet_on_lift']")
assert not models['rack_north'].findall(".//visual[@name='pallet_1_4']")
print('OK: SDF XML, clear A rack, empty conveyor, crane joints, Gazebo plugins, Python syntax')
