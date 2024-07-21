import asyncio

import discord
from discord import app_commands
from discord.ext import commands
from repositories import quiz_repo
from utils.database import db
from utils.quiz import (
    is_quiz_active,
    set_quiz_status,
)

TOPIC_SELECT_TIMER = quiz_repo.topic_select_timer()


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

    @app_commands.command(name="topic")
    async def topic(self, interaction: discord.Interaction) -> None:
        """Quiz command."""
        channel_id = interaction.channel_id

        # Check if there's already an active quiz in this channel
        if is_quiz_active(channel_id):
            await interaction.response.send_message("A quiz is already running in this channel.", ephemeral=True)
            return

        # Mark the quiz as active
        set_quiz_status(channel_id, True)

        voting_view = quiz_repo.VotingView()
        await interaction.response.send_message("Choose your topic! Time remaining: **10 seconds**", view=voting_view)
        message = await interaction.original_response()
        voting_view.message = message  # Store the original message in the view

        # Start the timer update task
        asyncio.create_task(voting_view.update_message())  # noqa: RUF006

        await asyncio.sleep(TOPIC_SELECT_TIMER)
        await voting_view.on_timeout()

async def setup(bot: commands.Bot) -> None:
    """Setups the Quiz command."""
    await bot.add_cog(QuizCommand(bot))
