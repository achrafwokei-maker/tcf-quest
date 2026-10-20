"""Online beta: invite codes, one private database per tester.

Off by default. Locally (TCFQUEST_MODE unset) every request uses the single learner's database,
exactly as before. With TCFQUEST_MODE=beta:

- TCFQUEST_OWNER is the owner's login, "name:scrypt$salt$hash" (scripts/beta_admin.py owner NAME).
  The name picks the database, so keep it the same when changing the password.
- TCFQUEST_INVITES (optional, for later testers) lists "name:sha256-of-code" pairs, comma-separated.
  Only hashes are stored, never the passwords or codes. Remove a name to revoke that login.
- TCFQUEST_SECRET signs the login cookie (HMAC), so it cannot be forged or edited.
- Every /api request needs a valid cookie, except the login endpoints and the health check.
  The tester's name selects their database (db.current_tester).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import threading
import time

from fastapi import HTTPException

from . import db

COOKIE = "tcfq_tester"
COOKIE_MAX_AGE = 180 * 24 * 3600
OPEN_PATHS = ("/api/beta/", "/api/auth/", "/api/health")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")

# Failed logins per client address: at most MAX_FAILS within WINDOW_S.
MAX_FAILS, WINDOW_S = 10, 15 * 60
_fails: dict[str, list[float]] = {}
_lock = threading.Lock()


def beta_mode() -> bool:
    return os.environ.get("TCFQUEST_MODE") == "beta"


def code_hash(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def password_hash(password: str, salt: bytes | None = None) -> str:
    """Slow, salted hash for a password the owner chose (stdlib scrypt)."""
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _matches(secret: str, stored: str) -> bool:
    if stored.startswith("scrypt$"):
        try:
            salt = bytes.fromhex(stored.split("$")[1])
        except (IndexError, ValueError):
            return False
        return hmac.compare_digest(password_hash(secret, salt), stored)
    return hmac.compare_digest(code_hash(secret), stored)


def invites() -> dict[str, str]:
    """Every allowed login: the owner first, then any invited testers."""
    out = {}
    pairs = [os.environ.get("TCFQUEST_OWNER", "")] + os.environ.get("TCFQUEST_INVITES", "").split(",")
    for pair in pairs:
        # Only the first word counts: pasting into a dashboard often drags along quotes, a newline
        # or the terminal prompt after the value.
        words = pair.replace('"', " ").replace("'", " ").split()
        name, _, digest = (words[0] if words else "").partition(":")
        if NAME.match(name) and name not in out and (len(digest) == 64 or digest.startswith("scrypt$")):
            out[name] = digest.lower()
    return out


def _secret() -> bytes:
    secret = os.environ.get("TCFQUEST_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("TCFQUEST_SECRET must be set (32+ characters) in beta mode")
    return secret.encode()


def sign(name: str) -> str:
    return f"{name}.{hmac.new(_secret(), name.encode(), hashlib.sha256).hexdigest()}"


def verify(cookie: str | None) -> str | None:
    """The tester name in a valid cookie, or None. Revoked testers are rejected."""
    if not cookie or "." not in cookie:
        return None
    name, _, sig = cookie.partition(".")
    if not hmac.compare_digest(sign(name), f"{name}.{sig}"):
        return None
    if os.environ.get("TCFQUEST_FIREBASE_PROJECT"):  # open accounts: any signed name, unless blocked
        blocked = {b.strip() for b in os.environ.get("TCFQUEST_BLOCKED", "").split(",")}
        return name if NAME.match(name) and name not in blocked else None
    return name if name in invites() else None


def login(code: str, client: str) -> str:
    """Returns the tester name for a correct code; raises 401/429 otherwise."""
    now = time.monotonic()
    with _lock:
        recent = [t for t in _fails.get(client, []) if now - t < WINDOW_S]
        _fails[client] = recent
        if len(recent) >= MAX_FAILS:
            raise HTTPException(429, "Too many attempts. Wait 15 minutes.")
    code = code.strip()
    for name, expected in invites().items():
        if _matches(code, expected):
            return name
    with _lock:
        _fails[client].append(now)
    raise HTTPException(401, "Wrong password.")


# ---------- per-tester database ----------

_ready: set[str] = set()


def ensure_ready(conn) -> None:
    """First use of a tester's database in this process: apply migrations, refresh derived data."""
    tester = db.current_tester.get()
    if not tester or tester in _ready:
        return
    from . import estimates, weakness  # late import: these import db too
    db.migrate(conn)
    with db.transaction(conn):
        weakness.backfill(conn)
        estimates.update(conn)
    _ready.add(tester)


class TesterMiddleware:
    """Pure ASGI middleware, so the tester context reaches handlers and background tasks."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not beta_mode():
            return await self.app(scope, receive, send)
        path = scope["path"]
        tester = verify(_cookie(scope))
        if path.startswith("/api/") and not path.startswith(OPEN_PATHS) and tester is None:
            return await _json(send, 401, b'{"detail":"invite_required"}')
        token = db.current_tester.set(tester or "")
        try:
            await self.app(scope, receive, send)
        finally:
            db.current_tester.reset(token)


def _cookie(scope) -> str | None:
    for key, value in scope.get("headers", []):
        if key == b"cookie":
            for part in value.decode("latin-1").split(";"):
                k, _, v = part.strip().partition("=")
                if k == COOKIE:
                    return v
    return None


async def _json(send, status: int, body: bytes) -> None:
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})
