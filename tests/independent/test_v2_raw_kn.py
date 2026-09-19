"""V2 — RAW probability/H_N/K_N evidence before presentation rounding."""
from __future__ import annotations

import asyncio

import pytest

from TUU.tuu_core import AgentMetricOutput, process_intent_lifecycle

from .reference import concentration_kn, find_key, normalized_entropy


def metric(intent: str, confidence: float) -> AgentMetricOutput:
    return AgentMetricOutput(
        intent=intent,
        confidence=confidence,
        feasibility=0.9,
        historical_success=0.9,
        risk=0.1,
    )


def test_runtime_exposes_raw_probability_vector_and_kn() -> None:
    """The contract requires raw evidence; rounded UI fields are insufficient."""
    result = asyncio.run(
        process_intent_lifecycle(
            [
                metric("echo", 0.94),
                metric("pwd", 0.03),
                metric("date", 0.03),
            ],
            entropy_consensus_threshold=0.0,
            s_min=0.0,
        )
    )
    payload = result.model_dump(mode="python")

    probabilities = find_key(payload, "probabilities_raw")
    h_raw = find_key(payload, "h_n_raw")
    k_raw = find_key(payload, "k_n_raw")

    assert probabilities is not None, (
        "V2 FAIL: runtime exposes no probabilities_raw field; "
        "a rounded H_N/K_N value cannot prove a pre-rounding invariant."
    )
    assert h_raw is not None, "V2 FAIL: runtime exposes no h_n_raw evidence."
    assert k_raw is not None, "V2 FAIL: runtime exposes no k_n_raw evidence."

    assert len(probabilities) == 3
    scores = [0.0, 0.0, 0.0]
    for candidate in result.candidates:
        index = {"echo": 0, "pwd": 1, "date": 2}[candidate.intent]
        scores[index] = candidate.score

    expected_h = normalized_entropy(scores)
    expected_k = concentration_kn(scores)

    assert h_raw == pytest.approx(expected_h, rel=0.0, abs=1e-12)
    assert k_raw == pytest.approx(expected_k, rel=0.0, abs=1e-12)
    assert sum(probabilities) == pytest.approx(1.0, rel=0.0, abs=1e-12)
