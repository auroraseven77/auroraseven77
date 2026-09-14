import pytest
from pydantic import ValidationError
from osint_toolkit.models import Observation


def test_observation_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Observation(source="test", target="example.com", entity_type="dns", value="A 1.2.3.4", confidence=0.9, unexpected=True)


def test_observation_rejects_naive_timestamp():
    with pytest.raises(ValidationError):
        Observation(source="test", timestamp="2026-01-01T00:00:00", target="example.com", entity_type="dns", value="x", confidence=0.9)
