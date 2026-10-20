"""Online accounts (Firebase): token checks, one database per account, owner mapping, cap, export.
Google's signing keys are replaced by a test key, so no network or real accounts are used."""

import datetime as dt
import tempfile
import time
from pathlib import Path

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient

from tcfquest import accounts, testers

PROJECT = "tcfquest-test"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _cert(key):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = dt.datetime.now(dt.timezone.utc)
    c = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
         .serial_number(1).not_valid_before(now).not_valid_after(now + dt.timedelta(days=1)).sign(key, hashes.SHA256()))
    return c.public_bytes(serialization.Encoding.PEM).decode()


def token(sub="uid-1", email="sam@example.com", verified=True, provider="google.com", key=KEY, aud=PROJECT, exp=3600):
    now = int(time.time())
    return jwt.encode({"iss": f"https://securetoken.google.com/{aud}", "aud": aud, "sub": sub, "iat": now,
                       "auth_time": now, "exp": now + exp, "email": email, "email_verified": verified,
                       "firebase": {"sign_in_provider": provider}}, key, algorithm="RS256", headers={"kid": "k1"})


@pytest.fixture()
def app(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        for k, v in {"TCFQUEST_MODE": "beta", "TCFQUEST_FIREBASE_PROJECT": PROJECT, "TCFQUEST_FIREBASE_API_KEY": "pub-key",
                     "TCFQUEST_TESTERS_DIR": tmp, "TCFQUEST_DB": str(Path(tmp) / "unused.db"),
                     "TCFQUEST_SECRET": "s" * 40, "TCFQUEST_ACCOUNT_MAP": "owner@example.com:achraf"}.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("TCFQUEST_TURSO_API_TOKEN", raising=False)
        monkeypatch.setattr(accounts, "_google_certs", lambda: {"k1": _cert(KEY)})
        accounts._known.clear()
        testers._ready.clear()
        from tcfquest.main import app as a
        yield a, Path(tmp)


def browser(app):
    return TestClient(app, base_url="https://testserver")


def sign_in(c, t):
    return c.post("/api/auth/firebase", json={"id_token": t})


def test_config_is_public_and_api_stays_closed(app):
    a, _ = app
    c = browser(a)
    me = c.get("/api/beta/me").json()
    assert me["tester"] is None and me["firebase"] == {"apiKey": "pub-key", "authDomain": f"{PROJECT}.firebaseapp.com", "projectId": PROJECT}
    assert c.get("/api/profile").status_code == 401 and c.get("/api/ai/budget").status_code == 401


def test_each_account_gets_its_own_database(app):
    a, tmp = app
    one, two = browser(a), browser(a)
    assert sign_in(one, token(sub="uid-1")).status_code == 200
    assert sign_in(two, token(sub="uid-2", email="lee@example.com")).status_code == 200
    one.put("/api/profile", json={"display_name": "Sam"})
    assert two.get("/api/profile").json() == {"profile": None}
    assert one.get("/api/profile").json()["profile"]["display_name"] == "Sam"
    assert len(list(tmp.glob("u-*.db"))) == 2
    again = browser(a)                                            # same Google account, new device
    sign_in(again, token(sub="uid-1"))
    assert again.get("/api/profile").json()["profile"]["display_name"] == "Sam"


def test_forged_expired_or_foreign_tokens_are_refused(app):
    a, _ = app
    c = browser(a)
    assert sign_in(c, token(key=OTHER_KEY)).status_code == 401
    assert sign_in(c, token(exp=-120)).status_code == 401
    assert sign_in(c, token(aud="someone-else")).status_code == 401
    assert sign_in(c, "not-a-token-at-all-xxxxxxx").status_code == 401
    assert c.get("/api/profile").status_code == 401


def test_email_password_needs_a_verified_email(app):
    a, _ = app
    c = browser(a)
    r = sign_in(c, token(provider="password", verified=False))
    assert r.status_code == 403 and r.json()["detail"] == "verify_email"
    assert sign_in(c, token(provider="password", verified=True)).status_code == 200


def test_owner_email_keeps_the_existing_database(app):
    a, tmp = app
    c = browser(a)
    assert sign_in(c, token(sub="google-uid", email="Owner@Example.com")).json()["tester"] == "achraf"
    assert sign_in(browser(a), token(sub="x", email="owner@example.com", verified=False)).json()["tester"] != "achraf"


def test_account_cap_and_blocking(app, monkeypatch):
    a, _ = app
    monkeypatch.setenv("TCFQUEST_MAX_ACCOUNTS", "1")
    first = browser(a)
    assert sign_in(first, token(sub="a")).status_code == 200
    first.put("/api/profile", json={"display_name": "A"})
    r = sign_in(browser(a), token(sub="b"))
    assert r.status_code == 403 and r.json()["detail"] == "accounts_full"
    assert sign_in(browser(a), token(sub="a")).status_code == 200     # existing accounts still get in
    name = first.get("/api/beta/me").json()["tester"]
    monkeypatch.setenv("TCFQUEST_BLOCKED", name)
    assert first.get("/api/profile").status_code == 401


def test_export_downloads_all_my_data(app):
    a, _ = app
    c = browser(a)
    sign_in(c, token())
    c.put("/api/profile", json={"display_name": "Sam"})
    r = c.get("/api/account/export")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    body = r.json()
    assert body["format"] == "tcfquest-export-1" and body["tables"]["profile"][0]["display_name"] == "Sam"
    assert "attempt" in body["tables"] and body["schema_version"] >= 14
