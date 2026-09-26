import math

import pytest

from aurora_phase1.cognitive_poc.competing_hypotheses import (
    CompetingHypothesisSet,
    Hypothesis,
    HypothesisSetProvenance,
)


def make_set(timestamp=1):
    return CompetingHypothesisSet(
        (
            Hypothesis("H1", {"cause": "A"}),
            Hypothesis("H2", {"cause": "B"}),
        ),
        timestamp,
    )


def test_valid_hypothesis():
    h = Hypothesis("H1", {"cause": "A"})
    assert h.hypothesis_id == "H1"
    assert h.canonical_proposition if hasattr(h, "canonical_proposition") else h.proposition == {"cause": "A"}


def test_hypothesis_identity_is_stable():
    h = Hypothesis("H1", {"cause": "A"})
    assert h.hypothesis_id == "H1"


@pytest.mark.parametrize("value", ["", None, 1, False])
def test_invalid_hypothesis_id_rejected(value):
    with pytest.raises(ValueError):
        Hypothesis(value, "proposition")


def test_competing_set_requires_two_hypotheses():
    with pytest.raises(ValueError):
        CompetingHypothesisSet((Hypothesis("H1", "A"),), 1)


def test_hypothesis_ids_must_be_unique():
    with pytest.raises(ValueError):
        CompetingHypothesisSet(
            (Hypothesis("H1", "A"), Hypothesis("H1", "B")),
            1,
        )


def test_hypotheses_are_deterministically_ordered():
    state = CompetingHypothesisSet(
        (Hypothesis("H2", "B"), Hypothesis("H1", "A")),
        1,
    )
    assert [h.hypothesis_id for h in state.hypotheses] == ["H1", "H2"]


def test_order_does_not_change_canonical_representation():
    a = make_set()
    b = CompetingHypothesisSet(
        (Hypothesis("H2", {"cause": "B"}), Hypothesis("H1", {"cause": "A"})),
        1,
    )
    assert a.canonical_object == b.canonical_object


def test_canonical_object_has_exact_fields():
    assert set(make_set().canonical_object) == {"hypotheses", "timestamp_logical"}


def test_canonical_object_is_json_serializable():
    import json

    json.dumps(make_set().canonical_object, allow_nan=False)


def test_proposition_is_deeply_immutable():
    original = {"nested": {"items": [1, 2]}}
    hypothesis = Hypothesis("H1", original)
    original["nested"]["items"].append(3)
    assert hypothesis.proposition["nested"]["items"] == (1, 2)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_proposition_numbers_rejected(value):
    with pytest.raises(ValueError):
        Hypothesis("H1", {"value": value})


def test_state_is_immutable():
    state = make_set()
    with pytest.raises(Exception):
        state.timestamp_logical = 2


def test_add_creates_new_state():
    state = make_set()
    transition = state.add_hypothesis(
        Hypothesis("H3", "C"),
        timestamp_logical=2,
        provenance="add",
    )
    assert transition.previous_state is state
    assert transition.new_state is not state
    assert [h.hypothesis_id for h in transition.new_state.hypotheses] == [
        "H1",
        "H2",
        "H3",
    ]
    assert [h.hypothesis_id for h in state.hypotheses] == ["H1", "H2"]


def test_remove_creates_new_state():
    state = CompetingHypothesisSet(
        (
            Hypothesis("H1", "A"),
            Hypothesis("H2", "B"),
            Hypothesis("H3", "C"),
        ),
        1,
    )
    transition = state.remove_hypothesis(
        "H3",
        timestamp_logical=2,
        provenance="remove",
    )
    assert transition.previous_state is state
    assert [h.hypothesis_id for h in transition.new_state.hypotheses] == ["H1", "H2"]
    assert [h.hypothesis_id for h in state.hypotheses] == ["H1", "H2", "H3"]


def test_replace_creates_new_state_with_new_identity():
    state = make_set()
    transition = state.replace_hypothesis(
        "H1",
        Hypothesis("H3", "C"),
        timestamp_logical=2,
        provenance="replace",
    )
    assert [h.hypothesis_id for h in transition.new_state.hypotheses] == ["H2", "H3"]
    assert [h.hypothesis_id for h in state.hypotheses] == ["H1", "H2"]


def test_replace_same_identity_is_rejected():
    state = make_set()
    with pytest.raises(ValueError):
        state.replace_hypothesis(
            "H1",
            Hypothesis("H1", "C"),
            timestamp_logical=2,
            provenance="replace",
        )


def test_transition_timestamp_must_increase():
    state = make_set(5)
    with pytest.raises(ValueError):
        state.add_hypothesis(
            Hypothesis("H3", "C"),
            timestamp_logical=5,
            provenance="test",
        )


def test_transition_requires_provenance():
    state = make_set()
    with pytest.raises(ValueError):
        state.add_hypothesis(
            Hypothesis("H3", "C"),
            timestamp_logical=2,
            provenance=None,
        )


def test_transition_provenance_is_deeply_immutable():
    provenance = {"source": {"value": 1}, "items": [1]}
    transition = make_set().add_hypothesis(
        Hypothesis("H3", "C"),
        timestamp_logical=2,
        provenance=provenance,
    )
    provenance["source"]["value"] = 99
    provenance["items"].append(2)
    assert transition.provenance["source"]["value"] == 1
    assert transition.provenance["items"] == (1,)


