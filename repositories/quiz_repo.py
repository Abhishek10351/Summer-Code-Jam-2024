import asyncio
import random
import time

import discord
from discord.ui import Button, View
from utils.quiz import (
    fetch_categories,
    set_quiz_status,
)

TOPIC_SELECT_TIMER = 10

class VotingView(View):
    """Topic voting message."""

    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.user_votes = {}
        self.topic_pool = list(fetch_categories().keys())
        for topic in [*random.sample(self.topic_pool, 3), "Random"]:
            self.add_item(VotingButton(label=topic, voting_view=self))

    async def update_message(self) -> None:
        """Update the message with the current countdown timer."""
        start_time = time.time()
        while True:
            elapsed_time = round(time.time() - start_time)
            remaining_time = TOPIC_SELECT_TIMER - elapsed_time
            if remaining_time <= 0:
                break
            timer_message = f"Choose your topic! Time remaining: **{remaining_time-1} seconds**"
            await self.message.edit(content=timer_message, view=self)
            await asyncio.sleep(0.5)

    async def on_timeout(self) -> None:
        """After timeout, select topic for the coming quizzes."""
        # Count votes
        vote_counts = {child.label_text: child.votes for child in self.children}

        # Find the highest selection(s)
        max_votes = max(vote_counts.values())
        winners = [topic for topic, votes in vote_counts.items() if votes == max_votes]

        # Determine the result
        result = random.choice(winners)  # noqa: S311

        # Send the result message
        result_message = f"The selected topic is: **{result}** *({max_votes} votes)*"
        await self.message.channel.send(result_message)

        # Delete the original message
        await self.message.delete()

        # Mark the quiz as ended
        set_quiz_status(self.message.channel.id, False)


class VotingButton(Button):
    """Topic select button layouts."""

    def __init__(self, label: str, voting_view: VotingView) -> None:
        super().__init__(label=f"{label} (0)", style=discord.ButtonStyle.primary)
        self.label_text = label
        self.votes = 0
        self.voting_view = voting_view

    async def callback(self, interaction: discord.Interaction) -> None:
        """Register and update buttons."""
        user_id = interaction.user.id
        previous_selection = self.voting_view.user_votes.get(user_id)

        # If user already voted, remove their vote from the previous selection
        if previous_selection:
            for child in self.voting_view.children:
                if child.label.startswith(previous_selection):
                    child.votes -= 1
                    child.label = f"{child.label_text} ({child.votes})"
                    break

        # Register the new vote
        self.voting_view.user_votes[user_id] = self.label_text
        self.votes += 1
        self.label = f"{self.label_text} ({self.votes})"

        # Update the view
        await interaction.response.edit_message(view=self.voting_view)


def topic_select_timer() -> int:
    """Return global variable for use in quiz.py."""
    return TOPIC_SELECT_TIMER
