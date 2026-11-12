#!/usr/bin/env python3
"""Offline ASRS SDF scene generator; primitives only, no remote Gazebo Fuel assets.

Safety: this is a visual learning environment, not physical or safety validation.
"""
from pathlib import Path
from xml.etree import ElementTree as E
from xml.dom.minidom import parseString
import math

sdf=E.Element('sdf', version='1.9')
w=E.SubElement(sdf,'world', name='asrs_warehouse')
def node(p,k,val=None,**attrs):
    e=E.SubElement(p,k,**attrs)
    if val is not None: e.text=str(val)
    return e

def pose(x=0,y=0,z=0,roll=0,pitch=0,yaw=0):
    return f'{x} {y} {z} {roll} {pitch} {yaw}'

node(w,'gravity','0 0 -9.81')
p=node(w,'physics',name='sim_physics',type='ignored'); node(p,'max_step_size','0.002'); node(p,'real_time_factor','1')
for short,qual in [('physics','Physics'),('user-commands','UserCommands'),('scene-broadcaster','SceneBroadcaster')]:
    node(w,'plugin',filename=f'gz-sim-{short}-system',name=f'gz::sim::systems::{qual}')
scene=node(w,'scene');node(scene,'ambient','0.6 0.65 0.7 1');node(scene,'background','0.12 0.15 0.19 1');node(scene,'shadows','true')
light=node(w,'light',name='sun',type='directional');node(light,'pose',pose(0,0,15));node(light,'diffuse','0.9 0.9 0.9 1');node(light,'specular','0.2 0.2 0.2 1');node(light,'direction','-0.4 0.5 -1');node(light,'cast_shadows','true')
# Put camera above and to the southeast to reveal both racks and aisle.
gui=node(w,'gui',fullscreen='0');ms=node(gui,'plugin',filename='MinimalScene',name='3D View'); gg=node(ms,'gz-gui');node(gg,'title','ASRS warehouse');node(gg,'property','docked',type='string',key='state');node(ms,'engine','ogre2');node(ms,'scene','scene');node(ms,'camera_pose','14 -15 13 0 0.6 2.5')
# MinimalScene draws the world, but does NOT provide camera mouse handling.
# Camera interaction must be loaded explicitly when defining a custom GUI.
for name in [
    'GzSceneManager',
    'InteractiveViewControl',  # drag to pan/orbit; wheel/right drag to zoom
    'CameraTracking',          # Move to / Follow on selected equipment
    'EntityContextMenuPlugin',# right-click menu in the 3D view
    'SelectEntities',          # pick crane and pallets in the scene
    'WorldControl', 'WorldStats', 'EntityTree',
]:
    plugin = node(gui, 'plugin', filename=name, name=name)
    if name in {'InteractiveViewControl', 'CameraTracking', 'EntityContextMenuPlugin', 'SelectEntities'}:
        gg = node(plugin, 'gz-gui')
        node(gg, 'property', 'floating', type='string', key='state')
        node(gg, 'property', 'false', type='bool', key='showTitleBar')
        node(gg, 'property', '5', type='double', key='width')
        node(gg, 'property', '5', type='double', key='height')

C={
 'floor':(0.45,0.47,0.49,1), 'rack':(0.13,0.29,0.48,1), 'beam':(1.0,0.54,0.11,1),
 'steel':(0.55,0.59,0.63,1),'crane':(0.96,0.7,0.13,1), 'dark':(0.17,0.22,0.27,1),
 'wood':(0.55,0.32,0.16,1),'box_blue':(0.12,0.42,0.79,1),'box_green':(0.12,0.59,0.38,1),
 'box_red':(0.78,0.25,0.21,1), 'yellow':(0.97,0.83,0.18,1),'red':(0.85,0.15,0.1,1),
 'skin':(0.82,0.59,0.40,1),'shirt':(0.97,0.67,0.08,1),'pants':(0.18,0.28,0.51,1),
 'green':(0.18,0.67,0.34,1),'glass':(0.25,0.63,0.8,1)
}

