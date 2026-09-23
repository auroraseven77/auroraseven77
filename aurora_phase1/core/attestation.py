"""Atestado de boot.

No início do mundo, o attestation sela os hashes SHA-256 de todos os
arquivos em `contracts/`. Qualquer mutação posterior (modificação,
deleção, adição) é detectada por `verify_disk_integrity()`.

Modo de falha:
- Opção A (default): hard stop. Boot falha, mundo não inicia.
- Opção B (--degraded): modo degradado. Mundo inicia com flag visível.
- Opção C: banida.

Invariantes:
- `seal()` lê o estado atual dos arquivos
- `verify_disk_integrity()` recomputa e compara
- Detecta modificação, deleção e adição
- `master_attestation_hash` é determinístico
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerificationResult:
    integrity: bool
    changes: dict  # {filename: "modified" | "deleted" | "added"}
    diagnostic: str

    def to_dict(self) -> dict:
        return {
            "integrity": self.integrity,
            "changes": dict(self.changes),
            "diagnostic": self.diagnostic,
        }


class AttestationEngine:
    """Sela hashes dos contratos no boot; verifica mutação em disco."""

    def __init__(self, contracts_dir: str | Path):
        self._contracts_dir = Path(contracts_dir)
        if not self._contracts_dir.exists():
            raise FileNotFoundError(
                f"Diretório de contratos não existe: {self._contracts_dir}"
            )
        if not self._contracts_dir.is_dir():
            raise NotADirectoryError(
                f"Não é diretório: {self._contracts_dir}"
            )
        self._attestation: dict[str, str] | None = None

    # ---- selagem ----

    @staticmethod
    def _hash_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _list_contract_files(self) -> list[Path]:
        """Arquivos JSON no diretório, ordenados por nome."""
        files = sorted(
            p for p in self._contracts_dir.iterdir()
            if p.is_file() and p.suffix == ".json"
        )
        return files

    def seal(self) -> dict[str, str]:
        """Lê os arquivos e sela. Retorna o dict de hashes."""
        attestation = {}
        for path in self._list_contract_files():
            attestation[path.name] = self._hash_file(path)
        self._attestation = attestation
        return dict(attestation)

    # ---- verificação ----

    def verify_disk_integrity(self) -> VerificationResult:
        """Recomputa e compara com o atestado selado."""
        if self._attestation is None:
            return VerificationResult(
                integrity=False,
                changes={},
                diagnostic=(
                    "Nenhum atestado foi selado. Chame seal() primeiro."
                ),
            )

        current_files = {p.name: p for p in self._list_contract_files()}
        changes: dict = {}

        # 1. modificados e deletados
        for name, expected_hash in self._attestation.items():
            if name not in current_files:
                changes[name] = "deleted"
                continue
            actual_hash = self._hash_file(current_files[name])
            if actual_hash != expected_hash:
                changes[name] = "modified"

        # 2. adicionados
        for name in current_files:
            if name not in self._attestation:
                changes[name] = "added"

        if not changes:
            return VerificationResult(
                integrity=True,
                changes={},
                diagnostic=(
                    f"Integridade verificada: "
                    f"{len(self._attestation)} contratos íntegros."
                ),
            )

        return VerificationResult(
            integrity=False,
            changes=changes,
            diagnostic=(
                f"Contract tampering detected. "
                f"Alterações: {changes}"
            ),
        )

    # ---- master ----

    @property
    def master_attestation_hash(self) -> str:
        """Hash do dict de hashes (ordem canônica)."""
        # Import local para evitar ciclo
        from aurora_phase1.core.crypto import hash_object
        if self._attestation is None:
            raise RuntimeError(
                "Nenhum atestado foi selado. Chame seal() primeiro."
            )
        return hash_object(dict(sorted(self._attestation.items())))

    @property
    def attestation(self) -> dict[str, str]:
        if self._attestation is None:
            return {}
        return dict(self._attestation)

    # ---- boot ----

    def boot_verify(self, *, degraded: bool = False) -> VerificationResult:
        """Verifica integridade. Aplica política de falha de boot.

        Se `degraded=True`, aceita a falha e retorna o resultado.
        Se `degraded=False` (default), levanta RuntimeError em falha.
        """
        result = self.verify_disk_integrity()

        if result.integrity:
            return result

        if degraded:
            return result

        raise RuntimeError(
            f"BootAttestationFailed: {result.diagnostic}. "
            f"Use degraded=True para iniciar em modo degradado."
        )


__all__ = ["AttestationEngine", "VerificationResult"]
