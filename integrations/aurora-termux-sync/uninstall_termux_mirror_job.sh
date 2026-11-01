#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
export PATH="${PREFIX:-/data/data/com.termux/files/usr}/bin:/system/bin:/system/xbin"
JOB_ID=517703
if command -v termux-job-scheduler >/dev/null 2>&1; then
  termux-job-scheduler --cancel --job-id "$JOB_ID" || true
fi
rm -f "$HOME/.local/bin/aurora-mirror-sync"
rm -f "$HOME/.config/aurora-sync-mirror/config.env"
rmdir "$HOME/.config/aurora-sync-mirror" 2>/dev/null || true
echo 'Job cancelled and installed runner/config removed.'
echo 'The mirror checkout and state/logs were preserved.'
