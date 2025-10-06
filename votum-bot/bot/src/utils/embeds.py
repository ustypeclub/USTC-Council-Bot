"""Helper functions for constructing Discord embeds.

Discord embeds provide richly formatted messages.  This module defines
functions to build common embeds used by the Votum bot.
"""

from __future__ import annotations

import discord


def motion_embed(text: str, author_name: str, majority: str) -> discord.Embed:
    """Create an embed for a newly proposed motion."""
    embed = discord.Embed(title="New Motion", description=text, colour=0x3498db)
    embed.add_field(name="Proposer", value=author_name, inline=False)
    embed.add_field(name="Majority", value=majority, inline=False)
    return embed


def vote_result_embed(motion_text: str, result: str, yes: float, no: float, abstain: float) -> discord.Embed:
    """Create an embed summarising the outcome of a motion."""
    embed = discord.Embed(title="Motion Result", description=motion_text, colour=0x2ecc71 if result == "passed" else 0xe74c3c)
    embed.add_field(name="Outcome", value=result.title(), inline=False)
    embed.add_field(name="Yes", value=str(yes), inline=True)
    embed.add_field(name="No", value=str(no), inline=True)
    embed.add_field(name="Abstain", value=str(abstain), inline=True)
    return embed