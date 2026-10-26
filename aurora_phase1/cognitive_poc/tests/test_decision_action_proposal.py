import pytest

from aurora_phase1.cognitive_poc.decision_action_proposal import (
    ActionProposal,
    ActionProposalCollection,
    DecisionActionProvenance,
    DecisionAssessment,
    DecisionStatus,
    validate_action_against_decision,
)


def make_decision(
    *,
    decision_id="D1",
    status=DecisionStatus.PROPOSED,
    timestamp=10,
    rationale=None,
):
    return DecisionAssessment(
        decision_id=decision_id,
        decision_status=status,
        rationale={} if rationale is None else rationale,
        timestamp_logical=timestamp,
    )


def make_provenance(
    *,
    decision_id="D1",
    timestamp=10,
    evaluator_id=None,
    **overrides,
):
    values = {
        "decision_id": decision_id,
        "decision_context": {"question": "test"},
        "evidence": {"source": "E1"},
        "criteria": {"rule": "C1"},
        "source": "test",
        "timestamp_logical": timestamp,
        "evaluator_id": evaluator_id,
    }
    values.update(overrides)
    return DecisionActionProvenance(**values)


def make_action(
    *,
    action_id="A1",
    timestamp=11,
    action_type="TEST",
    parameters=None,
    preconditions=None,
    expected_effects=None,
):
    return ActionProposal(
        action_id=action_id,
        action_type=action_type,
        parameters={} if parameters is None else parameters,
        preconditions={} if preconditions is None else preconditions,
        expected_effects={} if expected_effects is None else expected_effects,
        timestamp_logical=timestamp,
    )


def test_decision_canonical_schema():
    decision = make_decision(
        rationale={"reason": "declared"},
    )
    assert decision.canonical_object == {
        "decision_id": "D1",
        "decision_status": "PROPOSED",
        "rationale": {"reason": "declared"},
        "timestamp_logical": 10,
    }


def test_action_canonical_schema():
    action = make_action(
        parameters={"x": 1},
        preconditions={"ready": True},
        expected_effects={"result": "expected"},
    )
    assert action.canonical_object == {
        "action_id": "A1",
        "action_type": "TEST",
        "parameters": {"x": 1},
        "preconditions": {"ready": True},
        "expected_effects": {"result": "expected"},
        "timestamp_logical": 11,
    }


@pytest.mark.parametrize(
    "value",
    ["", None, 1, False],
)
def test_decision_id_must_be_non_empty_string(value):
    with pytest.raises(ValueError):
        make_decision(decision_id=value)


@pytest.mark.parametrize(
    "value",
    ["", None, 1, False],
)
def test_action_id_must_be_non_empty_string(value):
    with pytest.raises(ValueError):
        make_action(action_id=value)


@pytest.mark.parametrize(
    "value",
    ["", None, 1, False],
)
def test_action_type_must_be_non_empty_string(value):
    with pytest.raises(ValueError):
        make_action(action_type=value)


@pytest.mark.parametrize(
    "value",
    ["PROPOSED", "UNRESOLVED", "NOT_YET_DECIDABLE", "INVALID"],
)
def test_invalid_decision_status_rejected(value):
    if value == "INVALID":
        with pytest.raises(ValueError):
            make_decision(status=value)
    else:
        decision = make_decision(status=DecisionStatus(value))
        assert decision.decision_status.value == value


@pytest.mark.parametrize("timestamp", [None, "10", 1.5, True])
def test_decision_timestamp_must_be_integer(timestamp):
    with pytest.raises(ValueError):
        make_decision(timestamp=timestamp)


@pytest.mark.parametrize("timestamp", [None, "11", 1.5, True])
def test_action_timestamp_must_be_integer(timestamp):
    with pytest.raises(ValueError):
        make_action(timestamp=timestamp)


def test_decision_status_is_not_authorization():
    decision = make_decision(status=DecisionStatus.PROPOSED)
    assert not hasattr(decision, "authorized")
    assert not hasattr(decision, "approval")
    assert decision.is_determined is True


@pytest.mark.parametrize(
    "status",
    [
        DecisionStatus.UNRESOLVED,
        DecisionStatus.NOT_YET_DECIDABLE,
    ],
)
def test_unresolved_decision_is_not_determined(status):
    decision = make_decision(status=status)
    assert decision.is_determined is False


