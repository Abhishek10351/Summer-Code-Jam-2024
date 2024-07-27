import logging
import os
from dotenv import load_dotenv
import motor.motor_asyncio

logger = logging.getLogger("db")


class Database:
    """Database class."""

    def __init__(self, database: str) -> None:
        """Form Database Connection."""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(database)
        self.db = self.client["bot-data"]
        self.scores = self.db["scores"]
        self.commands_cache = self.db["commands_cache"]

        logger.info("Connected to MongoDB database.")

    async def get_score(self, user_id: int) -> int:
        """Get the score of a user."""
        score = await self.scores.find_one({"user_id": user_id})
        return score["score"] if score else 0

    async def set_score(self, user_id: int, score: int) -> None:
        """Set the score of a user."""
        await self.scores.update_one(
            {"user_id": user_id}, {"$set": {"score": score}}, upsert=True
        )

    async def command_is_active(self, command_name: str, channel_id: int) -> bool:
        """Check if a command is active."""
        command = await self.commands_cache.find_one(
            {"command_name": command_name, "channel_id": channel_id}
        )
        return command["active"] if command else False

    async def set_command_active(self, command_name: str, channel_id: int) -> None:
        """Set a command as active."""
        await self.commands_cache.update_one(
            {"command_name": command_name, "channel_id": channel_id},
            {"$set": {"active": True}},
            upsert=True,
        )

    async def set_command_inactive(self, command_name: str, channel_id: int) -> None:
        """Set a command as inactive."""
        await self.commands_cache.update_one(
            {"command_name": command_name, "channel_id": channel_id},
            {"$set": {"active": False}},
            upsert=True,
        )

    async def clear_command_cache(self) -> None:
        """Clear the command cache."""
        await self.commands_cache.delete_many({})

    async def close(self) -> None:
        """Close the database connection."""
        self.client.close()


db = Database(os.getenv("DATABASE"))
