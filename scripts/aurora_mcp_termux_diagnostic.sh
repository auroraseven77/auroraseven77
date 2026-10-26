#!/data/data/com.termux/files/usr/bin/bash
# Read-only Termux triage for the known Aurora MCP local HTTP bridge.
# Does not start/stop services, install packages, read env files, or write files.
set -u

printf '\n=== AURORA MCP — TERMUX DIAGNOSTIC (READ-ONLY) ===\n'
printf 'UTC: '
date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || printf 'unavailable\n'

printf '\n=== 1. TCP LISTENERS ===\n'
if command -v ss >/dev/null 2>&1; then
  ss_output="$(ss -ltn 2>&1)"
  ss_rc=$?
  printf '%s\n' "$ss_output"
  ss_visibility_error="$(printf '%s\n' "$ss_output" | awk 'tolower($0) ~ /permission denied|cannot open netlink socket|operation not permitted|not permitted/ { found=1 } END { print found+0 }')"
  if [ "$ss_rc" -ne 0 ] || [ "$ss_visibility_error" -eq 1 ]; then
    printf 'listener_state=INCONCLUSIVE (ss exit=%s; OS/socket visibility error detected)\n' "$ss_rc"
  else
    ss_rows="$(printf '%s\n' "$ss_output" | awk 'NR > 1 && NF && tolower($0) !~ /warning|permission denied|cannot open netlink/ { count++ } END { print count+0 }')"
    if [ "$ss_rows" -gt 0 ]; then
      printf 'listener_state=ROWS_REPORTED (rows=%s; inspect exact local addresses above)\n' "$ss_rows"
    else
      printf 'listener_state=NO_ROWS_REPORTED (not proof of global process absence; Android may restrict socket visibility)\n'
    fi
  fi
else
  printf 'listener_state=NOT_TESTED (ss unavailable)\n'
fi

printf '\n=== 2. RELEVANT PROCESS NAMES (BEST EFFORT) ===\n'
if command -v ps >/dev/null 2>&1; then
  # Android/Termux ps often lacks GNU-style "-o PID,COMM"; use portable default output.
  ps_output="$(ps -A 2>&1)"
  ps_rc=$?
  if [ "$ps_rc" -ne 0 ]; then
    printf '%s\n' "$ps_output"
    printf 'process_state=INCONCLUSIVE (ps -A exit=%s)\n' "$ps_rc"
  else
    printf '%s\n' "$ps_output" | awk '
      NR == 1 { print substr($0, 1, 180); next }
      NF {
        rows++
        if (tolower($0) ~ /node|python|mcp|aurora/) {
          print substr($0, 1, 180)
          matches++
        }
      }
      END {
        if (!rows) {
          print "process_state=INCONCLUSIVE (ps returned header only or no visible process rows)"
        } else if (!matches) {
          print "process_state=NO_RELEVANT_NAME_MATCH (not proof of absence; process visibility may be restricted)"
        } else {
          print "process_state=RELEVANT_ROWS_REPORTED (matches=" matches "; inspect command names above)"
        }
      }'
  fi
else
  printf 'process_state=NOT_TESTED (ps unavailable)\n'
fi

printf '\n=== 3. KNOWN DIRECTORIES (NAMES ONLY) ===\n'
for d in "$HOME/mcp-aurora" "$HOME/mcp-aurora-server"; do
  if [ -d "$d" ]; then
    printf '\n--- %s ---\n' "$d"
    if command -v git >/dev/null 2>&1 && git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      git -C "$d" status --short --branch 2>&1
    else
      printf 'NOT_GIT_WORKTREE (or git unavailable)\n'
    fi
    if command -v find >/dev/null 2>&1; then
      find "$d" -maxdepth 1 -type f \
        ! -name '.env' ! -name '.env.*' ! -name '*.env' \
        ! -iname '*token*' ! -iname '*secret*' ! -iname '*credential*' \
        -print 2>/dev/null | head -50
    else
      printf 'find unavailable; file names not listed\n'
    fi
  else
    printf '\nDirectory absent: %s\n' "$d"
  fi
done

printf '\n=== 4. HTTP HEALTH PATHS (LOOPBACK ONLY; NO SED REQUIRED) ===\n'
if ! command -v python3 >/dev/null 2>&1; then
  printf 'http_state=NOT_TESTED (python3 unavailable)\n'
  printf '\n=== END: NO SERVICE STARTED ===\n'
  exit 2
fi

python3 - <<'PY'
import http.client
import json
import socket
from datetime import datetime, timezone

host, port = "127.0.0.1", 8787
results = []
for path in ("/healthz", "/health"):
    conn = http.client.HTTPConnection(host, port, timeout=2.0)
    try:
        conn.request("GET", path, headers={"Accept": "application/json, text/plain", "Connection": "close"})
        response = conn.getresponse()
        response.read(1024)  # bounded discard; never print the body or headers
        results.append({"path": path, "http_status": response.status, "state": "HTTP_RESPONSE"})
    except (OSError, http.client.HTTPException, socket.timeout) as exc:
        results.append({"path": path, "http_status": None, "state": "NOT_CONNECTED", "error_type": type(exc).__name__})
    finally:
        conn.close()

statuses = [item["http_status"] for item in results if item["http_status"] is not None]
state = "HEALTH_REACHABLE" if any(200 <= status < 300 for status in statuses) else (
    "HTTP_REACHABLE_NO_HEALTH_SUCCESS" if statuses else "NOT_CONNECTED"
)
print(json.dumps({
    "schema_version": "1.0",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "target": {"host": host, "port": port},
    "state": state,
    "probes": results,
    "stdio_mcp": "NOT_TESTED_BY_HTTP_PROBE",
    "side_effects": "loopback HTTP GET only; no files, process launch, credentials, or response-body disclosure",
}, indent=2, sort_keys=True))
PY
probe_rc=$?

printf '\n=== END: NO SERVICE STARTED; NO PACKAGE INSTALLED ===\n'
exit "$probe_rc"
