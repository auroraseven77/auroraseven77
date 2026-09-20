import numpy as np
import pytest

from b1_motor.mps import svd_truncate


def test_svd_truncation_exact_loss():
    singular_values = np.array(
        [4.0, 3.0, 2.0, 1.0],
        dtype=np.float64,
    )
    matrix = np.diag(singular_values)

    _, kept, _, report = svd_truncate(
        matrix,
        chi_max=2,
        step=7,
    )

    expected_loss = 2.0**2 + 1.0**2

    assert np.allclose(
        kept,
        [4.0, 3.0],
        rtol=0.0,
        atol=1e-12,
    )
    assert report.step == 7
    assert report.bond_dimension_before == 4
    assert report.bond_dimension_after == 2
    assert report.chi_max_cap == 2
    assert np.isclose(
        report.discarded_weight_loss,
        expected_loss,
        rtol=0.0,
        atol=1e-12,
    )


def test_svd_without_truncation_has_zero_loss():
    matrix = np.diag(
        np.array(
            [4.0, 3.0, 2.0],
            dtype=np.float64,
        )
    )

    _, kept, _, report = svd_truncate(
        matrix,
        chi_max=3,
    )

    assert len(kept) == 3
    assert report.bond_dimension_before == 3
    assert report.bond_dimension_after == 3
    assert report.discarded_weight_loss == 0.0


def test_svd_hard_cap_rejects_129():
    matrix = np.eye(2)

    with pytest.raises(ValueError):
        svd_truncate(matrix, chi_max=129)


def test_svd_rejects_invalid_matrix_rank():
    matrix = np.ones((2, 2, 2))

    with pytest.raises(ValueError):
        svd_truncate(matrix, chi_max=2)


def test_svd_rejects_empty_matrix():
    matrix = np.empty((0, 2))

    with pytest.raises(ValueError):
        svd_truncate(matrix, chi_max=2)


def test_svd_rejects_negative_step():
    matrix = np.eye(2)

    with pytest.raises(ValueError):
        svd_truncate(matrix, chi_max=2, step=-1)
