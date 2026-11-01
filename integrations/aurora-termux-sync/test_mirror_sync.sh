#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd -P)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HOME_T="$TMP/home"
mkdir -p "$HOME_T"

# Test copy: use portable PATH and a synthetic allow-listed remote path.
sed \
  -e 's|^export PATH=.*$|export PATH="$PATH"|' \
  -e "s|https://github.com/auroraseven77/auroraseven77.git|$TMP/origin.git|g" \
  "$ROOT/aurora_mirror_sync.sh" > "$TMP/runner.sh"
chmod +x "$TMP/runner.sh"

git init --bare --initial-branch=main "$TMP/origin.git" >/dev/null
git init --initial-branch=main "$TMP/author" >/dev/null
git -C "$TMP/author" config user.name 'Aurora Sync Fixture'
git -C "$TMP/author" config user.email 'aurora-sync-fixture@example.invalid'
mkdir -p "$TMP/author/scripts"
cat > "$TMP/author/scripts/SHOULD_NOT_RUN.sh" <<'JOB'
#!/usr/bin/env bash
printf 'executed\n' > "$HOME/remote_code_executed"
JOB
chmod +x "$TMP/author/scripts/SHOULD_NOT_RUN.sh"
printf 'fixture version 1\n' > "$TMP/author/README.md"
git -C "$TMP/author" add .
git -C "$TMP/author" commit -m 'fixture initial' >/dev/null
git -C "$TMP/author" remote add origin "$TMP/origin.git"
git -C "$TMP/author" push -u origin main >/dev/null 2>&1

git clone --single-branch --branch main "$TMP/origin.git" "$HOME_T/mirror" >/dev/null 2>&1
git -C "$HOME_T/mirror" config user.name 'Aurora Sync Fixture'
git -C "$HOME_T/mirror" config user.email 'aurora-sync-fixture@example.invalid'
mkdir -p "$HOME_T/.config/aurora-sync-mirror"
printf 'REMOTE_URL=%s\nBRANCH=main\nMIRROR_DIR=%s\n' "$TMP/origin.git" "$HOME_T/mirror" > "$HOME_T/.config/aurora-sync-mirror/config.env"
chmod 600 "$HOME_T/.config/aurora-sync-mirror/config.env"

OUT1=$(HOME="$HOME_T" bash "$TMP/runner.sh")
[[ "$OUT1" == *'NO_CHANGE branch=main'* ]]
[[ ! -e "$HOME_T/remote_code_executed" ]]
printf 'PASS: no-op run leaves clean mirror unchanged and executes no repository code\n'

printf 'fixture version 2\n' > "$TMP/author/README.md"
git -C "$TMP/author" add README.md
git -C "$TMP/author" commit -m 'fixture remote update' >/dev/null
git -C "$TMP/author" push origin main >/dev/null 2>&1
TARGET=$(git -C "$TMP/author" rev-parse HEAD)
OUT2=$(HOME="$HOME_T" bash "$TMP/runner.sh")
[[ "$OUT2" == *"SYNCED branch=main"* && "$OUT2" == *"after=$TARGET"* ]]
[[ "$(git -C "$HOME_T/mirror" rev-parse HEAD)" == "$TARGET" ]]
grep -q 'fixture version 2' "$HOME_T/mirror/README.md"
[[ ! -e "$HOME_T/remote_code_executed" ]]
printf 'PASS: new remote commit is fast-forwarded into mirror without executing downloaded code\n'

printf 'local untracked marker\n' > "$HOME_T/mirror/local-dirty.txt"
printf 'fixture version 3\n' > "$TMP/author/README.md"
git -C "$TMP/author" add README.md
git -C "$TMP/author" commit -m 'fixture later update' >/dev/null
git -C "$TMP/author" push origin main >/dev/null 2>&1
BEFORE_DIRTY=$(git -C "$HOME_T/mirror" rev-parse HEAD)
if HOME="$HOME_T" bash "$TMP/runner.sh" > "$TMP/dirty.log" 2>&1; then
  echo 'FAIL: dirty mirror should be rejected.' >&2
  exit 1
fi
[[ "$(git -C "$HOME_T/mirror" rev-parse HEAD)" == "$BEFORE_DIRTY" ]]
[[ -e "$HOME_T/mirror/local-dirty.txt" ]]
printf 'PASS: dirty mirror is refused and local files remain untouched\n'
printf 'ALL AURORA MIRROR SYNC FIXTURES PASS\n'
