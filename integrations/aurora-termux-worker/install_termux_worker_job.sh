#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

JOB_ID="517704"
PERIOD_MS="900000"
MIRROR="$HOME/auroraseven77-sync-mirror"
INSTALL_DIR="$HOME/.local/lib/aurora-termux-worker"
STATE_DIR="$HOME/.local/state/aurora-termux-worker"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/aurora-sync-mirror"
TOKEN_FILE="$CONFIG_DIR/github_token"
WORKER_NAME="aurora_termux_worker.py"
LAUNCHER="$BIN_DIR/aurora-termux-worker"

fail() {
  printf 'AURORA_WORKER_INSTALL_ERROR: %s\n' "$*" >&2
  exit 1
}

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
worker_src="$script_dir/$WORKER_NAME"

[[ -f "$worker_src" ]] || fail "Worker source not found: $worker_src"
[[ -d "$MIRROR/.git" ]] || fail "Isolated mirror not found: $MIRROR"
command -v git >/dev/null 2>&1 || fail "git is required"
command -v termux-job-scheduler >/dev/null 2>&1 || fail "Termux:API termux-job-scheduler is required"

if printenv AURORA_WORKER_PYTHON >/dev/null 2>&1; then
  PYTHON_BIN="$(printenv AURORA_WORKER_PYTHON)"
else
  PYTHON_BIN="$(command -v python || true)"
fi
[[ -n "$PYTHON_BIN" && -x "$PYTHON_BIN" ]] || fail "Python executable not found"
[[ "$PYTHON_BIN" = /* ]] || PYTHON_BIN="$(command -v "$PYTHON_BIN")"
[[ -x "$PYTHON_BIN" ]] || fail "Python executable must be runnable"

top="$(git -C "$MIRROR" rev-parse --show-toplevel 2>/dev/null)" || fail "Mirror is not a Git repository"
[[ "$top" = "$MIRROR" ]] || fail "Configured mirror path is not the repository root"
remote="$(git -C "$MIRROR" remote get-url origin 2>/dev/null)" || fail "Mirror origin is missing"
case "$remote" in
  https://github.com/auroraseven77/auroraseven77.git|https://github.com/auroraseven77/auroraseven77) ;;
  *) fail "Mirror origin is not the allowlisted Aurora repository" ;;
esac
[[ -z "$(git -C "$MIRROR" status --porcelain)" ]] || fail "Mirror has local changes; refusing to overwrite or install from a dirty mirror"

"$PYTHON_BIN" -c 'import numpy, pytest' >/dev/null 2>&1 || fail "Python environment must already contain numpy and pytest; this script installs no packages"

mkdir -p "$INSTALL_DIR" "$STATE_DIR" "$BIN_DIR" "$CONFIG_DIR"
chmod 700 "$INSTALL_DIR" "$STATE_DIR" "$CONFIG_DIR"

# Save a token only if none exists. Terminal input is not echoed.
if [[ ! -e "$TOKEN_FILE" ]]; then
  printf 'Enter a fine-grained GitHub token restricted to this repository (Contents: Read and write).\n'
  printf 'It will be saved locally with mode 0600 and will not be displayed.\n'
  IFS= read -r -s -p 'GitHub token: ' TOKEN_INPUT || fail "Could not read token input"
  printf '\n'
  [[ -n "$TOKEN_INPUT" ]] || fail "Empty token; no job was scheduled"
  case "$TOKEN_INPUT" in
    github_pat_*|ghp_*) ;;
    *) unset TOKEN_INPUT; fail "Expected a GitHub token beginning with github_pat_ or ghp_" ;;
  esac
  case "$TOKEN_INPUT" in
    *[!A-Za-z0-9_]* ) unset TOKEN_INPUT; fail "Token contains unsupported characters; no job was scheduled" ;;
  esac
  token_tmp="$TOKEN_FILE.tmp.$$"
  (umask 077; printf '%s\n' "$TOKEN_INPUT" > "$token_tmp")
  unset TOKEN_INPUT
  chmod 600 "$token_tmp"
  mv -f "$token_tmp" "$TOKEN_FILE"
fi

[[ -f "$TOKEN_FILE" ]] || fail "Token file is not a regular file"
token_mode="$(stat -c '%a' "$TOKEN_FILE" 2>/dev/null)" || fail "Unable to inspect token file mode"
(( (8#$token_mode & 077) == 0 )) || fail "Token file must be mode 0600 or stricter"
"$PYTHON_BIN" -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text().strip(); sys.exit(0 if s and "\n" not in s and "\r" not in s else 1)' "$TOKEN_FILE" || fail "Token file must contain exactly one non-empty line"

install -m 600 "$worker_src" "$INSTALL_DIR/$WORKER_NAME"
cat > "$LAUNCHER" <<EOF
#!/data/data/com.termux/files/usr/bin/sh
exec "$PYTHON_BIN" "$INSTALL_DIR/$WORKER_NAME" --repo "$MIRROR" --state-dir "$STATE_DIR" --token-file "$TOKEN_FILE" "\$@"
EOF
chmod 700 "$LAUNCHER"

timeout 15s termux-job-scheduler \
  --script "$LAUNCHER" \
  --job-id "$JOB_ID" \
  --period-ms "$PERIOD_MS" \
  --network any \
  --battery-not-low true \
  --storage-not-low true \
  --charging false \
  --persisted true || fail "Termux did not accept the periodic worker job"

printf '\n=== AURORA WORKER SCHEDULED ===\n'
printf 'Worker: %s\nJob ID: %s\nPeriod: 15 minutes (Android may delay periodic jobs)\n' "$LAUNCHER" "$JOB_ID"
printf 'No task was executed by this installer.\n'
printf '\n=== PENDING JOB CONFIRMATION ===\n'
timeout 15s termux-job-scheduler --pending
