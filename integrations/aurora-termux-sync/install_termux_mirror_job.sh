#!/data/data/com.termux/files/usr/bin/bash
# One-time setup for an isolated, sync-only mirror; leaves active worktrees untouched.
set -Eeuo pipefail
umask 077
export PATH="${PREFIX:-/data/data/com.termux/files/usr}/bin:/system/bin:/system/xbin"

REMOTE_URL='https://github.com/auroraseven77/auroraseven77.git'
BRANCH='main'
DEFAULT_MIRROR="$HOME/auroraseven77-sync-mirror"
JOB_ID=517703
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
BIN_DIR="$HOME/.local/bin"
CFG_DIR="$HOME/.config/aurora-sync-mirror"
STATE_DIR="$HOME/.local/state/aurora-sync-mirror"

command -v git >/dev/null 2>&1 || { echo 'Git is required; no package will be installed automatically.' >&2; exit 2; }
command -v termux-job-scheduler >/dev/null 2>&1 || { echo 'termux-job-scheduler is missing. Install Termux:API and its matching companion app first.' >&2; exit 2; }

read -r -p "Absolute mirror directory [$DEFAULT_MIRROR]: " MIRROR_DIR
MIRROR_DIR=${MIRROR_DIR:-$DEFAULT_MIRROR}
[[ "$MIRROR_DIR" == "$HOME/"* && "$MIRROR_DIR" != *'/../'* && "$MIRROR_DIR" != *'/..' ]] || { echo 'Choose a normalized absolute path inside HOME.' >&2; exit 2; }
[[ "$MIRROR_DIR" != "$HOME/auroraseven77-test" ]] || { echo 'Refusing the active development checkout.' >&2; exit 2; }
[[ ! -L "$MIRROR_DIR" ]] || { echo 'Mirror path may not be a symlink.' >&2; exit 2; }

if [[ -e "$MIRROR_DIR" ]]; then
  [[ -d "$MIRROR_DIR/.git" && ! -L "$MIRROR_DIR/.git" ]] || { echo 'Path exists but is not a standard Git clone; nothing was changed.' >&2; exit 2; }
  ACTUAL_REMOTE=$(git -C "$MIRROR_DIR" remote get-url origin 2>/dev/null || true)
  [[ "$ACTUAL_REMOTE" == "$REMOTE_URL" ]] || { echo 'Existing mirror has a different origin; nothing was changed.' >&2; exit 2; }
  [[ "$(git -C "$MIRROR_DIR" branch --show-current)" == "$BRANCH" ]] || { echo 'Existing mirror is not on main; nothing was changed.' >&2; exit 2; }
  [[ -z "$(git -C "$MIRROR_DIR" status --porcelain=v1 --untracked-files=all)" ]] || { echo 'Existing mirror has local changes; nothing was changed.' >&2; exit 2; }
else
  git clone --single-branch --branch "$BRANCH" "$REMOTE_URL" "$MIRROR_DIR"
fi

mkdir -p "$BIN_DIR" "$CFG_DIR" "$STATE_DIR"
chmod 700 "$CFG_DIR" "$STATE_DIR"
install -m 700 "$SCRIPT_DIR/aurora_mirror_sync.sh" "$BIN_DIR/aurora-mirror-sync"
CONFIG_TMP="$CFG_DIR/config.env.tmp.$$"
printf 'REMOTE_URL=%s\nBRANCH=%s\nMIRROR_DIR=%s\n' "$REMOTE_URL" "$BRANCH" "$MIRROR_DIR" > "$CONFIG_TMP"
chmod 600 "$CONFIG_TMP"
mv -f "$CONFIG_TMP" "$CFG_DIR/config.env"

termux-job-scheduler --cancel --job-id "$JOB_ID" >/dev/null 2>&1 || true
termux-job-scheduler \
  --script "$BIN_DIR/aurora-mirror-sync" \
  --job-id "$JOB_ID" \
  --period-ms 21600000 \
  --network any \
  --battery-not-low true \
  --storage-not-low true \
  --charging false \
  --persisted true

# Initial one-shot sync only touches the isolated mirror; it does not execute repository code.
"$BIN_DIR/aurora-mirror-sync"
echo
echo 'Installed: sync-only Termux job (approximately every 6 hours).'
echo 'Mirror:' "$MIRROR_DIR"
echo 'Runner/log:' "$BIN_DIR/aurora-mirror-sync" "$STATE_DIR/runner.log"
echo 'This job fetches and fast-forwards only the isolated mirror; it never runs downloaded code or pushes local changes.'
