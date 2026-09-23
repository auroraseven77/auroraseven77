"""Reconstrução de estado do mundo a partir do ledger.

O reconstructor LÊ o ledger e reproduz o `world_state` que o Centro
teria naquele ponto. NUNCA escreve no ledger.

Invariantes:
- Não escreve no ledger
- Se a cadeia quebra no seq N, para no último bloco válido (N-1)
- Reproduz `world_state` a partir de `PROPOSAL_PROCESSED_AND_APPROVED`
- Reconstrói `seen_proposal_ids`
- Se encontra `event_type` desconhecido, avisa mas continua
- Determinístico: mesma entrada → mesmo `state_hash`
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional

from aurora_phase1.core.crypto import hash_object
from aurora_phase1.core.ledger import Ledger


# event_types conhecidos (extensível)
KNOWN_EVENT_TYPES = frozenset({
    "GENESIS_INITIALIZED",
    "AGENT_BORN",
    "AGENT_DIED",
    "PROPOSAL_PROCESSED_AND_APPROVED",
    "PROPOSAL_REJECTED",
    "ATTACK_FINDING_RECORDED",
    "QUANTUM_MEASUREMENT_COMPLETED",
})


@dataclass
class ReconstructionResult:
    success: bool
    state: dict
    state_hash: str
    stopped_at_seq: int
    blocks_processed: int
    seen_proposal_ids: frozenset[str]
    diagnostic: str

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "state": copy.deepcopy(self.state),
            "state_hash": self.state_hash,
            "stopped_at_seq": self.stopped_at_seq,
            "blocks_processed": self.blocks_processed,
            "seen_proposal_ids": sorted(self.seen_proposal_ids),
            "diagnostic": self.diagnostic,
        }


class WorldReconstructor:
    """Reproduz `world_state` a partir do ledger, com parada estrita."""

    def __init__(self, ledger: Ledger):
        if not isinstance(ledger, Ledger):
            raise TypeError("ledger deve ser Ledger")
        self._ledger = ledger

    def _empty_state(self) -> dict:
        return {
            "tick": 0,
            "observations": {},
            "hypotheses_sedimented": [],
            "rejected_attempts": 0,
            "completed_cycles": 0,
        }

    def reconstruct(self) -> ReconstructionResult:
        """Reconstrói estado. Para no último bloco válido se houver corrupção."""

        # 1. Auditoria de cadeia (identifica se há corrupção)
        audit = self._ledger.audit_chain()

        # 2. Ler blocos (até onde for válido)
        try:
            all_blocks = self._ledger.read_all()
        except ValueError as e:
            # Erro na leitura bruta (linha malformada). Sem blocos válidos.
            state = self._empty_state()
            return ReconstructionResult(
                success=False,
                state=state,
                state_hash=hash_object(state),
                stopped_at_seq=-1,
                blocks_processed=0,
                seen_proposal_ids=frozenset(),
                diagnostic=f"Falha ao ler ledger: {e}",
            )

        # 3. Determinar quantos blocos processar
        if audit.chain_integrity:
            valid_count = len(all_blocks)
        else:
            # Parar no último bloco válido: seq 0..audit.last_valid_seq
            valid_count = audit.last_valid_seq + 1

        blocks_to_process = all_blocks[:valid_count]

        # 4. Reproduzir estado
        state = self._empty_state()
        seen: set[str] = set()
        unknown_events: list[tuple[int, str]] = []

        for block in blocks_to_process:
            if block.event_type not in KNOWN_EVENT_TYPES:
                unknown_events.append((block.seq, block.event_type))
                continue

            self._apply_block(state, seen, block)

        state_hash = hash_object(state)

        # 5. Diagnóstico
        if audit.chain_integrity:
            diagnostic = (
                f"Reconstrução completa: {len(blocks_to_process)} blocos."
            )
            success = True
            stopped_at = (
                blocks_to_process[-1].seq if blocks_to_process else -1
            )
        else:
            diagnostic = (
                f"Cadeia corrompida em seq {audit.failed_seq}. "
                f"Reconstruído até seq {audit.last_valid_seq}. "
                f"{audit.diagnostic}"
            )
            success = False
            stopped_at = audit.last_valid_seq

        if unknown_events:
            diagnostic += (
                f" Eventos desconhecidos ignorados: "
                f"{[(s, e) for s, e in unknown_events]}"
            )

        return ReconstructionResult(
            success=success,
            state=state,
            state_hash=state_hash,
            stopped_at_seq=stopped_at,
            blocks_processed=len(blocks_to_process),
            seen_proposal_ids=frozenset(seen),
            diagnostic=diagnostic,
        )

    # ---- aplicação por tipo de evento ----

    @staticmethod
    def _apply_block(state: dict, seen: set[str], block) -> None:
        payload = block.payload
        et = block.event_type

        if et == "GENESIS_INITIALIZED":
            return

        if et == "AGENT_BORN":
            # nada a fazer no world_state (só ledger)
            return

        if et == "AGENT_DIED":
            return

        if et == "PROPOSAL_PROCESSED_AND_APPROVED":
            state["tick"] = max(state["tick"], block.tick)
            state["completed_cycles"] += 1

            pid = payload.get("proposal_id")
            if pid:
                seen.add(pid)

            # Reconstrói observação se o payload tiver dados suficientes
            agent_id = payload.get("agent_id")
            if agent_id:
                key = f"obs_tick_{block.tick}_{agent_id[:8]}"
                state["observations"][key] = {
                    "source_agent": agent_id,
                    "action_type": payload.get("action_type"),
                    "recorded_at_tick": block.tick,
                }
            return

        if et == "PROPOSAL_REJECTED":
            state["rejected_attempts"] += 1
            pid = payload.get("proposal_id")
            if pid:
                seen.add(pid)
            return

        if et == "ATTACK_FINDING_RECORDED":
            # Evidência — não altera world_state
            return

        if et == "QUANTUM_MEASUREMENT_COMPLETED":
            # Extensão futura — por agora não altera world_state
            return


__all__ = [
    "WorldReconstructor",
    "ReconstructionResult",
    "KNOWN_EVENT_TYPES",
]
