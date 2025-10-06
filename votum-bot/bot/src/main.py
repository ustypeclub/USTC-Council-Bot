"""
Votum Discord bot entrypoint.

This module defines the `VotumBot` class which subclasses `commands.Bot` to
provide slash commands grouped into cogs.  When started, it initialises the
database, loads cogs and synchronises application commands for the guilds
specified in `INITIAL_GUILD_IDS`.  It also handles graceful shutdown so that
database connections are closed properly.

Usage:

    python -m bot.src.main

Ensure that the environment variables defined in `.env.example` are set.  The
Discord token must be provided via `DISCORD_TOKEN`.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import contextlib
from typing import Iterable, Optional

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from dotenv import load_dotenv

from .db import migrate as db_migrate


log = logging.getLogger(__name__)


class VotumBot(commands.Bot):
    """Discord bot implementing the Votum small‑council voting system."""

    def __init__(self, *, token: str, database_url: str, initial_guilds: Optional[Iterable[int]] = None) -> None:
        intents = discord.Intents.default()
        # We need members intent to read guild members for lazyvoters and weighting.
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.token = token
        self.database_url = database_url
        self.db: Optional[aiosqlite.Connection] = None
        self.initial_guilds = list(initial_guilds) if initial_guilds else []

    async def setup_hook(self) -> None:
        """Initialise the bot before connecting to the gateway."""
        # Apply schema migrations.
        self.db = await aiosqlite.connect(self.database_url)
        await db_migrate.run_migrations(self.db)
        # Load cogs
        from .cogs.council import CouncilCog
        from .cogs.motions import MotionCog
        from .cogs.votes import VoteCog
        from .cogs.archive import ArchiveCog
        from .cogs.weights import WeightsCog
        from .cogs.announcer import AnnouncerCog
        from .cogs.listeners import ListenerCog

        await self.add_cog(CouncilCog(self))
        await self.add_cog(MotionCog(self))
        await self.add_cog(VoteCog(self))
        await self.add_cog(ArchiveCog(self))
        await self.add_cog(WeightsCog(self))
        await self.add_cog(AnnouncerCog(self))
        await self.add_cog(ListenerCog(self))

        # Copy slash commands to specific guilds if provided; otherwise sync globally
        if self.initial_guilds:
            for gid in self.initial_guilds:
                self.tree.copy_global_to(guild=discord.Object(id=gid))
            log.info("Synchronising commands for guilds %s", self.initial_guilds)
            await self.tree.sync()
        else:
            log.info("Synchronising commands globally")
            await self.tree.sync()

    async def close(self) -> None:
        # Overridden to close the DB connection on shutdown
        if self.db is not None:
            await self.db.close()
            self.db = None
        await super().close()


async def _run_bot() -> None:
    """Load configuration from environment and run the bot."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required to run the bot")
    database_url = os.getenv("DATABASE_URL", "bot.db")
    initial_guilds_env = os.getenv("INITIAL_GUILD_IDS", "")
    initial_guilds: list[int] = []
    if initial_guilds_env:
        initial_guilds = [int(g.strip()) for g in initial_guilds_env.split(",") if g.strip()]

    bot = VotumBot(token=token, database_url=database_url, initial_guilds=initial_guilds)

    loop = asyncio.get_event_loop()

    # Handle graceful shutdown
    stop = asyncio.Event()

    def handle_sig(*_: object) -> None:
        log.info("Received shutdown signal")
        stop.set()

    loop.add_signal_handler(signal.SIGINT, handle_sig)
    loop.add_signal_handler(signal.SIGTERM, handle_sig)

    async def run() -> None:
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            pass
        finally:
            await bot.close()

    runner = asyncio.create_task(run())
    await stop.wait()
    log.info("Shutting down bot")
    runner.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await runner


def main() -> None:
    """Entry point for running via `python -m bot.src.main`"""
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(_run_bot())
    except Exception as exc:
        log.exception("Exception in main: %s", exc)


if __name__ == "__main__":
    main()