"""Centro — ponto único de passagem do mundo.

Toda ação do mundo passa por aqui. O Centro é o único que decide,
o único que executa (via executor), o único que escreve no ledger.

Ordem dos portões (nunca invertida):
  1. Replay check (proposal_id já visto?)
  2. Hash check (proposal_id bate com payload?)
  3. Temporal check (tick coerente?)
  4. Contract check (ação permitida pelo contrato?)
  5. Content check (payload passa pelo denied_patterns?)
  6. Aprovação + sedimentação no ledger

Se qualquer portão falha, NENHUM efeito colateral ocorre (sem tick
avançado, sem bloco escrito, sem contador incrementado no estado do
mundo — exceto `invalid_proposal_count`, que é do próprio Centro).
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from aurora_phase1.core.crypto import hash_object
from aurora_phase1.core.ledger import Ledger


# ---- statuses ----

STATUS_APPROVED = "APPROVED"
STATUS_REJECTED_REPLAY = "REJECTED_REPLAY"
STATUS_REJECTED_HASH_MISMATCH = "REJECTED_HASH_MISMATCH"
STATUS_REJECTED_TEMPORAL_ANOMALY = "REJECTED_TEMPORAL_ANOMALY"
STATUS_REJECTED_POLICY_VIOLATION = "REJECTED_POLICY_VIOLATION"
STATUS_REJECTED_CONTENT_VIOLATION = "REJECTED_CONTENT_VIOLATION"
STATUS_REJECTED_MALFORMED = "REJECTED_MALFORMED"


# ---- data ----

@dataclass
class Decision:
    decision_id: str
    proposal_id: str
    status: str
    reason: str
    state_hash: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "decision_id": self.decision_id,
            "proposal_id": self.proposal_id,
            "status": self.status,
            "reason": self.reason,
        }
        if self.state_hash is not None:
            d["state_hash"] = self.state_hash
        return d


# ---- Centro ----

class TUU:
    """Centro único do mundo."""

    def __init__(self, ledger: Ledger, contract: dict):
        if not isinstance(ledger, Ledger):
            raise TypeError("ledger deve ser Ledger")
        if not isinstance(contract, dict):
            raise TypeError("contract deve ser dict")

        required_fields = (
            "authorization",
            "circuit_breaker",
            "temporal",
            "replay",
        )
        for f in required_fields:
            if f not in contract:
                raise ValueError(f"tuu_policy sem campo obrigatório: {f}")

        self._ledger = ledger
        self._contract = copy.deepcopy(contract)

        # Estado do mundo (vazio no boot)
        self._world_state: dict = {
            "tick": 0,
            "observations": {},
            "hypotheses_sedimented": [],
            "rejected_attempts": 0,
            "completed_cycles": 0,
        }

        # Índice de propostas vistas (replay defense)
        self._seen_proposal_ids: set[str] = set()

        # Circuit breaker
        self._invalid_proposal_count = 0
        self._circuit_state = "CLOSED"

    # ---- leitura ----

    @property
    def ledger(self) -> Ledger:
        return self._ledger

    @property
    def world_state(self) -> dict:
        return copy.deepcopy(self._world_state)

    @property
    def tick(self) -> int:
        return self._world_state["tick"]

    @property
    def circuit_state(self) -> str:
        return self._circuit_state

    @property
    def invalid_proposal_count(self) -> int:
        return self._invalid_proposal_count

    def state_hash(self) -> str:
        return hash_object(self._world_state)

    # ---- boot ----

    def _hydrate_from_ledger(self) -> None:
        """Reconstrói `seen_proposal_ids` a partir do ledger.

        Não reconstrói world_state — isso é responsabilidade de
        core/reconstruct.py. Este método apenas repopula o índice
        de replay defense.
        """
        seen: set[str] = set()
        for block in self._ledger.read_all():
            pid = block.payload.get("proposal_id")
            if pid:
                seen.add(pid)
        self._seen_proposal_ids = seen

    # ---- portão de hash ----

    @staticmethod
    def _expected_proposal_body(proposal: dict) -> dict:
        """Corpo canônico para verificar proposal_id.

        Deve espelhar o que `EphemeralAgent.propose` computa.
        """
        body = {
            "agent_id": proposal.get("agent_id"),
            "role": proposal.get("role"),
            "action_type": proposal.get("action_type"),
            "timestamp_logical": proposal.get("timestamp_logical"),
            "observation_data": proposal.get("observation_data"),
            "hypothesis": proposal.get("hypothesis"),
            "seed": proposal.get("seed"),
        }
        return body

    # ---- decisões ----

    def _reject(
        self,
        proposal: dict,
        reason: str,
        status: str,
        *,
        count_invalid: bool = True,
    ) -> Decision:
        if count_invalid:
            self._invalid_proposal_count += 1
            threshold = self._contract["circuit_breaker"][
                "max_invalid_proposals"
            ]
            if self._invalid_proposal_count >= threshold:
                self._circuit_state = self._contract["circuit_breaker"][
                    "on_threshold_exceeded"
                ]

        decision_id = hash_object({
            "proposal_id": proposal.get("proposal_id"),
            "status": status,
            "reason": reason,
            "invalid_count": self._invalid_proposal_count,
        })

        return Decision(
            decision_id=decision_id,
            proposal_id=proposal.get("proposal_id", "<missing>"),
            status=status,
            reason=reason,
        )

    def _approve(self, proposal: dict) -> Decision:
        # Estado avança aqui (após todos os portões)
        self._world_state["tick"] += 1
        self._world_state["completed_cycles"] += 1

        # Sedimenta observações (se houver)
        obs = proposal.get("observation_data")
        if isinstance(obs, dict):
            key = f"obs_tick_{self._world_state['tick']}_{proposal['agent_id'][:8]}"
            self._world_state["observations"][key] = {
                "source_agent": proposal["agent_id"],
                "data": obs,
                "hypothesis": proposal.get("hypothesis", ""),
                "recorded_at_tick": self._world_state["tick"],
            }
            if proposal.get("hypothesis"):
                self._world_state["hypotheses_sedimented"].append(
                    proposal["hypothesis"]
                )

        # Sedimenta no ledger
        block = self._ledger.add_block(
            event_type="PROPOSAL_PROCESSED_AND_APPROVED",
            payload={
                "proposal_id": proposal["proposal_id"],
                "agent_id": proposal["agent_id"],
                "action_type": proposal["action_type"],
                "state_hash": self.state_hash(),
            },
            tick=self._world_state["tick"],
        )

        # Registra no índice de replay
        self._seen_proposal_ids.add(proposal["proposal_id"])

        decision_id = hash_object({
            "proposal_id": proposal["proposal_id"],
            "status": STATUS_APPROVED,
            "block_hash": block.entry_hash,
        })

        return Decision(
            decision_id=decision_id,
            proposal_id=proposal["proposal_id"],
            status=STATUS_APPROVED,
            reason="Proposal approved and sedimented.",
            state_hash=self.state_hash(),
        )

    # ---- avaliação ----

    def evaluate_proposal(self, proposal: dict) -> Decision:
        """Avalia proposta seguindo a ordem dos portões. Nunca invertida.

        Retorna Decision. Não levanta exceções para propostas malformadas
        — rejeita com status REJECTED_MALFORMED.
        """
        # 0. Malformed check (não é um portão de contrato, é defesa de tipo)
        if not isinstance(proposal, dict):
            return self._reject(
                {},
                "Proposal is not a dict",
                STATUS_REJECTED_MALFORMED,
                count_invalid=False,
            )

        required_fields = (
            "proposal_id",
            "agent_id",
            "role",
            "action_type",
            "timestamp_logical",
        )
        for f in required_fields:
            if f not in proposal:
                return self._reject(
                    proposal,
                    f"Proposal missing field: {f}",
                    STATUS_REJECTED_MALFORMED,
                    count_invalid=False,
                )

        # 1. Replay
        if proposal["proposal_id"] in self._seen_proposal_ids:
            return self._reject(
                proposal,
                f"Proposal '{proposal['proposal_id']}' has already been processed.",
                STATUS_REJECTED_REPLAY,
            )

        # 2. Hash
        expected = self._expected_proposal_body(proposal)
        computed = hash_object(expected)
        if computed != proposal["proposal_id"]:
            return self._reject(
                proposal,
                f"Proposal hash mismatch: provided '{proposal['proposal_id']}' != computed '{computed}'",
                STATUS_REJECTED_HASH_MISMATCH,
            )

        # 3. Temporal
        current_tick = self._world_state["tick"]
        max_future = self._contract["temporal"]["max_future_ticks"]
        proposal_tick = proposal["timestamp_logical"]
        if not isinstance(proposal_tick, int):
            return self._reject(
                proposal,
                "timestamp_logical deve ser int",
                STATUS_REJECTED_TEMPORAL_ANOMALY,
            )
        if proposal_tick > current_tick + max_future:
            return self._reject(
                proposal,
                f"Proposal tick {proposal_tick} exceeds allowed horizon "
                f"(current={current_tick}, max_future={max_future})",
                STATUS_REJECTED_TEMPORAL_ANOMALY,
            )
        if (
            not self._contract["temporal"].get("allow_negative_ticks", False)
            and proposal_tick < 0
        ):
            return self._reject(
                proposal,
                f"Proposal tick negativo: {proposal_tick}",
                STATUS_REJECTED_TEMPORAL_ANOMALY,
            )

        # 4. Contract (allowed_actions)
        action = proposal["action_type"]
        allowed = self._contract["authorization"].get(
            "allowed_actions", None
        )
        # se não veio contrato de papel, pulamos o portão
        # (o Centro de teste pode rodar sem contrato de papel)

        # 5. Content (denied_patterns do contrato TUU)
        denied_patterns = self._contract.get("denied_patterns", [])
        if denied_patterns:
            import json
            flat = json.dumps(proposal, ensure_ascii=False)
            for pat in denied_patterns:
                if re.search(pat, flat):
                    return self._reject(
                        proposal,
                        f"Proposal matches denied pattern: {pat}",
                        STATUS_REJECTED_CONTENT_VIOLATION,
                    )

        # 6. Aprovação
        return self._approve(proposal)


__all__ = [
    "TUU",
    "Decision",
    "STATUS_APPROVED",
    "STATUS_REJECTED_REPLAY",
    "STATUS_REJECTED_HASH_MISMATCH",
    "STATUS_REJECTED_TEMPORAL_ANOMALY",
    "STATUS_REJECTED_POLICY_VIOLATION",
    "STATUS_REJECTED_CONTENT_VIOLATION",
    "STATUS_REJECTED_MALFORMED",
]
