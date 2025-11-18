"""
Album cover fetching and caching module for MetroMatch.

Supports fetching album artwork from Spotify and iTunes APIs,
with MongoDB caching for efficient retrieval.
"""

import base64
import logging
import requests
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

logger = logging.getLogger(__name__)


class AlbumCoverClient:
    """Client for fetching album covers from music APIs."""

    SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_URL = "https://api.spotify.com/v1"
    ITUNES_API_URL = "https://itunes.apple.com/search"

    def __init__(self, spotify_client_id: Optional[str] = None, spotify_client_secret: Optional[str] = None):
        """
        Initialize the album cover client.

        Args:
            spotify_client_id: Spotify API client ID (optional). If None, Spotify search will be unavailable.
            spotify_client_secret: Spotify API client secret (optional). If None, Spotify search will be unavailable.
        
        Note:
            If credentials are None, they remain None and authentication is skipped.
            Spotify token will only be set if valid credentials are provided.
        """
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MetroMatch/1.0"})

        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.spotify_token = None
        self.spotify_token_expiry = None

        # Authenticate with Spotify if credentials provided
        if spotify_client_id and spotify_client_secret:
            self._spotify_authenticate()

    def _spotify_authenticate(self) -> bool:
        """Authenticate with Spotify API and get access token."""
        try:
            auth_str = f"{self.spotify_client_id}:{self.spotify_client_secret}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()

            response = self.session.post(
                self.SPOTIFY_AUTH_URL,
                headers={"Authorization": f"Basic {auth_b64}"},
                data={"grant_type": "client_credentials"},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self.spotify_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self.spotify_token_expiry = datetime.now(timezone.utc).timestamp() + expires_in - 60

            logger.info("Spotify authentication successful")
            return True

        except requests.RequestException as e:
            logger.error(f"Spotify authentication failed: {e}")
            return False

    def _ensure_spotify_token(self) -> bool:
        """Ensure we have a valid Spotify token."""
        if not self.spotify_client_id or not self.spotify_client_secret:
            return False

        if not self.spotify_token or not self.spotify_token_expiry or datetime.now(timezone.utc).timestamp() > self.spotify_token_expiry:
            return self._spotify_authenticate()

        return True

    def search_spotify(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for album cover on Spotify.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Dict with image info or None if not found
        """
        if not self._ensure_spotify_token():
            return None

        try:
            query = f"track:{title} artist:{artist}"
            response = self.session.get(
                f"{self.SPOTIFY_API_URL}/search",
                headers={"Authorization": f"Bearer {self.spotify_token}"},
                params={
                    "q": query,
                    "type": "track",
                    "limit": 1
                },
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])

            if not tracks:
                logger.debug(f"No Spotify results for '{artist}' - '{title}'")
                return None

            track = tracks[0]
            album = track.get("album", {})
            images = album.get("images", [])

            if not images:
                return None

            # Get the largest image (first in list)
            image = images[0]

            return {
                "image_url": image.get("url"),
                "width": image.get("width", 640),
                "height": image.get("height", 640),
                "source": "spotify",
                "album_name": album.get("name"),
                "raw_data": track
            }

        except requests.RequestException as e:
            logger.error(f"Spotify search failed: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing Spotify response: {e}")
            return None

    def search_itunes(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for album cover on iTunes (fallback).

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Dict with image info or None if not found
        """
        try:
            query = f"{artist} {title}"
            response = self.session.get(
                self.ITUNES_API_URL,
                params={
                    "term": query,
                    "media": "music",
                    "entity": "song",
                    "limit": 1
                },
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.debug(f"No iTunes results for '{artist}' - '{title}'")
                return None

            track = results[0]
            artwork_url = track.get("artworkUrl100", "")

            if not artwork_url:
                return None

            # Get higher resolution (600x600 instead of 100x100)
            artwork_url = artwork_url.replace("100x100", "600x600")

            return {
                "image_url": artwork_url,
                "width": 600,
                "height": 600,
                "source": "itunes",
                "album_name": track.get("collectionName"),
                "raw_data": track
            }

        except requests.RequestException as e:
            logger.error(f"iTunes search failed: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing iTunes response: {e}")
            return None

    def search(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for album cover using available sources.

        Tries Spotify first, then falls back to iTunes.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Dict with image info or None if not found
        """
        # Try Spotify first
        result = self.search_spotify(artist, title)
        if result:
            return result

        # Fallback to iTunes
        result = self.search_itunes(artist, title)
        if result:
            return result

        logger.warning(f"No album cover found for '{artist}' - '{title}'")
        return None

    def download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from URL.

        Args:
            image_url: URL of the image to download

        Returns:
            Image bytes or None if download failed
        """
        try:
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                logger.error(f"Invalid content type: {content_type}")
                return None

            return response.content

        except requests.RequestException as e:
            logger.error(f"Image download failed: {e}")
            return None


class AlbumCoverCache:
    """MongoDB cache for album cover images."""

    def __init__(self, connection_string: str, database_name: str = "metromatch"):
        """
        Initialize the album cover cache.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        if MongoClient is None:
            raise ImportError("pymongo is required for MongoDB caching")

        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db.album_covers
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for efficient querying."""
        try:
            # Compound index for artist + title lookups
            self.collection.create_index(
                [("artist", 1), ("title", 1)],
                unique=True,
                background=True
            )
            # Index for cleanup by date
            self.collection.create_index("last_updated", background=True)
            logger.info("Album cover cache indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def get(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Get cached album cover.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Cached data with image_data or None if not found
        """
        try:
            result = self.collection.find_one({
                "artist": artist.lower(),
                "title": title.lower()
            })

            if result:
                logger.debug(f"Cache hit for '{artist}' - '{title}'")
                return {
                    "image_data": result.get("image_data"),
                    "image_url": result.get("image_url"),
                    "source": result.get("source"),
                    "album_name": result.get("album_name"),
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "last_updated": result.get("last_updated")
                }

            logger.debug(f"Cache miss for '{artist}' - '{title}'")
            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None

    def set(
        self,
        artist: str,
        title: str,
        image_data: bytes,
        image_url: str,
        source: str,
        album_name: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> bool:
        """
        Cache album cover image.

        Args:
            artist: Artist name
            title: Song title
            image_data: Binary image data
            image_url: Original image URL
            source: Source of the image (spotify, itunes, etc.)
            album_name: Name of the album
            width: Image width
            height: Image height

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            self.collection.update_one(
                {
                    "artist": artist.lower(),
                    "title": title.lower()
                },
                {
                    "$set": {
                        "artist": artist.lower(),
                        "title": title.lower(),
                        "image_data": image_data,
                        "image_url": image_url,
                        "source": source,
                        "album_name": album_name,
                        "width": width,
                        "height": height,
                        "last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            logger.info(f"Cached album cover for '{artist}' - '{title}'")
            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    def delete(self, artist: str, title: str) -> bool:
        """
        Delete cached album cover.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({
                "artist": artist.lower(),
                "title": title.lower()
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False

    def clear(self) -> int:
        """
        Clear all cached album covers.

        Returns:
            Number of entries deleted
        """
        try:
            result = self.collection.delete_many({})
            logger.info(f"Cleared {result.deleted_count} cached album covers")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        try:
            count = self.collection.count_documents({})
            stats = self.db.command("collStats", "album_covers")
            return {
                "count": count,
                "size_bytes": stats.get("size", 0),
                "avg_obj_size": stats.get("avgObjSize", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"count": 0, "size_bytes": 0, "avg_obj_size": 0}


class AlbumCoverManager:
    """Manager for album cover fetching and caching."""

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        database_name: str = "metromatch",
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None
    ):
        """
        Initialize the album cover manager.

        Args:
            mongodb_uri: MongoDB connection string (optional)
            database_name: MongoDB database name
            spotify_client_id: Spotify API client ID (optional)
            spotify_client_secret: Spotify API client secret (optional)
        """
        # Initialize cache if MongoDB URI provided
        self.cache = None
        if mongodb_uri:
            try:
                self.cache = AlbumCoverCache(mongodb_uri, database_name)
            except Exception as e:
                logger.error(f"Failed to initialize album cover cache: {e}")

        # Initialize client
        self.client = AlbumCoverClient(spotify_client_id, spotify_client_secret)

    def get_album_cover(
        self,
        artist: str,
        title: str,
        skip_cache: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get album cover for a song.

        Checks cache first, then fetches from API if not found.

        Args:
            artist: Artist name
            title: Song title
            skip_cache: Skip cache lookup and fetch fresh

        Returns:
            Dict with image_data and metadata, or None if not found
        """
        # Check cache first
        if self.cache and not skip_cache:
            cached = self.cache.get(artist, title)
            if cached and cached.get("image_data"):
                return cached

        # Search for album cover
        result = self.client.search(artist, title)
        if not result:
            return None

        # Download the image
        image_data = self.client.download_image(result["image_url"])
        if not image_data:
            return None

        # Cache the result
        if self.cache:
            self.cache.set(
                artist=artist,
                title=title,
                image_data=image_data,
                image_url=result["image_url"],
                source=result["source"],
                album_name=result.get("album_name"),
                width=result.get("width"),
                height=result.get("height")
            )

        return {
            "image_data": image_data,
            "image_url": result["image_url"],
            "source": result["source"],
            "album_name": result.get("album_name"),
            "width": result.get("width"),
            "height": result.get("height")
        }

    def get_album_cover_url(self, artist: str, title: str) -> Optional[str]:
        """
        Get just the album cover URL (without downloading).

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Image URL or None if not found
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(artist, title)
            if cached and cached.get("image_url"):
                return cached["image_url"]

        # Search for album cover
        result = self.client.search(artist, title)
        if result:
            return result["image_url"]

        return None

    def prefetch(self, tracks: list) -> int:
        """
        Prefetch album covers for multiple tracks.

        Args:
            tracks: List of dicts with 'artist' and 'title' keys

        Returns:
            Number of successfully fetched covers
        """
        success_count = 0
        for track in tracks:
            artist = track.get("artist")
            title = track.get("title")

            if not artist or not title:
                continue

            result = self.get_album_cover(artist, title)
            if result:
                success_count += 1

        logger.info(f"Prefetched {success_count}/{len(tracks)} album covers")
        return success_count
