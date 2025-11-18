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
        # Use realistic browser headers to avoid Cloudflare blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def search(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search for song BPM by artist and title.

        Two-step process:
        1. Search to find song ID
        2. Get song details (including BPM) by ID
        """
        try:
            # Search for song directly with artist and title
            # Format: song:{title} artist:{artist} (spaces become + in URL)
            # Use lowercase for better matching
            lookup = f"song:{title.lower()} artist:{artist.lower()}"
            params = {"api_key": self.api_key, "type": "both", "lookup": lookup}
            response = self.session.get(f"{self.BASE_URL}/search/", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            search_results = data.get("search")

            if not search_results or len(search_results) == 0:
                logger.warning(f"No results for: {artist} - {title}")
                return None

            # Get the first result's ID
            song_id = search_results[0].get("id")
            if not song_id:
                logger.warning(f"No song ID in search result for: {artist} - {title}")
                return None

            logger.info(f"Found song ID: {song_id} for {artist} - {title}")

            # Get full song data by ID (includes BPM/tempo)
            return self.get_by_id(song_id)

        except requests.RequestException as e:
            logger.error(f"Search request failed: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing search response: {e}")
            return None

    def get_by_id(self, song_id: str) -> Optional[Dict[str, Any]]:
        """Get song data by GetSongBPM ID."""
        try:
            params = {"api_key": self.api_key, "id": song_id}
            response = self.session.get(f"{self.BASE_URL}/song/", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            song_data = data.get("song")

            if song_data:
                return self._parse_song(song_data)

            logger.warning(f"No song data for ID: {song_id}")
            return None

        except requests.RequestException as e:
            logger.error(f"Song request failed: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing song response: {e}")
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
