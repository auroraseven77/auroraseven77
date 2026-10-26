#!/usr/bin/env python3
"""Validate required audit documentation without executing experiments."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "STATUS.md": ("# TUU — Estado de auditoria e evidências",),
    "docs/audits/COMPONENT-STATUS.md": (
        "# Inventário de componentes",
        "## Matriz",
        "b1_motor/",
        "B1-GEN-01A",
    ),
    "docs/audits/EVIDENCE-INDEX.md": (
        "# Índice de evidências",
        "## Regra para adicionar evidências",
        "00c371d3f3ebbcdc0d02f8fb89b5bb9110278825",
    ),
    "docs/audits/REPRODUCIBILITY.md": (
        "# Reprodução experimental",
        "BLOQUEADO",
        "scripts/reproduce-b1-gen-01a.sh",
    ),
    "scripts/reproduce-b1-gen-01a.sh": (
        "BLOCKED:",
        "python3 -m unittest discover",
    ),
}

def main() -> int:
    errors = []
    for relative, needles in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                errors.append(f"{relative}: missing required text {needle!r}")

    readme = ROOT / "README.md"
    if not readme.is_file() or "docs/audits/EVIDENCE-INDEX.md" not in readme.read_text(encoding="utf-8"):
        errors.append("README.md must link to docs/audits/EVIDENCE-INDEX.md")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: audit documentation structure is consistent.")
    print("NOTE: this check does not claim B1-GEN-01A was reproduced.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
