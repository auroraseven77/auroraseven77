import pytest

from aurora_phase1.cognitive_poc.belief_state import BeliefState
from aurora_phase1.cognitive_poc.belief_update import (
    BeliefUpdate,
    BeliefUpdateOutcome,
    UpdateRule,
    validate_belief_update,
)
from aurora_phase1.cognitive_poc.cognitive_evidence import (
    CognitiveEvidence,
    CognitiveEvidenceOccurrence,
    OccurrenceType,
    SemanticType,
)


def make_evidence():
    return CognitiveEvidence(
        semantic_type=SemanticType.OBSERVATION,
        type_version="1",
        constitutive_projection={"value": 42},
    )


def make_occurrence(evidence):
    return CognitiveEvidenceOccurrence(
        evidence_id=evidence.evidence_id,
        occurrence_type=OccurrenceType.OBSERVATION,
        type_version="1",
        normalized_occurrence_semantics={"t_occurrence": 10},
    )


def make_rule():
    return UpdateRule(
        rule_id="RULE-BELIEF-1",
        version="1",
        representation="deterministic-demo-rule",
        parameters={"alpha": 0.5},
    )


def test_belief_identity_is_canonical_hash():
    state = BeliefState("H1", 0.5, 1)
    assert len(state.belief_identity) == 64
    assert state.belief_identity != BeliefState("H1", 0.6, 1).belief_identity


def test_belief_identity_excludes_provenance():
    state = BeliefState("H1", 0.5, 1)
    assert state.belief_identity == BeliefState("H1", 0.5, 1).belief_identity


def test_update_rule_has_stable_identity():
    a = make_rule()
    b = make_rule()
    assert a.rule_identity == b.rule_identity


def test_update_rule_parameters_are_immutable():
    rule = make_rule()
    with pytest.raises(TypeError):
        rule.parameters["alpha"] = 0.9


def test_effective_update_requires_new_successor_identity():
    prior = BeliefState("H1", 0.5, 1)
    evidence = make_evidence()
    rule = make_rule()

    with pytest.raises(ValueError):
        BeliefUpdate(
            prior_identity=prior.belief_identity,
            evidence_id=evidence.evidence_id,
            update_rule=rule,
            successor_identity=prior.belief_identity,
        )


def test_effective_update_validates_evidence_and_occurrence_lineage():
    prior = BeliefState("H1", 0.5, 1)
    successor = BeliefState("H1", 0.7, 2)
    evidence = make_evidence()
    occurrence = make_occurrence(evidence)

    update = BeliefUpdate(
        prior_identity=prior.belief_identity,
        evidence_id=evidence.evidence_id,
        occurrence_id=occurrence.occurrence_id,
        update_rule=make_rule(),
        successor_identity=successor.belief_identity,
    )

    validate_belief_update(
        update,
        prior_state=prior,
        successor_state=successor,
        evidence=evidence,
        occurrence=occurrence,
    )


def test_mismatched_occurrence_is_rejected():
    prior = BeliefState("H1", 0.5, 1)
    successor = BeliefState("H1", 0.7, 2)
    evidence_a = make_evidence()
    evidence_b = CognitiveEvidence(
        semantic_type=SemanticType.OBSERVATION,
        type_version="1",
        constitutive_projection={"value": 99},
    )
    occurrence_b = make_occurrence(evidence_b)

    update = BeliefUpdate(
        prior_identity=prior.belief_identity,
        evidence_id=evidence_a.evidence_id,
        occurrence_id=occurrence_b.occurrence_id,
        update_rule=make_rule(),
        successor_identity=successor.belief_identity,
    )

    with pytest.raises(ValueError):
        validate_belief_update(
            update,
            prior_state=prior,
            successor_state=successor,
            evidence=evidence_a,
            occurrence=occurrence_b,
        )


def test_occurrence_cannot_be_silently_inferred():
    prior = BeliefState("H1", 0.5, 1)
    successor = BeliefState("H1", 0.7, 2)
    evidence = make_evidence()
    occurrence = make_occurrence(evidence)

    update = BeliefUpdate(
        prior_identity=prior.belief_identity,
        evidence_id=evidence.evidence_id,
        occurrence_id=occurrence.occurrence_id,
        update_rule=make_rule(),
        successor_identity=successor.belief_identity,
    )

    with pytest.raises(ValueError):
        validate_belief_update(
            update,
            prior_state=prior,
            successor_state=successor,
            evidence=evidence,
            occurrence=None,
        )


def test_no_update_has_no_successor():
    prior = BeliefState("H1", 0.5, 1)
    evidence = make_evidence()

    update = BeliefUpdate(
        prior_identity=prior.belief_identity,
        evidence_id=evidence.evidence_id,
        update_rule=make_rule(),
        successor_identity=None,
        outcome=BeliefUpdateOutcome.NO_UPDATE,
    )

    validate_belief_update(
        update,
        prior_state=prior,
        successor_state=None,
        evidence=evidence,
    )


def test_no_implicit_temporal_equivalence():
    prior = BeliefState("H1", 0.5, 100)
    successor = BeliefState("H1", 0.7, 101)
    evidence = make_evidence()
    occurrence = make_occurrence(evidence)

    update = BeliefUpdate(
        prior_identity=prior.belief_identity,
        evidence_id=evidence.evidence_id,
        occurrence_id=occurrence.occurrence_id,
        update_rule=make_rule(),
        successor_identity=successor.belief_identity,
    )

    validate_belief_update(
        update,
        prior_state=prior,
        successor_state=successor,
        evidence=evidence,
        occurrence=occurrence,
    )



def test_non_update_rejects_successor_identity():
    prior = BeliefState("H1", 0.5, 1)
    evidence = make_evidence()

    with pytest.raises(ValueError, match="non-UPDATE outcome"):
        BeliefUpdate(
            prior_identity=prior.belief_identity,
            evidence_id=evidence.evidence_id,
            update_rule=make_rule(),
            successor_identity="FORBIDDEN_SUCCESSOR",
            outcome=BeliefUpdateOutcome.NO_UPDATE,
        )


def test_update_requires_successor_identity():
    prior = BeliefState("H1", 0.5, 1)
    evidence = make_evidence()

    with pytest.raises(ValueError, match="UPDATE requires successor_identity"):
        BeliefUpdate(
            prior_identity=prior.belief_identity,
            evidence_id=evidence.evidence_id,
            update_rule=make_rule(),
            successor_identity=None,
            outcome=BeliefUpdateOutcome.UPDATE,
        )
