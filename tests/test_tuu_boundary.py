"""
tests/test_tuu_boundary.py
===========================
Suíte de testes de validação da fronteira epistêmica entre Agent Swarm e TUU Core.
Garante a imunidade contra injeção de score e a integridade da entropia.
"""

import asyncio

import pytest
from pydantic import ValidationError

from TUU.tuu_core import (
    AgentMetricOutput,
    CandidateEvaluation,
    compute_candidate_evaluation,
)
from Tuu_panel.circuit_breaker import calculate_normalized_entropy


def test_agent_metric_output_forbids_extra_fields():
    """Garante que extra='forbid' rejeite injeções de score pelos agentes."""
    with pytest.raises(ValidationError):
        AgentMetricOutput.model_validate({
            "confidence": 0.9,
            "feasibility": 0.8,
            "historical_success": 0.8,
            "risk": 0.1,
            "score": 0.99,
        })


def test_compute_candidate_evaluation_deterministic_score():
    """Valida S_i = 0.4C + 0.2H + 0.3V - 0.1R."""
    metrics = AgentMetricOutput(
        confidence=1.0,
        historical_success=1.0,
        feasibility=1.0,
        risk=0.0,
    )
    candidate = compute_candidate_evaluation("ls", metrics)

    assert pytest.approx(candidate.score, 0.0001) == 0.9
    assert isinstance(candidate, CandidateEvaluation)


def test_compute_candidate_evaluation_rejects_negative_score():
    """Valida a rejeição de S_i negativo para C=H=V=0, R=1."""
    metrics = AgentMetricOutput(
        confidence=0.0,
        historical_success=0.0,
        feasibility=0.0,
        risk=1.0,
    )
    with pytest.raises(ValueError, match="Score negativo"):
        compute_candidate_evaluation("unauthorized_cmd", metrics)


def test_circuit_breaker_consumes_canonical_candidate_evaluation():
    """Valida consumo do CandidateEvaluation canônico e H_N."""
    m1 = AgentMetricOutput(
        confidence=0.94,
        feasibility=0.90,
        historical_success=0.94,
        risk=0.08,
    )
    m2 = AgentMetricOutput(
        confidence=0.03,
        feasibility=0.35,
        historical_success=0.40,
        risk=0.75,
    )
    m3 = m2

    c1 = compute_candidate_evaluation("date", m1)
    c2 = compute_candidate_evaluation("pwd", m2)
    c3 = compute_candidate_evaluation("whoami", m3)

    entropy, h_n = calculate_normalized_entropy([c1, c2, c3])

    assert entropy > 0.0
    assert 0.0 <= h_n <= 1.0
    assert pytest.approx(h_n, 0.0001) == 0.63258


@pytest.mark.asyncio
async def test_swarm_async_dry_run_fan_in():
    """
    Valida fan-out assíncrono e computação determinística de S_i no fan-in.

    Os agentes retornam somente AgentMetricOutput; a computação de score ocorre
    exclusivamente depois do gather(), no TUU Core.
    """

    async def agent_eval(conf: float) -> AgentMetricOutput:
        await asyncio.sleep(0.01)
        return AgentMetricOutput(
            confidence=conf,
            feasibility=0.9,
            historical_success=0.8,
            risk=0.1,
        )

    candidates_raw = [("ls", 0.8), ("pwd", 0.1), ("date", 0.1)]
    metrics = await asyncio.gather(*(agent_eval(conf) for _, conf in candidates_raw))
    evaluations = [
        compute_candidate_evaluation(intent, metric)
        for (intent, _), metric in zip(candidates_raw, metrics)
    ]

    assert len(evaluations) == 3
    assert all(isinstance(e, CandidateEvaluation) for e in evaluations)
    assert max(evaluations, key=lambda x: x.score).intent == "ls"
