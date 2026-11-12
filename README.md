# ASRS Web Twin — Step-by-Step Setup and Run Guide

**Project:** Web-Based Interactive 3D Warehouse Visualization and Simulation Platform  
**Frontend:** React 19 + TypeScript + Vite 6 + Three.js / React Three Fiber  
**Runs at:** `http://localhost:3000`  
**Existing backends:** WCS at `http://localhost:8080`, WMS at `http://localhost:8081`  
**Tested project layout:** `asrs-web-twin-starter.zip` containing the `asrs-web-twin/` folder

This web app is a **read-only warehouse digital twin**. It shows rack locations, pallets, a crane, and sample forklift/AGV animations. It does **not** control the PLC. Use **Demo** mode without backends, or **Live APIs** mode to read your existing WMS/WCS data.

---

## 0. Before you start

You need:

- Ubuntu (your existing ROS 2 Jazzy ASRS machine is fine)
- Node.js 20+ (Node.js 22 recommended) and npm
- A current browser with WebGL support (Chrome, Edge, or Firefox)
- `asrs-web-twin-starter.zip` downloaded to `~/Downloads`
- For **Live APIs** only: your working Kotlin WMS, WCS, and virtual PLC; the ROS 2 planner if enabled

Check versions in a terminal:

```bash
node --version
npm --version
```

If `node` is missing or the version is below 20, install a supported Node.js version (Node.js 22 is recommended) using the official Node.js installation instructions, then open a new terminal and repeat these checks. **Do not use `sudo npm install` inside the project.**

> **Important directory rule:** In every command below, `~/workspaces/wm_asrs` is your existing main project. If you installed it somewhere else, substitute that path consistently.

---

## PART A — Run the 3D website alone (start here)

### Step 1 — Extract the source ZIP

**Terminal 1**:

```bash
mkdir -p ~/workspaces/wm_asrs
cd ~/workspaces/wm_asrs
unzip -o ~/Downloads/asrs-web-twin-starter.zip -d .
```

Check that the project files exist:

```bash
cd ~/workspaces/wm_asrs/asrs-web-twin
ls
```

You should see files such as:

```text
package.json
vite.config.ts
index.html
src/
scripts/
README.md
```

### Step 2 — Install JavaScript dependencies

```bash
cd ~/workspaces/wm_asrs/asrs-web-twin
npm install
```

This downloads React, Vite, Three.js, and their dependencies. Internet access is needed for the first installation unless your npm cache is already populated.

### Step 3 — Optional: check the production build

```bash
npm run build
```

If this completes successfully, the compiled site is in `dist/`. You **do not** need this step to run the development server, but it is useful to catch TypeScript errors.

### Step 4 — Start the website

```bash
npm run dev
```

The Vite console should show a local address similar to:

```text
Local: http://localhost:3000/
```

**Keep this terminal open.** Open a browser on the same Ubuntu computer:

**http://localhost:3000**

The website initially opens in **Demo** mode. It does not require ROS 2, WMS, WCS, the virtual PLC, or Gazebo to be running.

### Step 5 — Explore the 3D warehouse

In the 3D view:

| Action | Control |
|---|---|
| Rotate the warehouse | Left-mouse drag |
| Zoom in and out | Mouse wheel / trackpad scroll |
| Pan sideways | Right-mouse drag |
| Inspect a rack location | Click a rack slot |
| View example forklift/AGV movement | Keep **Demo** mode selected |

Verify that you see the racks, simulated crane, inventory/task panels, and demo mobile equipment.

> **Demo versus reality:** In Demo mode, crane, forklift, AGV, pallets, and task records are sample data. This is a preview, not live telemetry.

---

## PART B — Connect to your real project services (Live APIs)

For this section, keep the web app running in Terminal 1 and open additional terminals. The sequence below matches the existing ASRS source project. **You don't need Gazebo for the browser digital twin to work.**

### Step 6 — Start ROS 2 C++ planner (Terminal 2)

```bash
cd ~/workspaces/wm_asrs/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run asrs_ros_planner planner_node
```

Keep it running. In another terminal, you can test:

```bash
curl -i http://127.0.0.1:8091/health
```

