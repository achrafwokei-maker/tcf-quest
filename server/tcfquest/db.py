"""SQLite access and versioned migrations.

Migrations are numbered .sql files in ./migrations. Each runs once, in order, inside a
transaction; the applied version is stored in SQLite's user_version pragma.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Iterator

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def db_path() -> Path:
    tester = current_tester.get()
    if tester:  # online beta: one database file per tester, next to the default one
        return testers_dir() / f"{tester}.db"
    return Path(os.environ.get("TCFQUEST_DB", PROJECT_ROOT / "data" / "tcfquest.db"))


def testers_dir() -> Path:
    return Path(os.environ.get("TCFQUEST_TESTERS_DIR", PROJECT_ROOT / "data" / "testers"))


# Set per request in beta mode (see testers.py); empty locally, so the single learner's file is used.
current_tester: ContextVar[str] = ContextVar("current_tester", default="")


def backend() -> str:
    """'sqlite' (default, local) or 'libsql' (online beta, Turso-compatible)."""
    return os.environ.get("TCFQUEST_DB_BACKEND", "sqlite")


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if backend() == "libsql":
        return _libsql_connect(path)
    # One connection per request, used sequentially, may hop between FastAPI threads.
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrations() -> list[tuple[int, Path]]:
    found = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        found.append((int(f.name.split("_", 1)[0]), f))
    return found


def migrate(conn: sqlite3.Connection) -> int:
    current = schema_version(conn)
    for version, file in migrations():
        if version <= current:
            continue
        conn.execute("BEGIN")
        try:
            # executescript() would auto-commit, so run statement by statement instead.
            for statement in _split(file.read_text()):
                conn.execute(statement)
            _set_schema_version(conn, version)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        current = version
    return current


def schema_version(conn: sqlite3.Connection) -> int:
    """Applied migration number. SQLite keeps it in the user_version pragma; Turso doesn't allow
    writing that pragma, so online databases keep it in a one-row table instead."""
    if isinstance(conn, LibsqlConnection):
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    if isinstance(conn, LibsqlConnection):
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    else:
        conn.execute(f"PRAGMA user_version = {version}")


def _split(sql: str) -> list[str]:
    """Split a migration into statements (no semicolons inside our string literals)."""
    lines = [line.split("--", 1)[0] for line in sql.splitlines()]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def backup(conn: sqlite3.Connection, dest_dir: Path | None = None) -> Path:
    """Write a consistent copy of the database; returns its path."""
    if isinstance(conn, LibsqlConnection):
        raise RuntimeError("Backups of online databases are made by scripts/beta_backup.py")
    dest_dir = dest_dir or db_path().parent / "backups"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"tcfquest-{datetime.now():%Y%m%d-%H%M%S}.db"
    with sqlite3.connect(dest) as out:
        conn.backup(out)
    return dest


def restore(backup_file: Path, path: Path | None = None) -> None:
    """Replace the live database with a backup. Call only while the server is stopped."""
    path = path or db_path()
    shutil.copyfile(backup_file, path)


# ---------- libSQL (Turso) adapter ----------
# The libsql package speaks the sqlite3 API but has no row_factory, so rows come back as tuples.
# These thin wrappers give the rest of the code the same sqlite3.Row behaviour (r["col"], dict(r)).


class Row(tuple):
    """Tuple that can also be read by column name, like sqlite3.Row."""

    _cols: tuple[str, ...]

    def __new__(cls, values, cols):
        row = super().__new__(cls, values)
        row._cols = cols
        return row

    def keys(self) -> list[str]:
        return list(self._cols)

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                return tuple.__getitem__(self, self._cols.index(key))
            except ValueError:
                raise IndexError(f"No item with that key: {key}") from None
        return tuple.__getitem__(self, key)


class LibsqlCursor:
    def __init__(self, cur):
        self._cur = cur
        self._cols = tuple(d[0] for d in (cur.description or ()))
        # libsql reads these from the connection lazily; capture them now, as sqlite3 cursors do.
        self.lastrowid, self.rowcount = cur.lastrowid, cur.rowcount

    def _row(self, values):
        return None if values is None else Row(values, self._cols)

    def fetchone(self):
        return self._row(self._cur.fetchone())

    def fetchall(self):
        return [Row(v, self._cols) for v in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def description(self):
        return self._cur.description


_NAMED = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")


def _positional(sql: str, params) -> tuple[str, tuple]:
    """libsql accepts only ? parameters: rewrite :name placeholders (dict params) in order."""
    if not isinstance(params, dict):
        return sql, tuple(params)
    names = _NAMED.findall(sql)
    return _NAMED.sub("?", sql), tuple(params[n] for n in names)


class LibsqlConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        return LibsqlCursor(self._conn.execute(*_positional(sql, params)))

    def executemany(self, sql: str, seq):
        for params in seq:
            self._conn.execute(*_positional(sql, params))

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    @property
    def in_transaction(self) -> bool:
        return self._conn.in_transaction


def _libsql_connect(path: Path) -> sqlite3.Connection:
    import libsql  # optional dependency, installed only for the online beta (pyproject extra "beta")

    # Online: TCFQUEST_LIBSQL_URL_TEMPLATE, e.g. "libsql://tcfq-{tester}-myorg.aws-us-east-1.turso.io".
    # Remote mode (default) sends every statement to Turso: nothing is kept on the server's disk.
    # TCFQUEST_LIBSQL_REPLICA=1 keeps a local copy synced with Turso instead (faster reads).
    url = os.environ.get("TCFQUEST_LIBSQL_URL_TEMPLATE")
    tester = current_tester.get()
    if url and tester:
        remote, token = url.format(tester=tester), os.environ["TCFQUEST_LIBSQL_TOKEN"]
        if os.environ.get("TCFQUEST_LIBSQL_REPLICA") == "1":
            conn = libsql.connect(str(path), sync_url=remote, auth_token=token, isolation_level=None)
            conn.sync()
        else:
            conn = libsql.connect(remote, auth_token=token, isolation_level=None)
    else:  # local file through libsql: used by tests to prove compatibility
        conn = libsql.connect(str(path), isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    return LibsqlConnection(conn)  # type: ignore[return-value]
