import pytest

from b1_motor.ansatz_b12 import SymmetricVQEAnsatz


def test_linear_cx_topology_is_explicit_and_closed():
    ansatz = SymmetricVQEAnsatz(n_qubits=6)
    assert ansatz.rotation_order == ("RY", "RZ")
    assert ansatz.cx_pairs == (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
    )
    assert ansatz.cx_orientation == "lower_to_higher"
    assert ansatz.entangler_placement == "after_rotations"


@pytest.mark.parametrize("n_qubits", [2, 4, 6, 64])
def test_cx_count_per_layer_is_open_chain(n_qubits):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    assert len(ansatz.cx_pairs) == n_qubits - 1


def test_b12_cx_topology_boundaries():
    ansatz = SymmetricVQEAnsatz()
    assert ansatz.cx_pairs[0] == (0, 1)
    assert ansatz.cx_pairs[-1] == (62, 63)
    assert len(ansatz.cx_pairs) == 63
