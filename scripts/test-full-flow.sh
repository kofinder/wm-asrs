#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
import json, time, uuid, urllib.request, urllib.parse

def get(url):
    with urllib.request.urlopen(url, timeout=6) as r:
        return json.load(r)

planner = get('http://127.0.0.1:8091/health')
print('ROS planner:', planner)
plc = get('http://localhost:8080/api/crane/status')
print('PLC through WCS:', plc['MachineState'])
assert plc['Ready'] and not plc['Busy'] and plc['FaultCode'] == 0, 'Virtual crane is not ready'
pallet = 'LAB' + uuid.uuid4().hex[:6].upper()
body = urllib.parse.urlencode({'palletId': pallet, 'targetLocation': 'A-01-04'}).encode()
with urllib.request.urlopen('http://localhost:8081/putaway', data=body, timeout=8) as r:
    _ = r.read()
print('Submitted from WMS:', pallet)
for attempt in range(18):
    task = next((t for t in get('http://localhost:8081/api/wms/tasks') if t['palletId']==pallet), None)
    if task:
        print('WMS state:', task['status'], 'confirmedLocation:', task['storedLocation'])
        if task['status'] == 'COMPLETED':
            assert task['storedLocation'] == 'A-01-04'
            print('PASS: WMS updated location only after PLC completion')
            break
        if task['status'] == 'UNCERTAIN':
            raise SystemExit('FAILED/UNCERTAIN: check WCS and virtual PLC logs')
    time.sleep(1)
else:
    raise SystemExit('Timed out waiting for simulated completion')
PY
