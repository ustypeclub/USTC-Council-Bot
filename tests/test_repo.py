import asyncio
import aiosqlite
import pytest

from bot.src.db.migrate import run_migrations
from bot.src.db import repo


@pytest.mark.asyncio
async def test_council_create_and_fetch():
    db = await aiosqlite.connect(":memory:")
    await run_migrations(db)
    council_id = await repo.create_or_update_council(db, guild_id=1, channel_id=10, name="Test Council")
    council = await repo.get_council_by_channel(db, channel_id=10)
    assert council is not None
    assert council["id"] == council_id
    assert council["name"] == "Test Council"
    await db.close()


@pytest.mark.asyncio
async def test_config_set_and_get():
    db = await aiosqlite.connect(":memory:")
    await run_migrations(db)
    council_id = await repo.create_or_update_council(db, 1, 20, "Config Council")
    await repo.set_config(db, council_id, "test.key", {"x": 1})
    value = await repo.get_config(db, council_id, "test.key")
    assert value == {"x": 1}
    await repo.unset_config(db, council_id, "test.key")
    assert await repo.get_config(db, council_id, "test.key") is None
    await db.close()


@pytest.mark.asyncio
async def test_vote_flow_and_majority():
    db = await aiosqlite.connect(":memory:")
    await run_migrations(db)
    council_id = await repo.create_or_update_council(db, 1, 30, "Vote Council")
    motion_id = await repo.create_motion(db, council_id, author_id=42, text="Test motion", majority_num=1, majority_den=2, unanimous=False)
    # Cast two yes votes and one no vote
    await repo.cast_vote(db, motion_id, user_id=1, vote="yes", reason=None, weight=1)
    await repo.cast_vote(db, motion_id, user_id=2, vote="yes", reason="", weight=1)
    await repo.cast_vote(db, motion_id, user_id=3, vote="no", reason="", weight=1)
    votes = await repo.fetch_votes(db, motion_id)
    assert len(votes) == 3
    total_yes = sum(v["weight"] for v in votes if v["vote"] == "yes")
    total_no = sum(v["weight"] for v in votes if v["vote"] == "no")
    total_abstain = sum(v["weight"] for v in votes if v["vote"] == "abstain")
    from bot.src.utils.majority import has_majority
    assert has_majority(total_yes, total_no, total_abstain, 1, 2) is True
    await db.close()