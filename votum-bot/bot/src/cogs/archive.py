"""Cog implementing archive commands.

Archive commands allow admins and councilors to review past motions and export
detailed vote data.  In this simplified implementation, only `/archive export`
is provided, which returns a JSON document containing motions and their votes.
"""

from __future__ import annotations

import json
import logging
from typing import List
import io

import discord
from discord import app_commands
from discord.ext import commands

from ..db import repo
from ..utils import checks

log = logging.getLogger(__name__)


class ArchiveCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.archive_group = app_commands.Group(name="archive", description="Access motion archives")
        bot.tree.add_command(self.archive_group)

    async def cog_load(self) -> None:
        @self.archive_group.command(name="export", description="Export motion archives as JSON")
        async def export(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            # Only admins may export archives
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to export archives.", ephemeral=True)
                return
            # Fetch all motions for this council
            cur = await self.bot.db.execute(
                "SELECT id, text, author_id, majority_num, majority_den, unanimous, status, result, created_at, closed_at FROM motions WHERE council_id = ? ORDER BY id ASC",
                (council["id"],),
            )
            motions = await cur.fetchall()
            await cur.close()
            archive: List[dict] = []
            for m in motions:
                motion_id = m[0]
                votes = await repo.fetch_votes(self.bot.db, motion_id)
                archive.append(
                    {
                        "motion_id": m[0],
                        "text": m[1],
                        "author_id": m[2],
                        "majority_num": m[3],
                        "majority_den": m[4],
                        "unanimous": bool(m[5]),
                        "status": m[6],
                        "result": m[7],
                        "created_at": m[8],
                        "closed_at": m[9],
                        "votes": votes,
                    }
                )
            json_data = json.dumps(archive, indent=2)
            file = discord.File(fp=io.BytesIO(json_data.encode("utf-8")), filename="archive.json")
            await interaction.response.send_message("Archive export", file=file)
