"""Web scraper for SongBPM.com as fallback when API is unavailable."""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class SongBPMScraper:
    """Scraper for SongBPM.com website."""

    BASE_URL = "https://songbpm.com"

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def search(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for song BPM by artist and title.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Song data including BPM or None if not found
        """
        try:
            # Construct URL in format: https://songbpm.com/@artist/song-title
            artist_slug = artist.replace(" ", "-").lower()
            artist_slug = re.sub(r'[^a-z0-9-]', '', artist_slug)

            title_slug = title.replace(" ", "-").lower()
            title_slug = re.sub(r'[^a-z0-9-]', '', title_slug)

            # Try direct URL first with @ prefix for artist
            url = f"{self.BASE_URL}/@{artist_slug}/{title_slug}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 404:
                logger.debug(f"Direct URL not found, trying search")
                return self._search_page(artist, title)

            response.raise_for_status()

            # Parse the page
            soup = BeautifulSoup(response.content, 'html.parser')
            bpm = self._extract_bpm(soup)

            if bpm:
                logger.info(f"Scraped BPM for {artist} - {title}: {bpm}")
                return {
                    "bpm": bpm,
                    "artist": artist,
                    "title": title,
                    "source": "songbpm_scraper",
                    "url": url
                }

            logger.warning(f"Could not extract BPM from page: {url}")
            return None

        except requests.RequestException as e:
            logger.error(f"Scraping request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return None

    def _search_page(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search using the search page.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Song data including BPM or None if not found
        """
        try:
            params = {"q": f"{artist} {title}"}
            response = self.session.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try multiple selectors for search results
            selectors = [
                '.search-results a',
                'a[href*="/@"]',  # Links containing /@artist/
                '.result a',
                '.song-result a',
                'article a',
                'main a[href*="/@"]',
            ]

            # Find all potential song links
            all_links = []
            artist_slug = artist.lower().replace(' ', '-')
            artist_slug = re.sub(r'[^a-z0-9-]', '', artist_slug)

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    # Only match song links (/@artist/song format, not just /@artist)
                    if isinstance(href, str) and href.startswith('/@') and href.count('/') >= 2:
                        # Verify the link contains the artist name
                        href_lower = href.lower()
                        if artist_slug in href_lower or artist.lower().replace(' ', '') in href_lower:
                            all_links.append(link)
                        else:
                            logger.debug(f"Skipping unrelated link: {href}")

            # Filter and prioritize results - prefer non-instrumental versions
            result_link = None

            # First pass: find non-instrumental, non-remix version
            for link in all_links:
                href = link.get('href', '').lower()
                # Skip instrumentals, remixes, covers
                if '-instrumental' in href:
                    continue
                if '-remix' in href:
                    continue
                if '-cover' in href:
                    continue
                result_link = link
                logger.debug(f"Found original version: {href}")
                break

            # Fallback: use first result if no clean match
            if not result_link and all_links:
                result_link = all_links[0]
                logger.debug(f"Using first available result: {all_links[0].get('href')}")

            if result_link:
                href = result_link.get('href', '')
                if href.startswith('/@'):
                    song_url = self.BASE_URL + href
                else:
                    song_url = self.BASE_URL + href

                logger.debug(f"Fetching song page: {song_url}")
                response = self.session.get(song_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                bpm = self._extract_bpm(soup)

                if bpm:
                    return {
                        "bpm": bpm,
                        "artist": artist,
                        "title": title,
                        "source": "songbpm_scraper",
                        "url": song_url
                    }
            else:
                logger.debug(f"No search results found for: {artist} - {title}")

            return None

        except Exception as e:
            logger.error(f"Search page scraping failed: {e}")
            return None

    def _extract_bpm(self, soup: BeautifulSoup) -> Optional[float]:
        """
        Extract BPM from parsed HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            BPM value or None if not found
        """
        try:
            # Strategy 1: Look for BPM in the full page text
            text = soup.get_text()
            # Look for pattern like "116 BPM" (most common)
            matches = re.findall(r'(\d+(?:\.\d+)?)\s*BPM', text, re.I)
            if matches:
                # Return the most common BPM value (usually the second occurrence is the song BPM)
                bpm_values = [float(m) for m in matches]
                # Filter out unrealistic BPM values (typically 40-240)
                realistic_bpms = [bpm for bpm in bpm_values if 40 <= bpm <= 240]
                if realistic_bpms:
                    # Return the second value if available (first is often a category/genre BPM)
                    return realistic_bpms[1] if len(realistic_bpms) > 1 else realistic_bpms[0]

            # Strategy 2: Look for BPM in specific element with context
            bpm_elem = soup.find(string=re.compile(r'BPM', re.I))
            if bpm_elem:
                parent = bpm_elem.parent
                if parent:
                    # Try to find numeric value near BPM text
                    parent_text = parent.get_text()
                    match = re.search(r'(\d+(?:\.\d+)?)\s*BPM', parent_text, re.I)
                    if match:
                        bpm = float(match.group(1))
                        if 40 <= bpm <= 240:
                            return bpm

            # Strategy 3: Look for tempo data attributes
            tempo_elem = soup.select_one('[data-tempo], .tempo, #tempo')
            if tempo_elem:
                tempo_text = tempo_elem.get_text()
                match = re.search(r'(\d+(?:\.\d+)?)', tempo_text)
                if match:
                    bpm = float(match.group(1))
                    if 40 <= bpm <= 240:
                        return bpm

            return None

        except Exception as e:
            logger.error(f"Error extracting BPM: {e}")
            return None
