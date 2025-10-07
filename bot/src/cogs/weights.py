"""Stub cog for vote weight commands.

Vote weight commands are implemented in the CouncilCog for simplicity.  This
module provides a placeholder to satisfy imports in ``main.py``.  Future
implementations can move weight logic here.
"""

from discord.ext import commands


class WeightsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # This cog intentionally defines no commands; see CouncilCog for weight
    # management commands.