"""Basic usage example for MetroMatch."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manager import BPMManager

import time
from config import settings


def main():
    """Basic usage example."""
    print("="*50)
    print("MetroMatch - Basic Usage Example")
    print("="*50 + "\n")

    # Initialize the BPM Manager
    # Note: You'll need to provide your own MongoDB URI and API key
    manager = BPMManager(
        mongodb_uri="mongodb://localhost:27017",
        getsongbpm_api_key=settings.GETSONGBPM_API_KEY,  # Set to your API key or leave None to use scraper
        use_scraper=True
    )

    print("BPM Manager initialized\n")

    # Example 1: Get BPM for a specific song
    print("Example 1: Getting BPM for a song")
    print("-" * 50)

    artist = "Daft Punk"
    title = "Get Lucky"

    print(f"Searching for: {artist} - {title}")
    bpm = manager.get_bpm(artist, title)

    if bpm:
        print(f"Found BPM: {bpm}\n")
    else:
        print("BPM not found\n")

    # Example 2: Start metronome at a specific BPM
    print("Example 2: Starting metronome at 120 BPM")
    print("-" * 50)

    manager.start_metronome(120)
    print("Metronome started at 120 BPM")
    print("Playing for 5 seconds...\n")

    time.sleep(5)

    manager.stop_metronome()
    print("Metronome stopped\n")

    # Example 3: Change BPM while playing
    print("Example 3: Changing BPM while playing")
    print("-" * 50)

    manager.start_metronome(100)
    print("Metronome started at 100 BPM")
    time.sleep(3)

    manager.metronome.set_bpm(140)
    print("Changed to 140 BPM")
    time.sleep(3)

    manager.stop_metronome()
    print("Metronome stopped\n")

    # Example 4: Get manager status
    print("Example 4: Manager status")
    print("-" * 50)

    status = manager.get_status()
    print(f"Has cache: {status['has_cache']}")
    print(f"Has API: {status['has_api']}")
    print(f"Has scraper: {status['has_scraper']}")
    print(f"Metronome running: {status['metronome_running']}")
    print(f"Current BPM: {status['current_bpm']}\n")

    # Cleanup
    manager.cleanup()
    print("Cleanup completed")

    print("\n" + "="*50)
    print("Example completed!")
    print("="*50)


if __name__ == "__main__":
    main()
