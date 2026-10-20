"""Online beta: invite codes, isolated tester databases, web app serving. Off unless TCFQUEST_MODE=beta."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import testers

CODES = {"amina": "soleil-7421", "jo": "pluie-0388"}


@pytest.fixture()
def beta(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_MODE", "beta")
        monkeypatch.setenv("TCFQUEST_TESTERS_DIR", tmp)
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "must-not-be-used.db"))
        monkeypatch.setenv("TCFQUEST_SECRET", "x" * 40)
        monkeypatch.setenv("TCFQUEST_INVITES", ",".join(f"{n}:{testers.code_hash(c)}" for n, c in CODES.items()))
        testers._fails.clear()
        testers._ready.clear()
        from tcfquest.main import app

        yield app, Path(tmp)


def client_for(app, name=None):
    c = TestClient(app, base_url="https://testserver")  # the cookie is Secure: HTTPS only
    if name:
        assert c.post("/api/beta/login", json={"code": CODES[name]}).json() == {"beta": True, "tester": name}
    return c


def test_api_needs_an_invite(beta):
    app, _ = beta
    c = client_for(app)
    assert c.get("/api/profile").status_code == 401
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/beta/me").json() == {"beta": True, "tester": None, "firebase": None}
    assert c.post("/api/beta/login", json={"code": "wrong-code"}).status_code == 401


def test_each_tester_has_a_private_database(beta):
    app, tmp = beta
    a, b = client_for(app, "amina"), client_for(app, "jo")
    assert a.put("/api/profile", json={"display_name": "Amina"}).status_code == 200
    assert a.get("/api/profile").json()["profile"]["display_name"] == "Amina"
    assert b.get("/api/profile").json() == {"profile": None}
    assert {p.name for p in tmp.glob("*.db")} == {"amina.db", "jo.db"}


def test_forged_and_revoked_cookies_are_rejected(beta, monkeypatch):
    app, _ = beta
    c = client_for(app)
    c.cookies.set(testers.COOKIE, "amina.0000", domain="testserver")
    assert c.get("/api/profile").status_code == 401
    a = client_for(app, "amina")
    assert a.get("/api/profile").status_code == 200
    monkeypatch.setenv("TCFQUEST_INVITES", f"jo:{testers.code_hash(CODES['jo'])}")  # amina removed
    assert a.get("/api/profile").status_code == 401


def test_repeated_wrong_codes_are_slowed_down(beta):
    app, _ = beta
    c = client_for(app)
    for _ in range(testers.MAX_FAILS):
        assert c.post("/api/beta/login", json={"code": "guess-1234"}).status_code == 401
    assert c.post("/api/beta/login", json={"code": CODES["amina"]}).status_code == 429


def test_backup_endpoint_is_closed_online(beta):
    app, _ = beta
    assert client_for(app, "jo").post("/api/backup").status_code == 403


def test_local_mode_is_unchanged(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.delenv("TCFQUEST_MODE", raising=False)
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            assert c.get("/api/beta/me").json() == {"beta": False, "tester": None, "firebase": None}
            assert c.get("/api/profile").status_code == 200
            assert c.post("/api/beta/login", json={"code": "anything"}).status_code == 404


def test_serves_the_web_app_with_page_fallback(monkeypatch, tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "app-1a2b.js").write_text("js")
    (tmp_path.parent / "secret.txt").write_text("no")
    monkeypatch.setenv("TCFQUEST_SERVE_WEB", "1")
    monkeypatch.setenv("TCFQUEST_WEB_DIST", str(tmp_path))
    monkeypatch.setenv("TCFQUEST_DB", str(tmp_path / "t.db"))
    from tcfquest.main import app

    c = TestClient(app)
    assert c.get("/aventure").text == "<html>app</html>"
    r = c.get("/assets/app-1a2b.js")
    assert r.text == "js" and "immutable" in r.headers["cache-control"]
    assert c.get("/../secret.txt").text == "<html>app</html>"
    assert c.get("/%2e%2e/secret.txt").text == "<html>app</html>"
    assert c.get("/api/nothing-here").status_code == 404


def test_owner_password_login_and_changing_it_keeps_the_data(beta, monkeypatch):
    app, tmp = beta
    monkeypatch.delenv("TCFQUEST_INVITES")
    monkeypatch.setenv("TCFQUEST_OWNER", f"achraf:{testers.password_hash('quatre mots en ville')}")
    c = client_for(app)
    assert c.post("/api/beta/login", json={"code": "wrong password!"}).status_code == 401
    assert c.post("/api/beta/login", json={"code": "quatre mots en ville"}).json()["tester"] == "achraf"
    c.put("/api/profile", json={"display_name": "Achraf"})
    assert "scrypt$" in testers.invites()["achraf"] and "quatre" not in str(testers.invites())
    monkeypatch.setenv("TCFQUEST_OWNER", f"achraf:{testers.password_hash('un autre mot de passe')}")
    assert c.get("/api/profile").status_code == 200              # still signed in: same name, same data
    d = client_for(app)
    assert d.post("/api/beta/login", json={"code": "quatre mots en ville"}).status_code == 401
    assert d.post("/api/beta/login", json={"code": "un autre mot de passe"}).status_code == 200
    assert d.get("/api/profile").json()["profile"]["display_name"] == "Achraf"
    assert d.post("/api/eo/whatever/start").status_code != 401 and client_for(app).get("/api/ai/budget").status_code == 401


def test_health_check_works_before_sign_in(beta, monkeypatch):
    """Render's health check has no cookie; it must not touch any database (that crashed the first deploy)."""
    app, tmp = beta
    monkeypatch.setenv("TCFQUEST_DB_BACKEND", "libsql")
    monkeypatch.setenv("TCFQUEST_AI_PROVIDER", "workers")
    r = client_for(app).get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True
    assert not list(tmp.glob("*.db"))


def test_owner_value_survives_messy_pasting(beta, monkeypatch):
    app, _ = beta
    h = testers.password_hash("quatre mots en ville")
    for messy in (f"achraf:{h}\nachrafboudinar@Mac tcf-quest %", f'  "achraf:{h}"  ', f"achraf:{h} "):
        monkeypatch.setenv("TCFQUEST_OWNER", messy)
        assert testers.invites()["achraf"] == h
    assert client_for(app).post("/api/beta/login", json={"code": "quatre mots en ville"}).json()["tester"] == "achraf"


def test_first_requests_in_parallel_prepare_the_database_once(beta):
    """A new account's first page fires several requests at once; they must not collide."""
    from concurrent.futures import ThreadPoolExecutor
    app, _ = beta
    a = client_for(app, "amina")
    with ThreadPoolExecutor(6) as pool:
        codes = list(pool.map(lambda p: a.get(p).status_code, ["/api/profile", "/api/today", "/api/journey",
                                                               "/api/vocab", "/api/profile", "/api/ai/budget"]))
    assert codes == [200] * 6
