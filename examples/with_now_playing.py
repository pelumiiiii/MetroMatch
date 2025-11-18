"""Example showing integration with now playing detection."""

import sys
from pathlib import Path
import logging

# Enable debug logging to see scraper activity
logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manager import BPMManager
from config.settings import MONGODB_URI, GETSONGBPM_API_KEY
import time


def main():
    """Now playing integration example."""
    print("="*50)
    print("MetroMatch - Now Playing Integration Example")
    print("="*50 + "\n")

    # Initialize the BPM Manager
    manager = BPMManager(
        mongodb_uri=MONGODB_URI,
        getsongbpm_api_key=GETSONGBPM_API_KEY,  # Uses key from .env
        use_scraper=True,
        auto_sync=False  # We'll manually control syncing in this example
    )

    print("BPM Manager initialized")
    print("Make sure you have music playing in Spotify, Apple Music, or another supported player\n")

    # Example 1: Detect currently playing track
    print("Example 1: Detecting now playing track")
    print("-" * 50)

    track = manager.now_playing.get_current_track()

    if track:
        print(f"Currently playing:")
        print(f"  Artist: {track['artist']}")
        print(f"  Title: {track['title']}")
        print(f"  Album: {track.get('album', 'N/A')}")
        print(f"  Player: {track.get('player', 'N/A')}\n")
    else:
        print("No track currently playing")
        print("Please start playing music and run this example again\n")
        manager.cleanup()
        return

    # Example 2: Sync metronome to now playing
    print("Example 2: Syncing metronome to now playing track")
    print("-" * 50)

    success = manager.sync_to_now_playing()

    if success:
        print(f"Successfully synced to {manager.current_bpm} BPM")
        print("Starting metronome...")

        manager.start_metronome()
        print("Metronome playing for 10 seconds...\n")
        time.sleep(10)

        manager.stop_metronome()
        print("Metronome stopped\n")
    else:
        print("Could not find BPM for current track\n")

    # Example 3: Monitor for track changes
    print("Example 3: Monitoring for track changes")
    print("-" * 50)
    print("Monitoring for 30 seconds. Try changing tracks in your music player...\n")

    manager.start_metronome()
    current_track = track

    for i in range(30):
        new_track = manager.now_playing.get_current_track()

        if new_track and new_track != current_track:
            print(f"\nTrack changed!")
            print(f"  New track: {new_track['artist']} - {new_track['title']}")

            if manager.sync_to_now_playing():
                print(f"  Synced to {manager.current_bpm} BPM\n")

            current_track = new_track

        time.sleep(1)

    manager.stop_metronome()
    print("Monitoring completed\n")

    # Cleanup
    manager.cleanup()

    print("="*50)
    print("Example completed!")
    print("="*50)


if __name__ == "__main__":
    main()
