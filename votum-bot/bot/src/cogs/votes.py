"""Cog implementing voting commands.

Commands implemented:

* `/vote choice:<yes|no|abstain> reason:<string(optional)>` – cast a vote on the
  current motion.  If a reason is required by configuration, a modal should be
  presented to the user; this simplified implementation accepts an optional
  reason parameter.
* `/lazyvoters` – mention members of the council who have not yet voted.

After each vote, the bot recalculates the totals and ends the motion if the
majority threshold has been reached.  Weighted votes are supported via the
`weights` table.
"""

from __future__ import annotations

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..db import repo
from ..utils import checks, majority as majority_utils

log = logging.getLogger(__name__)


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # register slash command directly on tree, no group
        pass

    async def cog_load(self) -> None:
        """Register vote commands."""

        @app_commands.command(name="vote", description="Cast a vote on the active motion")
        @app_commands.describe(choice="Your vote: yes, no or abstain", reason="Optional reason for your vote")
        async def vote(interaction: discord.Interaction, choice: str, reason: Optional[str] = None) -> None:
            choice = choice.lower()
            if choice not in ("yes", "no", "abstain"):
                await interaction.response.send_message("Vote must be yes, no or abstain.", ephemeral=True)
                return
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            motion = await repo.get_active_motion(self.bot.db, council["id"])
            if not motion:
                await interaction.response.send_message("There is no active motion.", ephemeral=True)
                return
            # Determine weight for this member (sum of role and user weights)
            member = interaction.guild.get_member(interaction.user.id)
            role_ids = [role.id for role in member.roles] if member else []
            weight = await repo.get_weight_for_member(self.bot.db, council["id"], interaction.user.id, role_ids)
            # Save vote
            await repo.cast_vote(self.bot.db, motion["id"], interaction.user.id, choice, reason, weight)
            # Recalculate totals
            votes = await repo.fetch_votes(self.bot.db, motion["id"])
            total_yes = sum(v["weight"] for v in votes if v["vote"] == "yes")
            total_no = sum(v["weight"] for v in votes if v["vote"] == "no")
            total_abstain = sum(v["weight"] for v in votes if v["vote"] == "abstain")
            # Check majority
            if majority_utils.has_majority(
                total_yes,
                total_no,
                total_abstain,
                motion["majority_num"],
                motion["majority_den"],
                unanimous=motion.get("unanimous", False),
            ):
                # End motion and announce result
                await repo.end_motion(self.bot.db, motion["id"], status="passed", result="passed")
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="Motion Passed",
                        description=motion["text"],
                        colour=0x2ecc71,
                    )
                )
            await interaction.response.send_message(f"Your vote of {choice} has been recorded.", ephemeral=True)

        @app_commands.command(name="lazyvoters", description="Mention members who have not voted yet")
        async def lazyvoters(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            motion = await repo.get_active_motion(self.bot.db, council["id"])
            if not motion:
                await interaction.response.send_message("There is no active motion.", ephemeral=True)
                return
            votes = await repo.fetch_votes(self.bot.db, motion["id"])
            voted_users = {v["user_id"] for v in votes}
            # Determine potential voters: all members with view permission in channel
            channel_members = [m for m in interaction.channel.members if not m.bot]
            missing = [m for m in channel_members if m.id not in voted_users]
            if not missing:
                await interaction.response.send_message("Everyone has voted.", ephemeral=True)
                return
            mentions = ", ".join(m.mention for m in missing)
            await interaction.response.send_message(f"The following members have not voted yet: {mentions}")

        # Register commands on the tree
        self.bot.tree.add_command(vote)
        self.bot.tree.add_command(lazyvoters)