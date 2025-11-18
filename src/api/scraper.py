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
            # Use search directly - it's more reliable than guessing URLs
            # Search format: "artist title" (e.g., "the weeknd can't feel my face")
            return self._search_page(artist, title)

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
            logger.info(f"Scraper searching for: {artist} - {title}")
            print(f"[Scraper] Looking for: {artist} - {title}")

            # Strategy 1: Try Playwright UI search first (most reliable ~85-95% success)
            print(f"[Scraper] Trying Playwright UI search (most reliable)...")
            playwright_result = self._search_via_playwright(artist, title)
            if playwright_result:
                return playwright_result

            print(f"[Scraper] Playwright search failed, falling back to artist page browsing...")

            # Create artist slug
            artist_slug = artist.lower().replace(' ', '-')
            artist_slug = re.sub(r'[^a-z0-9-]', '', artist_slug)

            # Clean the title for matching
            clean_title = re.sub(r'\s*\(feat\.?[^)]+\)', '', title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s*\[feat\.?[^\]]+\]', '', clean_title, flags=re.IGNORECASE)
            title_words = clean_title.lower().split()

            # Strategy 2: Browse the artist page and find the song (~40-60% success)
            artist_url = f"{self.BASE_URL}/@{artist_slug}"
            print(f"[Scraper] Trying artist page: {artist_url}")

            response = self.session.get(artist_url, timeout=10)
            print(f"[Scraper] Artist page status: {response.status_code}")

            if response.status_code != 200:
                print(f"[Scraper] Artist page not found")
                return None

            response.raise_for_status()
            print(f"[Scraper] Response URL: {response.url}")
            print(f"[Scraper] Response status: {response.status_code}")

            # Debug: Show redirect history
            if response.history:
                print(f"[Scraper] Redirects: {[r.url for r in response.history]}")
            else:
                print(f"[Scraper] No redirects occurred")

            # Pagination loop - collect songs from multiple pages if needed
            all_links = []
            pages_checked = 0
            max_pages = 15  # Increased to handle artists with many songs (A-Z)
            current_url = artist_url

            while current_url and pages_checked < max_pages:
                pages_checked += 1
                response = self.session.get(current_url, timeout=10)

                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.content, 'html.parser')

                if pages_checked == 1:
                    # Debug info on first page only
                    page_title = soup.find('title')
                    all_page_links = soup.find_all('a', href=True)
                    print(f"[Scraper] Page title: {page_title.text if page_title else 'No title'}")
                    print(f"[Scraper] Total links on page: {len(all_page_links)}")

                # Find all potential song links on this page
                selectors = [
                    'a[href*="/@"]',  # Links containing /@artist/
                    'main a[href*="/@"]',
                ]

                print(f"[Scraper] Checking page {pages_checked}: {current_url}")

                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        # Only match song links (/@artist/song format, not just /@artist)
                        if isinstance(href, str) and href.startswith('/@') and href.count('/') >= 2:
                            # Verify the link contains the artist name
                            href_lower = href.lower()
                            if artist_slug in href_lower or artist.lower().replace(' ', '') in href_lower:
                                # Avoid duplicates
                                if link not in all_links:
                                    all_links.append(link)

                # Check if we found a match for the title on this page
                # Use strict matching: require the title slug to appear in the URL
                title_slug = clean_title.lower().replace(' ', '-')
                title_slug = re.sub(r'[^a-z0-9-]', '', title_slug)

                found_match = False
                for link in all_links:
                    href = link.get('href', '').lower()
                    # Check if the title slug (or most of it) appears in the URL
                    if title_slug in href:
                        found_match = True
                        print(f"[Scraper] Found exact match for '{title_slug}' in {href}")
                        break
                    # Also check if all significant words match at word boundaries
                    significant_words = [w for w in title_words if len(w) > 2]
                    if significant_words:
                        # Extract the song name part from the URL (after artist)
                        url_parts = href.split('/')
                        if len(url_parts) >= 3:
                            song_part = url_parts[-1]
                            word_matches = sum(1 for w in significant_words if f'-{w}-' in f'-{song_part}-')
                            if word_matches == len(significant_words):
                                found_match = True
                                print(f"[Scraper] Found word match for {title_words} in {href}")
                                break

                if found_match:
                    print(f"[Scraper] Found potential match, stopping pagination")
                    break

                # Find next page link
                next_link = soup.find('a', href=lambda h: bool(h and f'/@{artist_slug}?after=' in h))
                if next_link:
                    next_href = next_link.get('href', '')
                    current_url = f"{self.BASE_URL}{next_href}"
                else:
                    current_url = None

            print(f"[Scraper] Total matching links found: {len(all_links)} (checked {pages_checked} pages)")

            # Filter and prioritize results - match against title words
            result_link = None
            best_match_score = 0

            # Score each link based on title word matches
            for link in all_links:
                href = link.get('href', '').lower()

                # Skip instrumentals, remixes, covers
                if '-instrumental' in href:
                    continue
                if '-remix' in href:
                    continue
                if '-cover' in href:
                    continue

                # Calculate match score based on title words in href
                # Extract the song name part from the URL
                url_parts = href.split('/')
                song_part = url_parts[-1] if len(url_parts) >= 3 else href

                score = 0
                for word in title_words:
                    # Use word boundary matching (word surrounded by dashes or at start/end)
                    if len(word) > 2 and f'-{word}-' in f'-{song_part}-':
                        score += 1

                # Bonus for exact title slug match
                title_slug = clean_title.lower().replace(' ', '-')
                title_slug = re.sub(r'[^a-z0-9-]', '', title_slug)
                if title_slug in href:
                    score += len(title_words)  # Big bonus for exact match

                if score > best_match_score:
                    best_match_score = score
                    result_link = link
                    logger.debug(f"New best match (score {score}): {href}")
                    print(f"[Scraper] Best match so far (score {score}): {href}")

            # Fallback: use first non-instrumental result if no title match
            if not result_link and all_links:
                for link in all_links:
                    href = link.get('href', '').lower()
                    if '-instrumental' not in href and '-remix' not in href:
                        result_link = link
                        logger.debug(f"Using fallback result: {href}")
                        break
                if not result_link:
                    result_link = all_links[0]
                    logger.debug(f"Using first available result: {all_links[0].get('href')}")

            # If no good match found on artist page, try direct URL construction
            if not result_link or best_match_score == 0:
                # Construct song slug from title
                song_slug = clean_title.lower().replace(' ', '-')
                song_slug = re.sub(r'[^a-z0-9-]', '', song_slug)

                # Also try with featured artists if present
                # Pattern varies: "feat.-artist" or "feat--artist" (period or double dash)

                # Version with period: "feat.-duke-deuce"
                full_title_with_period = title.lower().replace(' ', '-')
                full_title_with_period = re.sub(r'\(feat\.?\s*', 'feat.-', full_title_with_period, flags=re.IGNORECASE)
                full_title_with_period = re.sub(r'\)', '', full_title_with_period)
                full_title_with_period = re.sub(r'[^a-z0-9.-]', '', full_title_with_period)
                full_title_with_period = re.sub(r'-+', '-', full_title_with_period)
                full_title_with_period = full_title_with_period.strip('-')

                # Version with double dash: "feat--duke-deuce"
                full_title_double_dash = title.lower().replace(' ', '-')
                full_title_double_dash = re.sub(r'-?\(feat\.?\s*', '-feat--', full_title_double_dash, flags=re.IGNORECASE)
                full_title_double_dash = re.sub(r'\)', '', full_title_double_dash)
                full_title_double_dash = re.sub(r'[^a-z0-9-]', '', full_title_double_dash)
                full_title_double_dash = re.sub(r'-+', '-', full_title_double_dash)  # Collapse multiple dashes except feat--
                full_title_double_dash = re.sub(r'feat-([^-])', r'feat--\1', full_title_double_dash)  # Ensure double dash after feat
                full_title_double_dash = full_title_double_dash.strip('-')

                # Version with single dash: "feat-kodak-black"
                full_title_single_dash = title.lower().replace(' ', '-')
                full_title_single_dash = re.sub(r'\(feat\.?\s*', 'feat-', full_title_single_dash, flags=re.IGNORECASE)
                full_title_single_dash = re.sub(r'\)', '', full_title_single_dash)
                full_title_single_dash = re.sub(r'[^a-z0-9-]', '', full_title_single_dash)
                full_title_single_dash = re.sub(r'-+', '-', full_title_single_dash)  # Collapse multiple dashes
                full_title_single_dash = full_title_single_dash.strip('-')

                # Try direct URLs with all patterns
                direct_urls = [
                    f"{self.BASE_URL}/@{artist_slug}/{full_title_with_period}",
                    f"{self.BASE_URL}/@{artist_slug}/{full_title_double_dash}",
                    f"{self.BASE_URL}/@{artist_slug}/{full_title_single_dash}",
                    f"{self.BASE_URL}/@{artist_slug}/{song_slug}",
                ]

                print(f"[Scraper] Trying URL patterns: period='{full_title_with_period}', double='{full_title_double_dash}', single='{full_title_single_dash}'")

                for direct_url in direct_urls:
                    print(f"[Scraper] Trying direct URL: {direct_url}")
                    try:
                        direct_response = self.session.get(direct_url, timeout=10)
                        if direct_response.status_code == 200:
                            print(f"[Scraper] Direct URL found!")
                            direct_soup = BeautifulSoup(direct_response.content, 'html.parser')
                            bpm = self._extract_bpm(direct_soup)
                            if bpm:
                                return {
                                    "bpm": bpm,
                                    "artist": artist,
                                    "title": title,
                                    "source": "songbpm_scraper",
                                    "url": direct_url
                                }
                    except Exception as e:
                        logger.debug(f"Direct URL failed: {e}")
                        continue

                # No match found - don't fall back to random song
                print(f"[Scraper] No match found for: {artist} - {title}")
                return None

            # Only use result_link if we have a good match
            if result_link and best_match_score > 0:
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

    def _search_via_playwright(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search using Playwright UI automation as final fallback.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Song data including BPM or None if not found
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed, skipping UI search fallback")
            print("[Scraper] Playwright not installed, skipping UI search")
            return None

        try:
            query = f"{artist} {title}"
            print(f"[Scraper] Playwright searching for: {query}")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to songbpm.com - use domcontentloaded instead of networkidle
                # networkidle times out on sites with continuous network activity
                page.goto("https://songbpm.com", wait_until="domcontentloaded", timeout=15000)

                # Wait for search box - uses name="query" and type="text"
                page.wait_for_selector("input[name='query']", timeout=5000)

                # Fill search box and submit
                page.fill("input[name='query']", query)
                page.keyboard.press("Enter")

                # Wait for results to load
                page.wait_for_selector("a[href^='/@']", timeout=5000)

                # Click first result
                first_result = page.query_selector("a[href^='/@']")
                if not first_result:
                    print("[Scraper] Playwright: No results found")
                    browser.close()
                    return None

                # Get the URL before clicking
                result_url = first_result.get_attribute("href")
                if result_url:
                    result_url = f"{self.BASE_URL}{result_url}"

                first_result.click()
                page.wait_for_timeout(2000)

                # Extract BPM from the page
                page_content = page.content()
                browser.close()

                # Parse the page content for BPM
                soup = BeautifulSoup(page_content, 'html.parser')
                bpm = self._extract_bpm(soup)

                if bpm:
                    print(f"[Scraper] Playwright found BPM: {bpm}")
                    return {
                        "bpm": bpm,
                        "artist": artist,
                        "title": title,
                        "source": "songbpm_playwright",
                        "url": result_url
                    }

                print("[Scraper] Playwright: Could not extract BPM from page")
                return None

        except Exception as e:
            logger.error(f"Playwright search failed: {e}")
            print(f"[Scraper] Playwright error: {e}")
            return None
