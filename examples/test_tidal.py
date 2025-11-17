"""Test Tidal now playing detection using window title monitoring."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detection.now_playing import NowPlayingDetector
import logging

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def main():
    """Test Tidal detection."""
    print("=" * 60)
    print("Tidal Now Playing Detection Test")
    print("=" * 60)
    print("\nThis test uses window title monitoring to detect Tidal playback.")
    print("Requirements:")
    print("  1. Tidal app must be running on screen")
    print("  2. A song must be playing")
    print("  3. Tidal window title must show: 'Artist - Song - TIDAL'")
    print("\nNote: This may require Accessibility permissions.")
    print("=" * 60)
    print()

    # Initialize detector
    detector = NowPlayingDetector()

    # Try to get current track
    print("Checking for currently playing track...")
    track = detector.get_current_track()

    if track:
        print("\n✅ SUCCESS! Found playing track:\n")
        print(f"  Artist:  {track.get('artist')}")
        print(f"  Title:   {track.get('title')}")
        print(f"  Album:   {track.get('album', 'N/A')}")
        print(f"  Player:  {track.get('player')}")
        print()
    else:
        print("\n❌ No track found.")
        print("\nTroubleshooting:")
        print("  - Make sure Tidal is running and playing a song")
        print("  - Check that Tidal window title shows track info")
        print("  - You may need to grant Accessibility permissions:")
        print("    System Preferences → Security & Privacy → Accessibility")
        print("    → Add Terminal or your Python IDE")
        print()

    print("=" * 60)


if __name__ == "__main__":
    main()
