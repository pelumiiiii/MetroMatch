"""Example showing batch BPM detection for multiple songs."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manager import BPMManager
import time


def main():
    """Batch processing example."""
    print("="*50)
    print("MetroMatch - Batch Processing Example")
    print("="*50 + "\n")

    # Initialize the BPM Manager
    manager = BPMManager(
        mongodb_uri="mongodb://localhost:27017",
        getsongbpm_api_key=None,
        use_scraper=True
    )

    print("BPM Manager initialized\n")

    # List of songs to process
    songs = [
        ("The Weeknd", "Blinding Lights"),
        ("Billie Eilish", "Bad Guy"),
        ("Drake", "One Dance"),
        ("Post Malone", "Circles"),
        ("Ed Sheeran", "Shape of You"),
        ("Taylor Swift", "Shake It Off"),
        ("Mark Ronson", "Uptown Funk"),
        ("Ariana Grande", "7 Rings"),
        ("Justin Bieber", "Sorry"),
        ("Daft Punk", "Get Lucky"),
    ]

    print(f"Processing {len(songs)} songs...")
    print("="*50 + "\n")

    results = []

    # Process each song
    for i, (artist, title) in enumerate(songs, 1):
        print(f"[{i}/{len(songs)}] {artist} - {title}")

        start_time = time.time()
        bpm = manager.get_bpm(artist, title)
        elapsed = time.time() - start_time

        if bpm:
            print(f"  ✓ Found: {bpm} BPM (took {elapsed:.2f}s)")
            results.append({
                "artist": artist,
                "title": title,
                "bpm": bpm,
                "success": True
            })
        else:
            print(f"  ✗ Not found (took {elapsed:.2f}s)")
            results.append({
                "artist": artist,
                "title": title,
                "bpm": None,
                "success": False
            })

        print()

    # Summary
    print("="*50)
    print("Batch Processing Summary")
    print("="*50)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"Total songs processed: {len(results)}")
    print(f"Successfully found: {successful}")
    print(f"Not found: {failed}")
    print(f"Success rate: {(successful/len(results)*100):.1f}%\n")

    # Display results sorted by BPM
    print("Results sorted by BPM:")
    print("-" * 50)

    sorted_results = sorted(
        [r for r in results if r["success"]],
        key=lambda x: x["bpm"]
    )

    for result in sorted_results:
        print(f"{result['bpm']:6.1f} BPM - {result['artist']} - {result['title']}")

    print()

    # BPM statistics
    if sorted_results:
        bpms = [r["bpm"] for r in sorted_results]
        avg_bpm = sum(bpms) / len(bpms)
        min_bpm = min(bpms)
        max_bpm = max(bpms)

        print("BPM Statistics:")
        print("-" * 50)
        print(f"Average BPM: {avg_bpm:.1f}")
        print(f"Slowest: {min_bpm} BPM")
        print(f"Fastest: {max_bpm} BPM")
        print()

    # Cleanup
    manager.cleanup()

    print("="*50)
    print("Example completed!")
    print("="*50)


if __name__ == "__main__":
    main()