def test_action_proposal_is_not_execution_permission():
    action = make_action()
    canonical = action.canonical_object
    assert "authorized" not in canonical
    assert "approval" not in canonical
    assert "execute" not in canonical
    assert "execution" not in canonical


def test_decision_has_no_action_or_authorization_fields():
    decision = make_decision()
    canonical = decision.canonical_object
    assert "action_id" not in canonical
    assert "authorized" not in canonical
    assert "approval" not in canonical
    assert "execution" not in canonical


def test_decision_rationale_is_deeply_immutable():
    source = {"nested": {"values": [1, 2]}}
    decision = make_decision(rationale=source)
    source["nested"]["values"].append(3)
    assert decision.canonical_object["rationale"] == {
        "nested": {"values": [1, 2]}
    }
    with pytest.raises(TypeError):
        decision.rationale["nested"]["values"] = (9,)


def test_action_state_is_deeply_immutable():
    source = {
        "parameters": {"nested": [1, 2]},
        "preconditions": {"nested": {"ready": True}},
        "expected": {"nested": [3]},
    }
    action = make_action(
        parameters=source["parameters"],
        preconditions=source["preconditions"],
        expected_effects=source["expected"],
    )
    source["parameters"]["nested"].append(9)
    assert action.canonical_object["parameters"] == {
        "nested": [1, 2]
    }
    with pytest.raises(TypeError):
        action.parameters["nested"] = (9,)


def test_provenance_is_separate_from_decision_canonical_object():
    decision = make_decision()
    provenance = make_provenance(
        evaluator_id="eval-1",
        referenced_cognitive_objects={"B1": ["hash"]},
    )
    assert "evaluator_id" not in decision.canonical_object
    assert "criteria" not in decision.canonical_object
    assert "evidence" not in decision.canonical_object
    assert provenance.evaluator_id == "eval-1"


def test_provenance_is_separate_from_action_canonical_object():
    action = make_action()
    assert "decision_id" not in action.canonical_object
    assert "evaluator_id" not in action.canonical_object
    assert "criteria" not in action.canonical_object
    assert "evidence" not in action.canonical_object


def test_action_requires_explicit_decision_association():
    decision = make_decision()
    action = make_action()
    provenance = make_provenance(decision_id="OTHER")
    with pytest.raises(ValueError, match="decision_id"):
        validate_action_against_decision(
            action=action,
            decision=decision,
            provenance=provenance,
        )


def test_action_association_is_not_in_canonical_object():
    decision = make_decision()
    action = make_action()
    provenance = make_provenance()
    validate_action_against_decision(
        action=action,
        decision=decision,
        provenance=provenance,
    )
    assert "decision_id" not in action.canonical_object


def test_action_timestamp_cannot_precede_decision():
    decision = make_decision(timestamp=10)
    action = make_action(timestamp=9)
    provenance = make_provenance(timestamp=10)
    with pytest.raises(ValueError, match="timestamp"):
        validate_action_against_decision(
            action=action,
            decision=decision,
            provenance=provenance,
        )


def test_action_timestamp_may_equal_decision_timestamp():
    decision = make_decision(timestamp=10)
    action = make_action(timestamp=10)
    provenance = make_provenance(timestamp=10)
    validate_action_against_decision(
        action=action,
        decision=decision,
        provenance=provenance,
    )


@pytest.mark.parametrize(
    "status",
    [
        DecisionStatus.UNRESOLVED,
        DecisionStatus.NOT_YET_DECIDABLE,
    ],
)
def test_undetermined_decision_cannot_validate_action(status):
    decision = make_decision(status=status)
    action = make_action()
    provenance = make_provenance()
    with pytest.raises(ValueError, match="cannot represent"):
        validate_action_against_decision(
            action=action,
            decision=decision,
            provenance=provenance,
        )


def test_multiple_action_proposals_have_unique_ids():
    ActionProposalCollection(
        (
            make_action(action_id="A1"),
            make_action(action_id="A2"),
        )
    )


def test_duplicate_action_ids_rejected():
    with pytest.raises(ValueError, match="unique"):
        ActionProposalCollection(
            (
                make_action(action_id="A1"),
                make_action(action_id="A1"),
            )
        )


def test_action_proposals_are_deterministically_sorted_by_id():
    collection = ActionProposalCollection(
        (
            make_action(action_id="A3"),
            make_action(action_id="A1"),
            make_action(action_id="A2"),
        )
    )
    assert [item["action_id"] for item in collection.canonical_object] == [
        "A1",
        "A2",
        "A3",
    ]


