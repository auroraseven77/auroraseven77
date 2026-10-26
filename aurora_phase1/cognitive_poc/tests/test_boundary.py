import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "cognitive_contract.json"


def load_contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_cognitive_core_has_no_execution_authority():
    contract = load_contract()

    assert contract["authority"]["execution_authority"] is False
    assert "EXECUTE" in contract["disallowed_capabilities"]


def test_cognitive_core_has_no_authorization_authority():
    contract = load_contract()

    assert contract["authority"]["authorization_authority"] is False
    assert "AUTHORIZE" in contract["disallowed_capabilities"]


def test_cognitive_state_is_separate_from_authorization():
    contract = load_contract()

    assert (
        "COGNITIVE_STATE_IS_NOT_AUTHORIZATION_STATE"
        in contract["invariants"]
    )


def test_tuu_remains_governance_gate():
    contract = load_contract()

    assert (
        contract["integration"]["governance_gate"]
        == "aurora_phase1.core.tuu.TUU"
    )


def test_existing_ledger_is_reused():
    contract = load_contract()

    assert (
        contract["integration"]["ledger"]
        == "aurora_phase1.core.ledger.Ledger"
    )


def test_existing_executor_is_not_reimplemented():
    contract = load_contract()

    assert (
        contract["integration"]["executor"]
        == "aurora_phase1.core.executor.IsolatedExecutor"
    )


def test_direct_ledger_write_is_forbidden():
    contract = load_contract()

    assert contract["authority"]["ledger_write_authority"] is False
    assert "WRITE_LEDGER_DIRECTLY" in contract["disallowed_capabilities"]
