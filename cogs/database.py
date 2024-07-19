import logging
import os

import motor.motor_asyncio

logger = logging.getLogger("bot")


class Database:
    def __init__(self, database: str) -> None:
        self.client = motor.motor_asyncio.AsyncIOMotorClient(database)
        self.db = self.client["bot-data"]
        self.scores = self.db["scores"]

        logger.info("Connected to MongoDB database.")

    async def get_score(self, user_id: int) -> int:
        score = await self.scores.find_one({"user_id": user_id})
        return score["score"] if score else 0

    async def set_score(self, user_id: int, score: int) -> None:
        await self.scores.update_one({"user_id": user_id}, {"$set": {"score": score}}, upsert=True)

    async def close(self) -> None:
        self.client.close()


db = Database(os.getenv("DATABASE"))