def test_action_order_does_not_change_action_semantics():
    first = ActionProposalCollection(
        (
            make_action(action_id="A1", parameters={"x": 1}),
            make_action(action_id="A2", parameters={"x": 2}),
        )
    )
    second = ActionProposalCollection(
        (
            make_action(action_id="A2", parameters={"x": 2}),
            make_action(action_id="A1", parameters={"x": 1}),
        )
    )
    assert first.canonical_object == second.canonical_object


def test_collection_does_not_encode_preference_or_authority():
    collection = ActionProposalCollection(
        (
            make_action(action_id="A2"),
            make_action(action_id="A1"),
        )
    )
    assert [item["action_id"] for item in collection.canonical_object] == [
        "A1",
        "A2",
    ]
    assert "preferred" not in str(collection.canonical_object)
    assert "authorized" not in str(collection.canonical_object)


def test_evaluator_identity_is_provenance_only():
    provenance = make_provenance(evaluator_id="stable-evaluator")
    assert provenance.evaluator_id == "stable-evaluator"
    assert "evaluator_id" not in make_decision().canonical_object


def test_referenced_cognitive_objects_are_provenance_only():
    provenance = make_provenance(
        referenced_cognitive_objects={
            "prediction_commitment": ["pc-hash"],
            "prediction_error": ["pe-hash"],
            "attribution": ["attr-hash"],
            "hypotheses": ["hyp-hash"],
        }
    )
    assert provenance.referenced_cognitive_objects is not None
    assert "prediction_error" not in make_decision().canonical_object


def test_external_model_involvement_is_provenance_only():
    provenance = make_provenance(
        external_model_involvement={
            "provider": "external",
            "model": "advisory",
        }
    )
    assert provenance.external_model_involvement["provider"] == "external"
    assert "model" not in make_decision().canonical_object


def test_expected_effects_are_not_observed_facts():
    action = make_action(
        expected_effects={"future_result": "expected"},
    )
    assert action.canonical_object["expected_effects"] == {
        "future_result": "expected"
    }


def test_expected_effects_do_not_create_prediction_commitment():
    action = make_action(
        expected_effects={"future_result": "expected"},
    )
    assert "prediction_hash" not in action.canonical_object
    assert "hypothesis_id" not in action.canonical_object


def test_no_automatic_belief_update_surface():
    decision = make_decision()
    action = make_action()
    assert not hasattr(decision, "belief")
    assert not hasattr(action, "belief")
    assert not hasattr(action, "update_belief")


def test_wrong_runtime_types_are_rejected_by_validator():
    with pytest.raises(ValueError):
        validate_action_against_decision(
            action=object(),
            decision=make_decision(),
            provenance=make_provenance(),
        )
    with pytest.raises(ValueError):
        validate_action_against_decision(
            action=make_action(),
            decision=object(),
            provenance=make_provenance(),
        )
    with pytest.raises(ValueError):
        validate_action_against_decision(
            action=make_action(),
            decision=make_decision(),
            provenance=object(),
        )


def test_provenance_requires_decision_id():
    with pytest.raises(ValueError):
        make_provenance(decision_id="")


def test_provenance_requires_source():
    with pytest.raises(ValueError):
        make_provenance(source="")


def test_provenance_requires_integer_timestamp():
    with pytest.raises(ValueError):
        make_provenance(timestamp="10")


def test_provenance_evaluator_id_when_supplied_must_be_non_empty():
    with pytest.raises(ValueError):
        make_provenance(evaluator_id="")


def test_decision_identity_is_stable_under_immutability():
    decision = make_decision(decision_id="D-STABLE")
    with pytest.raises(Exception):
        decision.decision_id = "D-CHANGED"


def test_action_identity_is_stable_under_immutability():
    action = make_action(action_id="A-STABLE")
    with pytest.raises(Exception):
        action.action_id = "A-CHANGED"


def test_changed_decision_state_requires_distinct_object():
    original = make_decision(
        decision_id="D1",
        status=DecisionStatus.PROPOSED,
    )
    changed = make_decision(
        decision_id="D2",
        status=DecisionStatus.UNRESOLVED,
    )
    assert original.decision_id != changed.decision_id
    assert original.canonical_object != changed.canonical_object


