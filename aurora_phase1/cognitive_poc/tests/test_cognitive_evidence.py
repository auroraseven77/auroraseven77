import pytest

from aurora_phase1.cognitive_poc.cognitive_evidence import (
    CognitiveEvidence,
    CognitiveEvidenceOccurrence,
    OccurrenceType,
    SemanticType,
)
from aurora_phase1.core.crypto import hash_object


def make_evidence(content="alpha"):
    return CognitiveEvidence(
        semantic_type=SemanticType.PROPOSITION,
        type_version="1",
        constitutive_projection={
            "assertion": "A",
            "content": content,
        },
    )


def test_evidence_id_is_deterministic():
    a = make_evidence()
    b = make_evidence()
    assert a.evidence_id == b.evidence_id
    assert a.evidence_id == hash_object(a.canonical_object)


def test_constitutive_change_changes_evidence_id():
    assert make_evidence("alpha").evidence_id != make_evidence("beta").evidence_id


def test_type_and_version_are_identity_bearing():
    a = make_evidence()
    b = CognitiveEvidence(
        SemanticType.OBSERVATION,
        "1",
        {"assertion": "A", "content": "alpha"},
    )
    c = CognitiveEvidence(
        SemanticType.PROPOSITION,
        "2",
        {"assertion": "A", "content": "alpha"},
    )
    assert a.evidence_id != b.evidence_id
    assert a.evidence_id != c.evidence_id


def test_evidence_is_immutable():
    e = make_evidence()
    with pytest.raises((AttributeError, TypeError)):
        e.type_version = "2"


def test_constitutive_projection_is_immutable():
    e = make_evidence()
    with pytest.raises(TypeError):
        e.constitutive_projection["content"] = "changed"


def test_multiple_occurrences_share_evidence_id():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 20},
    )
    assert a.evidence_id == b.evidence_id
    assert a.occurrence_id != b.occurrence_id


def test_occurrence_id_is_distinct_from_evidence_id():
    e = make_evidence()
    o = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    assert o.occurrence_id != e.evidence_id


def test_occurrence_id_is_deterministic():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    assert a.occurrence_id == b.occurrence_id
    assert a.occurrence_id == hash_object(a.canonical_object)


def test_occurrence_type_is_identity_bearing():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.PRODUCTION,
        "1",
        {"t_production": 10},
    )
    assert a.occurrence_id != b.occurrence_id


def test_registration_and_consumption_are_not_occurrence_types():
    assert {x.value for x in OccurrenceType} == {
        "OBSERVATION",
        "PRODUCTION",
        "AVAILABILITY",
        "COMPOSITE",
    }


def test_occurrence_is_immutable():
    e = make_evidence()
    o = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    with pytest.raises((AttributeError, TypeError)):
        o.evidence_id = "x"


def test_occurrence_semantics_are_immutable():
    e = make_evidence()
    o = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    with pytest.raises(TypeError):
        o.normalized_occurrence_semantics["t_occurrence"] = 20

def test_availability_uses_t_available():
    e = make_evidence()
    o = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.AVAILABILITY,
        "1",
        {"t_available": 42},
    )
    assert o.canonical_object["normalized_occurrence_semantics"] == {
        "t_available": 42
    }


def test_type_version_changes_occurrence_id():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "2",
        {"t_occurrence": 10},
    )
    assert a.occurrence_id != b.occurrence_id


def test_normalized_semantics_changes_occurrence_id():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 11},
    )
    assert a.occurrence_id != b.occurrence_id


def test_occurrence_id_is_independent_of_evidence_object_provenance():
    e = make_evidence()
    a = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    b = CognitiveEvidenceOccurrence(
        e.evidence_id,
        OccurrenceType.OBSERVATION,
        "1",
        {"t_occurrence": 10},
    )
    assert a.occurrence_id == b.occurrence_id

