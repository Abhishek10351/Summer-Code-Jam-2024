import random

import discord
from discord import app_commands
from discord.ext import commands
from utils.gemini import gemini_client


class FactCommand(commands.Cog):
    """Fact commands cog."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize FactCommand cog."""
        self.bot = bot

    @app_commands.command(name="discuss")
    async def discuss(self, interaction: discord.Interaction, topic: str) -> None:
        """Create a discussion on the given topic."""
        await interaction.response.send_message(f"You have started a discussion on the topic: {topic}")
        conversation = await gemini_client.generate_conversation(topic)
        users = random.sample([member for member in interaction.guild.members if not member.bot], k=3)

        webhooks = await interaction.channel.webhooks()
        if not webhooks:
            webhook = await interaction.channel.create_webhook(name="Discussion")
        else:
            webhook = webhooks[0]

        for message in conversation:
            user = users[message["userid"] % len(users)]
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            await webhook.send(content=message["message"], username=user.display_name, avatar_url=avatar_url)


async def setup(bot: commands.Bot) -> None:
    """Setups the Fact command."""
    await bot.add_cog(FactCommand(bot))
