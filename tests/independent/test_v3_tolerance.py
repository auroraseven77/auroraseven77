"""V3 — strict < 1e-9 tie tolerance."""
from __future__ import annotations

from TUU.tuu_core import CandidateEvaluation, calculate_swarm_consensus

from .reference import expected_tie_winner_index


def candidate(intent: str, score: float) -> CandidateEvaluation:
    return CandidateEvaluation(
        intent=intent,
        confidence=1.0,
        feasibility=1.0,
        historical_success=1.0,
        risk=0.0,
        score=score,
    )


def winner_intent(candidates: tuple[CandidateEvaluation, ...]) -> str:
    _, _, _, index = calculate_swarm_consensus(
        candidates, tau_k=0.0, s_min=0.0
    )
    return candidates[index].intent


def test_half_nanounit_delta_is_a_tie() -> None:
    candidates = (
        candidate("intent_beta", 0.8000000000),
        candidate("intent_alpha", 0.8000000005),
    )
    expected = expected_tie_winner_index(
        [c.intent for c in candidates],
        [c.score for c in candidates],
    )
    assert expected == 0
    assert winner_intent(candidates) == candidates[expected].intent


def test_exact_one_nanounit_delta_is_not_a_tie() -> None:
    candidates = (
        candidate("intent_beta", 0.8000000000),
        candidate("intent_alpha", 0.8000000010),
    )
    expected = expected_tie_winner_index(
        [c.intent for c in candidates],
        [c.score for c in candidates],
    )
    assert expected == 1
    assert winner_intent(candidates) == candidates[expected].intent


def test_two_nanounit_delta_is_not_a_tie() -> None:
    candidates = (
        candidate("intent_beta", 0.8000000000),
        candidate("intent_alpha", 0.8000000020),
    )
    expected = expected_tie_winner_index(
        [c.intent for c in candidates],
        [c.score for c in candidates],
    )
    assert expected == 1
    assert winner_intent(candidates) == candidates[expected].intent
