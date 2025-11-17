"""GetSongBPM API client for retrieving BPM data.

API Documentation: https://getsongbpm.com/api
- Free API with registration required
- Endpoints: /search/ (search by artist/song) and /song/ (get by ID)
"""

import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GetSongBPMClient:
    """Simplified client for GetSongBPM API.

    Usage:
        client = GetSongBPMClient(api_key="your_key")
        result = client.search("Daft Punk", "Get Lucky")
        if result:
            print(f"BPM: {result['bpm']}")
    """

    BASE_URL = "https://api.getsongbpm.com"

    def __init__(self, api_key: str):
        """Initialize with API key from https://getsongbpm.com/api"""
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MetroMatch/1.0"})

    def search(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search for song BPM by artist and title."""
        return self._request("/search/", {"artist": artist, "song": title}, "search")

    def get_by_id(self, song_id: str) -> Optional[Dict[str, Any]]:
        """Get song data by GetSongBPM ID."""
        return self._request("/song/", {"id": song_id}, "song")

    def _request(self, endpoint: str, params: Dict, data_key: str) -> Optional[Dict[str, Any]]:
        """Make API request and parse response."""
        try:
            params["api_key"] = self.api_key
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            song_data = data.get(data_key)

            # Handle list response (search) or dict response (get by ID)
            if isinstance(song_data, list):
                song_data = song_data[0] if song_data else None

            if song_data:
                return self._parse_song(song_data)

            logger.warning(f"No results from {endpoint} with params {params}")
            return None

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing response: {e}")
            return None

    def _parse_song(self, song: Dict) -> Dict[str, Any]:
        """Parse song data into standard format."""
        return {
            "bpm": float(song.get("tempo", 0)),
            "artist": song.get("artist", {}).get("name"),
            "title": song.get("song_title"),
            "source": "getsongbpm",
            "raw_data": song
        }
