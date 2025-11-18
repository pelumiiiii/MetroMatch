"""MongoDB cache implementation for storing BPM data."""

from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)


class MongoDBCache:
    """Cache for storing song BPM data in MongoDB."""

    def __init__(self, connection_string: str, database_name: str = "metromatch"):
        """
        Initialize MongoDB cache.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        # Set a short timeout to avoid blocking if MongoDB isn't running
        self.client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=2000,  # 2 second timeout
            connectTimeoutMS=2000
        )
        self.db = self.client[database_name]
        self.collection = self.db.bpm_cache
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for efficient querying."""
        try:
            self.collection.create_index([("artist", 1), ("title", 1)], unique=True)
            self.collection.create_index("last_updated")
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def get(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve BPM data from cache.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Cached BPM data or None if not found
        """
        try:
            result = self.collection.find_one({
                "artist": artist.lower(),
                "title": title.lower()
            })
            if result:
                logger.debug(f"Cache hit for {artist} - {title}")
                return result
            logger.debug(f"Cache miss for {artist} - {title}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, artist: str, title: str, bpm: float, metadata: Optional[Dict] = None):
        """
        Store BPM data in cache.

        Args:
            artist: Artist name
            title: Song title
            bpm: Beats per minute
            metadata: Additional metadata to store
        """
        try:
            from datetime import datetime, timezone

            document = {
                "artist": artist.lower(),
                "title": title.lower(),
                "bpm": bpm,
                "last_updated": datetime.now(timezone.utc),
                "metadata": metadata or {}
            }

            self.collection.update_one(
                {"artist": artist.lower(), "title": title.lower()},
                {"$set": document},
                upsert=True
            )
            logger.info(f"Cached BPM for {artist} - {title}: {bpm}")
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    def clear(self):
        """Clear all cached data."""
        try:
            result = self.collection.delete_many({})
            logger.info(f"Cleared {result.deleted_count} cached entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")
