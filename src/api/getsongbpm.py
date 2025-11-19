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
        # Note: Don't request brotli (br) encoding - requests doesn't decompress it automatically
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://getsongbpm.com/",
            "Origin": "https://getsongbpm.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
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

            # Log response details for debugging
            logger.debug(f"Search response status: {response.status_code}")
            logger.debug(f"Search response headers: {dict(response.headers)}")
            print(f"[GetSongBPM] Response status: {response.status_code}, length: {len(response.text)}")

            response.raise_for_status()

            # Check for empty response
            if not response.text:
                logger.warning(f"Empty response from API for: {artist} - {title}")
                print(f"[GetSongBPM] Empty response for: {artist} - {title}")
                return None

            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Invalid JSON response: {response.text[:200]}")
                print(f"[GetSongBPM] Invalid JSON: {response.text[:100]}")
                return None

            # Debug: print the actual response
            print(f"[GetSongBPM] Response data: {data}")

            search_results = data.get("search")

            # Handle different response formats:
            # Success: {'search': [{'id': '...', ...}]} - list of results
            # No results: {'search': {'error': 'no result'}} - dict with error
            if not search_results:
                logger.warning(f"No results for: {artist} - {title}")
                return None

            # Check if it's an error response (dict instead of list)
            if isinstance(search_results, dict):
                if "error" in search_results:
                    logger.warning(f"API returned error for {artist} - {title}: {search_results.get('error')}")
                    print(f"[GetSongBPM] No results found")
                    return None
                else:
                    logger.warning(f"Unexpected search format: {search_results}")
                    return None

            if not isinstance(search_results, list) or len(search_results) == 0:
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
