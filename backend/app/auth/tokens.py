"""Signed login tokens. The token says who the caller is."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class TokenError(Exception):
    """The token is missing, expired, or signed with a different secret."""


def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def issue_token(user_id: str, email: str, role: str, secret: str, ttl_seconds: int) -> str:
    header = _encode(b'{"alg":"HS256","typ":"JWT"}')
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    body = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(f"{header}.{body}", secret)
    return f"{header}.{body}.{signature}"


def read_token(token: str, secret: str) -> dict[str, Any]:
    try:
        header, body, signature = token.split(".")
    except ValueError as exc:
        raise TokenError("malformed token") from exc
    expected = _sign(f"{header}.{body}", secret)
    if not hmac.compare_digest(signature, expected):
        raise TokenError("bad signature")
    payload = json.loads(_decode(body))
    if not isinstance(payload, dict) or int(payload.get("exp", 0)) < time.time():
        raise TokenError("expired token")
    return payload


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return _encode(digest)
