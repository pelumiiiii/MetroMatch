# MetroMatch Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip or conda package manager
- MongoDB (for caching - optional but recommended)

## Installation Options

### Option 1: Minimal Installation (Recommended for getting started)

Install only the essential dependencies:

```bash
pip install -r requirements-minimal.txt
```

This includes:
- MongoDB driver (pymongo)
- HTTP requests and web scraping (requests, beautifulsoup4)
- Metronome audio backend (pygame)
- Environment variables support (python-dotenv)

### Option 2: Full Installation

Install all dependencies including optional features:

```bash
pip install -r requirements.txt
```

### Option 3: Conda Environment (Recommended)

Create and activate a conda environment:

```bash
# Create environment
conda create -n metromatch python=3.12

# Activate environment
conda activate metromatch

# Install dependencies
pip install -r requirements-minimal.txt

# Or for full installation
pip install -r requirements.txt
```

## Platform-Specific Setup

### macOS - Now Playing Detection

For detecting currently playing music from Spotify, Apple Music, etc.:

```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-ScriptingBridge
```

### Windows - Now Playing Detection

For detecting currently playing music:

```bash
pip install winrt
```

### Linux - Now Playing Detection

For MPRIS support (Spotify, VLC, etc.):

```bash
pip install dbus-python
```

## Optional Features

### Local BPM Detection

To detect BPM from local audio files:

```bash
pip install librosa soundfile numpy scipy audioread
```

⚠️ **Note**: These packages are large (~500MB) and may take time to install.

### Alternative Audio Backends

Instead of pygame, you can use:

```bash
# Lightweight alternative
pip install simpleaudio

# Or more control
pip install PyAudio
```

## Verify Installation

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_manager.py -v
```

Test imports:

```bash
python -c "from src.manager import BPMManager; print('✅ Installation successful!')"
```

## Setup MongoDB (Optional)

### Local MongoDB

1. Install MongoDB Community Edition from https://www.mongodb.com/try/download/community

2. Start MongoDB:
   ```bash
   # macOS (with Homebrew)
   brew services start mongodb-community

   # Linux
   sudo systemctl start mongod

   # Windows
   net start MongoDB
   ```

3. Initialize the database:
   ```bash
   python scripts/setup_db.py
   ```

### MongoDB Atlas (Cloud)

1. Create a free cluster at https://www.mongodb.com/cloud/atlas
2. Get your connection string
3. Add to `.env` file:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/metromatch
   ```

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   MONGODB_URI=mongodb://localhost:27017
   GETSONGBPM_API_KEY=your_api_key_here
   ```

3. Get a GetSongBPM API key (free) at: https://getsongbpm.com/api

## Running Examples

Try the example scripts:

```bash
# Basic usage
python examples/basic_usage.py

# With now playing detection
python examples/with_now_playing.py

# Batch processing
python examples/batch_processing.py
```

## Troubleshooting

### Import Errors

If you see import errors, make sure you're in the project root directory and the conda environment is activated:

```bash
cd /path/to/MetroMatch
conda activate metromatch
```

### Audio Not Working

If the metronome doesn't play sound:

1. Try a different audio backend in your code:
   ```python
   from src.metronome.player import MetronomePlayer
   player = MetronomePlayer(sound_backend="pygame")  # or "simpleaudio", "pyaudio"
   ```

2. Check your system audio settings

### MongoDB Connection Issues

If MongoDB connection fails:

1. Check MongoDB is running: `mongosh` (or `mongo`)
2. Verify connection string in `.env`
3. For MongoDB Atlas, ensure your IP is whitelisted

## Development Setup

For development with code quality tools:

```bash
pip install -r requirements-dev.txt
```

This includes:
- pytest, pytest-cov, pytest-mock (testing)
- black (code formatting)
- flake8, pylint (linting)
- mypy (type checking)

## Next Steps

- Read the [README.md](README.md) for usage examples
- Explore the [examples/](examples/) directory
- Run [scripts/seed_data.py](scripts/seed_data.py) to add sample BPM data
- Check out the [tests/](tests/) directory for more examples
