#!/usr/bin/env bash
set -euo pipefail
BASE="${ASRS_WCS_URL:-http://localhost:8080}"
echo "== Crane status =="
curl -fsS "$BASE/api/crane/status"; echo; echo

echo "== Submit putaway task =="
TASK_ID="DEMO-$(date +%s)"
curl -fsS -X POST "$BASE/api/tasks/putaway" \
  -H 'Content-Type: application/json' \
  -d "{\"externalTaskId\":\"$TASK_ID\",\"palletId\":\"P001\",\"targetLocation\":\"A-01-03\"}"
echo; echo

echo 'Waiting 4 seconds for the simulator movement...'
sleep 4
echo '== All tasks (look for COMPLETED) =='
curl -fsS "$BASE/api/tasks"; echo
