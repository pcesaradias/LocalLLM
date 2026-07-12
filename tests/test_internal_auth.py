"""Unit tests for the shared internal service-to-service auth module.

These verify the security-critical behavior: enforcement is opt-in when
INTERNAL_API_KEY is unset, and strict (constant-time) when it is set.
The module is loaded directly from a service directory since each service
vendors an identical copy.
"""
import importlib.util
import os
from pathlib import Path

import pytest
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "meta-orchestrator" / "internal_auth.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("internal_auth_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


internal_auth = _load_module()


@pytest.fixture(autouse=True)
def clear_key(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    yield


def test_unset_key_allows_and_returns_true():
    # Backward-compatible dev mode: no key configured -> request allowed.
    assert internal_auth.require_internal_key(authorization=None) is True


def test_set_key_accepts_matching_bearer(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    assert internal_auth.require_internal_key(authorization="Bearer s3cret") is True


def test_set_key_accepts_raw_token_without_bearer_prefix(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    assert internal_auth.require_internal_key(authorization="s3cret") is True


def test_set_key_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        internal_auth.require_internal_key(authorization="Bearer wrong")
    assert exc.value.status_code == 401


def test_set_key_rejects_missing_header(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        internal_auth.require_internal_key(authorization=None)
    assert exc.value.status_code == 401


def test_internal_headers_present_when_key_set(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    assert internal_auth.internal_headers() == {"Authorization": "Bearer s3cret"}


def test_internal_headers_empty_when_key_unset():
    assert internal_auth.internal_headers() == {}
