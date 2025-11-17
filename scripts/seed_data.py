"""Script to seed the database with sample BPM data."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample BPM data
SAMPLE_DATA = [
    {"artist": "daft punk", "title": "get lucky", "bpm": 116.0},
    {"artist": "the weeknd", "title": "blinding lights", "bpm": 171.0},
    {"artist": "billie eilish", "title": "bad guy", "bpm": 135.0},
    {"artist": "drake", "title": "one dance", "bpm": 104.0},
    {"artist": "post malone", "title": "circles", "bpm": 120.0},
    {"artist": "ed sheeran", "title": "shape of you", "bpm": 96.0},
    {"artist": "taylor swift", "title": "shake it off", "bpm": 160.0},
    {"artist": "bruno mars", "title": "uptown funk", "bpm": 115.0},
    {"artist": "ariana grande", "title": "7 rings", "bpm": 140.0},
    {"artist": "justin bieber", "title": "sorry", "bpm": 100.0},
    {"artist": "queen", "title": "bohemian rhapsody", "bpm": 144.0},
    {"artist": "the beatles", "title": "come together", "bpm": 82.0},
    {"artist": "nirvana", "title": "smells like teen spirit", "bpm": 117.0},
    {"artist": "led zeppelin", "title": "stairway to heaven", "bpm": 82.0},
    {"artist": "pink floyd", "title": "wish you were here", "bpm": 130.0},
    {"artist": "ac/dc", "title": "back in black", "bpm": 94.0},
    {"artist": "guns n' roses", "title": "sweet child o' mine", "bpm": 125.0},
    {"artist": "metallica", "title": "enter sandman", "bpm": 123.0},
    {"artist": "journey", "title": "don't stop believin'", "bpm": 119.0},
    {"artist": "bon jovi", "title": "livin' on a prayer", "bpm": 123.0},
]


def seed_database(connection_string: str = "mongodb://localhost:27017", database_name: str = "metromatch"):
    """
    Seed the database with sample BPM data.

    Args:
        connection_string: MongoDB connection string
        database_name: Name of the database
    """
    try:
        logger.info(f"Connecting to MongoDB at {connection_string}...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)

        # Test connection
        client.server_info()
        logger.info("Connected to MongoDB successfully")

        # Get database and collection
        db = client[database_name]
        collection = db.bpm_cache

        # Insert sample data
        inserted_count = 0
        updated_count = 0

        for song in SAMPLE_DATA:
            song_with_metadata = {
                **song,
                "last_updated": datetime.now(),
                "metadata": {
                    "source": "seed_data",
                    "verified": True
                }
            }

            result = collection.update_one(
                {"artist": song["artist"], "title": song["title"]},
                {"$set": song_with_metadata},
                upsert=True
            )

            if result.upserted_id:
                inserted_count += 1
                logger.info(f"Inserted: {song['artist']} - {song['title']} ({song['bpm']} BPM)")
            else:
                updated_count += 1
                logger.info(f"Updated: {song['artist']} - {song['title']} ({song['bpm']} BPM)")

        logger.info("Database seeding completed!")

        # Print summary
        print("\n" + "="*50)
        print("Database Seeding Summary")
        print("="*50)
        print(f"Total songs: {len(SAMPLE_DATA)}")
        print(f"New entries inserted: {inserted_count}")
        print(f"Existing entries updated: {updated_count}")
        print("="*50 + "\n")

        client.close()

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        sys.exit(1)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed MetroMatch database with sample data")
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

    seed_database(args.uri, args.database)


if __name__ == "__main__":
    main()
