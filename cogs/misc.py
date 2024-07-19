import random

import discord
from discord import app_commands
from discord.ext import commands


class MiscCommand(commands.Cog):
    """Misc commands cog."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize MiscCommand cog."""
        self.bot = bot

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Ping the bot."""
        await interaction.response.send_message(f"Pong! Latency: **{round(self.bot.latency * 1000)}ms**")

    @app_commands.command(name="randomize")
    async def randomize(self, interaction: discord.Interaction) -> None:
        """Tag a random user."""
        phrase = random.choice(["You've been chosen,", "I choose you,", "And the chosen one is"])  # noqa: S311
        user = random.choice(interaction.channel.guild.members)  # noqa: S311
        await interaction.response.send_message(f"{phrase} {user.mention}")


async def setup(bot: commands.Bot) -> None:
    """Setups the misc command."""
    await bot.add_cog(MiscCommand(bot))