def material(parent,color):
    m=node(parent,'material')
    s=' '.join(str(x) for x in C[color]);node(m,'ambient',s);node(m,'diffuse',s)

def geometry(parent,kind,dim):
    geo=node(parent,'geometry'); el=node(geo,kind)
    if kind=='box':node(el,'size',' '.join(str(x) for x in dim))
    elif kind=='sphere':node(el,'radius',dim)
    elif kind=='cylinder':node(el,'radius',dim[0]);node(el,'length',dim[1])

def shape(link,name,kind,dim,xyz,color,rpy=(0,0,0),collision=False):
    v=node(link,'visual',name=name);node(v,'pose',pose(*xyz,*rpy));geometry(v,kind,dim);material(v,color)
    if collision:
        col=node(link,'collision',name=f'{name}_collision');node(col,'pose',pose(*xyz,*rpy));geometry(col,kind,dim)

def box(link,name,xyz,dim,color,collision=False):shape(link,name,'box',dim,xyz,color,collision=collision)
def cylinder(link,name,xyz,radius,length,color,rpy=(0,0,0)):
    shape(link,name,'cylinder',(radius,length),xyz,color,rpy=rpy)
def sphere(link,name,xyz,radius,color):shape(link,name,'sphere',radius,xyz,color)

def static_model(name):
    m=node(w,'model',name=name);node(m,'static','true');return node(m,'link',name='body')

floor=static_model('factory_building')
box(floor,'concrete',(4.5,0,-0.18),(24,18,0.35),'floor',True)
# Painted pedestrian crossings, off-limits aisle band, and hazard markers.
for side,y in [('north',1.62),('south',-1.62)]:
    box(floor,f'paint_{side}',(4.5,y,0.006),(12,0.06,0.012),'yellow')
for i in range(8):
    box(floor,f'pedestrian_mark_{i}',(10.4,-4.8+i*0.68,0.008),(0.5,0.30,0.012),'yellow')
for i in range(4):
    box(floor,f'walkway_dashed_{i}',(-5.0+i*1.7,-6.2,0.01),(1.0,0.06,0.012),'green')
# Columns around outer perimeter help make this look like a warehouse.
for ix,x in enumerate([-6.0,0.0,6.0,12.0]):
    for jy,y in enumerate([-8.0,8.0]):
        box(floor,f'building_column_{ix}_{jy}',(x,y,3.7),(0.22,0.22,7.4),'steel')
# Pallet rack along both sides. Slots center x=c*1.5, level height=l*1.2.
for side,yc in [('north',3.25),('south',-3.25)]:
    r=static_model('rack_'+side)
    for i in range(7):
        x=0.75+i*1.5
        for y in (yc-0.93,yc+0.93):
            box(r,f'post_{i}_{y}',(x,y,2.84),(0.10,0.11,5.68),'rack')
    for level in range(1,5):
        z=level*1.2
        for y in (yc-0.93,yc+0.93):
            box(r,f'beam_{level}_{y}',(5.25,y,z),(9.1,0.12,0.12),'beam')
        for col in range(1,7):
            x=col*1.5
            box(r,f'shelf_{col}_{level}',(x,yc,z-0.04),(1.35,1.83,0.08),'steel')
            # Some bays intentionally empty, particularly A-01-04.
            # Keep A/north rack slots free for real task-driven visual deposits.
            if side == 'south' and (col*7+level*3+1)%5 not in (0,1):
                box(r,f'pallet_{col}_{level}',(x,yc,z+0.12),(1.12,1.0,0.16),'wood')
                box(r,f'goods_{col}_{level}',(x,yc,z+0.47),(0.99,0.9,0.55),['box_blue','box_green','box_red'][(col+level)%3])