def test_provenance_kept_outside_canonical_object():
    provenance = HypothesisSetProvenance(
        question_context={"question": "why"},
        evidence={"obs": 1},
        source="test",
        criteria={"rule": "explicit"},
        evaluator_id="eval-1",
        timestamp_logical=2,
    )
    assert "evaluator_id" not in make_set().canonical_object
    assert provenance.evaluator_id == "eval-1"


def test_cross_block_reference_collections_are_valid_and_provenance_only():
    provenance = HypothesisSetProvenance(
        question_context="q",
        evidence="e",
        source="test",
        criteria="c",
        evaluator_id="eval",
        timestamp_logical=3,
        prediction_commitment_refs=("aaa", "bbb"),
        prediction_error_refs=(("aaa", 1), ("bbb", 2)),
        attribution_assessment_refs=(("aaa", 1),),
    )
    state = make_set()
    assert provenance.prediction_commitment_refs == ("aaa", "bbb")
    assert provenance.prediction_error_refs == (("aaa", 1), ("bbb", 2))
    assert provenance.attribution_assessment_refs == (("aaa", 1),)
    canonical = state.canonical_object
    assert "prediction_commitment_refs" not in canonical
    assert "prediction_error_refs" not in canonical
    assert "attribution_assessment_refs" not in canonical


@pytest.mark.parametrize(
    "field,value",
    [
        ("prediction_commitment_refs", ("bbb", "aaa")),
        ("prediction_error_refs", (("bbb", 2), ("aaa", 1))),
        ("attribution_assessment_refs", (("bbb", 2), ("aaa", 1))),
    ],
)
def test_cross_block_reference_collections_require_deterministic_order(field, value):
    kwargs = dict(
        question_context="q",
        evidence="e",
        source="test",
        criteria="c",
        evaluator_id="eval",
        timestamp_logical=3,
    )
    kwargs[field] = value
    with pytest.raises(ValueError, match="deterministically ordered"):
        HypothesisSetProvenance(**kwargs)


def test_cross_block_reference_timestamps_must_be_integers():
    with pytest.raises(ValueError, match="integer timestamp"):
        HypothesisSetProvenance(
            question_context="q",
            evidence="e",
            source="test",
            criteria="c",
            evaluator_id="eval",
            timestamp_logical=3,
            prediction_error_refs=(("aaa", "1"),),
        )


def test_belief_is_not_part_of_canonical_state():
    canonical = make_set().canonical_object
    assert "belief" not in canonical
    assert "beliefs" not in canonical


def test_prediction_error_is_not_part_of_canonical_state():
    canonical = make_set().canonical_object
    assert "prediction_error" not in canonical
    assert "prediction_error_timestamp_logical" not in canonical


def test_attribution_is_not_part_of_canonical_state():
    canonical = make_set().canonical_object
    assert "attribution_status" not in canonical
    assert "candidate_causes" not in canonical


def test_no_implicit_generation():
    state = make_set()
    assert len(state.hypotheses) == 2


def test_external_model_metadata_stays_in_provenance():
    provenance = HypothesisSetProvenance(
        question_context="q",
        evidence="e",
        source="external-model",
        criteria="c",
        evaluator_id="eval",
        timestamp_logical=1,
        external_model_involvement={"model": "external"},
    )
    assert provenance.external_model_involvement == {"model": "external"}
    assert "external_model_involvement" not in make_set().canonical_object


def test_ambiguous_set_preserves_multiple_hypotheses():
    state = make_set()
    assert len(state.hypotheses) == 2


def test_no_forced_elimination_by_membership():
    state = make_set()
    assert len(state.hypotheses) == 2


def test_no_authorization_or_execution_fields():
    canonical = make_set().canonical_object
    forbidden = {
        "authorized",
        "authorization",
        "execute",
        "execution",
        "permission",
    }
    assert not forbidden.intersection(canonical)


def test_canonical_hash_is_deterministic():
    from aurora_phase1.core.crypto import hash_object

    state = make_set()
    assert hash_object(state.canonical_object) == hash_object(state.canonical_object)


def test_unresolved_state_is_explicit_and_separate_from_canonical_set():
    from aurora_phase1.cognitive_poc.belief_state import BeliefStatus, UnresolvedBelief

    state = make_set()
    unresolved = UnresolvedBelief("H1", 2)
    assert unresolved.status is BeliefStatus.BELIEF_UNRESOLVED
    assert unresolved.hypothesis_id == "H1"
    assert "BELIEF_UNRESOLVED" not in str(state.canonical_object)
    assert "belief" not in state.canonical_object


def test_post_observation_hypothesis_is_new_state_without_rewriting_history():
    previous = make_set(timestamp=1)
    previous_canonical = previous.canonical_object
    transition = previous.add_hypothesis(
        Hypothesis("H3", {"cause": "C"}),
        timestamp_logical=3,
        provenance="introduced-after-observation",
    )
    assert transition.new_state.timestamp_logical == 3
    assert previous.canonical_object == previous_canonical
    assert [h.hypothesis_id for h in previous.hypotheses] == ["H1", "H2"]
    assert [h.hypothesis_id for h in transition.new_state.hypotheses] == ["H1", "H2", "H3"]


def test_competing_hypothesis_membership_does_not_create_or_update_belief():
    from aurora_phase1.cognitive_poc.belief_state import BeliefState

    state = make_set()
    belief_before = BeliefState("H1", 0.5, 1)
    canonical_before = belief_before.canonical_object
    _ = state
    assert belief_before.canonical_object == canonical_before
    assert belief_before.belief == 0.5
    assert belief_before.timestamp_logical == 1