If your ROS package has not yet been built, from `ros2_ws` run:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select asrs_ros_planner
source install/setup.bash
```

> The WCS version used for this project normally has ROS planning enabled. If your WCS is configured with `ASRS_PLANNER_ENABLED=false`, the planner is optional for the current test.

### Step 7 — Start the virtual PLC (Terminal 3)

```bash
cd ~/workspaces/wm_asrs
chmod +x gradlew
./gradlew :asrs-simulator:run
```

Keep it running. The OPC UA endpoint is typically `opc.tcp://localhost:12686/milo`.

### Step 8 — Start WCS (Terminal 4)

```bash
cd ~/workspaces/wm_asrs
./gradlew :asrs-wcs:bootRun
```

Keep it running. Check WCS from an additional terminal:

```bash
curl -s http://localhost:8080/api/crane/status | python3 -m json.tool
curl -s http://localhost:8080/api/tasks | python3 -m json.tool
```

The crane response should include keys such as `AxisXPositionMm`, `AxisZPositionMm`, `MachineState`, and `CompletedCommandId`.

### Step 9 — Start WMS (Terminal 5)

```bash
cd ~/workspaces/wm_asrs
./gradlew :asrs-wms:bootRun
```

Keep it running. In a browser, WMS is at:

**http://localhost:8081**

Check the inventory API:

```bash
curl -s http://localhost:8081/api/wms/inventory | python3 -m json.tool
```

An empty `[]` is normal if you haven't stored any pallets in the current WMS session. This prototype uses **in-memory inventory**, which resets on WMS restart.

### Step 10 — Check the backend connections (Terminal 6)

```bash
cd ~/workspaces/wm_asrs/asrs-web-twin
bash scripts/check-backends.sh
```

The script checks:

- WCS crane status: `http://127.0.0.1:8080/api/crane/status`
- WCS task list: `http://127.0.0.1:8080/api/tasks`
- WMS confirmed inventory: `http://127.0.0.1:8081/api/wms/inventory`

All three should report `OK` / HTTP 200 for a complete Live API setup.

### Step 11 — Switch the browser to Live APIs

1. Go to **http://localhost:3000**.
2. In the left sidebar under **DATA MODE**, click **Live APIs**.
3. Check for a connected indicator and live crane feedback in the equipment inspector.
4. The site polls WMS and WCS approximately every **1.5 seconds**.

The frontend uses Vite's built-in local proxy, so you do **not** need to change your Spring Boot CORS settings for this development setup.

| Browser proxy endpoint | Backend endpoint | Data |
|---|---|---|
| `/bridge/wcs/api/crane/status` | `http://127.0.0.1:8080/api/crane/status` | Crane position/status |
| `/bridge/wcs/api/tasks` | `http://127.0.0.1:8080/api/tasks` | Recent tasks |
| `/bridge/wms/api/wms/inventory` | `http://127.0.0.1:8081/api/wms/inventory` | Confirmed pallets |

These mappings are configured in `asrs-web-twin/vite.config.ts`.

---

## PART C — Test a warehouse putaway and retrieval

### Step 12 — Put away a pallet

Open two browser tabs side by side:

- WMS: **http://localhost:8081** (create warehouse tasks)
- Web Twin: **http://localhost:3000** (**Live APIs** selected)

Optional third tab:

- WCS Communication Monitor: **http://localhost:8080/monitor**

In WMS, enter:

| Field | Test value |
|---|---|
| Pallet ID | `WEB-001` |
| Storage destination | `A-03-02` |

Submit the putaway. Expected results:

1. WMS submits the task to WCS.
2. WCS requests a rack plan from ROS 2 and sends an OPC UA command to the virtual PLC.
3. The virtual PLC updates the crane X/Z feedback; the browser 3D crane follows that reported position.
4. After verified completion, WMS lists `WEB-001` in confirmed inventory.
5. The pallet appears at rack `A-03-02` in the web 3D scene.

**Note:** The browser shows live inventory and crane position. It does not yet animate fork grasping or physical pallet transfer. Those more detailed sequences belong to the Gazebo visualization.

### Step 13 — Retrieve the same pallet (if enabled in your WMS version)

1. In WMS **Confirmed inventory**, find `WEB-001`.
2. Click **Retrieve**.
3. Wait for WCS/PLC to verify retrieval completion.
4. The pallet disappears from the web 3D rack after WMS removes it from confirmed inventory.

If your WMS does not have the retrieval button, skip this step until the retrieval-capable WMS version is installed. The Web Twin itself is read-only.

---

## PART D — Optional: run Gazebo alongside the web viewer

