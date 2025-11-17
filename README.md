# BPM Metronome

Automatic BPM detection and metronome synchronization for any song.

## Features

- 🎵 Automatic song detection from playing media
- ⚡ Fast BPM lookup with intelligent caching
- 🔄 Multi-source fallback (API → Scraping)
- 📊 MongoDB for scalable caching
- 🎼 Real-time metronome synchronization

## Installation

1. Clone repository
2. Install dependencies:

```bash
   pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure
4. Run setup:

```bash
   python scripts/setup_db.py
```

## Usage

```python
from src.manager import BPMManager

manager = BPMManager()
result = manager.get_bpm("Michael Jackson", "Billie Jean")
print(f"BPM: {result['bpm']}")
```

## Credits

BPM data provided by [GetSongBPM.com](https://getsongbpm.com)

## License

MIT
