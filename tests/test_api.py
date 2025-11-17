"""Tests for GetSongBPM API client."""

import unittest
from unittest.mock import Mock, patch
import requests
from src.api.getsongbpm import GetSongBPMClient


class TestGetSongBPMClient(unittest.TestCase):
    """Test cases for GetSongBPMClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = GetSongBPMClient(self.api_key)

    @patch('src.api.getsongbpm.requests.Session.get')
    def test_search_success(self, mock_get):
        """Test successful API search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "search": [{
                "tempo": "120.0",
                "artist": {"name": "Test Artist"},
                "song_title": "Test Song"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.client.search("Test Artist", "Test Song")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for linter
        self.assertEqual(result["bpm"], 120.0)
        self.assertEqual(result["artist"], "Test Artist")
        self.assertEqual(result["source"], "getsongbpm")

    @patch('src.api.getsongbpm.requests.Session.get')
    def test_search_no_results(self, mock_get):
        """Test API search with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"search": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.client.search("Unknown Artist", "Unknown Song")

        self.assertIsNone(result)

    @patch('src.api.getsongbpm.requests.Session.get')
    def test_search_api_error(self, mock_get):
        """Test API error handling."""
        mock_get.side_effect = requests.RequestException("API Error")

        result = self.client.search("Test Artist", "Test Song")

        self.assertIsNone(result)

    @patch('src.api.getsongbpm.requests.Session.get')
    def test_get_by_id(self, mock_get):
        """Test getting song by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "song": {
                "tempo": "128.0",
                "artist": {"name": "Test Artist"},
                "song_title": "Test Song"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        result = self.client.get_by_id("test_id")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for linter
        self.assertEqual(result["bpm"], 128.0)
        self.assertEqual(result["bpm"], 128.0)


if __name__ == '__main__':
    unittest.main()
