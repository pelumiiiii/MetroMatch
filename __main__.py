"""
MetroMatch - Main entry point
Run with: python -m metromatch
"""

import sys
import argparse
from pathlib import Path

# Add src to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from src.manager import BPMManager
from config.settings import (
    MONGODB_URI,
    GETSONGBPM_API_KEY,
    USE_SCRAPER,
    AUTO_SYNC,
    DEFAULT_BPM
)


def main():
    """Main entry point for MetroMatch CLI."""
    parser = argparse.ArgumentParser(
        description="MetroMatch - BPM Detection and Metronome Sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get BPM for a song
  python -m metromatch bpm "Daft Punk" "Get Lucky"

  # Start metronome at 120 BPM
  python -m metromatch metronome 120

  # Sync metronome to now playing
  python -m metromatch sync

  # Show statistics
  python -m metromatch stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # BPM command
    bpm_parser = subparsers.add_parser('bpm', help='Get BPM for a song')
    bpm_parser.add_argument('artist', help='Artist name')
    bpm_parser.add_argument('title', help='Song title')

    # Metronome command
    metronome_parser = subparsers.add_parser('metronome', help='Start metronome')
    metronome_parser.add_argument('bpm', type=float, nargs='?', default=DEFAULT_BPM,
                                  help=f'BPM (default: {DEFAULT_BPM})')
    metronome_parser.add_argument('--duration', type=int, default=None,
                                  help='Duration in seconds (default: infinite)')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync to now playing')
    sync_parser.add_argument('--auto', action='store_true',
                            help='Enable auto-sync loop')

    # Stats command
    subparsers.add_parser('stats', help='Show statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize manager
    print("🎵 Initializing MetroMatch...")
    manager = BPMManager(
        mongodb_uri=MONGODB_URI,
        getsongbpm_api_key=GETSONGBPM_API_KEY,
        use_scraper=USE_SCRAPER,
        auto_sync=AUTO_SYNC
    )

    try:
        if args.command == 'bpm':
            # Get BPM command
            print(f"\n🔍 Looking up: {args.artist} - {args.title}")
            bpm = manager.get_bpm(args.artist, args.title)

            if bpm:
                print(f"✅ BPM: {bpm}")
            else:
                print("❌ Could not find BPM")
                sys.exit(1)

        elif args.command == 'metronome':
            # Metronome command
            print(f"\n🥁 Starting metronome at {args.bpm} BPM")
            manager.start_metronome(args.bpm)

            if args.duration:
                import time
                print(f"⏱️  Running for {args.duration} seconds (Ctrl+C to stop)")
                time.sleep(args.duration)
            else:
                print("⏱️  Running (Ctrl+C to stop)")
                import time
                while True:
                    time.sleep(1)

        elif args.command == 'sync':
            # Sync command
            if args.auto:
                print("\n🔄 Starting auto-sync loop (Ctrl+C to stop)")
                manager.auto_sync = True
                manager.auto_sync_loop()
            else:
                print("\n🔄 Syncing to now playing...")
                if manager.sync_to_now_playing():
                    print(f"✅ Synced! BPM: {manager.current_bpm}")
                    if manager.current_track:
                        print(f"🎵 Track: {manager.current_track.get('artist')} - {manager.current_track.get('title')}")

                    # Start metronome
                    manager.start_metronome()
                    print("🥁 Metronome started (Ctrl+C to stop)")

                    import time
                    while True:
                        time.sleep(1)
                else:
                    print("❌ No track playing or BPM not found")
                    sys.exit(1)

        elif args.command == 'stats':
            # Stats command
            print("\n📊 MetroMatch Statistics")
            print("=" * 60)

            status = manager.get_status()
            print(f"Current BPM: {status['current_bpm'] or 'N/A'}")
            print(f"Metronome Running: {status['metronome_running']}")
            print(f"Auto Sync: {status['auto_sync']}")
            print(f"\nFeatures Available:")
            print(f"  - MongoDB Cache: {'✅' if status['has_cache'] else '❌'}")
            print(f"  - GetSongBPM API: {'✅' if status['has_api'] else '❌'}")
            print(f"  - Web Scraper: {'✅' if status['has_scraper'] else '❌'}")

            if status['current_track']:
                track = status['current_track']
                print(f"\nCurrent Track:")
                print(f"  {track.get('artist')} - {track.get('title')}")
                print(f"  Player: {track.get('player')}")

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
    finally:
        manager.cleanup()
        print("👋 Goodbye!")


if __name__ == '__main__':
    main()