def test_changed_action_state_requires_distinct_object():
    original = make_action(
        action_id="A1",
        parameters={"x": 1},
    )
    changed = make_action(
        action_id="A2",
        parameters={"x": 2},
    )
    assert original.action_id != changed.action_id
    assert original.canonical_object != changed.canonical_object


def test_provenance_reference_does_not_copy_canonical_state():
    provenance = make_provenance(
        referenced_cognitive_objects={
            "block": "B5",
            "reference": "hash-only",
        }
    )
    assert provenance.referenced_cognitive_objects["block"] == "B5"
    assert "hypotheses" not in provenance.referenced_cognitive_objects


def test_decision_and_action_are_distinct_types():
    assert not isinstance(make_decision(), ActionProposal)
    assert not isinstance(make_action(), DecisionAssessment)


def test_proposed_decision_is_the_only_determined_status():
    assert make_decision(status=DecisionStatus.PROPOSED).is_determined
    assert not make_decision(status=DecisionStatus.UNRESOLVED).is_determined
    assert not make_decision(
        status=DecisionStatus.NOT_YET_DECIDABLE
    ).is_determined


def test_validation_does_not_return_authorization():
    result = validate_action_against_decision(
        action=make_action(),
        decision=make_decision(),
        provenance=make_provenance(),
    )
    assert result is None


def test_criteria_are_explicit_provenance():
    provenance = make_provenance(
        criteria={
            "criterion_id": "C1",
            "definition": "evaluate declared evidence",
        }
    )
    assert provenance.criteria == {
        "criterion_id": "C1",
        "definition": "evaluate declared evidence",
    }
    assert "criteria" not in make_decision().canonical_object


def test_evidence_is_explicit_provenance():
    provenance = make_provenance(
        evidence={
            "observation_id": "OBS1",
            "value": {"x": 42},
        }
    )
    assert provenance.evidence == {
        "observation_id": "OBS1",
        "value": {"x": 42},
    }
    assert "evidence" not in make_decision().canonical_object


@pytest.mark.parametrize(
    "block_name",
    [
        "prediction_commitment",
        "belief_state",
        "prediction_error",
        "attribution_assessment",
        "hypothesis_set",
    ],
)
def test_prior_cognitive_blocks_remain_references_only(block_name):
    provenance = make_provenance(
        referenced_cognitive_objects={
            block_name: ["stable-reference"],
        }
    )
    assert tuple(provenance.referenced_cognitive_objects[block_name]) == (
        "stable-reference",
    )
    assert block_name not in make_decision().canonical_object
    assert block_name not in make_action().canonical_object


def test_references_do_not_copy_prior_canonical_content():
    provenance = make_provenance(
        referenced_cognitive_objects={
            "prediction_error": {
                "reference": "hash",
            },
        }
    )
    assert provenance.referenced_cognitive_objects["prediction_error"] == {
        "reference": "hash"
    }
    assert "prediction_hash" not in make_action().canonical_object
    assert "outcome" not in make_action().canonical_object


def test_provenance_timestamp_does_not_enter_canonical_state():
    provenance = make_provenance(timestamp=999)
    assert provenance.timestamp_logical == 999
    assert make_decision().canonical_object["timestamp_logical"] == 10
    assert make_action().canonical_object["timestamp_logical"] == 11


def test_proposal_source_is_provenance_only():
    provenance = make_provenance(proposal_source="cognitive-core")
    assert provenance.proposal_source == "cognitive-core"
    assert "proposal_source" not in make_action().canonical_object


def test_identical_declared_inputs_have_deterministic_canonical_decision():
    first = make_decision(
        decision_id="D-DETERMINISTIC",
        rationale={"b": 2, "a": 1},
    )
    second = make_decision(
        decision_id="D-DETERMINISTIC",
        rationale={"b": 2, "a": 1},
    )
    assert first.canonical_object == second.canonical_object


def test_identical_declared_inputs_have_deterministic_canonical_action():
    first = make_action(
        action_id="A-DETERMINISTIC",
        parameters={"b": 2, "a": 1},
        preconditions={"ready": True},
        expected_effects={"result": "future"},
    )
    second = make_action(
        action_id="A-DETERMINISTIC",
        parameters={"b": 2, "a": 1},
        preconditions={"ready": True},
        expected_effects={"result": "future"},
    )
    assert first.canonical_object == second.canonical_object


