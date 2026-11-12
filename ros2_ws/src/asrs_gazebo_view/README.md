**Forklift v4 update:** For current installation, standalone driving demo, and full WMS putaway/retrieval route see `../../../FORKLIFT_V4.md` at the project root.

# Gazebo pallet-create timeout fix (v0.2.1)

The first release used only 2,500 ms for Gazebo `/create` and `/set_pose`
requests. The timeout is now 20,000 ms by default and can be overridden with
`ASRS_GZ_SERVICE_TIMEOUT_MS` (1,000–60,000). This does **not** fix a stopped,
unresponsive, or misconfigured Gazebo server. When a service times out, first
make sure Gazebo is running and try:

```bash
gz service -s /world/asrs_warehouse/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 10000 --req 'pause: false'
```

Then rerun `scripts/test_pallet_smoke.py`, **before** attempting a new WMS
putaway. Since WCS simulates movement quickly, missed old tasks will not replay.

---

# NEW in v0.2 — Visible WMS pallet movement (Gazebo Harmonic)

This edition supersedes the earlier `asrs-gazebo-digital-twin-fixed.zip` package.
It fixes the misleading always-loaded crane by starting the crane platform empty,
removes the fake permanently occupied inbound conveyor pallet, and leaves the A
(north) rack bank empty so NEW WMS putaway tasks can visibly populate shelves.
The B (south) rack bank still contains example stock.

**What the animation DOES:** each NEW accepted WCS putaway produces a *visual-only*
pallet model at the inbound conveyor. On RUNNING it transfers that pallet to the
crane's platform, which follows reported (simulated) X/Z PLC encoders. On a WCS
COMPLETED task with a matching `CompletedCommandId` and `Position`, it animates a
short transfer to the A rack shelf and leaves the pallet visible there. A task
with `UNCERTAIN` status is **never visually deposited**. A repeated putaway to
an already visually occupied A rack slot is rejected by the visualization
(log warning); this does NOT fix the underlying WMS inventory constraints.

**What it DOES NOT do:** physical pickup from the conveyor by the crane, collision
checking, force simulation, genuine load attachment / fork contact, pallet-ID
tracking through sensors, or safety logic. Pickup from the conveyor to the crane
is an intentional *visual jump*. Shelf placement is a visual slide, not physical
fork kinematics. Gazebo does not authorize a completion or edit WMS stock.

## Upgrade instructions (run on your existing Ubuntu machine)

1. Close Gazebo and stop the existing ROS 2 visualization launch (`Ctrl+C`).
   Keep the WMS, WCS, ROS planner and virtual PLC available for final testing.
2. Download the ZIP and extract its single `asrs_gazebo_view` folder **over**
   your existing package:

   ```bash
   unzip -o ~/Downloads/asrs-gazebo-pallet-animation-v2.zip \
     -d ~/workspaces/wm_asrs/ros2_ws/src
   ```

3. Ensure your WCS `/api/crane/status` JSON includes `AxisXPositionMm`,
   `AxisZPositionMm`, `Position` and `CompletedCommandId`:

   ```bash
   curl -s http://127.0.0.1:8080/api/crane/status | python3 -m json.tool
   ```

   If axis values are absent, apply `patches/expose-axis-feedback.patch` to the
   Kotlin project if you have not applied it already, and restart WCS.

4. Build and source the updated package:

   ```bash
   cd ~/workspaces/wm_asrs/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --packages-select asrs_gazebo_view --symlink-install
   source install/setup.bash
   export GZ_CONFIG_PATH="/usr/share/gz${GZ_CONFIG_PATH:+:$GZ_CONFIG_PATH}"
   ros2 launch asrs_gazebo_view asrs_warehouse.launch.py
   ```

5. After the launch (including the `asrs_pallet_visual_sync` node) is up, submit
   a **NEW** WMS task `P005 -> A-02-01`. Watch the pallet spawn at conveyor,
   visually transfer to the crane, move to X=3.0m and Z=1.2m, then appear on
   the A-02-01 shelf after verified simulated PLC completion. Follow up with
   `P006 -> A-04-03`. Do not reuse an occupied location.

6. If no pallet appears, inspect the built-in Gazebo services and WCS tasks:

   ```bash
   gz service -l | grep -E '/world/asrs_warehouse/(create|set_pose)'
   ros2 node list | grep visual_sync
   curl -s http://127.0.0.1:8080/api/tasks | python3 -m json.tool
   ```

   The watcher deliberately ignores tasks that were COMPLETED or UNCERTAIN
   *before* it started. It must already be running when you submit the task.

## Optional Gazebo-only pallet smoke test (no WCS required)

Run only Gazebo on the corrected world, then in another terminal:

```bash
python3 ~/workspaces/wm_asrs/ros2_ws/src/asrs_gazebo_view/scripts/test_pallet_smoke.py
```

This creates a test pallet, teleports it to the crane lift, then moves it to
A-01-04. It validates Gazebo's `create` and `set_pose` services independently.
Restart Gazebo before starting integrated tests so the smoke-test pallet doesn't
obscure a real task pallet.

