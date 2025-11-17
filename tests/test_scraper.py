"""Tests for SongBPM scraper."""

import unittest
from unittest.mock import Mock, patch
from src.api.scraper import SongBPMScraper


class TestSongBPMScraper(unittest.TestCase):
    """Test cases for SongBPMScraper."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = SongBPMScraper()

    @patch('src.api.scraper.requests.Session.get')
    def test_search_success(self, mock_get):
        """Test successful scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
            <html>
                <body>
                    <div>120 BPM</div>
                </body>
            </html>
        '''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.scraper.search("Test Artist", "Test Song")

        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result["bpm"], 120.0)
            self.assertEqual(result["source"], "songbpm_scraper")

    @patch('src.api.scraper.requests.Session.get')
    def test_search_not_found(self, mock_get):
        """Test scraping when page not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Mock search page to return None
        with patch.object(self.scraper, '_search_page', return_value=None):
            result = self.scraper.search("Unknown Artist", "Unknown Song")
            self.assertIsNone(result)

    @patch('src.api.scraper.requests.Session.get')
    def test_search_network_error(self, mock_get):
        """Test network error handling."""
        mock_get.side_effect = Exception("Network Error")

        result = self.scraper.search("Test Artist", "Test Song")

        self.assertIsNone(result)

    def test_extract_bpm(self):
        """Test BPM extraction from HTML."""
        from bs4 import BeautifulSoup

        html = '<html><body><div>Tempo: 140 BPM</div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        bpm = self.scraper._extract_bpm(soup)

        self.assertEqual(bpm, 140.0)

    def test_extract_bpm_no_match(self):
        """Test BPM extraction when no BPM found."""
        from bs4 import BeautifulSoup

        html = '<html><body><div>No tempo information</div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        bpm = self.scraper._extract_bpm(soup)

        self.assertIsNone(bpm)


if __name__ == '__main__':
    unittest.main()
