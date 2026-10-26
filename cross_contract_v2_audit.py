from pathlib import Path
import re

root = Path("aurora_phase1/cognitive_poc/contracts")

files = {
    "B5": root / "prediction_commitment.md",
    "B6": root / "prediction_error.md",
    "ATTRIBUTION": root / "error_attribution.md",
    "B7": root / "belief_update.md",
}

print("=== AURORA PHASE 1 — CROSS-CONTRACT v2 ===")
print()

for name, path in files.items():
    if not path.exists():
        print(f"[FAIL] {name}: {path} ausente")
        raise SystemExit(1)
    print(f"[PASS] {name}: presente")

texts = {k: v.read_text(encoding="utf-8") for k, v in files.items()}

def check(label, condition):
    ok = bool(condition)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    return ok

results = []

print("\n=== B5 — PREDICTION COMMITMENT ===")
results += [
    check("identidade Prediction Commitment",
           "Prediction Commitment" in texts["B5"]),
    check("proteção/imutabilidade do compromisso",
           bool(re.search(
               r"immutable|immutability|MUST NOT.*mutat|não pode ser.*alter|não pode ser.*modific",
               texts["B5"], re.I | re.S))),
]

print("\n=== B6 — PREDICTION ERROR ===")
results += [
    check("referencia Prediction Commitment",
           "Prediction Commitment" in texts["B6"]),
    check("referencia Prediction Error",
           "Prediction Error" in texts["B6"]),
    check("proíbe mutação do Prediction Commitment",
           bool(re.search(
               r"(MUST NOT|must not|não pode).{0,100}(mutate|alter|modif|substitut|replace).{0,100}Prediction Commitment",
               texts["B6"], re.I | re.S))),
    check("commitment precede observation",
           bool(re.search(
               r"committed before the observation|antes da observação|antes do evento",
               texts["B6"], re.I))),
]

print("\n=== ATTRIBUTION ===")
results += [
    check("referencia Prediction Error",
           "Prediction Error" in texts["ATTRIBUTION"]),
    check("possui conceito causal/atribuição",
           bool(re.search(
               r"\b(causal|cause|causa|attribution|atribuição)\b",
               texts["ATTRIBUTION"], re.I))),
    check("não transforma attribution automaticamente em update",
           bool(re.search(
               r"(MUST\s+NOT|must\s+not|not|não|não constitui|does not).{0,120}"
               r"(automatically|automaticamente).{0,120}"
               r"(update|atualização|modify|modificar)",
               texts["ATTRIBUTION"], re.I | re.S))),
]

print("\n=== B7 — BELIEF UPDATE ===")
results += [
    check("referencia Error Attribution",
           "Error Attribution" in texts["B7"]),
    check("Attribution Is Not Update",
           "Attribution Is Not Update" in texts["B7"]),
    check("Update Decision",
           "Update Decision" in texts["B7"]),
    check("NO_UPDATE",
           "NO_UPDATE" in texts["B7"]),
    check("Prediction Commitment Preservation",
           "Prediction Commitment Preservation" in texts["B7"]),
    check("Prediction Error Preservation",
           "Prediction Error Preservation" in texts["B7"]),
    check("Attribution Preservation",
           "Attribution Preservation" in texts["B7"]),
    check("New Belief Identity",
           "New Belief Identity" in texts["B7"]),
    check("Reconstructible Update Chain",
           "Reconstructible Update Chain" in texts["B7"]),
]

print("\n=== SEPARAÇÃO EPISTÊMICA ===")
results += [
    check("Belief Is Not Evidence",
           "Belief Is Not Evidence" in texts["B7"]),
    check("Evidence Is Not Belief",
           "Evidence Is Not Belief" in texts["B7"]),
    check("Attribution Is Not Update",
           "Attribution Is Not Update" in texts["B7"]),
    check("Update Is Not Authorization",
           "Update Is Not Authorization" in texts["B7"]),
    check("Update Is Not Execution",
           "Update Is Not Execution" in texts["B7"]),
]

print("\n=== AUTORIDADE ===")
results += [
    check("No TUU Bypass",
           "No TUU Bypass" in texts["B7"]),
    check("No HEPHAESTUS Authority",
           "No HEPHAESTUS Authority" in texts["B7"]),
    check("Cognitive State Is Not Authorization",
           "Cognitive State Is Not Authorization" in texts["B7"]),
    check("LLM externo sem autoridade canônica",
           bool(re.search(
               r"(external.{0,120}canonical.{0,120}authority|"
               r"LLM.{0,120}(not|não).{0,120}canonical.{0,120}(state )?authority|"
               r"modelo externo.{0,160}(não|nao).{0,80}autoridade.{0,80}canônica)",
               texts["B7"], re.I | re.S))),
]

print("\n=== FLUXO CANÔNICO ===")

patterns = [
    ("Observation -> Prediction Error",
     r"Observation\s*↓\s*Prediction Error"),
    ("Prediction Error -> Error Attribution",
     r"Prediction Error\s*↓\s*Error Attribution"),
    ("Error Attribution -> Update Decision",
     r"Error Attribution\s*↓\s*Update Decision"),
    ("Update Decision -> Belief Update / NO_UPDATE",
     r"Update Decision\s*↓\s*Belief Update\s*/\s*NO_UPDATE"),
    ("Belief Update / NO_UPDATE -> Successor Belief",
     r"Belief Update\s*/\s*NO_UPDATE\s*↓\s*Successor Belief"),
]

for label, pattern in patterns:
    results.append(check(
        label,
        re.search(pattern, texts["B7"], re.I | re.M) is not None
    ))

print("\n=== RESULTADO ===")
passed = sum(results)
failed = len(results) - passed

print(f"PASS: {passed}")
print(f"FAIL: {failed}")

if failed == 0:
    print("\nCROSS-CONTRACT v2: CONSISTENTE")
    print("Nenhum gap estrutural detectado.")
else:
    print("\nCROSS-CONTRACT v2: EXISTEM FAILS PARA INVESTIGAR")
    print("Nenhum contrato deve ser alterado automaticamente.")
    raise SystemExit(1)

print("\n=== INTEGRIDADE ===")
print("[PASS] Auditoria somente leitura")
print("[PASS] Contratos não modificados pela auditoria")
print("[PASS] Nenhum commit")
print("[PASS] Nenhum push")
print("=== FIM ===")