# External safety boundary beyond the rack banks, not across the working fork path.
# This is a drawn boundary only; it has no certified safety function.
rails=static_model('aisle_rails_and_safety_fence')
for y in [-0.6,0.6]:box(rails,f'rail_{y}',(4.5,y,0.09),(11.0,0.13,0.18),'steel')
for y in [-4.85,4.85]:
    for i in range(13):
        x=-1+i*0.9
        box(rails,f'guard_post_{i}_{y}',(x,y,0.85),(0.065,0.065,1.7),'yellow')
    for z in [0.52,1.38]:
        box(rails,f'guard_bar_{y}_{z}',(4.4,y,z),(11.05,0.055,0.055),'yellow')
# Conveyor near end of crane aisle. Dynamic task pallets are spawned here.
# No permanently visible pallet: otherwise each task would duplicate stock.
conv=static_model('inbound_conveyor')
box(conv,'frame',(11.0,0,0.63),(2.8,1.35,0.14),'dark')
for x in (9.9,12.1):
    for y in (-0.53,0.53):box(conv,f'leg_{x}_{y}',(x,y,0.31),(0.1,0.1,0.62),'steel')
for i in range(11):cylinder(conv,f'roller_{i}',(9.75+i*0.25,0,0.75),0.055,1.18,'steel',rpy=(math.pi/2,0,0))
# Visual forklift is a single static Gazebo model whose MODEL pose is animated
# using Gazebo UserCommands set_pose/blocking. This is NOT a physics-driven vehicle.
# The local geometry uses the axle-center frame so turning rotates wheels / tines.
forklift_model=node(w,'model',name='asrs_forklift')
node(forklift_model,'static','true')
node(forklift_model,'pose',pose(9.5,-5.6,0))
forklift=node(forklift_model,'link',name='body')
box(forklift,'chassis',(0,0,0.55),(1.75,0.95,0.6),'dark')
box(forklift,'cab',(-0.4,0,1.35),(0.75,0.83,0.95),'yellow')
box(forklift,'mast',(0.85,0,1.2),(0.14,0.75,2.1),'steel')
for y in [-0.36,0.36]:
    box(forklift,f'tine_{y}',(1.40,y,0.94),(1.10,0.10,0.1),'steel')
for i,(x,y) in enumerate([(-0.65,-0.5),(-0.65,0.5),(0.60,-0.5),(0.60,0.5)]):
    cylinder(forklift,f'wheel_{i}',(x,y,0.3),0.25,0.15,'dark',rpy=(math.pi/2,0,0))
# Separate outbound roller conveyor. A retrieved pallet is not displayed as
# outbound until WCS and PLC confirm matching pickup, release and completion.
out=static_model('outbound_conveyor')
box(out,'frame',(11.0,-2.6,0.63),(2.8,1.35,0.14),'dark')
for x in (9.9,12.1):
    for y in (-3.13,-2.07):
        box(out,f'leg_{x}_{y}',(x,y,0.31),(0.1,0.1,0.62),'steel')
for i in range(11):
    cylinder(out,f'roller_{i}',(9.75+i*0.25,-2.6,0.75),0.055,1.18,'steel',rpy=(math.pi/2,0,0))
# Visual-only floor paint at forklift loading / unloading points.
for label,x,y,color in [('forklift_inbound_dock',11.4,-1.6,'green'),
                         ('forklift_outbound_dock',11.4,-4.0,'yellow')]:
    box(floor,label,(x,y,0.012),(1.55,0.07,0.018),color)
# Three simplified human figures stationed beyond crane guard rails.
for idx,(x,y,shirt) in enumerate([(-3.7,-5.6,'shirt'),(11.2,-6.9,'green'),(11.0,5.7,'shirt')]):
    worker=static_model(f'worker_{idx+1}_outside_guard')
    sphere(worker,'head',(x,y,1.65),0.17,'skin')
    box(worker,'torso',(x,y,1.18),(0.48,0.28,0.7),shirt)
    box(worker,'left_leg',(x,y-0.12,0.44),(0.16,0.17,0.82),'pants')
    box(worker,'right_leg',(x,y+0.12,0.44),(0.16,0.17,0.82),'pants')
    cylinder(worker,'helmet',(x,y,1.82),0.19,0.1,'yellow')
