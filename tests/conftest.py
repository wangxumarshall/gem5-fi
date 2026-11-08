"""Shared test fixtures.

`test_claim_concurrency.py` was written against a `check(name, condition,
message)` callable. No installed pytest plugin provides that signature
(pytest-check's fixture is `check(condition, message)` and was missing here
before v3.2.9), so the fixture is supplied explicitly. It only turns a false
condition into a test failure; it does not weaken any assertion.
"""
import pytest


@pytest.fixture
def check():
    def _check(name, condition, message=""):
        assert condition, f"{name}: {message}"
    return _check
