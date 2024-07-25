import asyncio
import time
from collections import defaultdict

import discord
from discord.ext import commands
from main import bot
from repositories import quiz_repo
from utils.database import db
from utils.quiz import (
    create_api_call,
    get_quizzes_with_token,
    get_sub_topic_id,
    get_topic_id,
    has_sub_topic,
    is_quiz_active,
    set_quiz_active,
    set_quiz_ended,
)

VOTING_TIME = quiz_repo.voting_time()


class QuizCommand(commands.Cog):
    """Quiz commands cog."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize QuizCommand cog."""
        self.bot = bot

    @bot.tree.command(name="get-score")
    async def get_score(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
        """Get the score of a user."""
        user = user or interaction.user
        score = await db.get_score(user.id)
        if score:
            embed = discord.Embed(
                description=f"{user.mention}'s Score: {score}",
                color=discord.Color.blurple(),
            )
            await interaction.response.send_message(
                embed=embed,
                allowed_mentions=None,
                ephemeral=True,
            )
        else:
            embed = discord.Embed(
                description=f"{user.mention} has not attempted the quiz yet.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed,
                allowed_mentions=None,
                ephemeral=True,
            )

    @bot.tree.command(name="quiz")
    async def quiz(self, interaction: discord.Interaction) -> None:
        """Start new quiz."""
        channel_id = interaction.channel_id

        # Check if there's already an active quiz in this channel
        if is_quiz_active(channel_id):
            embed = discord.Embed(
                description="A quiz is already running in this channel.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Mark the quiz as active
        set_quiz_active(channel_id)

        # Voting phase
        voting_view = quiz_repo.VotingView()
        await interaction.response.send_message(
            f"Choose your topic! Ends **<t:{int(time.time()) + 11}:R>**",
            view=voting_view,
        )
        voting_view.message = await interaction.original_response()  # Store the original message in the view

        await asyncio.sleep(VOTING_TIME)
        number, topic = await voting_view.on_timeout()

        # For dynamic topic
        if has_sub := has_sub_topic(topic):
            topic_id_correct_count = defaultdict(int)

        # Question phase
        participants = defaultdict(int)
        for i in range(1, number + 1):
            async with interaction.channel.typing():
                # Get topic id dynamically based on previous answers
                topic_id = get_sub_topic_id(topic, topic_id_correct_count) if has_sub else get_topic_id(topic)

                # Fetch question
                quiz = get_quizzes_with_token(channel_id, create_api_call(1, topic_id))[0]

                # Generate question UI
                question_view = quiz_repo.QuestionView(
                    i,
                    quiz["question"],
                    quiz["correct_answer"],
                    quiz["incorrect_answers"],
                    quiz["type"],
                )

                # Sending the question
                if i == number:
                    content = f"### {i}) {quiz['question']} Quiz ends **<t:{int(time.time()) + 11}:R>**"
                else:
                    content = f"### {i}) {quiz['question']} Next question **<t:{int(time.time()) + 11}:R>**"
                question_view.message = await interaction.channel.send(
                    content=content,
                    view=question_view,
                    silent=True,
                )

            # Set timer
            await asyncio.sleep(VOTING_TIME)
            correct_users = await question_view.on_timeout()

            # Track correct answers
            for user_id in correct_users:
                participants[user_id] += 1
                score = await db.get_score(user_id)
                await db.set_score(user_id, score + 1)

                # Register topic_id is correctly answered (for dynamic topic)
                if has_sub:
                    topic_id_correct_count[topic_id] += 1

        # Retrieve usernames and sort participants by scores
        top_participants = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:3]
        top_users = []
        for user_id, score in top_participants:
            user = await interaction.guild.fetch_member(user_id)
            top_users.append((user.display_name, score))

        # Send the top 3 users
        if top_users:
            result_message = ""
            for rank, (user_name, score) in enumerate(top_users, start=1):
                result_message += f"{rank}. **{user_name}** - {score} points\n"
            embed = discord.Embed(
                title="Top 3 participants",
                description=result_message,
                color=discord.Color.blurple(),
            )
        else:
            embed = discord.Embed(
                title="No participants.",
                color=discord.Color.red(),
            )
        await interaction.channel.send(content="## Quiz ended", embed=embed)

        # Mark the quiz as ended
        set_quiz_ended(channel_id)


async def setup(bot: commands.Bot) -> None:
    """Setups the Quiz command."""
    await bot.add_cog(QuizCommand(bot))
