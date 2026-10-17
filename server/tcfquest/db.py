"""SQLite access and versioned migrations.

Migrations are numbered .sql files in ./migrations. Each runs once, in order, inside a
transaction; the applied version is stored in SQLite's user_version pragma.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def db_path() -> Path:
    return Path(os.environ.get("TCFQUEST_DB", PROJECT_ROOT / "data" / "tcfquest.db"))


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
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
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, file in migrations():
        if version <= current:
            continue
        conn.execute("BEGIN")
        try:
            # executescript() would auto-commit, so run statement by statement instead.
            for statement in _split(file.read_text()):
                conn.execute(statement)
            conn.execute(f"PRAGMA user_version = {version}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        current = version
    return current


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
