"""MetroMatch Configuration - Load settings from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GETSONGBPM_API_KEY = os.getenv('GETSONGBPM_API_KEY', '')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'metromatch')

# Application Settings
USE_SCRAPER = os.getenv('USE_SCRAPER', 'true').lower() == 'true'
AUTO_SYNC = os.getenv('AUTO_SYNC', 'false').lower() == 'true'
DEFAULT_BPM = int(os.getenv('DEFAULT_BPM', '120'))

# Rate Limiting
API_RATE_LIMIT = float(os.getenv('API_RATE_LIMIT', '0.5'))
SCRAPER_RATE_LIMIT = float(os.getenv('SCRAPER_RATE_LIMIT', '1.5'))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'metromatch.log')

# Metronome Settings
SOUND_BACKEND = os.getenv('SOUND_BACKEND', 'auto')