**Offline checks** (do not require ROS or Gazebo):

```bash
cd ~/workspaces/wm_asrs/ros2_ws/src/asrs_gazebo_view
python3 tests/test_scene.py
python3 -m unittest discover -s tests -p 'test_pallet_*.py' -v
```

---

# ASRS Gazebo Digital Twin — ROS 2 Jazzy + Gazebo Harmonic

**2026-11-11 fix:** Corrected duplicate `y_fork` link/joint names that prevented Gazebo from loading the warehouse. The movable link remains `y_fork`; its joint is `fork_extension`.

This package adds a **3-D animated warehouse visualization** to the existing `wm_asrs` four-layer lab. It contains no vendor models or external assets.

## Included

- `worlds/asrs_warehouse.sdf`: offline warehouse: two 4-tier rack banks (A slots clear, B rack stocked), inbound roller conveyor, forklift, **three stationary worker figures outside the crane area**, columns, painted walkways, guard rails, and a yellow moving stacker crane.
- `worlds/generate_world.py`: regenerates the SDF from primitives.
- `launch/asrs_warehouse.launch.py`: starts Gazebo Harmonic, ROS 2 ↔ Gazebo topic bridge, and read-only WCS visual follower.
- `asrs_gazebo_view/wcs_visual_sync.py`: reads WCS crane status via HTTP and publishes *simulated measured X/Z* positions to Gazebo.
- `asrs_gazebo_view/pallet_visual_sync.py`: watches NEW WCS putaways and visually spawns / carries / deposits task-linked pallet models via Gazebo UserCommands; no WMS writes or PLC commands.
- `patches/expose-axis-feedback.patch`: optional, recommended Kotlin WCS patch to return simulator's `AxisXPositionMm` and `AxisZPositionMm` on `GET /api/crane/status`.

**Not provided:** real EtherCAT, a motion-rated control loop, lidar/perception, collision-based pallet pickup, real pedestrian motion, or certified functional-safety behavior. This is an **educational visualization** of your virtual crane, not a physics/engineering validation of an ASRS.

## Prerequisites (Ubuntu 24.04)

ROS 2 Jazzy, Gazebo Harmonic (`gz sim`), Python 3 `rclpy`, and ROS/Gazebo bridge:

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz-bridge python3-colcon-common-extensions
source /opt/ros/jazzy/setup.bash
ros2 pkg list | grep ros_gz_bridge
gz sim --version
```

`gz` missing? Follow the official Gazebo Harmonic installation instructions. Gazebo's **plugin filename spelling matters**; this file uses `gz-sim-physics-system` and other lower-case names.

## Install into the **existing** WMS/WCS/ROS workspace

This package intentionally does **not** overwrite your working WMS/WCS or ROS planner.

1. Extract the ZIP **into the existing ROS 2 source folder** so that the path becomes:

   `~/workspaces/wm_asrs/ros2_ws/src/asrs_gazebo_view/package.xml`

   Example, if `asrs-gazebo-digital-twin.zip` was downloaded into `~/Downloads`:

   ```bash
   unzip -o ~/Downloads/asrs-gazebo-digital-twin.zip -d ~/workspaces/wm_asrs/ros2_ws/src
   ```

2. Apply a **small WCS change to expose virtual axis feedback**; from project root:

   ```bash
   cd ~/workspaces/wm_asrs
   patch --dry-run -p1 < ros2_ws/src/asrs_gazebo_view/patches/expose-axis-feedback.patch
   patch -p1 < ros2_ws/src/asrs_gazebo_view/patches/expose-axis-feedback.patch
   ```

   If the patch does not apply because your WCS code differs, edit `asrs-wcs/src/main/kotlin/com/example/asrs/wcs/OpcUaClientService.kt` and add to `status()`:

   ```kotlin
   "AxisXPositionMm" to read("AxisXPositionMm"),
   "AxisZPositionMm" to read("AxisZPositionMm"),
   "SafetyState" to read("SafetyState"),
   "SimulatedGuardClosed" to read("SimulatedGuardClosed"),
   ```

   The simulator in the earlier four-layer lab already exposes these nodes.

3. Build the ROS 2 visualization package:

   ```bash
   cd ~/workspaces/wm_asrs/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --packages-select asrs_gazebo_view --symlink-install
   source install/setup.bash
   ```

4. Restart your Kotlin WCS after applying the patch; keep the WMS, PLC simulator, and ROS C++ planner running as usual.

## Test 1 — View the warehouse (NO WCS required)

```bash
cd ~/workspaces/wm_asrs/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
gz sim -r -v 3 src/asrs_gazebo_view/worlds/asrs_warehouse.sdf
```

You should see racks, pallets, crane, conveyor, forklift, and worker figures. Rotate and zoom in Gazebo with your mouse. The workers are decorative and **outside the guarded aisle**.

In a **second terminal**, move X manually with Gazebo Transport:

```bash
gz topic -t /asrs/crane/x_cmd -m gz.msgs.Double -p 'data: 1.5'
```

Then lift Z:

```bash
gz topic -t /asrs/crane/z_cmd -m gz.msgs.Double -p 'data: 4.8'
```

Then extend the visual fork (optional):

```bash
gz topic -t /asrs/crane/fork_cmd -m gz.msgs.Double -p 'data: 0.75'
```

Fork commands are **manual visualization only** and do not imply pallet deposit verification.

If no movement occurs, make sure the Gazebo simulation is **unpaused** and check `gz topic -l | grep /asrs/crane`. If plugin loading fails, try the standard `gz sim shapes.sdf` and check your installation first.

## Test 2 — Full path from WMS to Gazebo

Keep existing four applications running, in separate terminals:

1. ROS C++ planner: `ros2 run asrs_ros_planner planner_node` (port 8091).
2. Virtual PLC: `./gradlew :asrs-simulator:run` (OPC UA port 12686).
3. WCS: `./gradlew :asrs-wcs:bootRun` (REST port 8080).
4. WMS: `./gradlew :asrs-wms:bootRun` (FreeMarker web at port 8081).

Start the Gazebo visualization **in its own terminal**:

```bash
cd ~/workspaces/wm_asrs/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch asrs_gazebo_view asrs_warehouse.launch.py
```

Open http://localhost:8081 and request **pallet P001 → A-01-04**. Use an unused pallet ID and verify the PLC is ready.

Watch the 3-D crane move X to **1.5 m** and Z to **4.8 m** using status data that WCS reads from the virtual PLC. The actual WMS inventory result still comes from the WCS task state, **not from Gazebo**.

View status:

```bash
curl -s http://127.0.0.1:8080/api/crane/status | python3 -m json.tool
```

Look for `AxisXPositionMm`, `AxisZPositionMm`, `MachineState`, and `CompletedCommandId`.

To inspect ROS 2 topics (in another terminal with ROS setup sourced):

```bash
ros2 topic list | grep /asrs/crane
ros2 topic echo /asrs/crane/x_cmd
```

### Communication flow

```text
WMS (localhost:8081)
   │ REST
   ▼
