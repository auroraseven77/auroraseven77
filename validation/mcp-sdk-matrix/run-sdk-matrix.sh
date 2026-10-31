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
  cp -a "$ROOT/bridge/." "$target/"

  (
    cd "$target"
    echo "=== SDK $version / REGISTRY METADATA ==="
    npm view "@modelcontextprotocol/sdk@$version" version dist.tarball dist.integrity --json
    echo "=== SDK $version / ACQUIRE EXACT PACKAGE ==="
    npm install --ignore-scripts --save-exact "@modelcontextprotocol/sdk@$version"
    echo "=== SDK $version / CLEAN LOCKFILE INSTALL ==="
    rm -rf node_modules
    npm ci --ignore-scripts
    echo "=== SDK $version / INSTALLED DEPENDENCIES ==="
    npm ls @modelcontextprotocol/sdk zod --depth=1
    echo "=== SDK $version / SIGNATURE AUDIT ==="
    audit_rc=0
    npm audit signatures || audit_rc=$?
    printf 'npm_audit_signatures_exit=%s\n' "$audit_rc" > "$evidence/signature-audit-status.txt"
    if [ "$audit_rc" -ne 0 ]; then
      echo "ERROR: npm audit signatures failed for SDK $version (exit $audit_rc)" >&2
      exit 20
    fi
    echo "=== SDK $version / REAL SDK INTEGRATION ==="
    HOME="$FIXTURE_HOME" \
      AURORA_EXPECTED_SDK_VERSION="$version" \
      AURORA_UPSTREAM_SERVER="$UPSTREAM" \
      node --test integration-sdk.matrix.test.mjs
    echo "=== SDK $version / EVIDENCE ==="
    node -e "const p=require('./node_modules/@modelcontextprotocol/sdk/package.json'); console.log(JSON.stringify({sdk:p.version,node:process.version,npm:process.env.npm_config_user_agent},null,2))"
    sha256sum package.json package-lock.json integration-sdk.matrix.test.mjs \
      bridge-security.mjs tool-policy.mjs stdio-http-bridge.mjs \
      "$UPSTREAM"
    cp package.json package-lock.json "$evidence/"
    sha256sum package.json package-lock.json integration-sdk.matrix.test.mjs \
      bridge-security.mjs tool-policy.mjs stdio-http-bridge.mjs \
      "$UPSTREAM" > "$evidence/SHA256SUMS.txt"
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
