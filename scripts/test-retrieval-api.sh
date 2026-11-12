#!/usr/bin/env bash
# Starts real simulation tasks through WCS. Only run in the educational lab.
set -euo pipefail
PALLET="${1:-P-API-020}"
RACK="${2:-A-05-03}"
WCS="${ASRS_WCS_URL:-http://127.0.0.1:8080}"
post() {
  local endpoint="$1" payload="$2"
  curl -sS --fail-with-body -H 'Content-Type: application/json' -X POST "$WCS/api/tasks/$endpoint" -d "$payload"
}
get_id() { python3 -c 'import json,sys; print(json.load(sys.stdin)["taskId"])'; }
wait_complete() {
  local task_id="$1" operation="$2" json status
  for _ in $(seq 1 50); do
    json="$(curl -sS --fail-with-body "$WCS/api/tasks/$task_id")"
    status="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
    case "$status" in
      COMPLETED) echo "$operation task $task_id COMPLETED"; return 0;;
      UNCERTAIN) echo "$operation UNCERTAIN: $json" >&2; return 1;;
    esac
    sleep 0.5
  done
  echo "$operation did not finish within this test window; reconcile, do not retry automatically" >&2
  return 1
}
# The generated IDs below intentionally differ from WMS tasks. This script
# does not update the WMS stock ledger; use the dashboard for that flow.
PUT="$(post putaway "{\"palletId\":\"$PALLET\",\"targetLocation\":\"$RACK\"}")"
PUT_ID="$(printf '%s' "$PUT" | get_id)"
wait_complete "$PUT_ID" PUTAWAY
RET="$(post retrieval "{\"palletId\":\"$PALLET\",\"sourceLocation\":\"$RACK\"}")"
RET_ID="$(printf '%s' "$RET" | get_id)"
wait_complete "$RET_ID" RETRIEVAL
curl -sS --fail-with-body "$WCS/api/crane/status" | python3 -m json.tool
echo "PASS: retrieval feedback returned to outbound. Check ReleasedCommandId matches RETRIEVAL task commandId."
