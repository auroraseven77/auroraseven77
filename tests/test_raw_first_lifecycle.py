"""Regression tests for raw-first TUU consensus and authorization gates."""

import pytest

from TUU.tuu_core import (
    AgentMetricOutput,
    compute_candidate_evaluation,
    process_intent_lifecycle,
)


def metric(
    intent: str,
    *,
    confidence: float,
    feasibility: float = 0.5,
    historical_success: float = 0.5,
    risk: float = 0.0,
) -> AgentMetricOutput:
    return AgentMetricOutput(
        intent=intent,
        confidence=confidence,
        feasibility=feasibility,
        historical_success=historical_success,
        risk=risk,
    )


def test_candidate_score_preserves_raw_precision():
    candidate = compute_candidate_evaluation(
        "candidate",
        metric(
            "candidate",
            confidence=0.500001,
            feasibility=0.500001,
            historical_success=0.500001,
        ),
    )

    # 0.4*confidence + 0.2*history + 0.3*feasibility = 0.4500009.
    assert candidate.score == pytest.approx(0.4500009, abs=1e-15)
    assert candidate.score != round(candidate.score, 4)


@pytest.mark.asyncio
async def test_single_candidate_below_score_gate_cannot_reach_authorization(
    monkeypatch,
):
    def forbidden_authorization(*args, **kwargs):
        pytest.fail("low-score candidate must not reach authorization")

    def forbidden_execution(*args, **kwargs):
        pytest.fail("low-score candidate must not reach execution")

    monkeypatch.setattr(
        "TUU.tuu_core.evaluate_authorization", forbidden_authorization
    )
    monkeypatch.setattr(
        "TUU.tuu_core.execute_command_securely", forbidden_execution
    )

    result = await process_intent_lifecycle(
        [metric(
            "candidate",
            confidence=0.5,
            feasibility=0.5,
            historical_success=0.5,
            risk=0.0,
        )],
        s_min=0.5,
    )

    assert result.final_state == "resolving"
    assert result.collapsed_candidate is None
    assert result.authorization is None
    assert result.execution is None
    assert result.k_n_raw == pytest.approx(1.0)
    assert result.candidates[0].score == pytest.approx(0.45)
