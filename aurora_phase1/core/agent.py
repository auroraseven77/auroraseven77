"""Habitante efêmero do mundo.

Determinístico por (seed, context, contract). Nasce, propõe, morre.
Cada ciclo é autocontido.

Invariantes:
- Mesmo (seed, context, contract) → mesmo agent_id
- propose() valida contra o contrato do próprio papel (defesa camada 1)
- O Centro valida de novo (defesa camada 2)
- Pós-morte, propose() levanta RuntimeError
- propose() NÃO escreve no ledger; só o Centro escreve
- Tombstone é determinístico
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Optional

from aurora_phase1.core.crypto import hash_object


@dataclass
class Proposal:
    proposal_id: str
    agent_id: str
    role: str
    action_type: str
    timestamp_logical: int
    hypothesis: str
    seed: int
    observation_data: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "proposal_id": self.proposal_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "action_type": self.action_type,
            "timestamp_logical": self.timestamp_logical,
            "hypothesis": self.hypothesis,
            "seed": self.seed,
        }
        if self.observation_data is not None:
            d["observation_data"] = self.observation_data
        return d


@dataclass
class Tombstone:
    agent_id: str
    role: str
    cycles_completed: int
    proposals_made: int
    status: str = "TERMINATED"

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "cycles_completed": self.cycles_completed,
            "proposals_made": self.proposals_made,
            "status": self.status,
        }


class EphemeralAgent:
    """Habitante efêmero. Vive um ciclo e morre."""

    def __init__(self, seed: int, context: dict, contract: dict):
        if not isinstance(seed, int):
            raise TypeError("seed deve ser int")
        if not isinstance(context, dict):
            raise TypeError("context deve ser dict")
        if not isinstance(contract, dict):
            raise TypeError("contract deve ser dict")

        required_contract_fields = (
            "contract_id",
            "version",
            "role",
            "region",
            "allowed_actions",
            "disallowed_actions",
        )
        for f in required_contract_fields:
            if f not in contract:
                raise ValueError(f"contrato sem campo obrigatório: {f}")

        self._seed = seed
        self._context = copy.deepcopy(context)
        self._contract = copy.deepcopy(contract)
        self._alive = True
        self._cycles_completed = 0
        self._proposals_made = 0
        self._proposal_ids: list[str] = []

        self._agent_id = self._compute_agent_id()

    # ---- identidade ----

    def _compute_agent_id(self) -> str:
        payload = {
            "seed": self._seed,
            "context": self._context,
            "contract_id": self._contract["contract_id"],
            "contract_version": self._contract["version"],
        }
        return hash_object(payload)

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def role(self) -> str:
        return self._contract["role"]

    @property
    def region(self) -> str:
        return self._contract["region"]

    @property
    def is_alive(self) -> bool:
        return self._alive

    @property
    def cycles_completed(self) -> int:
        return self._cycles_completed

    @property
    def proposals_made(self) -> int:
        return self._proposals_made

    @property
    def proposal_ids(self) -> tuple[str, ...]:
        return tuple(self._proposal_ids)

    # ---- vida ----

    def propose(
        self,
        action_type: str,
        payload: Optional[dict] = None,
        *,
        timestamp_logical: int = 0,
        hypothesis: str = "",
    ) -> Proposal:
        """Monta proposta estruturada. Valida contra o contrato do papel.

        NÃO escreve no ledger. O Centro escreve.
        """
        if not self._alive:
            raise RuntimeError(
                f"Agent {self._agent_id} is already dead."
            )

        if not isinstance(action_type, str):
            raise TypeError("action_type deve ser str")

        if action_type in self._contract["disallowed_actions"]:
            raise PermissionError(
                f"Action '{action_type}' is disallowed for role "
                f"'{self.role}'. Disallowed: "
                f"{self._contract['disallowed_actions']}"
            )

        if action_type not in self._contract["allowed_actions"]:
            raise PermissionError(
                f"Action '{action_type}' is not in allowed_actions "
                f"for role '{self.role}'. Allowed: "
                f"{self._contract['allowed_actions']}"
            )

        if not isinstance(timestamp_logical, int):
            raise TypeError("timestamp_logical deve ser int")

        if len(hypothesis) > self._contract.get(
            "hypothesis_max_length", 512
        ):
            raise ValueError(
                f"hypothesis excede o limite de "
                f"{self._contract.get('hypothesis_max_length', 512)} chars"
            )

        # Camada 1 — agente valida seu próprio conteúdo
        self._validate_content(payload or {})

        # Monta proposta
        proposal_body = {
            "agent_id": self._agent_id,
            "role": self.role,
            "action_type": action_type,
            "timestamp_logical": timestamp_logical,
            "observation_data": payload,
            "hypothesis": hypothesis,
            "seed": self._seed,
        }
        proposal_id = hash_object(proposal_body)

        proposal = Proposal(
            proposal_id=proposal_id,
            agent_id=self._agent_id,
            role=self.role,
            action_type=action_type,
            timestamp_logical=timestamp_logical,
            hypothesis=hypothesis,
            seed=self._seed,
            observation_data=payload,
        )

        self._proposals_made += 1
        self._proposal_ids.append(proposal_id)
        return proposal

    def _validate_content(self, payload: dict) -> None:
        """Camada 1 — validação de conteúdo pelo próprio agente."""
        denied_patterns = self._contract.get("denied_patterns", [])
        if not denied_patterns:
            return
        import json
        import re
        flat = json.dumps(payload, ensure_ascii=False)
        for pat in denied_patterns:
            if re.search(pat, flat):
                raise PermissionError(
                    f"Payload contém padrão negado pelo contrato: {pat}"
                )

    # ---- morte ----

    def die(self) -> Tombstone:
        """Encerra o habitante. Idempotente."""
        if not self._alive:
            raise RuntimeError(
                f"Agent {self._agent_id} is already dead."
            )

        self._alive = False
        self._cycles_completed += 1

        return Tombstone(
            agent_id=self._agent_id,
            role=self.role,
            cycles_completed=self._cycles_completed,
            proposals_made=self._proposals_made,
        )


__all__ = ["EphemeralAgent", "Proposal", "Tombstone"]
