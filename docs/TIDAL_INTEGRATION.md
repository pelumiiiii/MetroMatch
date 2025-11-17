# Tidal Integration Guide

## Overview

Tidal does not provide native AppleScript/ScriptingBridge support like Spotify or Apple Music. To detect now playing information from Tidal, MetroMatch uses **window title monitoring** as a workaround.

## How It Works

### 1. Window Title Monitoring

When Tidal plays a song, it updates its window title to display the track information:

```
"Artist Name - Song Title - TIDAL"
```

MetroMatch monitors this window title using macOS Accessibility APIs to extract the artist and song information.

### 2. Technical Implementation

The implementation uses three macOS frameworks through PyObjC:

#### a) **NSWorkspace** (AppKit)
- Lists all running applications
- Finds Tidal by bundle identifier: `com.tidal.desktop`

#### b) **Accessibility API** (ApplicationServices)
- `AXUIElementCreateApplication(pid)` - Creates accessibility element for Tidal
- `AXUIElementCopyAttributeValue()` - Reads window attributes
- `kAXWindowsAttribute` - Gets list of windows
- `kAXTitleAttribute` - Reads window title

#### c) **Title Parsing**
- Extracts artist and song from format: `"Artist - Song - TIDAL"`
- Handles variations: `"Artist - Song"` (without app name)

## Code Flow

```python
1. _get_macos_track()
   ├─ Try AppleScript players (Spotify, Music, iTunes)
   └─ Fallback to _get_macos_now_playing_center()
      └─ Window title monitoring

2. _get_macos_now_playing_center()
   ├─ Get running apps via NSWorkspace
   ├─ Find Tidal (com.tidal.desktop)
   └─ Call _get_app_window_title()

3. _get_app_window_title(app, "TIDAL", parser)
   ├─ Create AX element for Tidal process
   ├─ Get window list (kAXWindowsAttribute)
   ├─ Get first window title (kAXTitleAttribute)
   └─ Parse with _parse_tidal_title()

4. _parse_tidal_title(title)
   ├─ Remove " - TIDAL" suffix
   ├─ Split on " - " to get [artist, song]
   └─ Return {artist, title, album: None, player: "TIDAL"}
```

## Requirements

### Python Dependencies
```bash
# Already included in requirements.txt
pip install pyobjc-framework-Cocoa
```

### macOS Permissions

**Accessibility Access Required**

Your app/terminal needs Accessibility permissions to read window titles:

1. Open **System Preferences** (or System Settings on macOS 13+)
2. Go to **Security & Privacy** → **Privacy** → **Accessibility**
3. Add your application:
   - **Terminal** (if running from terminal)
   - **VS Code** / **PyCharm** (if running from IDE)
   - Your app bundle (if packaged)

## Limitations

### 1. **Format Dependency**
- Only works if Tidal shows track info in window title
- Tidal must use `"Artist - Song"` format
- If Tidal changes format, parsing will break

### 2. **Window State**
- May not work if Tidal is minimized (depends on macOS version)
- Requires window to have focus or be visible
- Works best when Tidal is in foreground

### 3. **Accessibility Permissions**
- User must manually grant Accessibility access
- No way to programmatically request this
- App will fail silently without permission

### 4. **Performance**
- Accessing Accessibility API has slight overhead
- Not as efficient as native AppleScript
- Polling frequency should be limited (5-10 second intervals)

### 5. **No Playback State**
- Can't detect if track is paused/playing
- Only knows if window title contains track info
- No access to playback position, volume, etc.

## Testing

Run the test script to verify Tidal detection:

```bash
cd MetroMatch
python examples/test_tidal.py
```

Expected output if working:
```
✅ SUCCESS! Found playing track:

  Artist:  Daft Punk
  Title:   Get Lucky
  Album:   N/A
  Player:  TIDAL
  Source:  window_title
```

## Troubleshooting

### "No track found"

1. **Check Tidal is running and playing**
   ```bash
   # Verify Tidal is running
   osascript -e 'tell application "System Events" to get name of every process' | grep TIDAL
   ```

2. **Check window title format**
   ```bash
   # Get Tidal's current window title
   osascript -e 'tell application "System Events" to get name of window 1 of process "TIDAL"'
   ```
   Should return: `"Artist - Song - TIDAL"`

3. **Check Accessibility permissions**
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Verify Terminal/IDE is in the list with checkbox enabled

4. **Check bundle identifier**
   ```bash
   osascript -e 'tell application "System Events" to get bundle identifier of process "TIDAL"'
   ```
   Should return: `com.tidal.desktop`

### Import Errors

If you see `ImportError: No module named 'ApplicationServices'`:

```bash
# Install PyObjC frameworks
pip install pyobjc-framework-Cocoa
```

The `ApplicationServices` framework is included with `pyobjc-framework-Cocoa`.

## Alternative Approaches

If window title monitoring doesn't work for your use case:

### 1. **MediaRemote Framework (Private API)**
```objc
// Native approach using private APIs
#import <MediaRemote/MediaRemote.h>

MRMediaRemoteGetNowPlayingInfo(dispatch_get_main_queue(), ^(CFDictionaryRef information) {
    // Access track info
});
```
**Pros:** Works for all media apps including Tidal
**Cons:** Private API, not available in Python, could break

### 2. **Tidal Web API**
```python
# Use Tidal's official API
import requests

response = requests.get(
    "https://api.tidal.com/v1/sessions",
    headers={"Authorization": f"Bearer {token}"}
)
```
**Pros:** Official, reliable, full playback info
**Cons:** Requires OAuth, user authentication, internet connection

### 3. **Monitor Process Output**
Some apps log track info to stdout/system log.
**Pros:** No permissions needed
**Cons:** Unreliable, may not work with Tidal

## Adding Support for Other Apps

To add support for apps without AppleScript (like SoundCloud Desktop):

1. **Find bundle identifier**
   ```bash
   osascript -e 'tell application "System Events" to get bundle identifier of process "AppName"'
   ```

2. **Check window title format**
   ```bash
   osascript -e 'tell application "System Events" to get name of window 1 of process "AppName"'
   ```

3. **Add to `target_apps` list** in [now_playing.py:168](../src/detection/now_playing.py#L168):
   ```python
   target_apps = [
       ("com.tidal.desktop", "TIDAL", self._parse_tidal_title),
       ("com.soundcloud.desktop", "SoundCloud", self._parse_generic_title),
       ("your.bundle.id", "AppName", self._parse_generic_title),
   ]
   ```

4. **Create custom parser if needed** (if format differs from `"Artist - Song"`):
   ```python
   def _parse_custom_title(self, title: str, app_name: str) -> Optional[Dict[str, Any]]:
       # Custom parsing logic
       return {"artist": artist, "title": song, ...}
   ```

## References

- [macOS Accessibility API Documentation](https://developer.apple.com/documentation/applicationservices/axuielement)
- [PyObjC Documentation](https://pyobjc.readthedocs.io/)
- [NSWorkspace Reference](https://developer.apple.com/documentation/appkit/nsworkspace)
- [Tidal Desktop App](https://tidal.com/download)

## Summary

**Window title monitoring is a practical workaround** for apps like Tidal that don't support AppleScript:

✅ **Pros:**
- Works without API keys or authentication
- No private APIs (App Store safe)
- Simple implementation
- Extendable to other apps

❌ **Cons:**
- Requires Accessibility permissions
- Depends on window title format
- Limited to basic track info (no playback state)
- May not work when minimized

For production use, consider combining this with fallback strategies or encouraging users to use players with native AppleScript support (Spotify, Apple Music).
