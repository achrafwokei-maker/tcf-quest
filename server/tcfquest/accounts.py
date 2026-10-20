"""Online learner accounts via Firebase Authentication (Google + email/password), free Spark plan.

The browser signs in with Firebase and sends its ID token once. The server checks the token's
signature against Google's public keys, then gives the browser the same signed cookie as the
owner login (testers.py), so every other route works unchanged. One private database per account.

Settings (environment, beta only):
  TCFQUEST_FIREBASE_PROJECT, TCFQUEST_FIREBASE_API_KEY   public Firebase web config (not secrets)
  TCFQUEST_ACCOUNT_MAP     "email:name,..." keeps existing databases (e.g. the owner's "achraf")
  TCFQUEST_MAX_ACCOUNTS    new accounts allowed (default 50; Turso free = 100 databases)
  TCFQUEST_TURSO_ORG, TCFQUEST_TURSO_API_TOKEN   lets the server create each new account's database
"""

from __future__ import annotations

import hashlib
import os
import threading
import time

import httpx
from fastapi import HTTPException

from . import db

CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
TURSO_API = "https://api.turso.tech/v1/organizations"

_certs: dict[str, str] = {}
_certs_until = 0.0
_known: set[str] = set()
_lock = threading.Lock()


def project() -> str:
    return db.clean_setting(os.environ.get("TCFQUEST_FIREBASE_PROJECT", ""))


def enabled() -> bool:
    return os.environ.get("TCFQUEST_MODE") == "beta" and bool(project())


def public_config() -> dict | None:
    if not enabled():
        return None
    return {"apiKey": db.clean_setting(os.environ.get("TCFQUEST_FIREBASE_API_KEY", "")), "authDomain": f"{project()}.firebaseapp.com",
            "projectId": project()}


# ---------- ID token check ----------

def _google_certs() -> dict[str, str]:
    global _certs, _certs_until
    with _lock:
        if time.time() < _certs_until:
            return _certs
    r = httpx.get(CERTS_URL, timeout=10)
    r.raise_for_status()
    max_age = 3600
    for part in r.headers.get("cache-control", "").split(","):
        if part.strip().startswith("max-age="):
            max_age = int(part.strip()[8:])
    with _lock:
        _certs, _certs_until = r.json(), time.time() + max_age
        return _certs


def verify_id_token(token: str) -> dict:
    """Claims of a genuine, unexpired Firebase ID token for our project; 401 otherwise."""
    import jwt  # online-only dependencies (pyproject extra "beta")
    from cryptography import x509
    try:
        kid = jwt.get_unverified_header(token).get("kid", "")
        cert = _google_certs().get(kid)
        if not cert:
            raise jwt.InvalidTokenError("unknown signing key")
        key = x509.load_pem_x509_certificate(cert.encode()).public_key()
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=project(),
                            issuer=f"https://securetoken.google.com/{project()}", leeway=30,
                            options={"require": ["exp", "iat", "sub", "auth_time"]})
    except (jwt.PyJWTError, httpx.HTTPError, ValueError, KeyError) as e:
        raise HTTPException(401, "Sign-in could not be verified. Please try again.") from e
    if not claims.get("sub") or claims["auth_time"] > time.time() + 30:
        raise HTTPException(401, "Sign-in could not be verified. Please try again.")
    return claims


# ---------- account → database ----------

def account_map() -> dict[str, str]:
    out = {}
    for pair in os.environ.get("TCFQUEST_ACCOUNT_MAP", "").split(","):
        email, _, name = pair.strip().rpartition(":")
        if email and name:
            out[email.lower()] = name
    return out


def account_name(claims: dict) -> str:
    email = (claims.get("email") or "").lower()
    if email and claims.get("email_verified") and email in account_map():
        return account_map()[email]
    return "u-" + hashlib.sha256(claims["sub"].encode()).hexdigest()[:20]


def sign_in(id_token: str) -> tuple[str, str | None]:
    """(account name, email) after checking the token; creates the account's database if new."""
    claims = verify_id_token(id_token)
    provider = (claims.get("firebase") or {}).get("sign_in_provider")
    if provider == "password" and not claims.get("email_verified"):
        raise HTTPException(403, "verify_email")
    name = account_name(claims)
    ensure_database(name)
    return name, claims.get("email")


def _turso(method: str, path: str, **kw) -> dict:
    r = httpx.request(method, f"{TURSO_API}/{db.clean_setting(os.environ['TCFQUEST_TURSO_ORG'])}{path}", timeout=30,
                      headers={"Authorization": f"Bearer {db.clean_setting(os.environ['TCFQUEST_TURSO_API_TOKEN'])}"}, **kw)
    r.raise_for_status()
    return r.json() if r.content else {}


def _max_accounts() -> int:
    return int(os.environ.get("TCFQUEST_MAX_ACCOUNTS", "50"))


def ensure_database(name: str) -> None:
    """Every account has its own database. Refuses new accounts beyond the cap."""
    if name in _known:
        return
    if os.environ.get("TCFQUEST_TURSO_API_TOKEN") and db.backend() == "libsql":
        names = {d["Name"] for d in _turso("GET", "/databases").get("databases", [])}
        if f"tcfq-{name}" not in names:
            if sum(n.startswith("tcfq-") and n != "tcfq-selftest" for n in names) >= _max_accounts():
                raise HTTPException(403, "accounts_full")
            group = (_turso("GET", "/groups").get("groups") or [{"name": "default"}])[0]["name"]
            _turso("POST", "/databases", json={"name": f"tcfq-{name}", "group": group})
    else:  # local files (tests, local beta run)
        folder = db.testers_dir()
        if not (folder / f"{name}.db").exists() and len(list(folder.glob("*.db"))) >= _max_accounts():
            raise HTTPException(403, "accounts_full")
    _known.add(name)


# ---------- export ----------

def export(conn) -> dict:
    """Everything stored for this learner, as plain JSON (their copy, readable anywhere)."""
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]
    out = {}
    for t in tables:
        cur = conn.execute(f'SELECT * FROM "{t}"')
        out[t] = [dict(zip(r.keys(), tuple(r))) for r in cur.fetchall()]
    return {"format": "tcfquest-export-1", "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "schema_version": db.schema_version(conn), "tables": out}
