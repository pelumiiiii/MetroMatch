"""Tests for BPM Manager."""

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from src.manager import BPMManager


class TestBPMManager(unittest.TestCase):
    """Test cases for BPMManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_cache = patch('src.manager.MongoDBCache').start()
        self.mock_api = patch('src.manager.GetSongBPMClient').start()
        self.mock_scraper = patch('src.manager.SongBPMScraper').start()
        self.mock_detector = patch('src.manager.NowPlayingDetector').start()
        self.mock_metronome = patch('src.manager.MetronomePlayer').start()
        self.manager = BPMManager(
            mongodb_uri=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'),
            getsongbpm_api_key=os.environ.get('GETSONGBPM_API_KEY', 'test_key'),
            use_scraper=True
        )

    def tearDown(self):
        """Clean up patches."""
        patch.stopall()

    def test_get_bpm_from_cache(self):
        """Test getting BPM from cache."""
        self.manager.cache.get.return_value = {"bpm": 120.0}

        bpm = self.manager.get_bpm("Test Artist", "Test Song")

        self.assertEqual(bpm, 120.0)
        self.manager.cache.get.assert_called_once()

    def test_get_bpm_from_api(self):
        """Test getting BPM from API when cache misses."""
        self.manager.cache.get.return_value = None
        self.manager.api_client.search.return_value = {
            "bpm": 128.0,
            "source": "api"
        }

        bpm = self.manager.get_bpm("Test Artist", "Test Song")

        self.assertEqual(bpm, 128.0)
        self.manager.api_client.search.assert_called_once()
        self.manager.cache.set.assert_called_once()

    def test_get_bpm_from_scraper(self):
        """Test getting BPM from scraper as fallback."""
        self.manager.cache.get.return_value = None
        self.manager.api_client.search.return_value = None
        self.manager.scraper.search.return_value = {
            "bpm": 140.0,
            "source": "scraper"
        }

        bpm = self.manager.get_bpm("Test Artist", "Test Song")

        self.assertEqual(bpm, 140.0)
        self.manager.scraper.search.assert_called_once()

    def test_get_bpm_not_found(self):
        """Test when BPM cannot be found."""
        self.manager.cache.get.return_value = None
        self.manager.api_client.search.return_value = None
        self.manager.scraper.search.return_value = None

        bpm = self.manager.get_bpm("Unknown Artist", "Unknown Song")

        self.assertIsNone(bpm)

    def test_sync_to_now_playing(self):
        """Test syncing to currently playing track."""
        self.manager.now_playing.get_current_track.return_value = {
            "artist": "Test Artist",
            "title": "Test Song"
        }
        self.manager.cache.get.return_value = {"bpm": 120.0}

        success = self.manager.sync_to_now_playing()

        self.assertTrue(success)
        self.assertEqual(self.manager.current_bpm, 120.0)
        self.manager.metronome.set_bpm.assert_called_with(120.0)

    def test_sync_to_now_playing_no_track(self):
        """Test syncing when no track is playing."""
        self.manager.now_playing.get_current_track.return_value = None

        success = self.manager.sync_to_now_playing()

        self.assertFalse(success)

    def test_start_metronome_with_bpm(self):
        """Test starting metronome with specified BPM."""
        self.manager.start_metronome(140.0)

        self.manager.metronome.set_bpm.assert_called_with(140.0)
        self.manager.metronome.start.assert_called_once()
        self.assertEqual(self.manager.current_bpm, 140.0)

    def test_start_metronome_default_bpm(self):
        """Test starting metronome with default BPM."""
        self.manager.start_metronome()

        self.manager.metronome.set_bpm.assert_called_with(120)
        self.manager.metronome.start.assert_called_once()

    def test_stop_metronome(self):
        """Test stopping metronome."""
        self.manager.stop_metronome()

        self.manager.metronome.stop.assert_called_once()

    def test_get_status(self):
        """Test getting manager status."""
        self.manager.current_bpm = 120.0
        self.manager.metronome.is_running = True

        status = self.manager.get_status()

        self.assertEqual(status["current_bpm"], 120.0)
        self.assertTrue(status["metronome_running"])
        self.assertTrue(status["has_cache"])
        self.assertTrue(status["has_api"])
        self.assertTrue(status["has_scraper"])

    def test_cleanup(self):
        """Test cleanup."""
        self.manager.metronome.is_running = True

        self.manager.cleanup()

        self.manager.metronome.stop.assert_called_once()
        self.manager.cache.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
