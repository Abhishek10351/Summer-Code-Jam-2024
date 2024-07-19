import os
from datetime import datetime
from functools import partial

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
server = os.getenv("SERVER")
MY_GUILD = discord.Object(id=server)

intents = discord.Intents.all()
allowed_installs = discord.app_commands.AppInstallationType(guild=MY_GUILD)


class Bot(commands.Bot):
    """Bot class."""

    def __init__(self) -> None:
        """Bot Initialization."""
        super().__init__(
            command_prefix="!",
            case_insensitive=True,
            strip_after_prefix=True,
            intents=intents,
        )
        self.tree.command = partial(self.tree.command, guild=MY_GUILD)

    async def setup_hook(self) -> None:
        """Setups hook for the bot."""
        # This copies the global commands over to your guild.
        await self.load_extensions()
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self) -> None:
        """Call when bot is logged in."""
        await bot.change_presence(activity=discord.Game(name="/help"))
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\tLogged in as {bot.user} (ID: {bot.user.id})")  # noqa: DTZ005
        print("------")

    async def load_extensions(self) -> None:
        """Load all extensions in the cogs directory."""
        extension_path = "cogs"
        for filename in os.listdir(extension_path):
            if filename.endswith(".py") and filename != "__init__.py":
                await bot.load_extension(f"{extension_path}.{filename[:-3]}")
                print("Extension: " + filename + " loaded.")


bot = Bot()


@bot.tree.command(name="hello")
async def hello(interaction: discord.Interaction) -> None:
    """Say hello!."""
    await interaction.response.send_message(
        f"Hi, {interaction.user.mention}.. Whatcha doin?",
    )


try:
    bot.run(BOT_TOKEN)
except KeyboardInterrupt:
    print("\nKeyboardInterrupt is raised. Exiting.".upper())
