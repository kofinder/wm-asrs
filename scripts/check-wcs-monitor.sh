#!/usr/bin/env bash
# Read-only test of the WCS communication-monitor endpoint.
set -euo pipefail
BASE="${WCS_URL:-http://127.0.0.1:8080}"
command -v curl >/dev/null || { echo 'curl is required' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'python3 is required' >&2; exit 1; }
echo "Testing WCS communication monitor at $BASE ..."
curl -fsS "$BASE/monitor" >/dev/null
curl -fsS "$BASE/api/monitor/snapshot" | python3 -c '
import json,sys
x=json.load(sys.stdin)
assert isinstance(x.get("events"),list), "events missing"
assert isinstance(x.get("tasks"),list), "tasks missing"
assert isinstance(x.get("plcOnline"),bool), "plcOnline missing"
print("WCS monitor OK")
print("Tasks:", len(x["tasks"]))
print("Events:", len(x["events"]))
print("PLC online:", x["plcOnline"])
for e in x["events"][:5]:
 print(" -", e["protocol"], e["from"], "->", e["to"], e["action"], "["+e["outcome"]+"]")
'
