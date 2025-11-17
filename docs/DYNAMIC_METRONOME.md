# Dynamic Metronome

An advanced, standalone metronome application with customizable controls and developer features.

## Features

### Basic Controls

- **BPM Slider** (40-240 BPM): Adjust the tempo of the metronome
- **Volume Control** (0-100%): Set the playback volume
- **Pitch Control** (200-2000 Hz): Customize the click sound frequency
- **Time Signature** (1/4 to 7/8): Set the rhythmic pattern

### Visual Feedback

- **Beat Indicator**: Shows current beat position with visual circles
- **Beat Counter**: Displays "Beat: 1/4", "Beat: 2/4", etc.
- **Visual Accent**: First beat is highlighted

### Developer Mode 🔧

Advanced features for musicians and producers:

#### 1. **Dynamic BPM**
- ✅ Enable checkbox
- Randomly varies tempo within a specified range
- Useful for: Practicing tempo flexibility, humanizing recordings
- **Variance control**: ±1 to ±50 BPM

**Example**: Set BPM to 120 with ±10 variance → metronome randomly plays between 110-130 BPM

#### 2. **Swing**
- ✅ Enable checkbox
- Adds rhythmic "swing" feel by delaying off-beats
- **Ratio slider**: 50%-75%
  - 50% = No swing (straight eighth notes)
  - 66% = Classic swing (2:1 ratio)
  - 75% = Heavy swing

**Example**: Jazz drummers use 66% swing for authentic feel

#### 3. **Polyrhythm**
- ✅ Enable checkbox
- Plays two rhythms simultaneously
- **Ratio selector**: 3:2, 4:3, 5:4, 7:4, 5:3

**Example**: 3:2 polyrhythm = 3 beats in the time of 2 beats

## Installation

No additional dependencies beyond the main MetroMatch requirements.

## Usage

### Launch the Application

```bash
# From MetroMatch directory
python dynamic_metronome_app.py
```

Or import in your code:

```python
import tkinter as tk
from src.gui.dynamic_metronome import DynamicMetronome

root = tk.Tk()
app = DynamicMetronome(root)
root.mainloop()
```

### Quick Start

1. **Start the app**: Run `python dynamic_metronome_app.py`
2. **Adjust BPM**: Slide the BPM control to your desired tempo
3. **Click "▶ Start"**: Metronome begins playing
4. **Enable Developer Mode**: Check "🔧 Developer Mode" for advanced features

## Controls Reference

### Basic Mode

| Control | Range | Default | Description |
|---------|-------|---------|-------------|
| BPM | 40-240 | 120 | Beats per minute |
| Volume | 0-100% | 80% | Playback volume |
| Pitch | 200-2000 Hz | 1000 Hz | Click sound frequency |
| Time Signature | 1/4 - 7/8 | 4/4 | Rhythmic pattern |

### Developer Mode

| Feature | Control | Description |
|---------|---------|-------------|
| Dynamic BPM | ±1-50 BPM | Random tempo variation |
| Swing | 50-75% | Off-beat delay ratio |
| Polyrhythm | 3:2, 4:3, 5:4, 7:4, 5:3 | Dual rhythm patterns |

## Use Cases

### For Practice
- **Tempo Training**: Use Dynamic BPM to practice staying on beat with varying tempos
- **Jazz/Blues**: Enable Swing at 66% for authentic feel
- **Complex Rhythms**: Use Polyrhythm for advanced rhythm training

### For Recording
- **Humanization**: Record with Dynamic BPM for more natural feel
- **Guide Tracks**: Set time signature and BPM for recording sessions

### For Teaching
- **Rhythm Exercises**: Demonstrate different time signatures
- **Polyrhythm Training**: Teach complex rhythmic concepts

## Technical Details

### Audio Generation

The metronome generates audio programmatically using:
- **Sine wave synthesis** for pure tone clicks
- **Envelope shaping** for natural attack/decay
- **Accent beats** (first beat is louder and higher pitch)
- **Real-time generation** (no pre-recorded samples)

### Threading

- Uses separate thread for metronome timing
- Non-blocking UI updates
- Precise timing with `time.sleep()` adjustment

### Architecture

```
DynamicMetronome (GUI)
    ├── Basic Controls (always visible)
    │   ├── BPM Slider
    │   ├── Volume Slider
    │   ├── Pitch Slider
    │   └── Time Signature Selector
    │
    ├── Playback Control
    │   ├── Start/Stop Button
    │   └── Beat Indicator
    │
    └── Developer Mode (toggle visibility)
        ├── Dynamic BPM
        ├── Swing
        └── Polyrhythm
```

## Keyboard Shortcuts

*Coming soon*

## Standalone vs Integrated

### Standalone (Current)
- **Launch**: `python dynamic_metronome_app.py`
- **Use case**: General metronome practice
- **Features**: All basic + developer features

### Integration with BPM Manager (Future)
- Could be integrated to auto-sync with now-playing detection
- BPM slider could auto-update based on detected song

## Troubleshooting

### No Sound
- Check system volume
- Ensure pygame mixer is initialized
- Try adjusting Volume slider

### Timing Issues
- Close other audio applications
- Reduce buffer size in `pygame.mixer.init()`

### GUI Not Appearing
- Check tkinter installation: `python -c "import tkinter"`
- Ensure X server is running (if on Linux/SSH)

## Future Enhancements

- [ ] Save/Load presets
- [ ] MIDI sync support
- [ ] Tap tempo
- [ ] Visual metronome (flashing light)
- [ ] Subdivisions (eighth notes, sixteenth notes)
- [ ] Custom sounds (load audio files)
- [ ] Keyboard shortcuts
- [ ] Recording/playback of rhythm patterns

## Credits

Part of the **MetroMatch** project - BPM detection and metronome synchronization.

## License

Same as MetroMatch project.
