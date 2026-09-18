"""Integration tests for the TUU intent lifecycle."""

import pytest

from TUU.authorization import AuthorizationContext
from TUU.tuu_core import AgentMetricOutput, process_intent_lifecycle


@pytest.mark.asyncio
async def test_lifecycle_full_success_flow():
    metrics = [
        AgentMetricOutput(
            intent="echo Success",
            confidence=0.9,
            feasibility=0.9,
            historical_success=0.9,
            risk=0.1,
        ),
        AgentMetricOutput(
            intent="pwd",
            confidence=0.8,
            feasibility=0.8,
            historical_success=0.8,
            risk=0.2,
        ),
    ]

    result = await process_intent_lifecycle(
        metrics,
        authorization_context=AuthorizationContext(max_allowed_risk=0.5),
    )

    assert result.final_state == "completed"
    assert result.collapsed_candidate is not None
    assert result.collapsed_candidate.intent == "echo Success"
    assert result.authorization is not None
    assert result.authorization.status == "approved"
    assert result.execution is not None
    assert result.execution.executed is True
    assert "Success" in result.execution.stdout


@pytest.mark.asyncio
async def test_lifecycle_blocked_by_authorization():
    metrics = [
        AgentMetricOutput(
            intent="rm -rf /",
            confidence=0.95,
            feasibility=0.95,
            historical_success=0.95,
            risk=0.05,
        )
    ]

    result = await process_intent_lifecycle(metrics)

    assert result.final_state == "blocked"
    assert result.collapsed_candidate is not None
    assert result.collapsed_candidate.intent == "rm -rf /"
    assert result.authorization is not None
    assert result.authorization.status == "rejected"
    assert result.execution is None


@pytest.mark.asyncio
async def test_lifecycle_retained_in_resolving_low_entropy():
    metrics = [
        AgentMetricOutput(
            intent="echo A",
            confidence=0.8,
            feasibility=0.8,
            historical_success=0.8,
            risk=0.1,
        ),
        AgentMetricOutput(
            intent="echo B",
            confidence=0.1,
            feasibility=0.1,
            historical_success=0.1,
            risk=0.9,
        ),
    ]

    result = await process_intent_lifecycle(
        metrics,
        entropy_consensus_threshold=0.99,
    )

    assert result.final_state == "resolving"
    assert result.collapsed_candidate is None
    assert result.authorization is None
    assert result.execution is None
