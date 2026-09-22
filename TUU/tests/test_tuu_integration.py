"""Production integration contract tests for TUU invariants T1-T6."""
import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tuu_core import AgentMetricOutput, process_intent_lifecycle
from authorization import AuthorizationContext
from tuu_core import TUUCore
from tuu_executor import SandboxExecutor
from tuu_policy import AuthorizedRequest, PolicyDecision, PolicyEngine


class TuuIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = PolicyEngine()
        self.executor = SandboxExecutor()
        self.core = TUUCore(self.policy, self.executor)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_t2_deny_means_zero_executor_invocations(self):
        metrics = [
            AgentMetricOutput(
                intent="rm",
                confidence=0.9,
                feasibility=0.9,
                historical_success=0.9,
                risk=0.1,
            )
        ]

        result = self.run_async(
            process_intent_lifecycle(
                metrics=metrics,
                authorization_context=AuthorizationContext(
                    user_id="operator_01",
                    allowed_commands=frozenset({"echo"}),
                ),
                entropy_consensus_threshold=0.25,
                s_min=0.50,
                timeout=5.0,
            )
        )

        self.assertEqual(result.final_state, "blocked")
        self.assertIsNotNone(result.authorization)
        self.assertEqual(result.authorization.status, "rejected")
        self.assertEqual(
            result.authorization.policy_evaluated,
            "allowlist_policy",
        )
        self.assertIsNone(result.execution)

    def test_t3_high_analytical_risk_cannot_override_policy(self):
        metrics = [
            AgentMetricOutput(
                intent="echo",
                confidence=0.9,
                feasibility=0.9,
                historical_success=0.9,
                risk=0.95,
            )
        ]

        result = self.run_async(
            process_intent_lifecycle(
                metrics=metrics,
                authorization_context=AuthorizationContext(
                    user_id="operator_01",
                    max_allowed_risk=0.50,
                ),
                entropy_consensus_threshold=0.25,
                s_min=0.50,
                timeout=5.0,
            )
        )

        self.assertEqual(result.final_state, "blocked")
        self.assertIsNotNone(result.authorization)
        self.assertEqual(result.authorization.status, "rejected")
        self.assertEqual(
            result.authorization.policy_evaluated,
            "risk_threshold_policy",
        )
        self.assertIsNone(result.execution)

    def test_t4_allowlist_bypass_is_rejected(self):
        metrics = [
            AgentMetricOutput(
                intent="not_an_intent",
                confidence=0.9,
                feasibility=0.9,
                historical_success=0.9,
                risk=0.1,
            )
        ]

        result = self.run_async(
            process_intent_lifecycle(
                metrics=metrics,
                authorization_context=AuthorizationContext(
                    user_id="operator_01",
                ),
                entropy_consensus_threshold=0.25,
                s_min=0.50,
                timeout=5.0,
            )
        )

        self.assertEqual(result.final_state, "blocked")
        self.assertIsNotNone(result.authorization)
        self.assertEqual(result.authorization.status, "rejected")
        self.assertEqual(
            result.authorization.policy_evaluated,
            "allowlist_policy",
        )
        self.assertIsNone(result.execution)

    def test_t5_real_executor_timeout_contract(self):
        import subprocess
        from unittest.mock import patch

        from TUU.authorization import AuthorizationDecision
        from execution import execute_command_securely

        decision = AuthorizationDecision(
            intent="echo",
            status="approved",
            policy_evaluated="allowlist_policy",
            reason="timeout contract",
        )

        with patch(
            "execution.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd=["echo"],
                timeout=0.001,
            ),
        ):
            result = execute_command_securely(
                decision,
                timeout=0.001,
            )

        self.assertEqual(result.intent, decision.intent)
        self.assertFalse(result.executed)
        self.assertEqual(result.returncode, -1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertIsNotNone(result.error_message)
        self.assertIn("Timeout atingido", result.error_message)

    def test_argument_violation_is_denied_not_sanitized(self):
        result = self.process("echo", ["safe", "x;rm -rf /"])
        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_ARGUMENT_VIOLATION")
        self.assertEqual(self.executor.invocations, 0)

    def test_executor_rejects_unknown_mapping(self):
        request = AuthorizedRequest.create("rm", ["x"], {"timeout": 2.0})
        decision = PolicyDecision(
            "allow", "rm", "TEST_BYPASS", "synthetic barrier test", request
        )
        result = self.run_async(self.executor.execute(decision))
        self.assertEqual(result.transition, "rejected")
        self.assertEqual(result.error, "UNKNOWN_INTENT_MAPPING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
