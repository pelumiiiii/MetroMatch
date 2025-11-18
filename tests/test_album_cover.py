#!/usr/bin/env python3
"""Test script for album cover fetching functionality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.media.album_cover import AlbumCoverClient, AlbumCoverManager
from config.settings import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    MONGODB_URI,
    MONGODB_DATABASE
)

def test_spotify_auth():
    """Test Spotify authentication."""
    print("=" * 50)
    print("Testing Spotify Authentication")
    print("=" * 50)

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("ERROR: Spotify credentials not found in .env")
        print(f"  SPOTIFY_CLIENT_ID: {'Set' if SPOTIFY_CLIENT_ID else 'Missing'}")
        print(f"  SPOTIFY_CLIENT_SECRET: {'Set' if SPOTIFY_CLIENT_SECRET else 'Missing'}")
        return False

    print(f"Client ID: {SPOTIFY_CLIENT_ID[:8]}...{SPOTIFY_CLIENT_ID[-4:]}")
    print(f"Client Secret: {'*' * 20}")

    client = AlbumCoverClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    if client.spotify_token:
        print("SUCCESS: Spotify authentication successful!")
        print(f"Token: {client.spotify_token[:20]}...")
        return True
    else:
        print("ERROR: Spotify authentication failed")
        return False

def test_album_cover_search():
    """Test album cover search."""
    print("\n" + "=" * 50)
    print("Testing Album Cover Search")
    print("=" * 50)

    client = AlbumCoverClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    # Test searches
    test_cases = [
        ("Daft Punk", "Get Lucky"),
        ("The Weeknd", "Blinding Lights"),
        ("Taylor Swift", "Shake It Off"),
    ]

    for artist, title in test_cases:
        print(f"\nSearching: '{artist}' - '{title}'")

        # Try Spotify
        result = client.search_spotify(artist, title)
        if result:
            print(f"  Spotify: Found!")
            print(f"    Album: {result.get('album_name')}")
            print(f"    Size: {result.get('width')}x{result.get('height')}")
            print(f"    URL: {result.get('image_url', '')[:50]}...")
        else:
            print(f"  Spotify: Not found")

            # Try iTunes fallback
            result = client.search_itunes(artist, title)
            if result:
                print(f"  iTunes: Found!")
                print(f"    Album: {result.get('album_name')}")
                print(f"    URL: {result.get('image_url', '')[:50]}...")
            else:
                print(f"  iTunes: Not found")

    return True

def test_image_download():
    """Test image downloading."""
    print("\n" + "=" * 50)
    print("Testing Image Download")
    print("=" * 50)

    client = AlbumCoverClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    # Search for a known song
    result = client.search("Daft Punk", "Get Lucky")

    if not result:
        print("ERROR: Could not find album cover to test download")
        return False

    print(f"Downloading from: {result['source']}")
    image_data = client.download_image(result["image_url"])

    if image_data:
        print(f"SUCCESS: Downloaded {len(image_data)} bytes")
        print(f"  Size: {len(image_data) / 1024:.1f} KB")

        # Save to assets folder
        test_file = Path(__file__).parent.parent / "assets" / "test_cover.jpg"
        with open(test_file, "wb") as f:
            f.write(image_data)
        print(f"  Saved to: {test_file}")
        return True
    else:
        print("ERROR: Failed to download image")
        return False

def test_full_manager():
    """Test the full AlbumCoverManager."""
    print("\n" + "=" * 50)
    print("Testing AlbumCoverManager (Full Integration)")
    print("=" * 50)

    # Initialize without MongoDB for simple test
    manager = AlbumCoverManager(
        mongodb_uri=None,  # Skip MongoDB for this test
        spotify_client_id=SPOTIFY_CLIENT_ID,
        spotify_client_secret=SPOTIFY_CLIENT_SECRET
    )

    print("Manager initialized (without MongoDB cache)")

    # Test fetching
    result = manager.get_album_cover("Billie Eilish", "Bad Guy")

    if result:
        print(f"SUCCESS: Got album cover!")
        print(f"  Source: {result.get('source')}")
        print(f"  Album: {result.get('album_name')}")
        print(f"  Size: {len(result.get('image_data', b''))} bytes")
        return True
    else:
        print("ERROR: Failed to get album cover")
        return False

def main():
    """Run all tests."""
    print("\n" + "#" * 50)
    print("# MetroMatch Album Cover Feature Test")
    print("#" * 50)

    results = []

    # Test 1: Authentication
    results.append(("Spotify Auth", test_spotify_auth()))

    # Test 2: Search
    results.append(("Album Search", test_album_cover_search()))

    # Test 3: Download
    results.append(("Image Download", test_image_download()))

    # Test 4: Full manager
    results.append(("Full Manager", test_full_manager()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
