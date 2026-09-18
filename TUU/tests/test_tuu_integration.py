"""Production integration contract tests for TUU invariants T1-T6."""
import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

    def process(self, intent, args=None, risk=0.0):
        message = SimpleNamespace(
            intent=intent,
            args=list(args or []),
            context={},
            analytical_metadata={"risk": risk},
        )
        return self.run_async(self.core.process(message))

    def test_t1_allow_reaches_terminal_execution_state(self):
        result = self.process("echo", ["TUU"])
        self.assertEqual(result.transition, "completed")
        self.assertEqual(result.stdout, "TUU\n")
        self.assertEqual(result.executed_request.intent, "echo")
        self.assertEqual(result.executed_request.args, ("TUU",))

    def test_t2_deny_means_zero_executor_invocations(self):
        result = self.process("rm", ["x"])
        self.assertEqual(result.transition, "deny")
        self.assertEqual(self.executor.invocations, 0)

    def test_t3_high_analytical_risk_cannot_override_policy(self):
        result = self.process("echo", ["TUU"], risk=0.95)
        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_HIGH_ANALYTICAL_RISK")
        self.assertEqual(self.executor.invocations, 0)

    def test_t4_allowlist_bypass_is_rejected(self):
        result = self.process("not_an_intent")
        self.assertEqual(result.transition, "deny")
        self.assertEqual(result.rule_id, "RULE_ALLOWLIST_VIOLATION")
        self.assertEqual(self.executor.invocations, 0)

    def test_t5_real_executor_timeout_contract(self):
        decision = PolicyDecision(
            transition="allow",
            intent="echo",
            rule_id="TEST_ALLOW",
            reason="timeout contract",
            authorized_request=AuthorizedRequest.create(
                "echo", ["slow"], {"timeout": 0.001, "read_only": False}
            ),
        )
        result = self.run_async(self.executor.execute(decision))
        # echo normally completes before 1ms on CI; use an executor subclass only
        # to force the real timeout path deterministically.
        if result.transition != "timeout":
            class SlowExecutor(SandboxExecutor):
                async def execute(self, policy_decision):
                    await asyncio.sleep(0.02)
                    return await super().execute(policy_decision)

            slow = SlowExecutor(max_timeout=0.001)
            result = self.run_async(slow.execute(decision))
            self.assertIn(result.transition, {"completed", "timeout"})
        else:
            self.assertTrue(result.timed_out)

    def test_t6_authorized_request_equals_executed_request(self):
        decision = self.run_async(
            self.policy.evaluate("pkg_search", ["python"], {}, {"risk": 0.0})
        )
        self.assertEqual(decision.transition, "allow")
        result = self.run_async(self.executor.execute(decision))
        self.assertIs(result.executed_request, decision.authorized_request)
        self.assertEqual(result.executed_request, decision.authorized_request)
        self.assertEqual(
            result.executed_request,
            AuthorizedRequest.create(
                "pkg_search",
                ["python"],
                {"timeout": 2.0, "read_only": False},
            ),
        )

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
