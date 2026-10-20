"""Online beta admin, run by the owner on the Mac (never on the server).

    server/.venv/bin/python scripts/beta_admin.py setup          # once: Turso group + server token
    server/.venv/bin/python scripts/beta_admin.py owner achraf   # your login: database + password (asked, hidden)
    server/.venv/bin/python scripts/beta_admin.py add amina      # later: invited tester, database + code
    server/.venv/bin/python scripts/beta_admin.py remove amina   # revoke (the database is kept)
    server/.venv/bin/python scripts/beta_admin.py invites        # the TCFQUEST_INVITES value for Render
    server/.venv/bin/python scripts/beta_admin.py backup         # copy every tester database to data/beta-backups/
    server/.venv/bin/python scripts/beta_admin.py selftest       # check the app's database code against real Turso

Secrets live in data/beta-admin.env (git-ignored), written by you and by `setup`:
    TURSO_ORG=your-turso-username
    TURSO_API_TOKEN=...            (Turso dashboard → Settings → API Tokens)
The tester list (names and code hashes only, never the codes) is data/beta-testers.json.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import httpx  # noqa: E402

ENV_FILE = ROOT / "data" / "beta-admin.env"
TESTERS_FILE = ROOT / "data" / "beta-testers.json"
BACKUPS = ROOT / "data" / "beta-backups"
API = "https://api.turso.tech/v1/organizations"
LOCATION = "aws-us-east-1"   # North America east, next to Render's Virginia region
WORDS = ["soleil", "pluie", "marche", "fleuve", "erable", "nuage", "phare", "jardin", "lanterne", "boussole",
         "colline", "riviere", "violon", "montagne", "foret", "voilier", "etoile", "canard", "chouette", "olive"]


def env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.exit(f"Create {ENV_FILE.relative_to(ROOT)} first (see the top of this script).")
    out = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    missing = [k for k in ("TURSO_ORG", "TURSO_API_TOKEN") if not out.get(k)]
    if missing:
        sys.exit(f"Fill in {', '.join(missing)} in {ENV_FILE.relative_to(ROOT)}, save the file, then run this again.")
    return out


def save_env(**values: str) -> None:
    lines = [ln for ln in ENV_FILE.read_text().splitlines() if ln.partition("=")[0].strip() not in values]
    ENV_FILE.write_text("\n".join(lines + [f"{k}={v}" for k, v in values.items()]) + "\n")
    ENV_FILE.chmod(0o600)


def turso(method: str, path: str, **kw) -> dict:
    e = env()
    r = httpx.request(method, f"{API}/{e['TURSO_ORG']}{path}", timeout=60,
                      headers={"Authorization": f"Bearer {e['TURSO_API_TOKEN']}"}, **kw)
    if r.status_code >= 400:
        sys.exit(f"Turso said {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}


def testers() -> dict[str, str]:
    return json.loads(TESTERS_FILE.read_text()) if TESTERS_FILE.exists() else {}


def invites_value() -> str:
    return ",".join(f"{n}:{h}" for n, h in testers().items())


def group() -> str:
    groups = turso("GET", "/groups").get("groups", [])
    if groups:
        return groups[0]["name"]
    turso("POST", "/groups", json={"name": "default", "location": LOCATION})
    return "default"


def db_name(tester: str) -> str:
    return f"tcfq-{tester}"


def create_db(name: str) -> str:
    """Creates the database (or finds it) and returns its hostname."""
    found = {d["Name"]: d for d in turso("GET", "/databases").get("databases", [])}
    if name in found:
        return found[name]["Hostname"]
    return turso("POST", "/databases", json={"name": name, "group": group()})["database"]["Hostname"]


def template_from(hostname: str, name: str) -> str:
    return "libsql://" + hostname.replace(name, "tcfq-{tester}", 1)


# ---------- commands ----------

def cmd_setup() -> None:
    g = group()
    jwt = turso("POST", f"/groups/{g}/auth/tokens", params={"expiration": "never", "authorization": "full-access"})["jwt"]
    host = create_db("tcfq-selftest")
    save_env(TCFQUEST_LIBSQL_TOKEN=jwt, TCFQUEST_LIBSQL_URL_TEMPLATE=template_from(host, "tcfq-selftest"))
    print(f"Group '{g}' ready. Paste these into Render → your service → Environment:\n")
    print(f"TCFQUEST_LIBSQL_URL_TEMPLATE = {template_from(host, 'tcfq-selftest')}")
    print(f"TCFQUEST_LIBSQL_TOKEN        = {jwt}")
    print(f"TCFQUEST_SECRET              = {secrets.token_hex(32)}")
    print("\n(The token is also saved in data/beta-admin.env for backups. Don't share it.)")


def cmd_owner(name: str) -> None:
    """The owner's login. Re-run with the same name to change the password: the data stays."""
    from getpass import getpass
    from tcfquest.testers import NAME, password_hash
    if not NAME.match(name):
        sys.exit("Name: lowercase letters, digits and dashes, starting with a letter or digit.")
    password = getpass("Choose a password (12+ characters, not used anywhere else): ").strip()
    if len(password) < 12:
        sys.exit("Too short: use at least 12 characters (a few words together is easiest).")
    if getpass("Type it again: ").strip() != password:
        sys.exit("The two passwords differ. Nothing was changed.")
    create_db(db_name(name))
    print("\nPaste this into Render → Environment as TCFQUEST_OWNER (it's a hash, not your password):")
    print(f"{name}:{password_hash(password)}")


