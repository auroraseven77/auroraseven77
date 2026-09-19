"""Independent mathematical/cryptographic reference functions.

Do not import TUU production calculation or hashing helpers here.
"""

from __future__ import annotations

import hashlib
import math
from decimal import Decimal
from collections.abc import Mapping, Sequence
from typing import Any


def normalized_entropy(scores: Sequence[float]) -> float:
    if len(scores) <= 1:
        return 0.0

    effective = [max(0.0, float(score)) for score in scores]
    total = math.fsum(effective)
    if total <= 0.0:
        return 1.0

    probabilities = [score / total for score in effective]
    entropy = -math.fsum(
        probability * math.log2(probability)
        for probability in probabilities
        if probability > 0.0
    )
    return entropy / math.log2(len(probabilities))


def concentration_kn(scores: Sequence[float]) -> float:
    return 1.0 - normalized_entropy(scores)


def sha256_intent(intent: str) -> str:
    return hashlib.sha256(intent.encode("utf-8")).hexdigest()


def expected_tie_winner_index(
    intents: Sequence[str],
    scores: Sequence[float],
    *,
    tie_tolerance: float = 1e-9,
) -> int:
    if not scores or len(intents) != len(scores):
        raise ValueError("intents and scores must be non-empty and have equal length")

    max_score = max(scores)
    tolerance = Decimal(str(tie_tolerance))
    max_score_decimal = Decimal(str(max_score))
    tied = [
        index
        for index, score in enumerate(scores)
        if abs(Decimal(str(score)) - max_score_decimal) < tolerance
    ]
    return min(tied, key=lambda index: sha256_intent(intents[index]))


def find_key(obj: Any, key: str) -> Any:
    """Recursively find the first exact key in a JSON-like object."""
    if isinstance(obj, Mapping):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            found = find_key(value, key)
            if found is not None:
                return found
    return None
