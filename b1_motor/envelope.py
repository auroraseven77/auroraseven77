"""
TUU / B1.2 / P2.0 — Evidence Envelope.
Strict enforcement of authority == 'none' and evidence_source == 'computational_simulation_only'.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Tuple, Any
from b1_motor.types import AgentId, EvidenceSource, Authority

@dataclass(frozen=True)
class EvidenceEnvelope:
    schema_version: str
    source_agent: AgentId
    target_agent: AgentId
    experiment_id: str
    execution_id: str
    evidence_source: EvidenceSource = "computational_simulation_only"
    backend: str = "classical_mps"
    backend_version: str = ""
    circuit_id: str = ""
    input_hash: str = ""
    result_hash: str = ""
    telemetry_hash: str = ""
    timestamp: str = ""
    status: str = ""
    claims: Tuple[Any, ...] = field(default_factory=tuple)
    evidence: Tuple[Any, ...] = field(default_factory=tuple)
    authority: Authority = "none"

    def __post_init__(self) -> None:
        if self.authority != "none":
            raise ValueError(
                f"Security Violation: authority must remain 'none', got '{self.authority}'. "
                "Authority only enters through an explicit named port."
            )
        if self.evidence_source != "computational_simulation_only":
            raise ValueError(
                f"Security Violation: evidence_source must be 'computational_simulation_only', got '{self.evidence_source}'."
            )
