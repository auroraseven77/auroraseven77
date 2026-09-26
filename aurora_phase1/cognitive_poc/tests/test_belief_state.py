from dataclasses import FrozenInstanceError
import math
import pytest

from aurora_phase1.cognitive_poc.belief_state import BeliefState, BeliefStatus, BeliefTransition, UnresolvedBelief


def test_valid_belief_state():
    state = BeliefState(hypothesis_id="H1", belief=0.75, timestamp_logical=1)
    assert state.hypothesis_id == "H1"
    assert state.belief == 0.75
    assert state.timestamp_logical == 1


def test_reject_belief_below_zero():
    with pytest.raises(ValueError):
        BeliefState(hypothesis_id="H1", belief=-0.01, timestamp_logical=1)


def test_reject_belief_above_one():
    with pytest.raises(ValueError):
        BeliefState(hypothesis_id="H1", belief=1.01, timestamp_logical=1)


def test_reject_nan():
    with pytest.raises(ValueError):
        BeliefState(hypothesis_id="H1", belief=math.nan, timestamp_logical=1)


def test_reject_infinity():
    with pytest.raises(ValueError):
        BeliefState(hypothesis_id="H1", belief=math.inf, timestamp_logical=1)


def test_preserve_hypothesis_id():
    state = BeliefState(hypothesis_id="temperature_high", belief=0.6, timestamp_logical=7)
    assert state.hypothesis_id == "temperature_high"


def test_preserve_timestamp_logical():
    state = BeliefState(hypothesis_id="H1", belief=0.6, timestamp_logical=42)
    assert state.timestamp_logical == 42


def test_unresolved_is_explicit_and_not_numeric_belief():
    state = UnresolvedBelief(hypothesis_id="H1", timestamp_logical=1)
    assert state.status is BeliefStatus.BELIEF_UNRESOLVED
    assert not hasattr(state, "belief")


def test_belief_state_is_immutable():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        state.belief = 0.8


def test_update_creates_transition_with_provenance():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    provenance = {"event": "E1"}
    transition = state.update(belief=0.8, timestamp_logical=2, provenance=provenance)
    assert isinstance(transition, BeliefTransition)
    assert transition.previous_state is state
    assert transition.new_state is not state
    assert state.belief == 0.5
    assert transition.new_state.belief == 0.8
    assert transition.new_state.timestamp_logical == 2
    assert transition.provenance == provenance


def test_transition_provenance_is_not_canonical_state_data():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    transition = state.update(
        belief=0.8,
        timestamp_logical=2,
        provenance={"event": "E1", "source": "ARGOS"},
    )
    assert set(transition.new_state.canonical_object) == {
        "hypothesis_id",
        "belief",
        "timestamp_logical",
    }
    assert "provenance" not in transition.new_state.canonical_object


def test_update_rejects_temporal_rollback():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=5)
    with pytest.raises(ValueError):
        state.update(belief=0.8, timestamp_logical=4, provenance={"event": "E1"})


def test_cognitive_state_is_not_authorization_state():
    state = BeliefState(hypothesis_id="H1", belief=0.9, timestamp_logical=1)
    assert not hasattr(state, "authorize")
    assert not hasattr(state, "execute")
    assert not hasattr(state, "authorization_state")


def test_canonical_representation_is_deterministic():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    assert state.canonical_object == {"hypothesis_id": "H1", "belief": 0.5, "timestamp_logical": 1}
    assert list(state.canonical_object) == ["hypothesis_id", "belief", "timestamp_logical"]


def test_canonical_object_excludes_ledger_metadata():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    assert set(state.canonical_object) == {"hypothesis_id", "belief", "timestamp_logical"}
    assert "seq" not in state.canonical_object
    assert "tick" not in state.canonical_object
    assert "prev_hash" not in state.canonical_object
    assert "entry_hash" not in state.canonical_object


def test_update_requires_provenance():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    with pytest.raises((TypeError, ValueError)):
        state.update(belief=0.8, timestamp_logical=2, provenance=None)


def test_no_retroactive_mutation():
    state = BeliefState(hypothesis_id="H1", belief=0.5, timestamp_logical=1)
    transition = state.update(belief=0.8, timestamp_logical=2, provenance={"event": "E1"})
    assert state.canonical_object == {"hypothesis_id": "H1", "belief": 0.5, "timestamp_logical": 1}
    assert transition.new_state.canonical_object == {"hypothesis_id": "H1", "belief": 0.8, "timestamp_logical": 2}


def test_unresolved_is_not_encoded_as_zero_or_one():
    unresolved = UnresolvedBelief(hypothesis_id="H1", timestamp_logical=1)
    assert unresolved.status is BeliefStatus.BELIEF_UNRESOLVED
    assert unresolved.status not in (0.0, 1.0)
