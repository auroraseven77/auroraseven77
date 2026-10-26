"""Hash determinístico canônico para o Centro.

Serialização canônica (JSON sort_keys + separators estritos)
seguida de SHA-256 sobre UTF-8.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _json_default(obj: Any) -> Any:
    """Encoder default para tipos não-JSON (complex).

    Converte complex para string canônica determinística no formato
    "(real+imagj)". Permite hashing estável de objetos com coeficientes
    complexos.
    """
    if isinstance(obj, complex):
        return f"({obj.real}+{obj.imag}j)"
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonical_json(obj: Any) -> str:
    """Serialização JSON determinística.

    Regras:
    - chaves ordenadas alfabeticamente
    - sem espaços após separadores
    - sem ASCII escape (preserva UTF-8)
    - rejeita floats não-finitos
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=_json_default,
    )


def hash_object(obj: Any) -> str:
    """SHA-256 hex do objeto serializado canonicamente."""
    serialized = canonical_json(obj)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_string(text: str) -> str:
    """SHA-256 hex de uma string UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    """SHA-256 hex de bytes brutos."""
    return hashlib.sha256(data).hexdigest()


GENESIS_PREV_HASH = "0" * 64

__all__ = [
    "canonical_json",
    "hash_object",
    "hash_string",
    "hash_bytes",
    "GENESIS_PREV_HASH",
]
