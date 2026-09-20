from __future__ import annotations

import math

import pytest

from b1_motor.types import BoundaryExchangeReport, BoundaryID
from b1_motor.determinism import canonical_boundary_log, hash_boundary_log


def test_boundary_ids_are_closed():
    assert BoundaryID.AH.value == "21-22"
    assert BoundaryID.HE.value == "43-44"


def test_boundary_report_rejects_invalid_chi():
    with pytest.raises(ValueError):
        BoundaryExchangeReport(
            boundary_id=BoundaryID.AH,
            effective_bond_dim=129,
            singular_values_kept=(1.0,),
            singular_values_discarded=(),
            chi_used=129,
            truncation_applied=False,
            discarded_weight_loss=0.0,
        )


def test_normalized_spectrum_conservation():
    report = BoundaryExchangeReport(
        boundary_id=BoundaryID.AH,
        effective_bond_dim=2,
        singular_values_kept=(
            math.sqrt(0.75),
            math.sqrt(0.15),
        ),
        singular_values_discarded=(
            math.sqrt(0.10),
        ),
        chi_used=2,
        truncation_applied=True,
        discarded_weight_loss=0.10,
    )

    kept = sum(x * x for x in report.singular_values_kept)

    assert math.isclose(
        kept + report.discarded_weight_loss,
        1.0,
        rel_tol=0.0,
        abs_tol=report.normalization_tolerance,
    )


def test_raw_float_serialization_is_not_decimal_rounding():
    value = 0.1

    log = canonical_boundary_log(
        boundary_id=BoundaryID.AH,
        singular_values_kept=(value,),
        singular_values_discarded=(),
        chi_used=1,
        discarded_weight_loss=0.0,
    )

    assert "0.1" not in log
    assert value.hex() in log


def test_boundary_hash_is_reproducible():
    kwargs = dict(
        boundary_id=BoundaryID.HE,
        singular_values_kept=(0.8, 0.6),
        singular_values_discarded=(0.0,),
        chi_used=2,
        discarded_weight_loss=0.0,
    )

    first = hash_boundary_log(**kwargs)
    second = hash_boundary_log(**kwargs)

    assert first == second
    assert len(first) == 64
    assert all(c in "0123456789abcdef" for c in first)


def test_boundary_hash_changes_when_raw_float_changes():
    base = hash_boundary_log(
        boundary_id=BoundaryID.AH,
        singular_values_kept=(0.5,),
        singular_values_discarded=(),
        chi_used=1,
        discarded_weight_loss=0.75,
    )

    changed = hash_boundary_log(
        boundary_id=BoundaryID.AH,
        singular_values_kept=(0.5000000000001,),
        singular_values_discarded=(),
        chi_used=1,
        discarded_weight_loss=0.75,
    )

    assert base != changed
