from b1_motor.hamiltonian_b12 import (
    TFIMSignConvention,
    build_b12_hamiltonian,
)


def test_b12_hamiltonian_shape_and_agent_boundaries():
    hamiltonian = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        )
    )
    assert len(hamiltonian.terms) == 64 + 63 + 2

    boundary_terms = [
        term
        for term in hamiltonian.terms
        if term.sites in ((21, 22), (43, 44))
    ]
    assert [term.coefficient for term in boundary_terms] == [
        0.5 + 0j,
        0.5 + 0j,
    ]
    assert all(term.operators == ("Z", "Z") for term in boundary_terms)


def test_b12_signs_are_explicit():
    plus = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=1,
            field_sign=1,
        )
    )
    minus = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        )
    )
    assert plus.terms[0].coefficient == 1.0 + 0j
    assert plus.terms[63].coefficient == 1.0 + 0j
    assert minus.terms[0].coefficient == -1.0 + 0j
    assert minus.terms[63].coefficient == -1.0 + 0j


def test_b12_requires_an_explicit_sign_convention():
    import pytest

    with pytest.raises(TypeError):
        build_b12_hamiltonian()
