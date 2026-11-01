#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="${AURORA_MATRIX_WORK:-$ROOT/.matrix-work}"
UPSTREAM="$ROOT/baseline/mcp-readonly-safe-v1.0.1.cjs"
EXPECTED_UPSTREAM_SHA256="f2468deedd188b6040801993963a48cc47a4fbaec05b89f56ef9a05a6af403c9"
VERSIONS=("1.30.1" "1.32.2")
PROJECTS=(
  "auroraseven77"
  "auroraseven77-test"
  "auroraseven77-v21-validation"
  "auroraseven77-b12-audit"
  "auroraseven77-b13-repro"
  "auroraseven77-b13-energy"
)

run_required() {
  "$@" || return 1
}

command -v node >/dev/null || { echo 'ERROR: Node.js required' >&2; exit 2; }
command -v npm >/dev/null || { echo 'ERROR: npm required' >&2; exit 2; }
command -v sha256sum >/dev/null || { echo 'ERROR: sha256sum required' >&2; exit 2; }
test -f "$UPSTREAM" || { echo "ERROR: upstream server missing: $UPSTREAM" >&2; exit 2; }
ACTUAL_UPSTREAM_SHA256="$(sha256sum "$UPSTREAM" | awk '{print $1}')"
[ "$ACTUAL_UPSTREAM_SHA256" = "$EXPECTED_UPSTREAM_SHA256" ] || {
  echo "ERROR: upstream SHA-256 mismatch: $ACTUAL_UPSTREAM_SHA256" >&2
  exit 3
}

export npm_config_registry="https://registry.npmjs.org/"
export npm_config_fetch_retries="5"
export npm_config_fetch_retry_mintimeout="15000"
export npm_config_fetch_retry_maxtimeout="120000"
export npm_config_fetch_timeout="300000"

mkdir -p "$WORK/logs" "$WORK/evidence"
FIXTURE_HOME="$WORK/fixture-home"
mkdir -p "$FIXTURE_HOME"
for project in "${PROJECTS[@]}"; do mkdir -p "$FIXTURE_HOME/$project"; done
printf '# Aurora MCP CI fixture\n\nSynthetic, non-production evidence fixture.\n' > "$FIXTURE_HOME/auroraseven77-test/CHANGELOG.md"

{
  printf 'Node: '; node --version
  printf 'npm: '; npm --version
  printf 'Platform: %s/%s\n' "$(uname -s)" "$(uname -m)"
  printf 'Registry: %s\n' "$npm_config_registry"
  printf 'Upstream SHA-256: %s\n' "$ACTUAL_UPSTREAM_SHA256"
} | tee "$WORK/evidence/environment.txt"

run_one() {
  local version="$1"
  local target="$WORK/sdk-$version"
  local evidence="$WORK/evidence/$version"
  rm -rf "$target" "$evidence"
  mkdir -p "$target" "$evidence"
  run_required cp -a "$ROOT/bridge/." "$target/" || return 1

  (
    cd "$target"
    echo "=== SDK $version / REGISTRY METADATA ==="
    run_required npm view "@modelcontextprotocol/sdk@$version" version dist.tarball dist.integrity --json || return 1
    echo "=== SDK $version / ACQUIRE EXACT PACKAGE ==="
    run_required npm install --ignore-scripts --save-exact "@modelcontextprotocol/sdk@$version" || return 1
    echo "=== SDK $version / CLEAN LOCKFILE INSTALL ==="
    rm -rf node_modules
    run_required npm ci --ignore-scripts || return 1
    echo "=== SDK $version / INSTALLED DEPENDENCIES ==="
    run_required npm ls @modelcontextprotocol/sdk zod --depth=1 || return 1
    run_required cp package.json package-lock.json "$evidence/" || return 1
    echo "=== SDK $version / SIGNATURE AUDIT ==="
    run_required npm audit signatures || return 1
    printf 'npm_audit_signatures=PASS\n' > "$evidence/signature-audit-status.txt"
    echo "=== SDK $version / REAL SDK INTEGRATION ==="
    run_required env HOME="$FIXTURE_HOME" \
      AURORA_EXPECTED_SDK_VERSION="$version" \
      AURORA_UPSTREAM_SERVER="$UPSTREAM" \
      node --test integration-sdk.matrix.test.mjs || return 1
    echo "=== SDK $version / EVIDENCE ==="
    run_required node -e "const p=require('./node_modules/@modelcontextprotocol/sdk/package.json'); console.log(JSON.stringify({sdk:p.version,node:process.version,npm:process.env.npm_config_user_agent},null,2))" || return 1
    run_required sha256sum package.json package-lock.json integration-sdk.matrix.test.mjs \
      bridge-security.mjs tool-policy.mjs stdio-http-bridge.mjs \
      "$UPSTREAM" || return 1
    run_required sha256sum package.json package-lock.json integration-sdk.matrix.test.mjs \
      bridge-security.mjs tool-policy.mjs stdio-http-bridge.mjs \
      "$UPSTREAM" > "$evidence/SHA256SUMS.txt" || return 1
    rm -rf node_modules
  )
}

failed=0
for version in "${VERSIONS[@]}"; do
  log="$WORK/logs/sdk-$version.log"
  echo "=== BEGIN SDK $version ==="
  if run_one "$version" >"$log" 2>&1; then
    printf 'PASS %s\n' "$version" | tee -a "$WORK/evidence/summary.txt"
  else
    rc=$?
    printf 'FAIL %s exit=%s\n' "$version" "$rc" | tee -a "$WORK/evidence/summary.txt"
    failed=1
  fi
  cat "$log"
done

if [ "$failed" -ne 0 ]; then
  echo 'FAIL: one or more SDK matrix versions failed; inspect logs and evidence.'
  exit 1
fi
echo 'PASS: SDK matrix completed for 1.30.1 and 1.32.2'
