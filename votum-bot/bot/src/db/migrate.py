"""Database schema migration helper.

This module exposes a single coroutine `run_migrations` that reads the SQL
statements in `schema.sql` and applies them to a SQLite database.  The
migration mechanism is intentionally simple: it executes all `CREATE TABLE IF
NOT EXISTS` statements.  Future versions can extend this to support versioned
migrations stored in the `schema_migrations` table.
"""

from __future__ import annotations

import importlib.resources
import logging
from typing import Optional

import aiosqlite

log = logging.getLogger(__name__)


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Apply schema migrations by executing SQL from `schema.sql`.

    Parameters
    ----------
    db: aiosqlite.Connection
        Connection to an open SQLite database.  `PRAGMA foreign_keys` will
        automatically be enabled.
    """
    # Always enable foreign key constraints
    await db.execute("PRAGMA foreign_keys = ON;")
    # Load schema.sql from the same package
    schema_sql: Optional[str] = None
    try:
        schema_sql = importlib.resources.read_text(__package__, "schema.sql")
    except FileNotFoundError:
        log.error("schema.sql not found in db package")
        return
    log.info("Applying database schema")
    await db.executescript(schema_sql)
    await db.commit()