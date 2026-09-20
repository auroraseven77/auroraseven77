"""V1 — semantic permutation invariance of swarm collapse."""
from __future__ import annotations

import itertools

from TUU.tuu_core import CandidateEvaluation, calculate_swarm_consensus

from .reference import concentration_kn, normalized_entropy, sha256_intent


def candidate(intent: str, score: float) -> CandidateEvaluation:
    return CandidateEvaluation(
        intent=intent,
        confidence=1.0,
        feasibility=1.0,
        historical_success=1.0,
        risk=0.0,
        score=score,
    )


def test_all_arrival_order_permutations_have_same_semantic_result() -> None:
    candidates = (
        candidate("echo", 0.88),
        candidate("pwd", 0.22),
        candidate("date", 0.12),
    )

    expected_h = normalized_entropy([0.88, 0.22, 0.12])
    expected_k = concentration_kn([0.88, 0.22, 0.12])
    expected_intent = min(
        (item.intent for item in candidates),
        key=sha256_intent,
    )

    observed = []
    for permutation in itertools.permutations(candidates):
        h_n, k_n, selected_score, winner_index = calculate_swarm_consensus(
            permutation, tau_k=0.25, s_min=0.50
        )
        winner = permutation[winner_index]
        state = (
            "consensus"
            if k_n >= 0.25 and selected_score >= 0.50
            else "resolving"
        )
        observed.append((winner.intent, state, h_n, k_n, selected_score))

    assert all(item[0] == expected_intent for item in observed)
    assert all(item[1] == "consensus" for item in observed)
    assert all(item[2] == round(expected_h, 6) for item in observed)
    assert all(item[3] == round(expected_k, 6) for item in observed)
    assert all(item[4] == 0.88 for item in observed)
