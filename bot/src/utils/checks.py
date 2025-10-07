"""Permission and role checking helpers for slash commands.

`discord.py` uses *check* predicates to guard commands.  This module defines
common checks used by the Votum bot.  They return callables that accept a
`discord.Interaction` and return a boolean.  When a check returns `False`, the
command will not run and a default error message is raised.
"""

from __future__ import annotations

from typing import Callable, Iterable

import discord


def is_admin() -> Callable[[discord.Interaction], bool]:
    """Return a predicate that checks whether the invoking user is an admin.

    A user is considered an admin if they have the Manage Guild permission or
    possess a role called "Votum Admin".  The check inspects the guild
    permissions and roles of the interaction user.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild or not interaction.user:
            return False
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False
        if member.guild_permissions.manage_guild:
            return True
        for role in member.roles:
            if role.name.lower() == "votum admin".lower():
                return True
        return False

    return predicate


def is_councilor(channel_id: int) -> Callable[[discord.Interaction], bool]:
    """Return a predicate that checks whether the user is a councilor in the given channel.

    For simplicity this check currently always returns True.  In a complete
    implementation you would query the configuration for `councilor.role` and
    verify the member has that role.  This function is provided for future
    expansion.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        # TODO: check councilor role from config
        return True

    return predicate