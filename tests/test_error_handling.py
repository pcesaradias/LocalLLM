"""Unit tests for the shared CircuitBreaker, focused on call_async.

These verify the resiliency-critical behavior: httpx transport failures
must trip the breaker (the meta-orchestrator makes all outbound calls with
httpx.AsyncClient), an OPEN breaker must reject fast with 503, and the
breaker must recover through HALF_OPEN after the timeout. The module is
loaded directly from a service directory since each service vendors an
identical copy.
"""
import asyncio
import importlib.util
import time
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "meta-orchestrator" / "error_handling.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("error_handling_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


error_handling = _load_module()


def _breaker(threshold=3, recovery=1):
    return error_handling.CircuitBreaker(
        failure_threshold=threshold,
        recovery_timeout=recovery,
        expected_exception=httpx.HTTPError,
    )


async def _failing():
    raise httpx.ConnectError("connection refused")


async def _ok():
    return "fine"


def test_httpx_failures_trip_breaker_to_open():
    # The breaker must count httpx transport errors, not requests' — the
    # orchestrator's outbound calls are all httpx.
    cb = _breaker()
    for _ in range(3):
        with pytest.raises(httpx.HTTPError):
            asyncio.run(cb.call_async(_failing))
    assert cb.state == "OPEN"


def test_open_breaker_rejects_with_503_without_calling():
    cb = _breaker()
    for _ in range(3):
        with pytest.raises(httpx.HTTPError):
            asyncio.run(cb.call_async(_failing))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(cb.call_async(_ok))
    assert exc.value.status_code == 503


def test_breaker_recovers_after_timeout():
    cb = _breaker(recovery=1)
    for _ in range(3):
        with pytest.raises(httpx.HTTPError):
            asyncio.run(cb.call_async(_failing))

    time.sleep(1.1)
    assert asyncio.run(cb.call_async(_ok)) == "fine"
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0


def test_success_passes_result_through():
    cb = _breaker()
    assert asyncio.run(cb.call_async(_ok)) == "fine"
    assert cb.state == "CLOSED"


def test_sync_call_still_works():
    cb = _breaker()
    assert cb.call(lambda: 42) == 42
