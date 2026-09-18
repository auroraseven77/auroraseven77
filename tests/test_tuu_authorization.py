"""tests/test_tuu_authorization.py - Testes da fronteira de autorização."""

import pytest
from pydantic import ValidationError

from TUU.authorization import (
    AuthorizationContext,
    AuthorizationDecision,
    evaluate_authorization,
)
from TUU.tuu_core import CandidateEvaluation


def make_candidate(intent: str, risk: float = 0.10) -> CandidateEvaluation:
    return CandidateEvaluation(
        intent=intent,
        confidence=0.90,
        feasibility=0.90,
        historical_success=0.90,
        risk=risk,
        score=0.80,
    )


def test_authorization_decision_is_frozen():
    decision = AuthorizationDecision(
        intent="ls",
        status="approved",
        policy_evaluated="strict_local_policy",
        reason="ok",
    )

    with pytest.raises(ValidationError):
        decision.status = "rejected"


def test_authorization_decision_deep_immutability():
    """Garante que objeto e mapa interno de metadata sejam imutáveis."""
    decision = AuthorizationDecision(
        intent="ls",
        status="approved",
        policy_evaluated="strict_local_policy",
        reason="ok",
        metadata={"execution_id": "123"},
    )

    with pytest.raises(ValidationError):
        decision.status = "rejected"

    with pytest.raises(TypeError):
        decision.metadata["tampered"] = True


def test_authorization_rejects_command_outside_allowlist():
    decision = evaluate_authorization(
        make_candidate("rm"),
        AuthorizationContext(),
    )

    assert decision.status == "rejected"
    assert decision.policy_evaluated == "allowlist_policy"


def test_authorization_rejects_risk_above_threshold():
    decision = evaluate_authorization(
        make_candidate("ls", risk=0.51),
        AuthorizationContext(max_allowed_risk=0.50),
    )

    assert decision.status == "rejected"
    assert decision.policy_evaluated == "risk_threshold_policy"


def test_authorization_approves_allowed_low_risk_command():
    decision = evaluate_authorization(
        make_candidate("ls", risk=0.10),
        AuthorizationContext(),
    )

    assert decision.status == "approved"
    assert decision.policy_evaluated == "strict_local_policy"
