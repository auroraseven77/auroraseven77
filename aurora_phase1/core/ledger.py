"""Ledger criptográfico append-only.

Cada bloco é encadeado por SHA-256. O bloco N referencia o hash do bloco
N-1 via `prev_hash`. O `entry_hash` de cada bloco é o hash canônico do
bloco completo (sem o próprio `entry_hash`).

Invariantes:
- append-only (nunca reescreve bloco anterior)
- hash chain contínua (prev_hash = entry_hash do bloco anterior)
- audit_chain() detecta quebra e retorna o seq exato
- record_finding() ancora hash de arquivo de evidência

Formato de cada linha `.jsonl`:

    {
      "seq": <int>,
      "tick": <int>,
      "event_type": <str>,
      "payload": <dict>,
      "prev_hash": <64 hex chars>,
      "entry_hash": <64 hex chars>
    }
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from aurora_phase1.core.crypto import (
    GENESIS_PREV_HASH,
    hash_object,
    hash_string,
)


BLOCK_FIELDS = ("seq", "tick", "event_type", "payload", "prev_hash")


@dataclass(frozen=True)
class Block:
    seq: int
    tick: int
    event_type: str
    payload: dict
    prev_hash: str
    entry_hash: str


@dataclass(frozen=True)
class AuditResult:
    chain_integrity: bool
    failed_seq: Optional[int]
    last_valid_seq: int
    total_blocks: int
    diagnostic: str


class Ledger:
    """Ledger append-only com encadeamento SHA-256."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    # ---- leitura ----

    def read_all(self) -> list[Block]:
        """Lê todos os blocos do arquivo. Levanta se linha malformada."""
        blocks = []
        with self.path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Linha {lineno} não é JSON válido: {e}"
                    ) from e
                try:
                    block = Block(
                        seq=obj["seq"],
                        tick=obj["tick"],
                        event_type=obj["event_type"],
                        payload=obj["payload"],
                        prev_hash=obj["prev_hash"],
                        entry_hash=obj["entry_hash"],
                    )
                except KeyError as e:
                    raise ValueError(
                        f"Bloco na linha {lineno} não tem campo obrigatório: {e}"
                    ) from e
                blocks.append(block)
        return blocks

    def count(self) -> int:
        with self.path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    def last(self) -> Optional[Block]:
        blocks = self.read_all()
        return blocks[-1] if blocks else None

    # ---- cálculo ----

    @staticmethod
    def _compute_entry_hash(block_dict: dict) -> str:
        """entry_hash = SHA-256 dos campos canônicos (sem entry_hash)."""
        normalized = {k: block_dict[k] for k in BLOCK_FIELDS}
        return hash_object(normalized)

    # ---- escrita ----

    def add_block(
        self,
        event_type: str,
        payload: dict,
        tick: int = 0,
    ) -> Block:
        """Anexa bloco. Verifica prev_hash contra último bloco."""
        if not isinstance(payload, dict):
            raise TypeError("payload deve ser dict")
        if not isinstance(tick, int):
            raise TypeError("tick deve ser int")

        blocks = self.read_all()

        if blocks:
            expected_prev = blocks[-1].entry_hash
            seq = blocks[-1].seq + 1
        else:
            expected_prev = GENESIS_PREV_HASH
            seq = 0

        block_dict = {
            "seq": seq,
            "tick": tick,
            "event_type": event_type,
            "payload": payload,
            "prev_hash": expected_prev,
        }
        block_dict["entry_hash"] = self._compute_entry_hash(block_dict)

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(block_dict, ensure_ascii=False) + "\n")

        return Block(**block_dict)

    def record_finding(
        self,
        attack_id: str,
        evidence_path: str | Path,
        tick: int = 0,
    ) -> Block:
        """Registra hash SHA-256 de um arquivo de evidência no ledger."""
        evidence_path = Path(evidence_path)
        if not evidence_path.exists():
            raise FileNotFoundError(
                f"Arquivo de evidência não existe: {evidence_path}"
            )
        content = evidence_path.read_bytes()
        evidence_hash = hash_string(content.decode("utf-8"))

        payload = {
            "attack_id": attack_id,
            "evidence_path": str(evidence_path),
            "evidence_hash": evidence_hash,
        }
        return self.add_block(
            event_type="ATTACK_FINDING_RECORDED",
            payload=payload,
            tick=tick,
        )

    # ---- auditoria ----

    def audit_chain(self) -> AuditResult:
        """Valida a cadeia inteira. Retorna diagnóstico estruturado."""
        try:
            blocks = self.read_all()
        except ValueError as e:
            return AuditResult(
                chain_integrity=False,
                failed_seq=None,
                last_valid_seq=-1,
                total_blocks=-1,
                diagnostic=str(e),
            )

        if not blocks:
            return AuditResult(
                chain_integrity=True,
                failed_seq=None,
                last_valid_seq=-1,
                total_blocks=0,
                diagnostic="Ledger vazio (sem blocos).",
            )

        expected_prev = GENESIS_PREV_HASH
        last_valid = -1

        for i, block in enumerate(blocks):
            # 1. seq sequencial
            if block.seq != i:
                return AuditResult(
                    chain_integrity=False,
                    failed_seq=block.seq,
                    last_valid_seq=last_valid,
                    total_blocks=len(blocks),
                    diagnostic=(
                        f"Seq fora de ordem no bloco {i}: "
                        f"esperado {i}, encontrado {block.seq}"
                    ),
                )

            # 2. prev_hash aponta para o bloco anterior
            if block.prev_hash != expected_prev:
                return AuditResult(
                    chain_integrity=False,
                    failed_seq=block.seq,
                    last_valid_seq=last_valid,
                    total_blocks=len(blocks),
                    diagnostic=(
                        f"Hash anterior quebrado no seq {block.seq}: "
                        f"esperado {expected_prev}, encontrado {block.prev_hash}"
                    ),
                )

            # 3. entry_hash recomputado bate
            recomputed = self._compute_entry_hash({
                "seq": block.seq,
                "tick": block.tick,
                "event_type": block.event_type,
                "payload": block.payload,
                "prev_hash": block.prev_hash,
            })
            if recomputed != block.entry_hash:
                return AuditResult(
                    chain_integrity=False,
                    failed_seq=block.seq,
                    last_valid_seq=last_valid,
                    total_blocks=len(blocks),
                    diagnostic=(
                        f"entry_hash inválido no seq {block.seq}: "
                        f"esperado {recomputed}, encontrado {block.entry_hash}"
                    ),
                )

            expected_prev = block.entry_hash
            last_valid = block.seq

        return AuditResult(
            chain_integrity=True,
            failed_seq=None,
            last_valid_seq=last_valid,
            total_blocks=len(blocks),
            diagnostic=f"Cadeia íntegra: {len(blocks)} blocos.",
        )

    # ---- helpers ----

    def top_hash(self) -> str:
        """Hash do topo da cadeia (ou GENESIS se vazio)."""
        last = self.last()
        return last.entry_hash if last else GENESIS_PREV_HASH

    def seen_proposal_ids(self) -> set[str]:
        """Conjunto de proposal_id já registrados (aprovadas ou rejeitadas)."""
        seen: set[str] = set()
        for block in self.read_all():
            pid = block.payload.get("proposal_id")
            if pid:
                seen.add(pid)
        return seen


__all__ = ["Ledger", "Block", "AuditResult", "BLOCK_FIELDS"]
