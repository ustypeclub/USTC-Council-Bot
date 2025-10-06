"""Event listeners for Votum.

This cog registers global event listeners to handle transcripts, cleanup and
error logging.  Only a placeholder implementation is provided.
"""

from discord.ext import commands


class ListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Placeholder for event listeners
    # In a full implementation you would add @commands.Cog.listener methods here