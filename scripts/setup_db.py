"""Script to initialize MongoDB database for MetroMatch."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database(connection_string: str = "mongodb://localhost:27017", database_name: str = "metromatch"):
    """
    Initialize the MongoDB database with indexes and collections.

    Args:
        connection_string: MongoDB connection string
        database_name: Name of the database to create
    """
    try:
        logger.info(f"Connecting to MongoDB at {connection_string}...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)

        # Test connection
        client.server_info()
        logger.info("Connected to MongoDB successfully")

        # Get database
        db = client[database_name]
        logger.info(f"Using database: {database_name}")

        # Create collections
        collections = ["bpm_cache", "search_history"]

        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")

        # Create indexes on bpm_cache
        bpm_cache = db.bpm_cache
        bpm_cache.create_index([("artist", 1), ("title", 1)], unique=True)
        bpm_cache.create_index("last_updated")
        logger.info("Created indexes on bpm_cache collection")

        # Create indexes on search_history
        search_history = db.search_history
        search_history.create_index("timestamp")
        search_history.create_index([("artist", 1), ("title", 1)])
        logger.info("Created indexes on search_history collection")

        logger.info("Database setup completed successfully!")

        # Print summary
        print("\n" + "="*50)
        print("Database Setup Summary")
        print("="*50)
        print(f"Database: {database_name}")
        print(f"Collections: {', '.join(collections)}")
        print("="*50 + "\n")

        client.close()

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.error("Make sure MongoDB is running on your system")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize MetroMatch database")
    parser.add_argument(
        "--uri",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI (default: mongodb://localhost:27017)"
    )
    parser.add_argument(
        "--database",
        default="metromatch",
        help="Database name (default: metromatch)"
    )

    args = parser.parse_args()

    setup_database(args.uri, args.database)


if __name__ == "__main__":
    main()
