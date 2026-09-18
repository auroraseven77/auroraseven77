"""Adversarial regression tests for TUU v2.1 invariants."""

import hashlib

import pytest

from TUU.tuu_core import CandidateEvaluation
from TUU.invariant_engine import InvariantEngine, InvariantViolationError


def candidate(intent: str, score: float) -> CandidateEvaluation:
    return CandidateEvaluation(
        intent=intent,
        confidence=1.0,
        feasibility=1.0,
        historical_success=1.0,
        risk=0.0,
        score=score,
    )


def test_math_invariant_accepts_exact_relation():
    InvariantEngine.validate_math_invariant(0.482, 0.518)


def test_math_invariant_rejects_wrong_relation():
    with pytest.raises(InvariantViolationError):
        InvariantEngine.validate_math_invariant(0.482, 0.25)


@pytest.mark.parametrize(
    ("k_n", "score", "expected"),
    [
        (0.25, 0.50, "consensus"),
        (0.24999, 0.50, "resolving"),
        (0.25001, 0.50, "consensus"),
        (0.25, 0.49999, "resolving"),
        (0.25, 0.50001, "consensus"),
    ],
)
def test_inclusive_decision_boundaries(k_n, score, expected):
    InvariantEngine.validate_decision_invariant(
        expected, k_n, score, tau_k=0.25, s_min=0.50
    )


def test_decision_invariant_rejects_entropy_style_inversion():
    with pytest.raises(InvariantViolationError):
        InvariantEngine.validate_decision_invariant(
            "resolving", k_n=1.0, selected_score=0.9
        )


def test_sha256_tie_break_is_order_independent():
    a = candidate("intent_alpha", 0.80)
    b = candidate("intent_beta", 0.80)
    original = (a, b)
    permuted = (b, a)

    expected_intent = min(
        (a.intent, b.intent),
        key=lambda intent: hashlib.sha256(intent.encode("utf-8")).hexdigest(),
    )

    InvariantEngine.validate_determinism_invariant(
        original, 0 if original[0].intent == expected_intent else 1
    )
    InvariantEngine.validate_determinism_invariant(
        permuted, 0 if permuted[0].intent == expected_intent else 1
    )


def test_near_tie_uses_declared_tolerance():
    a = candidate("intent_alpha", 0.8000000000)
    b = candidate("intent_beta", 0.8000000005)
    expected = min(
        (a, b),
        key=lambda c: hashlib.sha256(c.intent.encode("utf-8")).hexdigest(),
    )
    selected = 0 if a.intent == expected.intent else 1
    InvariantEngine.validate_determinism_invariant(
        (a, b), selected, tie_tolerance=1e-9
    )


def test_non_tie_must_not_use_sha256_to_override_maximum():
    a = candidate("intent_alpha", 0.70)
    b = candidate("intent_beta", 0.80)
    with pytest.raises(InvariantViolationError):
        InvariantEngine.validate_determinism_invariant((a, b), 0)


def test_empty_candidates_are_rejected_by_determinism_validator():
    with pytest.raises(InvariantViolationError):
        InvariantEngine.validate_determinism_invariant((), 0)
