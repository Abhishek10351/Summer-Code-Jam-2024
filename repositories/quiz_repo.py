import asyncio
import random
import time

import discord
from discord.ui import Button, View
from utils.quiz import (
    fetch_categories,
    set_quiz_ended,
)

TOPIC_SELECT_TIMER = 10


class VotingView(View):
    """Topic voting message."""

    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.user_votes = {}
        self.topic_pool = list(fetch_categories().keys())
        for topic in [*random.sample(self.topic_pool, 3), "Random"]:
            self.add_item(TopicButton(label=topic, value=topic, voting_view=self, row=0))

        for count in [5, 10, 15]:
            self.add_item(NumQuestionButton(label=f"{count} Questions", count=count, voting_view=self, row=1))

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
        """After timeout, select topic and number of questions for the coming quizzes."""

        def determine_winner(buttons: TopicButton | NumQuestionButton) -> str:
            """Determine the winning selection from the buttons."""
            counts = {child.value: child.votes for child in buttons}
            max_votes = max(counts.values())
            winners = [value for value, votes in counts.items() if votes == max_votes]
            return random.choice(winners)  # noqa: S311

        def update_button(buttons: TopicButton | NumQuestionButton, selected: str) -> None:
            """Update the original message to highlight the selected options and disable buttons."""
            for child in buttons:
                if child.value == selected:
                    child.style = discord.ButtonStyle.success
                child.disabled = True

        # Separate TopicButton and NumQuestionButton
        topic_buttons = [child for child in self.children if isinstance(child, TopicButton)]
        question_buttons = [child for child in self.children if isinstance(child, NumQuestionButton)]

        # Determine the final selection
        selected_topic = determine_winner(topic_buttons)
        selected_number = determine_winner(question_buttons)

        # Update final buttons
        update_button(topic_buttons, selected_topic)
        update_button(question_buttons, selected_number)

        # Edit bot's message
        result_message = f"Started **{selected_number} questions** on the topic: **{selected_topic}**"
        await self.message.edit(content=result_message, view=self)

        # Mark the quiz as ended
        set_quiz_ended(self.message.channel.id)


class BaseVotingButton(Button):
    """Topic select button layouts."""

    def __init__(
        self, label: str, value: int | str, voting_view: VotingView, row: int, style: discord.ButtonStyle,
    ) -> None:
        super().__init__(label=f"{label} (0)", style=style, row=row)
        self.label_text = label
        self.value = value
        self.votes = 0
        self.voting_view = voting_view

    async def callback(self, interaction: discord.Interaction) -> None:
        """Register and update buttons."""
        user_id = interaction.user.id
        previous_selection = self.voting_view.user_votes.get(user_id, {})

        # Determine the type of the current button (topic or question count)
        is_topic_button = isinstance(self, TopicButton)
        previous_value = previous_selection.get("topic" if is_topic_button else "count")

        # If user already voted, remove their vote from the previous selection
        if previous_value is not None:
            for child in self.voting_view.children:
                if isinstance(child, BaseVotingButton) and child.value == previous_value:
                    child.votes -= 1
                    child.label = f"{child.label_text} ({child.votes})"
                    break

        # Register the new vote
        previous_selection["topic" if is_topic_button else "count"] = self.value
        self.voting_view.user_votes[user_id] = previous_selection
        self.votes += 1
        self.label = f"{self.label_text} ({self.votes})"

        # Update the view
        await interaction.response.edit_message(view=self.voting_view)


class TopicButton(BaseVotingButton):
    """Topic select button layouts."""

    def __init__(self, label: str, value: str, voting_view: VotingView, row: int) -> None:
        super().__init__(label=label, value=value, voting_view=voting_view, row=row, style=discord.ButtonStyle.primary)


class NumQuestionButton(BaseVotingButton):
    """Button for selecting the number of questions."""

    def __init__(self, label: str, count: int, voting_view: VotingView, row: int) -> None:
        super().__init__(
            label=label, value=count, voting_view=voting_view, row=row, style=discord.ButtonStyle.secondary,
        )


def topic_select_timer() -> int:
    """Return global variable for use in quiz.py."""
    return TOPIC_SELECT_TIMER