WCS (localhost:8080) ──HTTP──► ROS 2 C++ planner (localhost:8091)
   │ OPC UA                              (returns rack coordinates)
   ▼
Virtual PLC (localhost:12686)
   │ reports virtual X/Z positions
   ▼
WCS /api/crane/status ──read-only HTTP──► ROS 2 visual sync node
                                           │ ROS 2 std_msgs/Float64
                                           ▼
                                        ros_gz_bridge
                                           │ Gazebo gz.msgs.Double
                                           ▼
                                         Gazebo Sim
                                           │
                                           ▼
                                        Animated crane
```

The ROS visual bridge is an **observer**. It doesn't send motion commands to the virtual PLC. In this edition, the C++ planner and Gazebo visual follower are separate ROS 2 nodes.

## Boundaries / limitations

- Only rack columns `01..06`, levels `01..04` are displayed (e.g. `A-01-04`). The planner and simulator may support more, but the visualization intentionally warns on coordinates outside its 9.0 m X / 5.2 m Z limits.
- Fork extension is an optional visual action for the new pallet deposit follower; no real fork-to-pallet contact is modeled. There is no physics-driven pallet transfer or drive feedback from Gazebo to the PLC.
- No simulated EtherCAT packets, no collision/safety validation, and no actual human detection. Worker figures are **not** animated agents.
- `use_velocity_commands` uses idealized Gazebo joint positioning. This does **not** model realistic servo dynamics.
- WCS feedback polling adds several OPC UA reads per request; this is acceptable for the local demo, not a validated production load profile.
- Do not interpret `SimulatedGuardClosed` as a real protective interlock.
- Gazebo / ROS / Gradle dependencies cannot be exercised here; run full launch tests on your Ubuntu PC.

## Troubleshooting

**`gz: command not found`**: Gazebo Harmonic not installed or not on PATH.

**`Could not find shared library gz-sim-...`**: Check you are running Gazebo Harmonic and the plugins exist. The plugin filenames in this SDF use the correct lowercase spelling.

**No movement**: Confirm Gazebo is unpaused; check topics, bridge and ROS node logs; `ros2 topic list` and `gz topic -l`.

**Visual sync reports WCS unavailable**: The simulator + WCS must be running. Verify `curl http://127.0.0.1:8080/api/crane/status`. If only `Position` is present, the adapter can move to completed rack locations, but won't show intermediate motion. Apply WCS patch for animated X/Z feedback.

**Graphics / EGL / NVIDIA warnings**: First test `gz sim shapes.sdf`; for debugging a GPU rendering issue, `LIBGL_ALWAYS_SOFTWARE=1 gz sim -r -v 3 <world.sdf>` may help, at the cost of performance.

**Worker location**: the static people are placed outside the crane fence as a visual safety-zone illustration.

## References

- https://gazebosim.org/docs/harmonic/sdf_worlds/
- https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1JointPositionController.html
- https://gazebosim.org/docs/harmonic/ros2_integration/
