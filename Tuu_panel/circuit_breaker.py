"""
Tuu_panel/circuit_breaker.py
============================
Circuit Breaker baseado em Entropia de Shannon (H_N)

Responsabilidade única:
  Avaliar a ambiguidade estrutural da superposição de hipóteses
  e decidir entre 'resolving' (colapso permitido) ou 'consensus'.

Não autoriza. Não executa. Não seleciona intenção.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

from TUU.tuu_core import CandidateEvaluation


@dataclass(frozen=True)
class CircuitBreakerDecision:
    """Resultado da avaliação do circuit breaker."""
    transition: Literal["resolving", "consensus"]
    entropy: float
    normalized_entropy: float
    threshold: float
    candidate_count: int
    reason: str


def calculate_normalized_entropy(
    candidates: Sequence[CandidateEvaluation],
) -> tuple[float, float]:
    """
    Calcula H e H_N a partir dos scores.

    Regras (compatíveis com TUU/tuu_collapse.py):
    - scores negativos -> ValueError
    - total == 0 -> distribuição uniforme
    - n <= 1 -> H_N = 0.0
    """
    n = len(candidates)
    if n <= 1:
        return 0.0, 0.0

    scores = [float(c.score) for c in candidates]
    if any(s < 0.0 for s in scores):
        raise ValueError("Candidate scores must be non-negative.")

    total = sum(scores)
    if total <= 0.0:
        probs = [1.0 / n] * n
    else:
        probs = [s / total for s in scores]

    entropy = -sum(p * math.log2(p) for p in probs if p > 0.0)
    max_entropy = math.log2(n)
    normalized = entropy / max_entropy if max_entropy > 0.0 else 0.0

    return entropy, normalized


class EntropyCircuitBreaker:
    """
    Circuit Breaker preditivo baseado em entropia normalizada.

    Configuração:
        entropy_threshold ∈ [0.0, 1.0]
        - valores baixos -> mais sensível
        - valores altos -> mais tolerante a ambiguidade
    """

    def __init__(self, entropy_threshold: float = 0.75):
        if not 0.0 <= entropy_threshold <= 1.0:
            raise ValueError("entropy_threshold must be between 0.0 and 1.0")
        self.entropy_threshold = entropy_threshold

    def evaluate(
        self,
        candidates: Sequence[CandidateEvaluation],
    ) -> CircuitBreakerDecision:
        """Avalia a superposição e retorna a transição analítica."""
        if not candidates:
            return CircuitBreakerDecision(
                transition="consensus",
                entropy=0.0,
                normalized_entropy=0.0,
                threshold=self.entropy_threshold,
                candidate_count=0,
                reason="No candidates available — forced escalation to consensus.",
            )

        entropy, h_n = calculate_normalized_entropy(candidates)

        if h_n >= self.entropy_threshold:
            return CircuitBreakerDecision(
                transition="consensus",
                entropy=entropy,
                normalized_entropy=h_n,
                threshold=self.entropy_threshold,
                candidate_count=len(candidates),
                reason=(
                    f"High structural ambiguity detected "
                    f"(H_N={h_n:.6f} >= threshold={self.entropy_threshold}). "
                    "Automatic collapse blocked."
                ),
            )

        return CircuitBreakerDecision(
            transition="resolving",
            entropy=entropy,
            normalized_entropy=h_n,
            threshold=self.entropy_threshold,
            candidate_count=len(candidates),
            reason=(
                f"Structural uncertainty within acceptable bounds "
                f"(H_N={h_n:.6f} < threshold={self.entropy_threshold}). "
                "Collapse permitted."
            ),
        )


async def apply_circuit_breaker(
    candidates: list[CandidateEvaluation],
    breaker: EntropyCircuitBreaker,
) -> CircuitBreakerDecision:
    """Ponto de integração limpo no process_intent_lifecycle."""
    return breaker.evaluate(candidates)
