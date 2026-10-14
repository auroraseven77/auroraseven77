#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPERIMENT="experiments/B1-GEN-01A"
TESTS="$EXPERIMENT/tests"
MANIFEST="$EXPERIMENT/target-manifest.json"
CHECKSUMS="$EXPERIMENT/TARGET-MANIFEST-SHA256SUMS"

if [[ ! -f "$MANIFEST" || ! -f "$CHECKSUMS" || ! -d "$TESTS" ]]; then
  echo "BLOCKED: B1-GEN-01A não está completo nesta revisão." >&2
  echo "Esperado: $MANIFEST, $CHECKSUMS e $TESTS" >&2
  echo "Nenhum benchmark foi executado; publique e valide os artefatos originais." >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "BLOCKED: python3 não encontrado." >&2
  exit 2
fi

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$EXPERIMENT" && sha256sum --check "$(basename "$CHECKSUMS")")
elif command -v shasum >/dev/null 2>&1; then
  (cd "$EXPERIMENT" && shasum -a 256 -c "$(basename "$CHECKSUMS")")
else
  echo "BLOCKED: requer sha256sum ou shasum para validar os artefatos." >&2
  exit 2
fi

python3 -m unittest discover -s "$TESTS" -v
