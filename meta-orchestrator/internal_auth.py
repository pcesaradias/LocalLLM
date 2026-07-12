"""Shared internal service-to-service authentication.

Backend services that are only reached over the internal network protect their
endpoints with require_internal_key(); callers attach internal_headers() to
outbound requests. The shared secret is INTERNAL_API_KEY.

Enforcement is opt-in: if INTERNAL_API_KEY is unset the dependency allows the
request (dev/backward-compatible) but logs a warning. Set INTERNAL_API_KEY in
every service (docker-compose does this) to enforce in production.
"""
import logging
import os
import secrets

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def require_internal_key(authorization: str = Header(None)) -> bool:
    """FastAPI dependency: require a valid internal bearer token when configured."""
    expected = os.getenv("INTERNAL_API_KEY")
    if not expected:
        logger.warning(
            "INTERNAL_API_KEY not set; internal endpoint is UNAUTHENTICATED. "
            "Set INTERNAL_API_KEY to enforce service-to-service auth."
        )
        return True
    token = (authorization or "")
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    token = token.strip()
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing internal credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


def internal_headers() -> dict:
    """Authorization header for outbound calls to internal services."""
    key = os.getenv("INTERNAL_API_KEY", "")
    return {"Authorization": f"Bearer {key}"} if key else {}
