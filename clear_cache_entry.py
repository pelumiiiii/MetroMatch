#!/usr/bin/env python3
"""Clear a specific entry from the BPM cache."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import MONGODB_URI, MONGODB_DATABASE
from pymongo import MongoClient

def main():
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db.bpm_cache

    # Delete the cached entry for CZARFACE - Break in the Action
    artist = "czarface"
    title = "break in the action"

    result = collection.delete_one({
        "artist": artist.lower(),
        "title": title.lower()
    })

    if result.deleted_count > 0:
        print(f"Deleted cache entry for '{artist}' - '{title}'")
        print("Run the example again to fetch the correct BPM (96)")
    else:
        print(f"No cache entry found for '{artist}' - '{title}'")

    client.close()

if __name__ == "__main__":
    main()
