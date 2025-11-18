#!/usr/bin/env python3
"""Manually add a song's BPM to the cache."""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import MONGODB_URI, MONGODB_DATABASE
from pymongo import MongoClient

def main():
    if len(sys.argv) < 4:
        print("Usage: python add_to_cache.py <artist> <title> <bpm>")
        print("Example: python add_to_cache.py 'CZARFACE' 'Break in the Action' 96")
        return

    artist = sys.argv[1]
    title = sys.argv[2]
    bpm = float(sys.argv[3])

    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db.bpm_cache

    # Add to cache
    collection.update_one(
        {
            "artist": artist.lower(),
            "title": title.lower()
        },
        {
            "$set": {
                "artist": artist.lower(),
                "title": title.lower(),
                "bpm": bpm,
                "last_updated": datetime.now(timezone.utc),
                "metadata": {
                    "source": "manual",
                    "original_artist": artist,
                    "original_title": title
                }
            }
        },
        upsert=True
    )

    print(f"Added to cache: {artist} - {title} = {bpm} BPM")
    client.close()

if __name__ == "__main__":
    main()
