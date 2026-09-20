import numpy as np

from b1_motor.determinism import (
    build_raw_log,
    canonical_json,
    hash_raw_log,
)
from b1_motor.mps import svd_truncate


def test_svd_repeatability():
    matrix = np.array(
        [
            [4.0, 0.0, 0.0],
            [0.0, 3.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    result_a = svd_truncate(matrix, chi_max=2, step=11)
    result_b = svd_truncate(matrix, chi_max=2, step=11)

    ua, sa, vha, report_a = result_a
    ub, sb, vhb, report_b = result_b

    assert np.array_equal(ua, ub)
    assert np.array_equal(sa, sb)
    assert np.array_equal(vha, vhb)

    assert report_a == report_b


def test_canonical_json_is_key_order_independent():
    value_a = {
        "z": 3,
        "a": 1,
        "nested": {
            "y": 2,
            "x": 1,
        },
    }

    value_b = {
        "nested": {
            "x": 1,
            "y": 2,
        },
        "a": 1,
        "z": 3,
    }

    assert canonical_json(value_a) == canonical_json(value_b)


def test_raw_log_hash_is_reproducible():
    raw_a = build_raw_log(
        experiment_id="B1.2-64Q-VQE",
        execution_id="P2.2-001",
        matrix_shape=(4, 4),
        chi_max=2,
        step=11,
        singular_values=[4.0, 3.0],
        discarded_weight_loss=2.0,
    )

    raw_b = build_raw_log(
        experiment_id="B1.2-64Q-VQE",
        execution_id="P2.2-001",
        matrix_shape=(4, 4),
        chi_max=2,
        step=11,
        singular_values=[4.0, 3.0],
        discarded_weight_loss=2.0,
    )

    assert raw_a == raw_b
    assert hash_raw_log(raw_a) == hash_raw_log(raw_b)


def test_raw_log_hash_changes_when_result_changes():
    raw_a = build_raw_log(
        experiment_id="B1.2-64Q-VQE",
        execution_id="P2.2-001",
        matrix_shape=(4, 4),
        chi_max=2,
        step=11,
        singular_values=[4.0, 3.0],
        discarded_weight_loss=2.0,
    )

    raw_b = build_raw_log(
        experiment_id="B1.2-64Q-VQE",
        execution_id="P2.2-001",
        matrix_shape=(4, 4),
        chi_max=2,
        step=11,
        singular_values=[4.0, 3.0],
        discarded_weight_loss=2.000001,
    )

    assert hash_raw_log(raw_a) != hash_raw_log(raw_b)


def test_timestamp_is_not_part_of_raw_log_hash():
    raw = build_raw_log(
        experiment_id="B1.2-64Q-VQE",
        execution_id="P2.2-001",
        matrix_shape=(4, 4),
        chi_max=2,
        step=11,
        singular_values=[4.0, 3.0],
        discarded_weight_loss=2.0,
    )

    hash_before = hash_raw_log(raw)

    telemetry = dict(raw)
    telemetry["timestamp"] = "2026-09-19T23:59:59Z"

    assert hash_raw_log(telemetry) != hash_before
    assert hash_raw_log(raw) == hash_before