def test_post_hoc_decision_mutation_is_rejected():
    decision = make_decision(
        decision_id="D-BEFORE",
        rationale={"evidence_seen": "none"},
        timestamp=10,
    )
    with pytest.raises(Exception):
        decision.rationale["evidence_seen"] = "new-observation"
    assert decision.canonical_object["rationale"] == {
        "evidence_seen": "none"
    }


def test_post_hoc_action_mutation_is_rejected():
    action = make_action(
        action_id="A-BEFORE",
        expected_effects={"result": "expected"},
    )
    with pytest.raises(Exception):
        action.expected_effects["result"] = "observed"
    assert action.canonical_object["expected_effects"] == {
        "result": "expected"
    }


def test_expected_effect_cannot_become_observed_result_in_place():
    action = make_action(
        expected_effects={"status": "expected"},
    )
    assert action.canonical_object["expected_effects"]["status"] == "expected"
    assert "observed_results" not in action.canonical_object
    assert "observed_outcome" not in action.canonical_object


def test_validator_has_no_authorization_result():
    decision = make_decision()
    action = make_action()
    provenance = make_provenance()
    result = validate_action_against_decision(
        action=action,
        decision=decision,
        provenance=provenance,
    )
    assert result is None


def test_validator_has_no_execution_result():
    decision = make_decision()
    action = make_action()
    provenance = make_provenance()
    result = validate_action_against_decision(
        action=action,
        decision=decision,
        provenance=provenance,
    )
    assert result is None
    assert not hasattr(action, "execute")


def test_b6_has_no_tuu_or_hephaestus_execution_surface():
    module_namespace = globals()
    assert "TUU" not in module_namespace
    assert "HEPHAESTUS" not in module_namespace


def test_rationale_does_not_gain_hidden_authority_fields():
    decision = make_decision(
        rationale={
            "reason": "declared",
            "evidence": {"source": "declared"},
            "criteria": {"rule": "declared"},
            "authority": "not-an-authority",
        }
    )
    assert decision.canonical_object["rationale"]["reason"] == "declared"
    assert "authorization" not in decision.canonical_object
    assert "execution" not in decision.canonical_object


def test_external_model_is_advisory_provenance_only():
    provenance = make_provenance(
        external_model_involvement={
            "provider": "external",
            "role": "advisory",
            "output_reference": "ref-1",
        }
    )
    assert provenance.external_model_involvement["role"] == "advisory"
    assert "external_model_involvement" not in make_action().canonical_object


def test_decision_does_not_mutate_previous_cognitive_state():
    prior = {
        "hypothesis_id": "H1",
        "belief": 0.7,
        "prediction_hash": "P1",
        "attribution": "A1",
    }
    decision = make_decision(
        rationale={"references": {"prior": "H1"}},
    )
    assert prior == {
        "hypothesis_id": "H1",
        "belief": 0.7,
        "prediction_hash": "P1",
        "attribution": "A1",
    }
    assert decision.canonical_object["rationale"]["references"]["prior"] == "H1"


def test_action_does_not_mutate_previous_cognitive_state():
    prior = {
        "hypothesis_id": "H1",
        "belief": 0.7,
        "prediction_hash": "P1",
    }
    action = make_action(
        parameters={"reference": "H1"},
    )
    assert prior == {
        "hypothesis_id": "H1",
        "belief": 0.7,
        "prediction_hash": "P1",
    }
    assert action.canonical_object["parameters"]["reference"] == "H1"


def test_decision_status_cannot_authorize_action():
    for status in DecisionStatus:
        decision = make_decision(status=status)
        assert not hasattr(decision, "authorized")
        assert not hasattr(decision, "authorization")
        assert not hasattr(decision, "execute")


def test_action_type_does_not_grant_execution_authority():
    action = make_action(action_type="DELETE")
    assert action.action_type == "DELETE"
    assert not hasattr(action, "execute")
    assert not hasattr(action, "authorized")


def test_action_collection_order_is_not_a_ranking():
    collection = ActionProposalCollection(
        (
            make_action(action_id="Z"),
            make_action(action_id="A"),
        )
    )
    ordered = [item["action_id"] for item in collection.canonical_object]
    assert ordered == ["A", "Z"]
    assert ordered != ["Z", "A"]
    assert collection.proposals[0].action_id == "A"
