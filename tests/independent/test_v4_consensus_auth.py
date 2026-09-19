"""V4 — consensus is descriptive; authorization remains normative."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from TUU.tuu_core import AgentMetricOutput, AuthorizationContext, process_intent_lifecycle


def metric(intent: str, confidence: float) -> AgentMetricOutput:
    return AgentMetricOutput(
        intent=intent,
        confidence=confidence,
        feasibility=0.9,
        historical_success=0.9,
        risk=0.1,
    )


@pytest.mark.asyncio
async def test_consensus_does_not_bypass_authorization() -> None:
    metrics = [
        metric("rm", 1.0),
        metric("echo", 0.1),
        metric("pwd", 0.1),
    ]

    context = AuthorizationContext(
        allowed_commands=frozenset({"echo", "pwd", "date", "ls", "uname", "whoami", "ping"})
    )

    with patch(
        "TUU.tuu_core.execute_command_securely",
        side_effect=AssertionError("executor must not run after authorization rejection"),
    ):
        result = await process_intent_lifecycle(
            metrics,
            authorization_context=context,
            entropy_consensus_threshold=0.25,
            s_min=0.50,
        )

    assert result.final_state == "blocked"
    assert result.collapsed_candidate is not None
    assert result.collapsed_candidate.intent == "rm"
    assert result.authorization is not None
    assert result.authorization.status == "rejected"
    assert result.authorization.policy_evaluated == "allowlist_policy"
    assert any(event.state == "consensus" for event in result.events)