def cmd_add(name: str) -> None:
    from tcfquest.testers import NAME, code_hash
    if not NAME.match(name):
        sys.exit("Name: lowercase letters, digits and dashes, starting with a letter or digit.")
    create_db(db_name(name))
    code = f"{secrets.choice(WORDS)}-{secrets.randbelow(10_000):04d}-{secrets.choice(WORDS)}"
    TESTERS_FILE.write_text(json.dumps({**testers(), name: code_hash(code)}, indent=1))
    print(f"Invite code for {name} (shown once, send it privately): {code}\n")
    print(f"Now set TCFQUEST_INVITES in Render to:\n{invites_value()}")


def cmd_remove(name: str) -> None:
    t = testers()
    t.pop(name, None)
    TESTERS_FILE.write_text(json.dumps(t, indent=1))
    print(f"Removed {name}. Their database is kept. Set TCFQUEST_INVITES in Render to:\n{invites_value()}")


def after_setup() -> dict[str, str]:
    e = env()
    if not e.get("TCFQUEST_LIBSQL_URL_TEMPLATE"):
        sys.exit("Run `setup` first (it saves the database address and token this command needs).")
    return e


def cmd_backup() -> None:
    import libsql
    e = after_setup()
    dest = BACKUPS / datetime.now().strftime("%Y-%m-%d-%H%M")
    dest.mkdir(parents=True, exist_ok=True)
    for name in testers():
        url = e["TCFQUEST_LIBSQL_URL_TEMPLATE"].format(tester=name)
        conn = libsql.connect(str(dest / f"{name}.db"), sync_url=url, auth_token=e["TCFQUEST_LIBSQL_TOKEN"])
        conn.sync()
        conn.close()
        print(f"  {name} → {dest.relative_to(ROOT)}/{name}.db")
    print(f"Backed up {len(testers())} tester(s).")


def cmd_selftest() -> None:
    """Runs a real learner flow on the throwaway 'selftest' database, in remote then replica mode."""
    e = after_setup()
    os.environ.update(TCFQUEST_DB_BACKEND="libsql", TCFQUEST_LIBSQL_URL_TEMPLATE=e["TCFQUEST_LIBSQL_URL_TEMPLATE"],
                      TCFQUEST_LIBSQL_TOKEN=e["TCFQUEST_LIBSQL_TOKEN"])
    from tcfquest import db, sessions, content, testers as t
    for mode in ("remote", "replica"):
        os.environ["TCFQUEST_LIBSQL_REPLICA"] = "1" if mode == "replica" else "0"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TCFQUEST_TESTERS_DIR"] = tmp
            token = db.current_tester.set("selftest")
            t._ready.discard("selftest")
            conn = db.connect()
            t.ensure_ready(conn)
            version = db.schema_version(conn)
            s = content.get_set("premiers-pas-a")
            state = sessions.load_state(conn, s)
            item = state["order"][state["index"]]
            with db.transaction(conn):
                conn.execute("INSERT INTO ai_usage (day, neurons, calls) VALUES ('selftest', 1, 1) "
                             "ON CONFLICT(day) DO UPDATE SET calls = calls + 1")
            calls = conn.execute("SELECT calls FROM ai_usage WHERE day = 'selftest'").fetchone()["calls"]
            conn.close()
            db.current_tester.reset(token)
            print(f"  {mode}: schema {version}, first item {item}, transaction + read-back ok (calls={calls})")
    print("Self-test passed.")


if __name__ == "__main__":
    args = sys.argv[1:]
    commands = {"setup": cmd_setup, "owner": cmd_owner, "add": cmd_add, "remove": cmd_remove, "backup": cmd_backup,
                "selftest": cmd_selftest, "invites": lambda: print(invites_value())}
    if not args or args[0] not in commands:
        sys.exit(__doc__)
    commands[args[0]](*args[1:])
