"""Low‑level database access functions for Votum.

These functions encapsulate the SQL queries used throughout the bot.  They are
kept deliberately simple so that calling code can decide on higher‑level
behaviour and caching.  All functions expect an `aiosqlite.Connection` or
`aiosqlite.Cursor` as their first argument.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

import aiosqlite


# ---------------------------------------------------------------------------
# Councils

async def get_council_by_channel(db: aiosqlite.Connection, channel_id: int) -> Optional[Dict[str, Any]]:
    cur = await db.execute("SELECT id, guild_id, channel_id, name FROM councils WHERE channel_id = ?", (channel_id,))
    row = await cur.fetchone()
    await cur.close()
    if row:
        return {"id": row[0], "guild_id": row[1], "channel_id": row[2], "name": row[3]}
    return None


async def create_or_update_council(db: aiosqlite.Connection, guild_id: int, channel_id: int, name: str) -> int:
    # Upsert semantics: update name if exists, otherwise insert
    council = await get_council_by_channel(db, channel_id)
    if council:
        await db.execute("UPDATE councils SET name = ?, guild_id = ? WHERE channel_id = ?", (name, guild_id, channel_id))
        await db.commit()
        return council["id"]
    cur = await db.execute(
        "INSERT INTO councils (guild_id, channel_id, name) VALUES (?, ?, ?)",
        (guild_id, channel_id, name),
    )
    await db.commit()
    return cur.lastrowid


async def delete_council(db: aiosqlite.Connection, channel_id: int) -> None:
    await db.execute("DELETE FROM councils WHERE channel_id = ?", (channel_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# Configuration

async def set_config(db: aiosqlite.Connection, council_id: int, key: str, value: Any) -> None:
    value_json = json.dumps(value)
    await db.execute(
        "INSERT INTO configs (council_id, key, value) VALUES (?, ?, ?) ON CONFLICT(council_id, key) DO UPDATE SET value=excluded.value",
        (council_id, key, value_json),
    )
    await db.commit()


async def unset_config(db: aiosqlite.Connection, council_id: int, key: str) -> None:
    await db.execute("DELETE FROM configs WHERE council_id = ? AND key = ?", (council_id, key))
    await db.commit()


async def get_config(db: aiosqlite.Connection, council_id: int, key: str) -> Optional[Any]:
    cur = await db.execute("SELECT value FROM configs WHERE council_id = ? AND key = ?", (council_id, key))
    row = await cur.fetchone()
    await cur.close()
    if row:
        return json.loads(row[0])
    return None


async def get_all_configs(db: aiosqlite.Connection, council_id: int) -> Dict[str, Any]:
    cur = await db.execute("SELECT key, value FROM configs WHERE council_id = ?", (council_id,))
    rows = await cur.fetchall()
    await cur.close()
    return {key: json.loads(value) for key, value in rows}


# ---------------------------------------------------------------------------
# Vote weights

async def set_weight(db: aiosqlite.Connection, council_id: int, target_type: str, target_id: int, weight: int) -> None:
    await db.execute(
        "INSERT INTO weights (council_id, target_type, target_id, weight) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(council_id, target_type, target_id) DO UPDATE SET weight=excluded.weight",
        (council_id, target_type, target_id, weight),
    )
    await db.commit()


async def get_weights(db: aiosqlite.Connection, council_id: int) -> List[Tuple[str, int, int]]:
    cur = await db.execute("SELECT target_type, target_id, weight FROM weights WHERE council_id = ?", (council_id,))
    rows = await cur.fetchall()
    await cur.close()
    return rows


async def get_weight_for_member(db: aiosqlite.Connection, council_id: int, user_id: int, role_ids: Iterable[int]) -> float:
    """Compute the effective weight for a member: user weight plus all matching role weights.

    Parameters
    ----------
    db : aiosqlite.Connection
        The database connection.
    council_id : int
        ID of the council.
    user_id : int
        Discord user ID.
    role_ids : Iterable[int]
        Iterable of role IDs the member has in this guild.

    Returns
    -------
    float
        The sum of all applicable weights or 1.0 if none set.
    """
    cur = await db.execute(
        "SELECT target_type, target_id, weight FROM weights WHERE council_id = ?",
        (council_id,),
    )
    rows = await cur.fetchall()
    await cur.close()
    total = 0.0
    for target_type, target_id, weight in rows:
        if target_type == "user" and target_id == user_id:
            total += weight
        elif target_type == "role" and target_id in role_ids:
            total += weight
    return total if total > 0 else 1.0


# ---------------------------------------------------------------------------
# Motions and votes

async def create_motion(
    db: aiosqlite.Connection,
    council_id: int,
    author_id: int,
    text: str,
    majority_num: int,
    majority_den: int,
    unanimous: bool,
    expires_at: Optional[str] = None,
) -> int:
    cur = await db.execute(
        "INSERT INTO motions (council_id, author_id, text, majority_num, majority_den, unanimous, expires_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (council_id, author_id, text, majority_num, majority_den, int(unanimous), expires_at),
    )
    await db.commit()
    return cur.lastrowid


async def get_active_motion(db: aiosqlite.Connection, council_id: int) -> Optional[Dict[str, Any]]:
    cur = await db.execute(
        "SELECT id, author_id, text, majority_num, majority_den, unanimous, status, created_at, expires_at FROM motions"
        " WHERE council_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
        (council_id,),
    )
    row = await cur.fetchone()
    await cur.close()
    if row:
        return {
            "id": row[0],
            "author_id": row[1],
            "text": row[2],
            "majority_num": row[3],
            "majority_den": row[4],
            "unanimous": bool(row[5]),
            "status": row[6],
            "created_at": row[7],
            "expires_at": row[8],
        }
    return None


async def end_motion(db: aiosqlite.Connection, motion_id: int, status: str, result: Optional[str], closed_at: Optional[str] = None) -> None:
    await db.execute(
        "UPDATE motions SET status = ?, result = ?, closed_at = COALESCE(?, CURRENT_TIMESTAMP) WHERE id = ?",
        (status, result, closed_at, motion_id),
    )
    await db.commit()


async def cast_vote(
    db: aiosqlite.Connection,
    motion_id: int,
    user_id: int,
    vote: str,
    reason: Optional[str],
    weight: float,
) -> None:
    # Upsert semantics: update reason and weight if user changes their vote
    await db.execute(
        "INSERT INTO votes (motion_id, user_id, vote, reason, weight) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(motion_id, user_id) DO UPDATE SET vote=excluded.vote, reason=excluded.reason, weight=excluded.weight",
        (motion_id, user_id, vote, reason, weight),
    )
    await db.commit()


async def fetch_votes(db: aiosqlite.Connection, motion_id: int) -> List[Dict[str, Any]]:
    cur = await db.execute(
        "SELECT user_id, vote, reason, weight, created_at FROM votes WHERE motion_id = ?",
        (motion_id,),
    )
    rows = await cur.fetchall()
    await cur.close()
    return [
        {
            "user_id": row[0],
            "vote": row[1],
            "reason": row[2],
            "weight": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]