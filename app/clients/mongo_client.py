import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.core.config import settings

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:
    AsyncIOMotorClient = None


logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        if AsyncIOMotorClient is None:
            logger.warning("Motor library not available. MongoDB Atlas connection skipped.")
            return

        try:
            logger.info("Connecting to MongoDB Atlas (quality database)...")
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.MONGODB_DB_NAME]
            logger.info(f"Successfully connected to MongoDB database: '{settings.MONGODB_DB_NAME}'")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB Atlas connection closed.")

    async def upsert_quality_result(self, content_id: str, data: Dict[str, Any]) -> bool:
        if self.db is None:
            return False
        try:
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.db["quality_results"].update_one(
                {"content_id": content_id},
                {"$set": data},
                upsert=True
            )
            logger.info(f"Successfully upserted quality result for content_id: {content_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert quality result to MongoDB: {e}")
            return False

    async def update_label(self, content_id: str, label_data: Dict[str, Any]) -> bool:
        if self.db is None:
            return False
        try:
            update_payload = {
                "user_corrected": True,
                "corrected_at": datetime.now(timezone.utc).isoformat(),
            }
            for k, v in label_data.items():
                if v is not None:
                    update_payload[k] = v

            await self.db["quality_results"].update_one(
                {"content_id": content_id},
                {"$set": update_payload},
                upsert=True
            )
            logger.info(f"Successfully updated label for content_id: {content_id} in MongoDB Atlas.")
            return True
        except Exception as e:
            logger.error(f"Failed to update label in MongoDB: {e}")
            return False

    async def get_result(self, content_id: str) -> Optional[Dict[str, Any]]:
        if self.db is None:
            return None
        try:
            res = await self.db["quality_results"].find_one({"content_id": content_id}, {"_id": 0})
            return res
        except Exception as e:
            logger.error(f"Failed to get quality result from MongoDB: {e}")
            return None

    async def list_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.db is None:
            return []
        try:
            cursor = self.db["quality_results"].find({}, {"_id": 0}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to list quality results from MongoDB: {e}")
            return []


mongo_client = MongoDBClient()

