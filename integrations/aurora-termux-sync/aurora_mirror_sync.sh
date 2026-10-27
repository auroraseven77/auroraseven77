#!/data/data/com.termux/files/usr/bin/bash
# Sync-only mirror updater. It NEVER runs code from the mirrored repository.
set -Eeuo pipefail
umask 077
export PATH="${PREFIX:-/data/data/com.termux/files/usr}/bin:/system/bin:/system/xbin"

CONFIG="${HOME}/.config/aurora-sync-mirror/config.env"
STATE_DIR="${HOME}/.local/state/aurora-sync-mirror"
LOCK_DIR="${STATE_DIR}/lock"
LOG_FILE="${STATE_DIR}/runner.log"
EXPECTED_REMOTE='https://github.com/auroraseven77/auroraseven77.git'

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

rotate_log() {
  if [[ -f "$LOG_FILE" ]]; then
    local size
    size=$(wc -c < "$LOG_FILE" 2>/dev/null || printf '0')
    if [[ "$size" -gt 262144 ]]; then
      mv -f "$LOG_FILE" "${LOG_FILE}.1"
    fi
  fi
}
rotate_log
log() {
  local line
  line="$(date -u '+%Y-%m-%dT%H:%M:%SZ') $*"
  printf '%s\n' "$line" >> "$LOG_FILE"
  printf '%s\n' "$line"
}
fail() { log "ERROR: $*"; exit 2; }

[[ -f "$CONFIG" && ! -L "$CONFIG" ]] || fail "Missing or symlinked config: $CONFIG"
[[ "$(stat -c '%a' "$CONFIG" 2>/dev/null || printf '600')" == 600 ]] || fail 'Config permissions must be 600.'

REMOTE_URL=''
BRANCH=''
MIRROR_DIR=''
seen_remote=0 seen_branch=0 seen_mirror=0
while IFS='=' read -r key value || [[ -n "${key:-}" ]]; do
  [[ -n "${key:-}" ]] || continue
  case "$key" in
    REMOTE_URL) (( seen_remote == 0 )) || fail 'Duplicate REMOTE_URL'; REMOTE_URL="$value"; seen_remote=1 ;;
    BRANCH) (( seen_branch == 0 )) || fail 'Duplicate BRANCH'; BRANCH="$value"; seen_branch=1 ;;
    MIRROR_DIR) (( seen_mirror == 0 )) || fail 'Duplicate MIRROR_DIR'; MIRROR_DIR="$value"; seen_mirror=1 ;;
    *) fail "Unknown config key: $key" ;;
  esac
done < "$CONFIG"
[[ "$REMOTE_URL" == "$EXPECTED_REMOTE" ]] || fail 'Remote URL is not on the allow-list.'
[[ "$BRANCH" == main ]] || fail 'Only the configured main branch is allowed.'
[[ "$MIRROR_DIR" == "$HOME/"* && "$MIRROR_DIR" != *'/../'* && "$MIRROR_DIR" != *'/..' ]] || fail 'Mirror path must be a normalized path under HOME.'
[[ "$MIRROR_DIR" != "$HOME/auroraseven77-test" ]] || fail 'Refusing to operate on the active development checkout.'
[[ ! -L "$MIRROR_DIR" ]] || fail 'Mirror path may not be a symlink.'
[[ -d "$MIRROR_DIR/.git" && ! -L "$MIRROR_DIR/.git" ]] || fail 'Mirror must be a standard Git clone, not a worktree or bare repo.'

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log 'SKIP: another sync run holds the lock.'
  exit 0
fi
cleanup() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM

ACTUAL_REMOTE=$(git -C "$MIRROR_DIR" remote get-url origin 2>/dev/null) || fail 'Cannot read origin URL.'
[[ "$ACTUAL_REMOTE" == "$REMOTE_URL" ]] || fail 'Mirror origin URL mismatch.'
CURRENT_BRANCH=$(git -C "$MIRROR_DIR" branch --show-current)
[[ "$CURRENT_BRANCH" == "$BRANCH" ]] || fail "Mirror is on '$CURRENT_BRANCH', expected '$BRANCH'."
[[ -z "$(git -C "$MIRROR_DIR" status --porcelain=v1 --untracked-files=all)" ]] || fail 'Mirror has local changes; refusing to overwrite them.'

BEFORE_SHA=$(git -C "$MIRROR_DIR" rev-parse 'HEAD^{commit}') || fail 'Cannot read local HEAD.'
if ! git -C "$MIRROR_DIR" fetch --no-tags origin "refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}" >> "$LOG_FILE" 2>&1; then
  fail 'Fetch failed; mirror checkout was not changed.'
fi
TARGET_SHA=$(git -C "$MIRROR_DIR" rev-parse "refs/remotes/origin/${BRANCH}^{commit}") || fail 'Cannot read fetched commit.'

if [[ "$BEFORE_SHA" == "$TARGET_SHA" ]]; then
  log "NO_CHANGE branch=$BRANCH sha=$BEFORE_SHA"
  exit 0
fi
if ! git -C "$MIRROR_DIR" merge-base --is-ancestor "$BEFORE_SHA" "$TARGET_SHA"; then
  fail "Remote history is not a fast-forward (local=$BEFORE_SHA remote=$TARGET_SHA). No checkout performed."
fi
if ! git -C "$MIRROR_DIR" merge --ff-only "$TARGET_SHA" >> "$LOG_FILE" 2>&1; then
  fail 'Fast-forward failed; no reset or forced update was attempted.'
fi
AFTER_SHA=$(git -C "$MIRROR_DIR" rev-parse 'HEAD^{commit}') || fail 'Cannot verify resulting HEAD.'
[[ "$AFTER_SHA" == "$TARGET_SHA" ]] || fail 'Post-sync SHA differs from fetched target.'
[[ -z "$(git -C "$MIRROR_DIR" status --porcelain=v1 --untracked-files=all)" ]] || fail 'Mirror is not clean after sync.'
log "SYNCED branch=$BRANCH before=$BEFORE_SHA after=$AFTER_SHA mode=ff-only execution=disabled"
