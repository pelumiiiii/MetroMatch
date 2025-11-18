#!/usr/bin/env python3
"""Check and clear cache entries."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import MONGODB_URI, MONGODB_DATABASE
from pymongo import MongoClient

def main():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db.bpm_cache

    # Find all CZARFACE entries
    print("Looking for CZARFACE cache entries...\n")

    entries = list(collection.find({
        "artist": {"$regex": "czarface", "$options": "i"}
    }))

    if entries:
        for entry in entries:
            print(f"Found: {entry['artist']} - {entry['title']}")
            print(f"  BPM: {entry.get('bpm')}")
            print(f"  ID: {entry.get('_id')}")
            print()

        # Delete all CZARFACE entries
        result = collection.delete_many({
            "artist": {"$regex": "czarface", "$options": "i"}
        })
        print(f"Deleted {result.deleted_count} entries")
    else:
        print("No CZARFACE entries found in cache")

    client.close()

if __name__ == "__main__":
    main()
