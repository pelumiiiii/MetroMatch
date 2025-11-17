"""Main BPM Manager that coordinates all components."""

from typing import Optional, Dict, Any
import logging

from .cache.mongodb_cache import MongoDBCache
from .api.getsongbpm import GetSongBPMClient
from .api.scraper import SongBPMScraper
from .detection.now_playing import NowPlayingDetector
from .metronome.player import MetronomePlayer

logger = logging.getLogger(__name__)


class BPMManager:
    """Main manager that coordinates BPM detection and metronome playback."""

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        getsongbpm_api_key: Optional[str] = None,
        use_scraper: bool = True,
        auto_sync: bool = True
    ):
        """
        Initialize the BPM Manager.

        Args:
            mongodb_uri: MongoDB connection string (optional)
            getsongbpm_api_key: API key for GetSongBPM (optional)
            use_scraper: Whether to use web scraper as fallback
            auto_sync: Automatically sync metronome to now playing
        """
        # Initialize components
        self.cache = MongoDBCache(mongodb_uri) if mongodb_uri else None
        self.api_client = GetSongBPMClient(getsongbpm_api_key) if getsongbpm_api_key else None  # toggle to fallback to scraper
        self.scraper = SongBPMScraper() if use_scraper else None
        self.now_playing = NowPlayingDetector()
        self.metronome = MetronomePlayer()

        self.auto_sync = auto_sync
        self.current_track: Optional[Dict[str, Any]] = None
        self.current_bpm: Optional[float] = None

        logger.info("BPM Manager initialized")

    def get_bpm(self, artist: str, title: str) -> Optional[float]:
        """
        Get BPM for a song, trying cache, API, and scraper in order.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            BPM value or None if not found
        """
        # Try cache first
        if self.cache:
            cached = self.cache.get(artist, title)
            if cached:
                logger.info(f"BPM found in cache: {cached['bpm']}")
                return cached['bpm']

        # Try API
        if self.api_client:
            api_result = self.api_client.search(artist, title)
            if api_result and api_result.get('bpm'):
                bpm = api_result['bpm']
                logger.info(f"BPM found via API: {bpm}")

                # Cache the result
                if self.cache:
                    self.cache.set(artist, title, bpm, api_result)

                return bpm

        # Try scraper as fallback
        if self.scraper:
            scrape_result = self.scraper.search(artist, title)
            if scrape_result and scrape_result.get('bpm'):
                bpm = scrape_result['bpm']
                logger.info(f"BPM found via scraper: {bpm}")

                # Cache the result
                if self.cache:
                    self.cache.set(artist, title, bpm, scrape_result)

                return bpm

        logger.warning(f"Could not find BPM for {artist} - {title}")
        return None

    def sync_to_now_playing(self) -> bool:
        """
        Sync metronome to currently playing track.

        Returns:
            True if sync was successful, False otherwise
        """
        track = self.now_playing.get_current_track()

        if not track:
            logger.info("No track currently playing")
            return False

        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')

        logger.info(f"Now playing: {artist} - {title}")

        bpm = self.get_bpm(artist, title)

        if bpm:
            self.current_track = track
            self.current_bpm = bpm
            self.metronome.set_bpm(bpm)
            logger.info(f"Synced metronome to {bpm} BPM")
            return True

        return False

    def start_metronome(self, bpm: Optional[float] = None):
        """
        Start the metronome.

        Args:
            bpm: BPM to use (uses current BPM if not specified)
        """
        if bpm:
            self.metronome.set_bpm(bpm)
            self.current_bpm = bpm
        elif self.current_bpm:
            self.metronome.set_bpm(self.current_bpm)
        else:
            logger.warning("No BPM set, using default 120 BPM")
            self.metronome.set_bpm(120)

        self.metronome.start()

    def stop_metronome(self):
        """Stop the metronome."""
        self.metronome.stop()

    def auto_sync_loop(self, check_interval: float = 5.0):
        """
        Automatically sync metronome to now playing track.

        Args:
            check_interval: How often to check for track changes (seconds)
        """
        import time

        logger.info(f"Starting auto-sync loop (checking every {check_interval}s)")

        try:
            while self.auto_sync:
                track = self.now_playing.get_current_track()

                # Check if track changed
                if track and track != self.current_track:
                    logger.info("Track changed, syncing...")
                    if self.sync_to_now_playing():
                        if not self.metronome.is_running:
                            self.start_metronome()

                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Auto-sync loop interrupted")
            self.stop_metronome()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the manager.

        Returns:
            Dictionary with current status information
        """
        return {
            "current_track": self.current_track,
            "current_bpm": self.current_bpm,
            "metronome_running": self.metronome.is_running,
            "auto_sync": self.auto_sync,
            "has_cache": self.cache is not None,
            "has_api": self.api_client is not None,
            "has_scraper": self.scraper is not None
        }

    def cleanup(self):
        """Clean up resources."""
        if self.metronome.is_running:
            self.stop_metronome()

        if self.cache:
            self.cache.close()

        logger.info("BPM Manager cleaned up")
