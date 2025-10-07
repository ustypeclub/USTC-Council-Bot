"""Cog implementing council management commands.

Commands implemented:

* `/council create name:<string>` – mark the current channel as a council.  If a
  council already exists for this channel the name is updated.
* `/council remove` – unmark the current channel.
* `/council stats` – show a summary of the council, including active motion.
* `/config set` and `/config unset` – set or unset configuration keys.
* `/setweight` and `/voteweights show` – assign vote weights and inspect the
  current weight map.

This cog depends on the `utils.checks.is_admin` predicate to restrict
administrative commands.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..db import repo
from ..utils import checks, jsonschema, parsing


log = logging.getLogger(__name__)


class CouncilCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Create a top‑level group for council commands
        self.council_group = app_commands.Group(name="council", description="Manage councils")
        self.config_group = app_commands.Group(name="config", description="Manage council configuration")
        self.voteweights_group = app_commands.Group(name="voteweights", description="View vote weight map")
        # Register commands with the tree in setup_hook
        bot.tree.add_command(self.council_group)
        bot.tree.add_command(self.config_group)
        bot.tree.add_command(self.voteweights_group)

    # ---------------------------------------------------------------------
    # Council commands
    #

    # We cannot define commands at class definition time because we need access
    # to the group created in ``__init__``.  Instead, commands are added in
    # ``cog_load``, which runs when the cog is registered.
    # ---------------------------------------------------------------------
    # Configuration commands
    #

    # The same pattern is used for config commands.

    # ---------------------------------------------------------------------
    # Vote weight commands
    #

    async def cog_load(self) -> None:
        """Called when the cog is loaded; register group commands here."""
        # Because app_commands.Group instances cannot have commands added until
        # runtime, we define them here in cog_load.

        @self.council_group.command(name="create", description="Mark this channel as a council")
        @app_commands.describe(name="The name of the council")
        async def create(interaction: discord.Interaction, name: str) -> None:
            # Check permissions
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to create councils.", ephemeral=True)
                return
            guild_id = interaction.guild.id if interaction.guild else 0
            channel_id = interaction.channel.id if interaction.channel else 0
            council_id = await repo.create_or_update_council(self.bot.db, guild_id, channel_id, name)
            await interaction.response.send_message(f"Council `{name}` set for this channel.", ephemeral=True)

        @self.council_group.command(name="remove", description="Unmark this channel as a council")
        async def remove(interaction: discord.Interaction) -> None:
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to remove councils.", ephemeral=True)
                return
            channel_id = interaction.channel.id if interaction.channel else 0
            await repo.delete_council(self.bot.db, channel_id)
            await interaction.response.send_message("This channel is no longer a council.", ephemeral=True)

        @self.council_group.command(name="stats", description="Show council statistics")
        async def stats(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            # Fetch active motion if any
            motion = await repo.get_active_motion(self.bot.db, council["id"])
            if motion:
                description = f"Active motion: {motion['text']} (proposer <@{motion['author_id']}>)"
            else:
                description = "No active motion."
            embed = discord.Embed(title=f"Council {council['name']}", description=description, colour=0x95a5a6)
            await interaction.response.send_message(embed=embed)

        # -----------------------------------------------------------------
        # Config commands

        @self.config_group.command(name="set", description="Set a configuration key")
        @app_commands.describe(key="Configuration key", value="Value as JSON string")
        async def config_set(interaction: discord.Interaction, key: str, value: str) -> None:
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to modify configuration.", ephemeral=True)
                return
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                await interaction.response.send_message("Invalid JSON for value.", ephemeral=True)
                return
            if not jsonschema.validate_config_value(key, parsed_value):
                await interaction.response.send_message("Invalid configuration value.", ephemeral=True)
                return
            await repo.set_config(self.bot.db, council["id"], key, parsed_value)
            await interaction.response.send_message(f"Configuration `{key}` updated.", ephemeral=True)

        @self.config_group.command(name="unset", description="Unset a configuration key")
        @app_commands.describe(key="Configuration key")
        async def config_unset(interaction: discord.Interaction, key: str) -> None:
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to modify configuration.", ephemeral=True)
                return
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            await repo.unset_config(self.bot.db, council["id"], key)
            await interaction.response.send_message(f"Configuration `{key}` removed.", ephemeral=True)

        # -----------------------------------------------------------------
        # Weight commands

        @self.voteweights_group.command(name="show", description="Show the vote weight map")
        async def voteweights_show(interaction: discord.Interaction) -> None:
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            rows = await repo.get_weights(self.bot.db, council["id"])
            if not rows:
                await interaction.response.send_message("No custom vote weights set.", ephemeral=True)
                return
            lines = []
            for target_type, target_id, weight in rows:
                prefix = "@" if target_type == "user" else "@&"
                lines.append(f"{prefix}{target_id}: {weight}")
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @app_commands.command(name="setweight", description="Assign a vote weight to a user or role")
        @app_commands.describe(target="The user or role", weight="Numeric weight >= 1")
        async def setweight(interaction: discord.Interaction, target: discord.Member | discord.Role, weight: int) -> None:
            if not await checks.is_admin()(interaction):
                await interaction.response.send_message("You lack permission to assign vote weights.", ephemeral=True)
                return
            if weight < 1:
                await interaction.response.send_message("Weight must be at least 1.", ephemeral=True)
                return
            channel_id = interaction.channel.id if interaction.channel else 0
            council = await repo.get_council_by_channel(self.bot.db, channel_id)
            if not council:
                await interaction.response.send_message("This channel is not a council.", ephemeral=True)
                return
            target_type = "user" if isinstance(target, discord.Member) else "role"
            await repo.set_weight(self.bot.db, council["id"], target_type, target.id, weight)
            await interaction.response.send_message(f"Weight of {weight} assigned to {target.mention}.", ephemeral=True)

        # Add the non‑group weight command to the tree
        self.bot.tree.add_command(setweight)

    # Override ``setup`` for old versions of discord.py 2.x (not required here)
