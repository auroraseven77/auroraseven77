"""Constrói o ledger persistente a partir dos findings.

Roda uma vez (ou sempre que um finding novo for adicionado) para:
1. Criar aurora_phase1/logs/tuu_ledger.jsonl
2. Registrar o hash SHA-256 de cada finding
3. Emitir o master_attestation_hash final

Uso:
    cd auroraseven77-b12-audit
    python3 aurora_phase1/evidence/build_ledger.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from aurora_phase1.core.ledger import Ledger


FINDINGS_DIR = REPO_ROOT / "aurora_phase1" / "evidence"
LOG_DIR = REPO_ROOT / "aurora_phase1" / "logs"
LEDGER_PATH = LOG_DIR / "tuu_ledger.jsonl"


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Se o ledger já existe, apaga para reconstruir do zero
    if LEDGER_PATH.exists():
        LEDGER_PATH.unlink()

    ledger = Ledger(LEDGER_PATH)

    # Bloco genesis
    ledger.add_block("GENESIS_INITIALIZED", {
        "project": "aurora_phase1",
        "purpose": "Persistent evidence ledger for the reconstructed world",
    }, tick=0)

    # Encontra os findings (ordena para determinismo)
    findings = sorted(FINDINGS_DIR.glob("*_finding.md"))
    if not findings:
        print("Nenhum finding encontrado.")
        return 1

    print(f"Encontrados {len(findings)} findings:")
    for f in findings:
        block = ledger.record_finding(
            attack_id=f.stem,
            evidence_path=str(f),
            tick=0,
        )
        print(f"  {f.name}: {block.payload['evidence_hash'][:16]}...")

    # Auditoria final
    audit = ledger.audit_chain()
    print()
    print(f"Total de blocos: {audit.total_blocks}")
    print(f"chain_integrity: {audit.chain_integrity}")
    print(f"top_hash: {ledger.top_hash()}")
    print(f"Ledger escrito em: {LEDGER_PATH}")

    return 0 if audit.chain_integrity else 1


if __name__ == "__main__":
    sys.exit(main())
