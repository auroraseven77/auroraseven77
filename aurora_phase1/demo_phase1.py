"""demo_phase1.py — verificação das 5 provas da Fase 1.

Provas:
  1. Habitante produz propostas estruturadas
  2. Centro decide com base em contrato
  3. Resultado é registrado no ledger
  4. Habitante morre; memória é efêmera
  5. Reconstrução tabula rasa: 0.00% divergência

Rodar de dentro de auroraseven77-b12-audit/:
    python3 aurora_phase1/demo_phase1.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Permite rodar como `python3 aurora_phase1/demo_phase1.py`
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from aurora_phase1.core.agent import EphemeralAgent
from aurora_phase1.core.ledger import Ledger
from aurora_phase1.core.reconstruct import WorldReconstructor
from aurora_phase1.core.tuu import (
    TUU,
    STATUS_APPROVED,
    STATUS_REJECTED_POLICY_VIOLATION,
)


DEMO_SEED = 42
DEMO_CONTEXT = {
    "fluxo_entropico": 0.142,
    "pressao_interna": 101.3,
    "temperatura_simulada": 298.15,
}


def _load_contracts(repo_root: Path) -> tuple[dict, dict]:
    contracts_dir = repo_root / "aurora_phase1" / "contracts"
    argos = json.loads(
        (contracts_dir / "argos_role.json").read_text(encoding="utf-8")
    )
    tuu_policy = json.loads(
        (contracts_dir / "tuu_policy.json").read_text(encoding="utf-8")
    )
    return argos, tuu_policy


def _line(char: str = "=", n: int = 70) -> str:
    return char * n


def main() -> int:
    results = {
        "prova_1": False,
        "prova_2": False,
        "prova_3": False,
        "prova_4": False,
        "prova_5": False,
        "artifacts": {},
    }

    print(_line())
    print(" FASE 1 — INICIALIZAÇÃO DO MUNDO E MARCO ZERO")
    print(_line())

    # Setup
    tmpdir = Path(tempfile.mkdtemp())
    ledger_path = tmpdir / "tuu_ledger.jsonl"
    output_path = tmpdir / "demo_phase1_output.json"

    argos_contract, tuu_policy = _load_contracts(REPO_ROOT)

    ledger = Ledger(ledger_path)
    tuu = TUU(ledger=ledger, contract=tuu_policy)

    print(f"[SETUP] Ledger: {ledger_path}")
    print(f"[SETUP] Contrato ARGOS: {argos_contract['contract_id']} v{argos_contract['version']}")
    print(f"[SETUP] Estado inicial: tick={tuu.tick}, circuit={tuu.circuit_state}")
    print()

    # ============ PROVA 1 ============
    print(_line("-"))
    print(" PROVA 1: O HABITANTE PRODUZ PROPOSTAS")
    print(_line("-"))

    agent = EphemeralAgent(
        seed=DEMO_SEED,
        context=DEMO_CONTEXT,
        contract=argos_contract,
    )
    print(f"[PROVA 1] Agent ID: {agent.agent_id}")
    print(f"[PROVA 1] Role: {agent.role}")
    print(f"[PROVA 1] Region: {agent.region}")

    proposal = agent.propose(
        "PROPOSE_OBSERVATION",
        {
            "fluxo_entropico": 0.142,
            "pressao_interna": 101.3,
            "temperatura_simulada": 298.15,
        },
        timestamp_logical=0,
        hypothesis="Equilíbrio térmico e barométrico normal nos limites operacionais.",
    )
    print(f"[PROVA 1] Proposal ID: {proposal.proposal_id}")
    print(f"[PROVA 1] Hypothesis: {proposal.hypothesis}")
    results["artifacts"]["agent_id"] = agent.agent_id
    results["artifacts"]["proposal_id"] = proposal.proposal_id
    results["prova_1"] = True
    print(">>> PROVA 1 SATISFEITA")
    print()

    # ============ PROVA 2 ============
    print(_line("-"))
    print(" PROVA 2: O CENTRO DECIDE")
    print(_line("-"))

    decision = tuu.evaluate_proposal(proposal.to_dict())
    print(f"[PROVA 2] Status: {decision.status}")
    print(f"[PROVA 2] Decision ID: {decision.decision_id}")
    print(f"[PROVA 2] Tick após: {tuu.tick}")

    if decision.status != STATUS_APPROVED:
        print(f"!! FALHA: esperado {STATUS_APPROVED}, obtido {decision.status}")
        return 1

    # Teste de violação
    print()
    print("[PROVA 2b] Teste de violação: agente tenta ação disallowed")
    try:
        agent.propose("EXECUTE_DIRECTLY", {}, timestamp_logical=1)
        print("!! FALHA: exceção não levantada")
        return 1
    except PermissionError as e:
        print(f"[PROVA 2b] PermissionError: {e}")

    results["artifacts"]["decision_id"] = decision.decision_id
    results["artifacts"]["final_state_hash"] = tuu.state_hash()
    results["prova_2"] = True
    print(">>> PROVA 2 SATISFEITA")
    print()

    # ============ PROVA 3 ============
    print(_line("-"))
    print(" PROVA 3: O RESULTADO É REGISTRADO NO LEDGER")
    print(_line("-"))

    audit = ledger.audit_chain()
    print(f"[PROVA 3] Total de blocos: {audit.total_blocks}")
    print(f"[PROVA 3] chain_integrity: {audit.chain_integrity}")
    print(f"[PROVA 3] last_valid_seq: {audit.last_valid_seq}")
    print(f"[PROVA 3] diagnostic: {audit.diagnostic}")

    for block in ledger.read_all():
        print(f"  Bloco #{block.seq} [tick {block.tick}] {block.event_type}")

    if not audit.chain_integrity:
        print("!! FALHA: cadeia não íntegra")
        return 1

    results["artifacts"]["blocks_count"] = audit.total_blocks
    results["prova_3"] = True
    print(">>> PROVA 3 SATISFEITA")
    print()

    # ============ PROVA 4 ============
    print(_line("-"))
    print(" PROVA 4: O HABITANTE MORRE (EFEMERIDADE)")
    print(_line("-"))

    tombstone = agent.die()
    print(f"[PROVA 4] Tombstone: {tombstone.to_dict()}")
    print(f"[PROVA 4] is_alive: {agent.is_alive}")

    # Pós-morte, propose deve levantar
    try:
        agent.propose("PROPOSE_OBSERVATION", {}, timestamp_logical=2)
        print("!! FALHA: pós-morte deveria ter levantado RuntimeError")
        return 1
    except RuntimeError as e:
        print(f"[PROVA 4] RuntimeError pós-morte: {e}")

    results["artifacts"]["tombstone"] = tombstone.to_dict()
    results["prova_4"] = True
    print(">>> PROVA 4 SATISFEITA")
    print()

    # ============ PROVA 5 ============
    print(_line("-"))
    print(" PROVA 5: RECONSTRUÇÃO TABULA RASA")
    print(_line("-"))

    original_state_hash = tuu.state_hash()
    print(f"[PROVA 5] Hash do estado original (RAM): {original_state_hash}")

    # Simula wipe: descarta a TUU, mas o ledger persiste em disco
    del tuu

    # Reconstrói do zero
    ledger_fresh = Ledger(ledger_path)
    reconstructor = WorldReconstructor(ledger_fresh)
    reconstruction = reconstructor.reconstruct()

    print(f"[PROVA 5] success: {reconstruction.success}")
    print(f"[PROVA 5] blocks_processed: {reconstruction.blocks_processed}")
    print(f"[PROVA 5] state_hash reconstruído: {reconstruction.state_hash}")
    print(f"[PROVA 5] diagnostic: {reconstruction.diagnostic}")

    # Compara
    # Obs: state_hash do TUU inclui campos que o reconstructor também preenche.
    # Se bater, prova 5 OK.

    results["artifacts"]["reconstructed_state_hash"] = reconstruction.state_hash
    results["artifacts"]["original_state_hash"] = original_state_hash
    results["artifacts"]["divergence"] = (
        0.0 if reconstruction.state_hash == original_state_hash else 1.0
    )

    if reconstruction.state_hash == original_state_hash:
        print(f">>> PROVA 5 SATISFEITA (divergência 0.00%)")
        results["prova_5"] = True
    else:
        print(f">>> PROVA 5: divergência detectada")
        print(f"    original:    {original_state_hash}")
        print(f"    reconstruído: {reconstruction.state_hash}")

    print()

    # Salva resultado estruturado
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[SETUP] Resultado salvo em: {output_path}")
    print()

    # Resumo
    print(_line("="))
    all_pass = all([
        results["prova_1"],
        results["prova_2"],
        results["prova_3"],
        results["prova_4"],
        results["prova_5"],
    ])
    if all_pass:
        print(" RESULTADO FINAL: FASE 1 COMPLETADA COM ÊXITO ")
    else:
        print(" RESULTADO FINAL: FALHA EM UMA OU MAIS PROVAS ")
    print(_line("="))

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
