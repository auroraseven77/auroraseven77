"""Pure validation of the TUU v2.1 defensible invariants.
This module observes state; it does not authorize, mutate, or execute.
"""

from __future__ import annotations

import hashlib
import math
from typing import Sequence

from TUU.tuu_core import CandidateEvaluation


class InvariantViolationError(Exception):
    """Raised when a TUU v2.1 invariant is violated."""


class InvariantEngine:
    """Pure observer for mathematical, decision, and determinism contracts."""

    @staticmethod
    def validate_math_invariant(h_n: float, k_n: float, tol: float = 1e-6) -> None:
        """Require K_N = 1 - H_N within the declared numerical tolerance."""
        if not (math.isfinite(h_n) and math.isfinite(k_n)):
            raise InvariantViolationError("H_N and K_N must be finite.")
        if abs(k_n - (1.0 - h_n)) > tol:
            raise InvariantViolationError(
                f"Mathematical invariant violated: K_N={k_n} != 1-H_N={1.0-h_n}."
            )

    @staticmethod
    def validate_decision_invariant(
        decision_state: str,
        k_n: float,
        selected_score: float,
        tau_k: float = 0.25,
        s_min: float = 0.50,
    ) -> None:
        """Require the decision boundary to use K_N and S_min inclusively."""
        expected_state = (
            "consensus"
            if k_n >= tau_k and selected_score >= s_min
            else "resolving"
        )
        if decision_state != expected_state:
            raise InvariantViolationError(
                "Decision invariant violated: "
                f"state={decision_state!r}, expected={expected_state!r}, "
                f"K_N={k_n}, tau_K={tau_k}, S_min={s_min}, "
                f"selected_score={selected_score}."
            )

    @staticmethod
    def validate_determinism_invariant(
        candidates: Sequence[CandidateEvaluation],
        selected_index: int,
        tie_tolerance: float = 1e-9,
    ) -> None:
        """Require SHA-256(intent) as the deterministic tie-break key."""
        if not candidates:
            raise InvariantViolationError(
                "Determinism invariant requires at least one candidate."
            )
        if not 0 <= selected_index < len(candidates):
            raise InvariantViolationError(
                f"Selected index {selected_index} is outside candidate range."
            )

        scores = [candidate.score for candidate in candidates]
        max_score = max(scores)
        tied_indices = [
            index for index, score in enumerate(scores)
            if abs(score - max_score) < tie_tolerance
        ]
        expected_index = min(
            tied_indices,
            key=lambda index: hashlib.sha256(
                candidates[index].intent.encode("utf-8")
            ).hexdigest(),
        )

        if selected_index != expected_index:
            raise InvariantViolationError(
                "Determinism invariant violated: "
                f"selected_index={selected_index}, expected_index={expected_index}."
            )
