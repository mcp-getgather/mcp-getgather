import sqlite3
from contextlib import contextmanager
from typing import Any, Generator, Sequence

from getgather.config import settings


def dict_factory(cursor: sqlite3.Cursor, row: Sequence[Any]) -> dict[str, Any]:
    """Convert sqlite row to dictionary."""
    d: dict[str, Any] = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@contextmanager
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with automatic cleanup.

    Usage:
        with db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions")
    """
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = dict_factory  # Make rows return as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple[Any, ...] | None = None) -> None:
    """Execute a query without returning results."""
    with db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())


def execute_insert(query: str, params: tuple[Any, ...] | None = None) -> int:
    """Execute an insert query and return the last inserted row ID."""
    with db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to get last inserted row ID")
        return cursor.lastrowid


def fetch_one(query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    """Execute a query and return one row."""
    with db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchone()


def fetch_all(query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    """Execute a query and return all rows."""
    with db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()
