from __future__ import annotations

import hashlib
import math
import json
from typing import Any, Mapping


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_canonical(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_raw_log(
    *,
    experiment_id: str,
    execution_id: str,
    matrix_shape: tuple[int, int],
    chi_max: int,
    step: int,
    singular_values: list[float],
    discarded_weight_loss: float,
) -> dict[str, Any]:
    return {
        "schema_version": "P2.2",
        "experiment_id": experiment_id,
        "execution_id": execution_id,
        "operation": "svd_truncate",
        "matrix_shape": list(matrix_shape),
        "chi_max": chi_max,
        "step": step,
        "singular_values": singular_values,
        "discarded_weight_loss": discarded_weight_loss,
    }


def hash_raw_log(raw_log: Mapping[str, Any]) -> str:
    return sha256_canonical(dict(raw_log))

from enum import Enum
from typing import Sequence
from b1_motor.types import BoundaryID


def _canonical_float(value: float) -> str:
    """Represent a finite Python float without decimal rounding."""
    if not isinstance(value, float):
        raise TypeError("boundary numeric values must be float")

    if not math.isfinite(value):
        raise ValueError("boundary numeric values must be finite")

    return value.hex()


def _canonical_float_array(values: Sequence[float]) -> str:
    return "[" + ",".join(
        _canonical_float(value) for value in values
    ) + "]"


def canonical_boundary_log(
    *,
    boundary_id: BoundaryID,
    singular_values_kept: Sequence[float],
    singular_values_discarded: Sequence[float],
    chi_used: int,
    discarded_weight_loss: float,
) -> str:
    """Build the deterministic RAW boundary representation."""
    if not isinstance(boundary_id, BoundaryID):
        raise TypeError("boundary_id must be a BoundaryID")

    if not isinstance(chi_used, int):
        raise TypeError("chi_used must be int")

    if chi_used < 1:
        raise ValueError("chi_used must be >= 1")

    return (
        "{"
        f'"boundary_id":"{boundary_id.value}",'
        f'"chi_used":{chi_used},'
        f'"singular_values_kept":'
        f'{_canonical_float_array(singular_values_kept)},'
        f'"singular_values_discarded":'
        f'{_canonical_float_array(singular_values_discarded)},'
        f'"discarded_weight_loss":'
        f'{_canonical_float(discarded_weight_loss)}'
        "}"
    )


def hash_boundary_log(
    *,
    boundary_id: BoundaryID,
    singular_values_kept: Sequence[float],
    singular_values_discarded: Sequence[float],
    chi_used: int,
    discarded_weight_loss: float,
) -> str:
    payload = canonical_boundary_log(
        boundary_id=boundary_id,
        singular_values_kept=singular_values_kept,
        singular_values_discarded=singular_values_discarded,
        chi_used=chi_used,
        discarded_weight_loss=discarded_weight_loss,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()
