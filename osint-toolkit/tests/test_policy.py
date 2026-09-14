import pytest
from osint_toolkit.policy import AuthorizationError, authorize


def test_policy_requires_scope():
    with pytest.raises(AuthorizationError):
        authorize("example.com", [])


def test_policy_accepts_explicit_domain():
    assert authorize("sub.example.com", ["example.com"]) == "sub.example.com"


def test_policy_rejects_sibling_domain():
    with pytest.raises(AuthorizationError):
        authorize("example.net", ["example.com"])
