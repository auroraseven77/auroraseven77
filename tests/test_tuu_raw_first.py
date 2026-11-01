"""Regression tests for RAW-first TUU consensus and lifecycle gates.

Base: main a3f51c544400ce1be49dc2b098d4b6a7600bd5b9 (2026-10-28).
These tests intentionally preserve the existing negative-score rejection and
exact-equality SHA-256 tie contract. No tolerance-based tie rule is introduced
in this change.
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
    _calculate_swarm_consensus_raw,
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


def metric(
    intent: str,
    *,
    confidence: float = 0.0,
    historical_success: float = 0.0,
    feasibility: float = 0.0,
    risk: float = 0.0,
) -> AgentMetricOutput:
    return AgentMetricOutput(
        intent=intent,
        confidence=confidence,
        historical_success=historical_success,
        feasibility=feasibility,
        risk=risk,
    )


def raw_entropy(scores: tuple[float, ...]) -> tuple[tuple[float, ...], float, float]:
    total = math.fsum(scores)
    if len(scores) == 1:
        probabilities = (1.0,)
        h_n = 0.0
    elif total <= 0.0:
        probabilities = tuple(1.0 / len(scores) for _ in scores)
        h_n = 1.0
    else:
        probabilities = tuple(score / total for score in scores)
        entropy = -math.fsum(
            p * math.log2(p) for p in probabilities if p > 0.0
        )
        h_n = entropy / math.log2(len(scores))
    return probabilities, h_n, 1.0 - h_n


def test_negative_raw_score_is_still_rejected() -> None:
    metrics = metric("rm", confidence=0.0, historical_success=0.0, feasibility=0.0, risk=1.0)

    with pytest.raises(ValueError, match="Score negativo"):
        compute_candidate_evaluation("rm", metrics)


def test_candidate_score_retains_raw_precision_after_negative_guard() -> None:
    metrics = metric(
        "echo",
        confidence=0.8888,
        historical_success=0.7777,
        feasibility=0.6666,
        risk=0.1111,
    )
    expected_raw = (
        0.4 * metrics.confidence
        + 0.2 * metrics.historical_success
        + 0.3 * metrics.feasibility
        - 0.1 * metrics.risk
    )

    result = compute_candidate_evaluation("echo", metrics)

    assert expected_raw == pytest.approx(0.69993, abs=1e-15)
    assert result.score == expected_raw
    assert result.score != round(expected_raw, 4)


def test_raw_consensus_exposes_probabilities_h_n_and_k_n_before_rounding() -> None:
    scores = (0.70000004, 0.29999996)
    candidates = (
        candidate("intent_high", scores[0]),
        candidate("intent_low", scores[1]),
    )
    expected_probabilities, expected_h_n, expected_k_n = raw_entropy(scores)

    h_n_raw, k_n_raw, probabilities_raw, selected_score_raw, winner_index = (
        _calculate_swarm_consensus_raw(candidates)
    )

    assert probabilities_raw == pytest.approx(expected_probabilities, abs=1e-15)
    assert sum(probabilities_raw) == pytest.approx(1.0, abs=1e-15)
    assert h_n_raw == pytest.approx(expected_h_n, abs=1e-15)
    assert k_n_raw == pytest.approx(expected_k_n, abs=1e-15)
    assert selected_score_raw == scores[0]
    assert winner_index == 0
    assert h_n_raw != round(h_n_raw, 6)
    assert k_n_raw != round(k_n_raw, 6)


def test_public_consensus_tuple_remains_rounded_for_compatibility() -> None:
    candidates = (
        candidate("intent_high", 0.70000004),
        candidate("intent_low", 0.29999996),
    )
    h_n_raw, k_n_raw, _, selected_score_raw, raw_winner = (
        _calculate_swarm_consensus_raw(candidates)
    )

    h_n, k_n, selected_score, winner = calculate_swarm_consensus(candidates)

    assert winner == raw_winner
    assert h_n == round(h_n_raw, 6)
    assert k_n == round(k_n_raw, 6)
    assert selected_score == round(selected_score_raw, 4)


def test_lifecycle_gate_uses_raw_k_n_not_rounded_presentation_value() -> None:
    metrics = [
        metric("rm", confidence=0.75),
        metric("echo", confidence=0.25),
    ]
    computed_scores = tuple(
        compute_candidate_evaluation(item.intent, item).score for item in metrics
    )
    _, _, raw_k_n = raw_entropy(computed_scores)
    rounded_k_n = round(raw_k_n, 6)
    assert raw_k_n < rounded_k_n

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

    assert result.final_state == "resolving"
    assert result.h_n_raw == pytest.approx(1.0 - raw_k_n, abs=1e-15)
    assert result.k_n_raw == pytest.approx(raw_k_n, abs=1e-15)
    assert result.k_n_raw < rounded_k_n
    assert result.entropy_normalized == round(result.h_n_raw, 6)
    assert result.authorization is None
    assert result.execution is None
    execute.assert_not_called()


def test_lifecycle_gate_uses_raw_selected_score_not_rounded_score() -> None:
    # S_raw = 0.4*1.0 + 0.2*0.499995 = 0.499999, which displays as 0.5000.
    metrics = [metric("echo", confidence=1.0, historical_success=0.499995)]

    context = AuthorizationContext(allowed_commands=frozenset({"echo"}))
    with patch("TUU.tuu_core.execute_command_securely") as execute:
        result = asyncio.run(
            process_intent_lifecycle(
                metrics,
                authorization_context=context,
                entropy_consensus_threshold=0.25,
                s_min=0.5,
            )
        )

    assert result.candidates[0].score == pytest.approx(0.499999, abs=1e-15)
    assert round(result.candidates[0].score, 4) == 0.5
    assert result.final_state == "resolving"
    assert result.authorization is None
    assert result.execution is None
    execute.assert_not_called()


def test_exact_score_tie_remains_sha256_deterministic_and_order_independent() -> None:
    low_hash_intent = "intent_low"
    high_hash_intent = "intent_high"
    assert hashlib.sha256(low_hash_intent.encode()).hexdigest() < (
        hashlib.sha256(high_hash_intent.encode()).hexdigest()
    )

    pair = (
        candidate(low_hash_intent, 0.8),
        candidate(high_hash_intent, 0.8),
    )
    first = _calculate_swarm_consensus_raw(pair)
    second = _calculate_swarm_consensus_raw(tuple(reversed(pair)))

    assert pair[first[4]].intent == low_hash_intent
    reversed_pair = tuple(reversed(pair))
    assert reversed_pair[second[4]].intent == low_hash_intent


def test_high_score_does_not_bypass_authorization_or_execute_rejected_intent() -> None:
    metrics = [
        metric(
            "rm",
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

    assert result.candidates[0].score == pytest.approx(0.9, abs=1e-15)
    assert result.final_state == "blocked"
    assert result.authorization is not None
    assert result.authorization.status == "rejected"
    assert result.execution is None
    execute.assert_not_called()
