"""Teste de integração — roda demo_phase1 e verifica 5/5 provas."""
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO = REPO_ROOT / "aurora_phase1" / "demo_phase1.py"


class TestDemoPhase1(unittest.TestCase):

    def test_demo_runs_and_returns_zero(self):
        """O demo_phase1 deve rodar e retornar código 0 (5/5 provas)."""
        result = subprocess.run(
            [sys.executable, str(DEMO)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=60,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        # Verifica exit code 0
        self.assertEqual(
            result.returncode,
            0,
            f"Demo falhou (exit {result.returncode}).\n"
            f"STDOUT:\n{stdout}\n"
            f"STDERR:\n{stderr}",
        )

        # Verifica as 5 provas no output
        for n in range(1, 6):
            self.assertIn(
                f"PROVA {n} SATISFEITA",
                stdout,
                f"Prova {n} não satisfeita no output",
            )

        # Verifica resultado final
        self.assertIn("FASE 1 COMPLETADA COM ÊXITO", stdout)


if __name__ == "__main__":
    unittest.main()
