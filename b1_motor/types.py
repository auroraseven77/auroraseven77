from __future__ import annotations
import enum
import math
from dataclasses import dataclass
from typing import Tuple, Dict

CHI_MAX = 128
LOGICAL_QUBITS_MAX = 64

class AgentId(enum.Enum):
    ARGOS = "ARGOS"
    HEPHAESTUS = "HEPHAESTUS"
    HERMES = "HERMES"

AgentID = AgentId

class BoundaryID(enum.Enum):
    AH = "21-22"
    HE = "43-44"

class EvidenceSource(enum.Enum):
    SIMULATION = "SIMULATION"
    MEASUREMENT = "MEASUREMENT"
    MOTOR = "MOTOR"
    AGENT = "AGENT"

class Authority(enum.Enum):
    LOCAL = "LOCAL"
    GLOBAL = "GLOBAL"
    CONSENSUS = "CONSENSUS"

CANONICAL_RANGES = {
    AgentId.ARGOS: (0, 21),
    AgentId.HEPHAESTUS: (22, 43),
    AgentId.HERMES: (44, 63),
}

@dataclass(frozen=True)
class AgentPartition:
    agent_id: AgentId | str
    qubit_range: Tuple[int, int]
    boundary_left: BoundaryID | None = None
    boundary_right: BoundaryID | None = None

    def __post_init__(self):
        # Normaliza agent_id para enum se vier como string
        resolved_id = self.agent_id
        if isinstance(resolved_id, str):
            try:
                resolved_id = AgentId(resolved_id)
            except ValueError:
                raise ValueError(f"Unknown agent_id: {self.agent_id}")
        
        if resolved_id not in CANONICAL_RANGES:
            raise ValueError(f"Unknown agent_id: {self.agent_id}")
            
        expected = CANONICAL_RANGES[resolved_id]
        if self.qubit_range != expected:
            raise ValueError(
                f"Invalid range {self.qubit_range} for {self.agent_id}. "
                f"Expected {expected}"
            )

    def __iter__(self):
        return iter(self.qubit_range)

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.qubit_range == other
        if isinstance(other, AgentPartition):
            return (str(self.agent_id) == str(other.agent_id) and 
                    self.qubit_range == other.qubit_range and
                    self.boundary_left == other.boundary_left and
                    self.boundary_right == other.boundary_right)
        return False

PARTITIONS: Dict[str, AgentPartition] = {
    "ARGOS": AgentPartition(AgentId.ARGOS, (0, 21), None, BoundaryID.AH),
    "HEPHAESTUS": AgentPartition(AgentId.HEPHAESTUS, (22, 43), BoundaryID.AH, BoundaryID.HE),
    "HERMES": AgentPartition(AgentId.HERMES, (44, 63), BoundaryID.HE, None),
}

@dataclass(frozen=True)
class TruncationReport:
    step: int = 0
    bond_dimension_before: int = 0
    bond_dimension_after: int = 0
    discarded_weight_loss: float = 0.0
    chi_max_cap: int = CHI_MAX
    chi_before: int = 0
    chi_after: int = 0
    discarded_weight: float = 0.0
    truncation_applied: bool = False

    def __post_init__(self):
        if self.step < 0:
            raise ValueError("step must be >= 0")
        if self.bond_dimension_before < 0 or self.bond_dimension_after < 0:
            raise ValueError("bond dimensions must be >= 0")
        if self.chi_max_cap < 1 or self.chi_max_cap > CHI_MAX:
            raise ValueError(f"chi_max_cap must be between 1 and {CHI_MAX}")
        if self.bond_dimension_after > self.bond_dimension_before:
            raise ValueError("bond_dimension_after cannot exceed bond_dimension_before")
        if self.bond_dimension_after > self.chi_max_cap:
            raise ValueError("bond_dimension_after cannot exceed chi_max_cap")
        if self.discarded_weight_loss < 0.0 or not math.isfinite(self.discarded_weight_loss):
            raise ValueError("discarded_weight_loss must be finite and >= 0")

        if self.bond_dimension_before != 0 and self.chi_before == 0:
            object.__setattr__(self, 'chi_before', self.bond_dimension_before)
        if self.bond_dimension_after != 0 and self.chi_after == 0:
            object.__setattr__(self, 'chi_after', self.bond_dimension_after)
        if self.discarded_weight_loss != 0.0 and self.discarded_weight == 0.0:
            object.__setattr__(self, 'discarded_weight', self.discarded_weight_loss)
        if not self.truncation_applied and self.discarded_weight_loss > 0:
            object.__setattr__(self, 'truncation_applied', True)

@dataclass(frozen=True)
class BoundaryExchangeReport:
    boundary_id: BoundaryID
    effective_bond_dim: int
    chi_used: int
    singular_values_kept: Tuple[float, ...]
    singular_values_discarded: Tuple[float, ...]
    truncation_applied: bool
    discarded_weight_loss: float
    agent_left_id: str = "ARGOS"
    agent_right_id: str = "HEPHAESTUS"
    qubit_left_id: int = 21
    qubit_right_id: int = 22
    hash_tensor_left_in: str = "dummy_hash"
    hash_tensor_right_in: str = "dummy_hash"
    normalization_tolerance: float = 1e-12

    def __post_init__(self) -> None:
        if not isinstance(self.boundary_id, BoundaryID):
            raise ValueError("boundary_id must be a BoundaryID")
            
        if not 1 <= self.effective_bond_dim <= CHI_MAX:
            raise ValueError(f"effective_bond_dim must satisfy 1 <= value <= {CHI_MAX}")
            
        if not 1 <= self.chi_used <= CHI_MAX:
            raise ValueError(f"chi_used must satisfy 1 <= value <= {CHI_MAX}")
            
        if self.effective_bond_dim != self.chi_used:
            raise ValueError("effective_bond_dim must equal chi_used")

        kept = tuple(self.singular_values_kept)
        discarded = tuple(self.singular_values_discarded)

        if len(kept) != self.effective_bond_dim:
            raise ValueError("number of kept singular values must equal effective_bond_dim")

        all_values = kept + discarded
        for value in all_values:
            if not math.isfinite(value):
                raise ValueError("singular values must be finite")
            if value < 0.0:
                raise ValueError("singular values cannot be negative")

        if any(kept[i] < kept[i + 1] for i in range(len(kept) - 1)):
            raise ValueError("kept singular values must be non-increasing")
            
        if any(discarded[i] < discarded[i + 1] for i in range(len(discarded) - 1)):
            raise ValueError("discarded singular values must be non-increasing")

        if self.discarded_weight_loss < 0.0 or not math.isfinite(self.discarded_weight_loss):
            raise ValueError("discarded_weight_loss must be positive and finite")

        calculated_discarded_loss = sum(v * v for v in discarded)
        if not math.isclose(calculated_discarded_loss, self.discarded_weight_loss, rel_tol=0.0, abs_tol=self.normalization_tolerance):
            raise ValueError("discarded_weight_loss must equal the squared norm of singular_values_discarded")

        if self.truncation_applied != bool(discarded):
            raise ValueError("truncation_applied must match presence of discarded singular values")

        total_weight = sum(v * v for v in all_values)
        if not math.isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=self.normalization_tolerance):
            raise ValueError("normalized boundary spectrum must satisfy sum(singular_values^2) = 1 within fixed tolerance")