Gazebo is **not required** to run the web viewer, but you can run both to compare the two visualizations.

In a new terminal:

```bash
cd ~/workspaces/wm_asrs/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export GZ_CONFIG_PATH="/usr/share/gz${GZ_CONFIG_PATH:+:$GZ_CONFIG_PATH}"
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  ros2 launch asrs_gazebo_view asrs_warehouse.launch.py
```

This uses your previously verified NVIDIA offloading setup. **Gazebo and the browser viewer are separate consumers of ASRS state**, so an AGV or forklift animated in Web Twin Demo mode is *not* an actual Gazebo/PLC pose reading.

---

## Troubleshooting

### Browser shows a blank page, `npm` errors, or missing dependencies

```bash
cd ~/workspaces/wm_asrs/asrs-web-twin
node --version
npm --version
npm install
npm run build
```

Use Node.js 20+; Node.js 22 is recommended. If a dependency install fails, share the **first** npm error, not just the last line.

### `npm run dev` reports port 3000 already in use

```bash
ss -ltnp | grep ':3000'
```

Stop the earlier Vite process (often in another terminal) with `Ctrl+C`, then start `npm run dev` again.

### Live APIs disconnected

Check the three backend URLs directly:

```bash
curl -i http://127.0.0.1:8080/api/crane/status
curl -i http://127.0.0.1:8080/api/tasks
curl -i http://127.0.0.1:8081/api/wms/inventory
```

If the browser works in Demo mode but not Live mode, this is usually a backend connection or response-shape issue. Make sure the WCS and WMS are running and expose those exact endpoints.

### Web Twin shows no stored pallets

Make sure you are in **Live APIs** mode, the WMS inventory endpoint returns pallet records, and you submitted a **new** putaway that actually completed. The web viewer intentionally displays only **confirmed WMS inventory**; it does not invent stock from rack models.

### The forklift/AGV does not move in Live mode

**Expected in v0.1.** The current backend does not publish AGV or forklift telemetry. They are animated only in Demo mode and parked in Live mode. Real vehicle motion requires a new WCS equipment telemetry interface.

### 3D view is slow

Start by closing Gazebo (if running) and testing only the browser app. Your laptop has an AMD integrated GPU and an NVIDIA RTX 3050; the browser renderer is independent of the terminal running Vite. Reduce browser tab load and check hardware acceleration in your browser settings before changing the 3D code.

### `./gradlew: Permission denied`

```bash
cd ~/workspaces/wm_asrs
chmod +x gradlew
```

Or run `bash ./gradlew :asrs-wcs:bootRun` (or whichever Gradle task you need).

### Need to stop or restart

Press `Ctrl+C` in the application terminal. Restart the backend first, then refresh the browser. WMS and WCS data may reset on restart because the prototype uses in-memory task/stock ledgers.

---

## Quick command reference

| Service | Start command (from appropriate directory) | URL / Port |
|---|---|---|
| Web Twin | `cd ~/workspaces/wm_asrs/asrs-web-twin && npm run dev` | http://localhost:3000 |
| ROS Planner | `ros2 run asrs_ros_planner planner_node` (after sourcing ROS environments) | 8091 |
| Virtual PLC | `./gradlew :asrs-simulator:run` | OPC UA 12686 |
| WCS | `./gradlew :asrs-wcs:bootRun` | http://localhost:8080 |
| WMS | `./gradlew :asrs-wms:bootRun` | http://localhost:8081 |
| WCS Monitor | Included in the running WCS process | http://localhost:8080/monitor |
| Gazebo | `ros2 launch asrs_gazebo_view asrs_warehouse.launch.py` | Optional GUI |

## Next development milestones

1. Expose **live AGV/forklift telemetry** from WCS, including equipment ID, X/Y, heading, operating state, battery, timestamps and sequence numbers.
2. Replace HTTP polling with WebSocket/SSE event streaming.
3. Align web 3D layout and rack coordinates precisely with the actual facility design.
4. Add task history replay, fault alerts, occupancy checks and operator permissions.
5. Separate read-only live digital twin from a **clearly isolated simulation sandbox**. Real PLC and safety functions remain outside browser control.

**Success criteria for your first run:** `http://localhost:3000` works in Demo mode; then in Live APIs mode it displays WCS X/Z feedback and confirmed WMS inventory from your running ASRS services.