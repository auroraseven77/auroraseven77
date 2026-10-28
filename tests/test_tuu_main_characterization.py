"""Characterization tests for TUU main as of 2026-10-28.

These tests intentionally describe current behavior, not a proposed replacement
contract. In particular, main currently uses exact score equality for SHA-256
tie-breaking and uses rounded H_N/K_N presentation values in the lifecycle gate.
If the normative policy changes, update these tests only after an explicit
contract decision and with independent boundary tests.
"""
from __future__ import annotations

import asyncio
import hashlib
import math
from unittest.mock import patch

import pytest

from TUU.authorization import AuthorizationContext
from TUU.tuu_core import (
    AgentMetricOutput,
    CandidateEvaluation,
    calculate_swarm_consensus,
    compute_candidate_evaluation,
    process_intent_lifecycle,
)


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
    _, _, _, index = calculate_swarm_consensus(candidates)
    assert index >= 0
    return candidates[index].intent


def test_main_rejects_negative_raw_candidate_score_instead_of_clamping() -> None:
    metrics = AgentMetricOutput(
        intent="rm",
        confidence=0.0,
        historical_success=0.0,
        feasibility=0.0,
        risk=1.0,
    )

    with pytest.raises(ValueError, match="Score negativo"):
        compute_candidate_evaluation("rm", metrics)


def test_exact_score_tie_uses_sha256_and_is_permutation_invariant() -> None:
    low_hash_intent = "intent_low"
    high_hash_intent = "intent_high"
    assert hashlib.sha256(low_hash_intent.encode("utf-8")).hexdigest() < (
        hashlib.sha256(high_hash_intent.encode("utf-8")).hexdigest()
    )

    first = (candidate(low_hash_intent, 0.8), candidate(high_hash_intent, 0.8))
    reversed_order = tuple(reversed(first))

    assert winner_intent(first) == low_hash_intent
    assert winner_intent(reversed_order) == low_hash_intent


@pytest.mark.parametrize("delta", [0.5e-9, 1.0e-9, 2.0e-9])
def test_main_near_tie_still_selects_strict_maximum(delta: float) -> None:
    """Characterizes current exact-equality behavior across the 1e-9 boundary.

    The lower score has the lexicographically smaller SHA-256 intent. Therefore,
    a future tolerance-based tie rule (< 1e-9) would select it only for the
    0.5e-9 case. This characterization deliberately records that current main
    selects the strictly larger numeric score in all three cases.
    """
    lower_score = 0.8
    higher_score = lower_score + delta
    assert lower_score < higher_score
    assert hashlib.sha256(b"intent_low").hexdigest() < hashlib.sha256(
        b"intent_high"
    ).hexdigest()

    candidates = (
        candidate("intent_low", lower_score),
        candidate("intent_high", higher_score),
    )

    assert winner_intent(candidates) == "intent_high"


def test_consensus_api_returns_rounded_presentation_values_not_raw_values() -> None:
    scores = (0.70000004, 0.29999996)
    candidates = (
        candidate("intent_high", scores[0]),
        candidate("intent_low", scores[1]),
    )

    total = sum(scores)
    probabilities = tuple(score / total for score in scores)
    raw_h_n = -sum(
        probability * math.log2(probability)
        for probability in probabilities
        if probability > 0.0
    ) / math.log2(len(scores))
    raw_k_n = 1.0 - raw_h_n

    h_n, k_n, selected_score, winner_index = calculate_swarm_consensus(candidates)

    assert winner_index == 0
    assert h_n == round(raw_h_n, 6)
    assert k_n == round(raw_k_n, 6)
    assert selected_score == round(scores[0], 4)
    assert not math.isclose(h_n, raw_h_n, rel_tol=0.0, abs_tol=1e-10)
    assert not math.isclose(k_n, raw_k_n, rel_tol=0.0, abs_tol=1e-10)
    assert selected_score != scores[0]


def test_lifecycle_gate_uses_rounded_kn_then_applies_authorization_gate() -> None:
    """A rounded K_N at the threshold proceeds to auth, but cannot bypass it."""
    metrics = [
        AgentMetricOutput(
            intent="rm",
            confidence=0.75,
            historical_success=0.0,
            feasibility=0.0,
            risk=0.0,
        ),
        AgentMetricOutput(
            intent="echo",
            confidence=0.25,
            historical_success=0.0,
            feasibility=0.0,
            risk=0.0,
        ),
    ]
    # Scores after the current main's four-decimal presentation are 0.3 and 0.1.
    raw_h_n = -sum(
        probability * math.log2(probability)
        for probability in (0.75, 0.25)
    ) / math.log2(2)
    raw_k_n = 1.0 - raw_h_n
    rounded_k_n = round(raw_k_n, 6)
    assert raw_k_n < rounded_k_n  # rounding moves K_N up to the configured boundary

    context = AuthorizationContext(allowed_commands=frozenset({"echo"}))
    with patch("TUU.tuu_core.execute_command_securely") as execute:
        result = asyncio.run(
            process_intent_lifecycle(
                metrics,
                authorization_context=context,
                entropy_consensus_threshold=rounded_k_n,
                s_min=0.0,
            )
        )

    assert any(event.state == "consensus" for event in result.events)
    assert result.final_state == "blocked"
    assert result.collapsed_candidate is not None
    assert result.collapsed_candidate.intent == "rm"
    assert result.authorization is not None
    assert result.authorization.status == "rejected"
    assert result.execution is None
    execute.assert_not_called()


def test_high_score_cannot_bypass_authorization_or_invoke_executor() -> None:
    metrics = [
        AgentMetricOutput(
            intent="rm",
            confidence=1.0,
            historical_success=1.0,
            feasibility=1.0,
            risk=0.0,
        )
    ]

    context = AuthorizationContext(allowed_commands=frozenset({"echo"}))
    with patch("TUU.tuu_core.execute_command_securely") as execute:
        result = asyncio.run(
            process_intent_lifecycle(
                metrics,
                authorization_context=context,
            )
        )

    assert result.collapsed_candidate is not None
    assert result.collapsed_candidate.score >= 0.5
    assert result.final_state == "blocked"
    assert result.authorization is not None
    assert result.authorization.status == "rejected"
    assert result.execution is None
    execute.assert_not_called()
