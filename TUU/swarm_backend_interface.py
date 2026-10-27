from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Tuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
)
from typing_extensions import Annotated


__all__ = [
    "CodecType",
    "HashAlgorithm",
    "PayloadPointer",
    "TensorMetadata",
    "StateVersion",
    "ContractionInput",
    "OperationType",
    "TensorContractionRequest",
    "ContractionOutput",
    "TensorContractionResult",
    "ComputeBackend",
]


NonEmptyStrictStr = Annotated[StrictStr, Field(min_length=1)]
PositiveInt = Annotated[StrictInt, Field(gt=0)]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]


class CodecType(str, Enum):
    """Binary representation used by a payload store/transport."""

    RAW_BYTES = "raw_bytes"
    SAFETENSORS = "safetensors"


class HashAlgorithm(str, Enum):
    """Digest algorithm used to address and verify a payload."""

    SHA256 = "sha256"
    BLAKE3 = "blake3"


class PayloadPointer(BaseModel):
    """Immutable content-addressed reference to binary tensor data.

    The tensor bytes are deliberately not part of the Pydantic contract.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    payload_hash: StrictStr = Field(
        ...,
        pattern=r"^[0-9a-fA-F]{64}$",
        description="64-hex-character digest for the selected hash algorithm.",
    )
    byte_length: StrictInt = Field(
        ...,
        gt=0,
        description="Exact payload size in bytes.",
    )
    codec: CodecType
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256


class TensorMetadata(BaseModel):
    """Immutable, backend-neutral tensor metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    shape: Tuple[PositiveInt, ...]
    dtype: NonEmptyStrictStr = Field(
        ...,
        description="Backend-neutral dtype identifier, e.g. complex128.",
    )
    bond_dimension: Optional[PositiveInt] = None


class StateVersion(BaseModel):
    """Immutable logical version of the distributed MPS state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_id: StrictInt = Field(..., ge=0)
    qubits_affected: Tuple[NonNegativeInt, ...] = Field(
        ...,
        description="Canonical sorted unique qubit identifiers touched by the operation.",
    )

    @field_validator("qubits_affected")
    @classmethod
    def validate_qubit_ids(
        cls,
        value: Tuple[int, ...],
    ) -> Tuple[int, ...]:
        if len(value) != len(set(value)):
            raise ValueError("qubits_affected must contain unique qubit identifiers")
        if value != tuple(sorted(value)):
            raise ValueError("qubits_affected must be sorted in ascending order")
        return value


class ContractionInput(BaseModel):
    """Named immutable reference to one input tensor/gate payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStrictStr = Field(
        ...,
        description="Logical identifier such as q0_tensor, q1_tensor, or gate.",
    )
    pointer: PayloadPointer
    metadata: TensorMetadata


class OperationType(str, Enum):
    GATE_CONTRACTION_SVD = "gate_contraction_svd"


class TensorContractionRequest(BaseModel):
    """Immutable request for a two-qubit gate contraction followed by SVD."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: NonEmptyStrictStr
    parent_task_ids: Tuple[NonEmptyStrictStr, ...] = Field(
        default_factory=tuple,
        description="Explicit DAG dependencies in the swarm.",
    )
    state_version: StateVersion
    operation_type: OperationType
    chi_max: StrictInt = Field(
        ...,
        gt=0,
        description="Maximum permitted output bond dimension.",
    )
    truncation_threshold: StrictFloat = Field(
        1e-10,
        ge=0.0,
        description="Non-negative finite threshold used by the backend's truncation policy.",
    )
    inputs: Tuple[ContractionInput, ...]

    @field_validator("truncation_threshold")
    @classmethod
    def validate_threshold(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("truncation_threshold must be finite")
        return value


class ContractionOutput(BaseModel):
    """Immutable reference to a tensor produced by a contraction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStrictStr = Field(
        ...,
        description="Logical identifier of the resulting tensor.",
    )
    pointer: PayloadPointer
    metadata: TensorMetadata


class TensorContractionResult(BaseModel):
    """Immutable result of a distributed tensor contraction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: NonEmptyStrictStr
    success: StrictBool
    new_state_version: StateVersion
    outputs: Tuple[ContractionOutput, ...] = Field(default_factory=tuple)
    truncation_error: StrictFloat = Field(
        0.0,
        ge=0.0,
        description=(
            "Discarded singular-value weight: sum(sigma_discarded**2). "
            "This matches the existing MPS TruncationReport.discarded_weight_loss."
        ),
    )
    singular_values_pointer: Optional[PayloadPointer] = Field(
        None,
        description="Optional externalized binary payload containing retained/discarded singular values.",
    )
    error_message: Optional[NonEmptyStrictStr] = None

    @field_validator("truncation_error")
    @classmethod
    def validate_truncation_error(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("truncation_error must be finite")
        return value


class ComputeBackend(ABC):
    """Backend boundary for local or distributed tensor computation.

    Implementations own payload resolution, tensor algebra, result persistence,
    and construction of the immutable result contract. The contract itself
    contains no HERMES/ARGOS/HEPHAESTUS-specific concepts.
    """

    @abstractmethod
    def contract_two_qubit_gate(
        self,
        request: TensorContractionRequest,
    ) -> TensorContractionResult:
        """Execute a two-qubit gate contraction followed by SVD/truncation."""
        raise NotImplementedError
