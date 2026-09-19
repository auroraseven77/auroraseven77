"""
tests/test_tuu_execution.py
============================
Suíte de testes da camada de execução isolada (TUU/execution.py).
"""

import pytest
from pydantic import ValidationError

from TUU.authorization import AuthorizationDecision
from TUU.execution import ExecutionResult, execute_command_securely


def test_execution_success_echo():
    decision = AuthorizationDecision(
        intent="echo Hello TUU Core",
        status="approved",
        policy_evaluated="strict_local_policy",
        reason="Aprovado em teste",
    )
    result = execute_command_securely(decision)
    assert result.executed is True
    assert result.returncode == 0
    assert "Hello TUU Core" in result.stdout
    assert result.error_message is None


def test_execution_unapproved_decision_raises():
    decision = AuthorizationDecision(
        intent="ls",
        status="rejected",
        policy_evaluated="risk_threshold_policy",
        reason="Risco alto",
    )
    with pytest.raises(PermissionError) as exc_info:
        execute_command_securely(decision)
    assert "status 'rejected'" in str(exc_info.value)


def test_execution_disallowed_binary_defense_in_depth():
    decision = AuthorizationDecision(
        intent="cat /etc/passwd",
        status="approved",
        policy_evaluated="bypassed_policy",
        reason="Erro hipotético",
    )
    with pytest.raises(PermissionError) as exc_info:
        execute_command_securely(decision)
    assert "não consta na allowlist" in str(exc_info.value)


def test_execution_timeout_handling():
    decision = AuthorizationDecision(
        intent="ping 127.0.0.1",
        status="approved",
        policy_evaluated="strict_local_policy",
        reason="Teste de timeout",
    )
    result = execute_command_securely(decision, timeout=0.05)
    assert result.executed is False
    assert result.returncode == -1
    assert "Timeout atingido" in result.error_message


def test_execution_result_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ExecutionResult.model_validate({
            "intent": "echo test",
            "executed": True,
            "returncode": 0,
            "stdout": "test\n",
            "stderr": "",
            "unauthorized_field": "hack",
        })


def test_execution_result_is_frozen():
    result = ExecutionResult(
        intent="pwd",
        executed=True,
        returncode=0,
        stdout="/root\n",
        stderr="",
    )
    with pytest.raises(ValidationError):
        result.returncode = 1
