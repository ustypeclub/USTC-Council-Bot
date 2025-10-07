"""Announcement cog.

In the full Votum implementation, this cog would listen for motion end
events and send configured announcements to designated channels.  For the
purposes of this example, it is a placeholder only.
"""

from discord.ext import commands


class AnnouncerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # In a full implementation you would register listeners for motion
    # resolution and send announcements or forward proposals to other councils.