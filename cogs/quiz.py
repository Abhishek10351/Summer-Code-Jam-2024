import discord
from discord import app_commands
from discord.ext import commands

from .database import db


class QuizCommand(commands.Cog):
    """Quiz commands cog."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize QuizCommand cog."""
        self.bot = bot

    @app_commands.command(name="get-score")
    async def get_score(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
        """Get the score of a user."""
        user = user or interaction.user
        score = await db.get_score(user.id)
        if score:
            await interaction.response.send_message(f"User's Score: {score}")
        else:
            await interaction.response.send_message(
                f"{user.mention} has not attempted the quiz yet.",
                allowed_mentions=None,
            )

    @app_commands.command(name="quiz")
    async def quiz(self, interaction: discord.Interaction) -> None:
        """Start the quiz."""
        score = await db.get_score(interaction.user.id)
        await interaction.response.send_message("Congratulations! You got all questions right on the quiz.")
        await db.set_score(interaction.user.id, score + 1)


async def setup(bot: commands.Bot) -> None:
    """Setups the Quiz command."""
    await bot.add_cog(QuizCommand(bot))