# Dynamic crane: fixed track base, carriage X slide, platform Z lift, Y fork extension.
m=node(w,'model',name='asrs_crane');node(m,'pose',pose())

def dynamic_link(name,mass):
    l=node(m,'link',name=name);node(l,'gravity','false')
    inert=node(l,'inertial');node(inert,'mass',mass)
    inertia=node(inert,'inertia')
    for v in ['ixx','iyy','izz']:node(inertia,v,str(mass/5))
    for v in ['ixy','ixz','iyz']:node(inertia,v,'0')
    return l
base=dynamic_link('anchor_link',500)
box(base,'track_anchor',(0,0,0.07),(0.35,0.35,0.14),'dark')
car=dynamic_link('x_carriage',150)
box(car,'running_gear',(0,0,0.23),(1.2,1.05,0.35),'dark')
for sy in [-0.42,0.42]:
    box(car,f'wheel_mount_{sy}',(0,sy,0.15),(0.5,0.12,0.2),'steel')
for sy in [-0.33,0.33]:box(car,f'mast_{sy}',(0,sy,3.15),(0.22,0.20,6.3),'crane')
box(car,'top_bridge',(0,0,6.26),(0.62,0.83,0.20),'crane')
box(car,'control_cab',(0,-0.35,0.85),(0.62,0.42,0.9),'yellow')
platform=dynamic_link('z_platform',65)
box(platform,'load_platform',(0,0,0.27),(1.36,1.08,0.14),'crane')
# The lift starts empty. Pallets follow the X/Z crane feedback as separate
# visual-only entities spawned by pallet_visual_sync.py.
fork=dynamic_link('y_fork',18)
# Two fork tines point toward +Y (north rack A); X positions are their separation.
for fx in (-0.40,0.40):box(fork,f'fork_tine_{fx}',(fx,0.55,0.13),(0.11,1.25,0.10),'steel')

def joint(name,typ,parent,child,axis=None,lower=None,upper=None):
    j=node(m,'joint',name=name,type=typ);node(j,'parent',parent);node(j,'child',child)
    if axis:
        ax=node(j,'axis');node(ax,'xyz',axis)
        limit=node(ax,'limit');node(limit,'lower',lower);node(limit,'upper',upper)
        node(limit,'effort','500000');node(limit,'velocity','2.5')
    return j
joint('world_anchor','fixed','world','anchor_link')
joint('x_travel','prismatic','anchor_link','x_carriage','1 0 0',0,9.0)
joint('z_lift','prismatic','x_carriage','z_platform','0 0 1',0,5.2)
joint('fork_extension','prismatic','z_platform','y_fork','0 1 0',0,2.3)
for joint_name,topic,speed in [('x_travel','x_cmd',2.0),('z_lift','z_cmd',1.4),('fork_extension','fork_cmd',1.4)]:
    plug=node(m,'plugin',filename='gz-sim-joint-position-controller-system',name='gz::sim::systems::JointPositionController')
    node(plug,'joint_name',joint_name)
    node(plug,'topic','/asrs/crane/'+topic)
    node(plug,'use_velocity_commands','true') # visual educational motion; no servo dynamics
    node(plug,'cmd_max',speed)
    node(plug,'cmd_min',-speed)

out=Path(__file__).resolve().with_name('asrs_warehouse.sdf')
raw=E.tostring(sdf,encoding='utf-8')
out.write_text(parseString(raw).toprettyxml(indent='  '),encoding='utf-8')
print(f'Generated {out.name}: {out.stat().st_size:,} bytes')
