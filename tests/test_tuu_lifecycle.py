"""Integration tests for the TUU intent lifecycle."""

import hashlib
from unittest.mock import patch

import pytest

from TUU.tuu_core import (
    AgentMetricOutput,
    AuthorizationContext,
    AuthorizationDecision,
    ExecutionResult,
    calculate_swarm_consensus,
    compute_candidate_evaluation,
    process_intent_lifecycle,
)


@pytest.fixture
def dummy_context():
    return AuthorizationContext(
        user_id="operator_01",
        allowed_commands={"deploy_service"},
    )


def create_metric(
    intent: str,
    confidence: float = 0.9,
    historical_success: float = 0.9,
) -> AgentMetricOutput:
    return AgentMetricOutput(
        intent=intent,
        confidence=confidence,
        feasibility=0.9,
        historical_success=historical_success,
        risk=0.1,
    )


def test_sha256_tie_break_selection():
    """Valida se o desempate seleciona a menor hash SHA-256."""
    m1 = create_metric("intent_beta", confidence=0.8)
    m2 = create_metric("intent_alpha", confidence=0.8)

    c1 = compute_candidate_evaluation(m1.intent, m1)
    c2 = compute_candidate_evaluation(m2.intent, m2)

    hash_beta = hashlib.sha256("intent_beta".encode("utf-8")).hexdigest()
    hash_alpha = hashlib.sha256("intent_alpha".encode("utf-8")).hexdigest()

    expected_winner = "intent_beta" if hash_beta < hash_alpha else "intent_alpha"

    _, _, _, i_star = calculate_swarm_consensus(
        (c1, c2),
        tau_k=0.0,
        s_min=0.0,
    )

    assert (c1, c2)[i_star].intent == expected_winner


@pytest.mark.asyncio
async def test_full_lifecycle_execution(dummy_context):
    """
    Testa o pipeline completo com polarização de scores suficiente
    para garantir K_N >= 0.25 e atingir 'completed'.
    """
    metrics = [
        create_metric("deploy_service", confidence=1.0, historical_success=1.0),
        create_metric("deploy_service", confidence=0.95, historical_success=0.9),
        AgentMetricOutput(
            intent="alternative_cmd",
            confidence=0.0,
            feasibility=0.5,
            historical_success=0.0,
            risk=1.0,
        ),
    ]

    mock_auth = AuthorizationDecision(
        status="approved",
        reason="Policy pass",
        intent="deploy_service",
        policy_evaluated="default_policy",
    )

    mock_exec = ExecutionResult(
        intent="deploy_service",
        executed=True,
        returncode=0,
        stdout="Success",
        stderr="",
    )

    with patch("TUU.tuu_core.evaluate_authorization", return_value=mock_auth), \
        patch("TUU.tuu_core.execute_command_securely", return_value=mock_exec):

        result = await process_intent_lifecycle(
            metrics=metrics,
            authorization_context=dummy_context,
            entropy_consensus_threshold=0.25,
            s_min=0.50,
            timeout=5.0,
        )

        assert result.final_state == "completed"
        assert result.collapsed_candidate is not None
        assert result.collapsed_candidate.intent == "deploy_service"
        assert result.authorization is not None
        assert result.authorization.status == "approved"
        assert result.execution is not None
        assert result.execution.intent == "deploy_service"
        assert result.execution.returncode == 0


@pytest.mark.asyncio
async def test_lifecycle_retained_in_resolving_due_to_entropy(dummy_context):
    """
    Valida que propostas com scores quase idênticos (altamente entrópicas,
    K_N próximo de 0) são corretamente retidas em 'resolving'.
    """
    metrics = [
        create_metric("deploy_service", confidence=0.90),
        create_metric("deploy_service", confidence=0.89),
    ]

    result = await process_intent_lifecycle(
        metrics=metrics,
        authorization_context=dummy_context,
        entropy_consensus_threshold=0.25,
        s_min=0.50,
    )

    assert result.final_state == "resolving"
    assert result.collapsed_candidate is None
    assert result.authorization is None
