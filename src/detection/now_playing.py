"""Now playing detection using system media session APIs."""

import platform
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NowPlayingDetector:
    """Detector for currently playing music across different platforms."""

    def __init__(self):
        """Initialize the detector based on current platform."""
        self.platform = platform.system()
        logger.info(f"Initializing NowPlayingDetector for {self.platform}")

        if self.platform == "Darwin":  # macOS
            self._init_macos()
        elif self.platform == "Windows":
            self._init_windows()
        elif self.platform == "Linux":
            self._init_linux()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")

    def _init_macos(self):
        """Initialize macOS-specific detection using ScriptingBridge."""
        try:
            # Try to import macOS-specific modules
            # ScriptingBridge is used in _get_macos_track()
            import ScriptingBridge  # noqa: F401
            self.has_media_support = True
            logger.info("macOS media detection initialized (ScriptingBridge)")
        except ImportError as e:
            logger.warning(f"macOS media detection not available: {e}")
            logger.info("Install with: pip install pyobjc-framework-ScriptingBridge")
            self.has_media_support = False

    def _init_windows(self):
        """Initialize Windows-specific detection using Windows.Media API."""
        try:
            # Try to import Windows-specific modules
            import winrt.windows.media.control as media_control # type: ignore
            self.has_media_support = True
            logger.info("Windows media detection initialized")
        except ImportError:
            logger.warning("Windows media detection not available (winrt not installed)")
            self.has_media_support = False

    def _init_linux(self):
        """Initialize Linux-specific detection using MPRIS."""
        try:
            import dbus # type: ignore
            self.has_media_support = True
            logger.info("Linux media detection initialized (MPRIS)")
        except ImportError:
            logger.warning("Linux media detection not available (dbus not installed)")
            self.has_media_support = False

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track information.

        Returns:
            Dictionary with artist, title, and album information or None
        """
        if not self.has_media_support:
            logger.warning("Media detection not supported on this system")
            return None

        if self.platform == "Darwin":
            return self._get_macos_track()
        elif self.platform == "Windows":
            return self._get_windows_track()
        elif self.platform == "Linux":
            return self._get_linux_track()

        return None

    def _get_macos_track(self) -> Optional[Dict[str, Any]]:
        """Get currently playing track on macOS using ScriptingBridge."""
        try:
            from ScriptingBridge import SBApplication # type: ignore

            # Try common music players with their bundle identifiers
            # Note: Only players with AppleScript/ScriptingBridge support will work
            # Tidal does not have native AppleScript support (has scripting terminology: false)
            # For Tidal, use macOS Media Remote API or Now Playing Center instead
            players = [
                ("Music", "com.apple.Music"),
                ("Spotify", "com.spotify.client"),
                ("iTunes", "com.apple.iTunes"),
                # ("Tidal", "com.tidal.desktop"),  # Disabled - no AppleScript support
            ]

            # First try AppleScript-capable players
            for player_name, bundle_id in players:
                try:
                    player = SBApplication.applicationWithBundleIdentifier_(bundle_id)

                    # Check if player is running
                    if not player or not player.isRunning():
                        continue

                    # Get current track
                    track = player.currentTrack()
                    if not track:
                        continue

                    # Safely extract track information with proper None checks
                    artist = track.artist() if hasattr(track, 'artist') else None
                    title = track.name() if hasattr(track, 'name') else None
                    album = track.album() if hasattr(track, 'album') else None

                    # Ensure we have at least artist and title
                    if artist and title:
                        logger.info(f"Found track from {player_name}: {artist} - {title}")
                        return {
                            "artist": str(artist),
                            "title": str(title),
                            "album": str(album) if album else None,
                            "player": player_name
                        }

                except Exception as e:
                    logger.debug(f"Could not get track from {player_name}: {e}")
                    continue

            # If no track found from AppleScript players, try window title monitoring
            # This catches TIDAL and other apps without AppleScript support
            logger.debug("No track from AppleScript players, checking window title monitoring")
            try:
                track_info = self._get_macos_now_playing_center()
                if track_info:
                    return track_info
            except Exception as e:
                logger.debug(f"Could not get track from Now Playing Center: {e}")

            return None

        except ImportError as e:
            logger.error(f"ScriptingBridge not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting macOS track: {e}")
            return None

    def _get_macos_now_playing_center(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track from apps without AppleScript support.
        This monitors window titles for apps like Tidal.

        How it works:
        1. Gets all running applications using NSWorkspace
        2. Looks for target apps (Tidal, etc.) by bundle ID
        3. Reads the window title which often contains: "Artist - Song - App"
        4. Parses the title to extract artist and song info

        Limitations:
        - Only works if app shows track info in window title
        - Parsing format may vary between apps
        - May not work if window is minimized or app is in background
        """
        try:
            from AppKit import NSWorkspace  # type: ignore

            workspace = NSWorkspace.sharedWorkspace()

            # Apps to check (bundle ID, name, title parsing pattern)
            target_apps = [
                ("com.tidal.desktop", "TIDAL", self._parse_tidal_title),
                ("com.soundcloud.desktop", "SoundCloud", self._parse_generic_title),
            ]

            for bundle_id, app_name, parser in target_apps:
                try:
                    # Get all running applications
                    running_apps = workspace.runningApplications()

                    for app in running_apps:
                        if app.bundleIdentifier() == bundle_id:
                            # Try to get window title using accessibility API
                            track_info = self._get_app_window_title(app, app_name, parser)
                            if track_info:
                                return track_info

                except Exception as e:
                    logger.debug(f"Could not check {app_name}: {e}")
                    continue

            return None

        except ImportError:
            logger.debug("AppKit not available for window title monitoring")
            return None
        except Exception as e:
            logger.debug(f"Error in window title monitoring: {e}")
            return None

    def _get_app_window_title(self, app, app_name: str, parser) -> Optional[Dict[str, Any]]:
        """
        Get window title from an NSRunningApplication using AppleScript.

        This uses osascript which doesn't require PyObjC Accessibility frameworks.
        For apps like Tidal that only show windows when active, this activates them first.

        Args:
            app: NSRunningApplication instance (not used, kept for compatibility)
            app_name: Name of the application
            parser: Function to parse the window title

        Returns:
            Track info dict or None
        """
        import subprocess
        
        try:

            # First, check if the app has windows - if not, activate it
            # This is needed for apps like Tidal that hide windows when in background
            check_script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    if exists then
                        return count of windows
                    end if
                end tell
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', check_script],
                capture_output=True,
                text=True,
                timeout=2
            )

            window_count = 0
            if result.returncode == 0 and result.stdout.strip().isdigit():
                window_count = int(result.stdout.strip())

            # If no windows, activate the app to make window visible
            if window_count == 0:
                logger.debug(f"{app_name} has no visible windows, activating...")
                activate_script = f'tell application "{app_name}" to activate'
                subprocess.run(
                    ['osascript', '-e', activate_script],
                    capture_output=True,
                    timeout=1
                )
                # Give it a moment to show the window
                import time
                time.sleep(0.3)

            # Now get the window title
            get_title_script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    if exists then
                        try
                            return name of window 1
                        end try
                    end if
                end tell
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', get_title_script],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and result.stdout:
                title = result.stdout.strip()
                if title:
                    # Parse the title using the provided parser
                    track_info = parser(title, app_name)
                    if track_info:
                        logger.info(f"Found track from {app_name} window title: {title}")
                        return track_info

            return None

        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout getting window title for {app_name}")
            return None
        except Exception as e:
            logger.debug(f"Error getting window title for {app_name}: {e}")
            return None

    def _parse_tidal_title(self, title: str, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse Tidal window title.

        Tidal formats observed:
        - "Song Title - Artist Name(s)" (most common)
        - "Song Title - Artist1, Artist2, Artist3"
        - "Artist - Song Title - TIDAL" (older format)

        Args:
            title: Window title string
            app_name: Name of the app (for metadata)

        Returns:
            Track info dict or None
        """
        if not title or title == "TIDAL" or title == app_name:
            return None

        # Remove trailing " - TIDAL" or " - Tidal" if present
        title = title.replace(" - TIDAL", "").replace(" - Tidal", "").strip()

        # Split on " - " to get parts
        parts = title.split(" - ", 1)

        if len(parts) >= 2:
            # Tidal shows: "Song - Artist(s)"
            # So parts[0] is song, parts[1] is artist(s)
            song = parts[0].strip()
            artist = parts[1].strip()

            # Extract only the first artist if multiple are listed
            if ',' in artist:
                artist = artist.split(',')[0].strip()

            if artist and song:
                return {
                    "artist": artist,
                    "title": song,
                    "album": '-',
                    "player": app_name,
                }

        return None

    def _parse_generic_title(self, title: str, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Generic parser for "Artist - Song" format.

        Args:
            title: Window title string
            app_name: Name of the app

        Returns:
            Track info dict or None
        """
        if not title or title == app_name:
            return None

        # Remove app name from end if present
        title = title.replace(f" - {app_name}", "").strip()

        # Split on " - "
        parts = title.split(" - ", 1)

        if len(parts) >= 2:
            artist = parts[0].strip()
            song = parts[1].strip()

            if artist and song:
                return {
                    "artist": artist,
                    "title": song,
                    "album": '-',
                    "player": app_name,
                }

        return None

    def _get_windows_track(self) -> Optional[Dict[str, Any]]:
        """Get currently playing track on Windows."""
        try:
            import asyncio
            from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager  # type: ignore

            async def get_media_info():
                sessions = await MediaManager.request_async()
                current_session = sessions.get_current_session()

                if current_session:
                    info = await current_session.try_get_media_properties_async()
                    return {
                        "artist": info.artist,
                        "title": info.title,
                        "album": info.album_title,
                        "player": current_session.source_app_user_model_id
                    }
                return None

            return asyncio.run(get_media_info())

        except Exception as e:
            logger.error(f"Error getting Windows track: {e}")
            return None

    def _get_linux_track(self) -> Optional[Dict[str, Any]]:
        """Get currently playing track on Linux using MPRIS."""
        try:
            import dbus  # type: ignore

            bus = dbus.SessionBus()

            # Get list of MPRIS players
            players = [name for name in bus.list_names()
                      if name.startswith('org.mpris.MediaPlayer2.')]

            for player_name in players:
                try:
                    player = bus.get_object(player_name, '/org/mpris/MediaPlayer2')
                    interface = dbus.Interface(
                        player,
                        dbus_interface='org.freedesktop.DBus.Properties'
                    )
                    metadata = interface.Get(
                        'org.mpris.MediaPlayer2.Player',
                        'Metadata'
                    )

                    if metadata:
                        artists = metadata.get('xesam:artist', [])
                        return {
                            "artist": artists[0] if artists else "Unknown",
                            "title": metadata.get('xesam:title', "Unknown"),
                            "album": metadata.get('xesam:album'),
                            "player": player_name.split('.')[-1]
                        }
                except Exception as e:
                    logger.debug(f"Could not get track from {player_name}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error getting Linux track: {e}")
            return None

    def is_playing(self) -> bool:
        """
        Check if any media is currently playing.

        Returns:
            True if media is playing, False otherwise
        """
        track = self.get_current_track()
        return track is not None
