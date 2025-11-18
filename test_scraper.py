#!/usr/bin/env python3
"""Quick test for the scraper."""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

sys.path.insert(0, str(Path(__file__).parent))

from src.api.scraper import SongBPMScraper

def main():
    scraper = SongBPMScraper()

    # Test with CZARFACE
    print("Testing: CZARFACE - Break in the Action")
    print("-" * 50)

    result = scraper.search("CZARFACE", "Break in the Action")

    if result:
        print(f"SUCCESS! BPM: {result['bpm']}")
        print(f"URL: {result.get('url')}")
    else:
        print("Not found - check debug output above")

        # Try the URL manually
        url = "https://songbpm.com/@czarface/break-in-the-action"
        print(f"\nTry visiting: {url}")

if __name__ == "__main__":
    main()
