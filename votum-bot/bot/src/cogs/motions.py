"""Cog implementing motion management commands.

Commands implemented:

* `/motion show` – display the currently active motion in this council.
* `/motion new text:<string> majority:<fraction|percent>=default unanimous:<bool>=false` – open a new motion.  The motion is stored in the database and an embed is posted in the channel.  In a full implementation this would also create a private deliberation thread.
* `/motion kill` – end the active motion (author or admin only).

This cog demonstrates how to parse majority specifications and interact with
the repository layer.  It does not include queueing or expiration logic.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..db import repo
from ..utils import checks, embeds, majority as majority_utils

log = logging.getLogger(__name__)


class MotionCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.motion_group = app_commands.Group(name="motion", description="Manage motions")
        bot.tree.add_command(self.motion_group)

    async def cog_load(self) -> None:
        """Register slash commands for motions."""

        @self.motion_group.command(name="show", description="Show the currently active motion in this council")
        async def show(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            motion = await repo.get_active_motion(self.bot.db, council["id"])
            if not motion:
                await interaction.response.send_message("No active motion.", ephemeral=True)
                return
            embed = embeds.motion_embed(
                motion["text"],
                author_name=f"<@{motion['author_id']}>",
                majority=f"{motion['majority_num']}/{motion['majority_den']}{' (unanimous)' if motion['unanimous'] else ''}"
            )
            await interaction.response.send_message(embed=embed)

        @self.motion_group.command(name="new", description="Propose a new motion")
        @app_commands.describe(text="The motion text", majority="Required majority (e.g. 1/2, 66%)", unanimous="Require unanimous vote")
        async def new(interaction: discord.Interaction, text: str, majority: Optional[str] = None, unanimous: Optional[bool] = False) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            guild_id = interaction.guild.id if interaction.guild else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            # Determine majority
            if majority:
                try:
                    num, den = majority_utils.parse_majority(majority)
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True)
                    return
            else:
                # default to simple majority 1/2
                num, den = 1, 2
            # Create motion
            motion_id = await repo.create_motion(
                self.bot.db,
                council_id=council["id"],
                author_id=interaction.user.id,
                text=text,
                majority_num=num,
                majority_den=den,
                unanimous=bool(unanimous),
                expires_at=None,
            )
            embed = embeds.motion_embed(text, author_name=interaction.user.display_name, majority=f"{num}/{den}{' (unanimous)' if unanimous else ''}")
            await interaction.response.send_message("Motion proposed successfully.", embed=embed)
            # In a full implementation we would create a private deliberation thread here

        @self.motion_group.command(name="kill", description="End the active motion")
        async def kill(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            motion = await repo.get_active_motion(self.bot.db, council["id"])
            if not motion:
                await interaction.response.send_message("No active motion to kill.", ephemeral=True)
                return
            # Only proposer or admin may kill
            if interaction.user.id != motion["author_id"] and not await checks.is_admin()(interaction):
                await interaction.response.send_message("Only the proposer or an admin can kill the motion.", ephemeral=True)
                return
            await repo.end_motion(self.bot.db, motion["id"], status="killed", result="killed")
            await interaction.response.send_message("Motion has been killed.")