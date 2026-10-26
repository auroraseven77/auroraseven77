"""Testes de aurora_phase1.core.executor (Bloco 7)."""
import os
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.executor import IsolatedExecutor


def _make_contract(sandbox: Path) -> dict:
    return {
        "contract_id": "role_hephaestus_v1",
        "version": "1.0.0",
        "role": "HEPHAESTUS",
        "region": "EXECUTION",
        "allowed_paths": [str(sandbox)],
        "allowed_commands": ["echo", "cat", "sha256sum", "pwd"],
        "max_runtime_ms": 2000,
        "max_output_bytes": 1024,
        "denied_patterns": ["\\.\\.", ";", "\\|", "&", "`"],
    }


class TestExecutor(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.sandbox = self.tmpdir / "sandbox"
        self.sandbox.mkdir()
        self.contract = _make_contract(self.sandbox)
        self.executor = IsolatedExecutor(self.contract)

    def test_echo_hello(self):
        r = self.executor.execute("echo", ["hello"])
        self.assertIsNone(r.error_type)
        self.assertEqual(r.exit_code, 0)
        self.assertEqual(r.stdout.strip(), "hello")
        self.assertEqual(len(r.command_hash), 64)

    def test_disallowed_command(self):
        r = self.executor.execute("rm", ["-rf", "/"])
        self.assertEqual(r.error_type, "REJECTED_COMMAND_NOT_ALLOWED")
        self.assertIsNone(r.exit_code)

    def test_injection_in_args(self):
        r = self.executor.execute("echo", ["hello", "; rm -rf /"])
        self.assertEqual(r.error_type, "REJECTED_CONTENT_VIOLATION")

    def test_cwd_outside_allowed(self):
        r = self.executor.execute("echo", ["hello"], cwd="/etc")
        self.assertEqual(r.error_type, "REJECTED_PATH_ESCAPE")

    def test_cwd_inside_allowed(self):
        r = self.executor.execute("echo", ["hello"], cwd=str(self.sandbox))
        self.assertIsNone(r.error_type)
        self.assertEqual(r.exit_code, 0)

    def test_timeout(self):
        executor_fast = IsolatedExecutor({
            **self.contract,
            "allowed_commands": ["python3"],
            "max_runtime_ms": 300,
            "denied_patterns": [],
        })
        r = executor_fast.execute("python3", ["-c", "while True: pass"])
        self.assertTrue(r.timed_out)
        self.assertEqual(r.exit_code, 124)

    def test_output_truncated(self):
        executor_bomb = IsolatedExecutor({
            **self.contract,
            "allowed_commands": ["python3"],
            "max_output_bytes": 100,
            "denied_patterns": [],
        })
        r = executor_bomb.execute("python3", ["-c", 'print("x" * 5000)'])
        self.assertTrue(r.truncated)
        self.assertLessEqual(len(r.stdout), 100)

    def test_env_sterile(self):
        os.environ["SECRET_PAI"] = "valor_secreto_do_pai"
        executor_env = IsolatedExecutor({
            **self.contract,
            "allowed_commands": ["python3"],
            "denied_patterns": [],
        })
        script = self.sandbox / "test_secret.py"
        script.write_text(
            'import os\nprint(os.environ.get("SECRET_PAI", "NOT_FOUND"))\n'
        )
        r = executor_env.execute("python3", [str(script)])
        self.assertEqual(r.stdout.strip(), "NOT_FOUND")

    def test_env_has_user(self):
        executor_env = IsolatedExecutor({
            **self.contract,
            "allowed_commands": ["python3"],
            "denied_patterns": [],
        })
        script = self.sandbox / "test_user.py"
        script.write_text('import os\nprint(os.environ.get("USER"))\n')
        r = executor_env.execute("python3", [str(script)])
        self.assertIn("aurora_sandbox", r.stdout)

    def test_shell_false(self):
        r = self.executor.execute("echo", ["$HOME"])
        self.assertIn("$HOME", r.stdout)

    def test_determinism(self):
        r1 = self.executor.execute("echo", ["hello"], cwd=str(self.sandbox))
        r2 = self.executor.execute("echo", ["hello"], cwd=str(self.sandbox))
        self.assertEqual(r1.command_hash, r2.command_hash)
        self.assertEqual(r1.stdout, r2.stdout)

    def test_malformed(self):
        r = self.executor.execute("", [])
        self.assertEqual(r.error_type, "REJECTED_MALFORMED")


if __name__ == "__main__":
    unittest.main()
