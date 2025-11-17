"""Local BPM detection from audio files (optional feature)."""

import librosa
import numpy as np
from typing import Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalBPMDetector:
    """Detector for BPM from local audio files."""

    def __init__(self):
        """Initialize the local BPM detector."""
        self.supported_formats = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']

    def detect_bpm(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect BPM from a local audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary with BPM and confidence or None if detection fails
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"Unsupported format: {path.suffix}")
                return None

            logger.info(f"Analyzing {file_path}...")

            # Load audio file
            y, sr = librosa.load(file_path, sr=None, duration=120)  # Analyze first 2 minutes

            # Detect tempo
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

            # Calculate confidence based on beat strength
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            beat_strength = np.mean(onset_env[beats]) if len(beats) > 0 else 0
            confidence = min(beat_strength / 10.0, 1.0)  # Normalize to 0-1

            logger.info(f"Detected BPM: {tempo:.2f} (confidence: {confidence:.2f})")

            return {
                "bpm": float(tempo),
                "confidence": float(confidence),
                "beats_detected": len(beats),
                "source": "local_detection",
                "file": str(path)
            }

        except Exception as e:
            logger.error(f"Error detecting BPM from file: {e}")
            return None

    def detect_bpm_advanced(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Advanced BPM detection with multiple analysis methods.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary with BPM estimates from different methods
        """
        try:
            y, sr = librosa.load(file_path, sr=None, duration=120)

            # Method 1: Standard beat tracking
            tempo1, _ = librosa.beat.beat_track(y=y, sr=sr)

            # Method 2: Tempogram-based analysis
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
            tempo2 = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]

            # Method 3: Autocorrelation
            ac = librosa.autocorrelate(onset_env)
            tempo3 = 60.0 * sr / (np.argmax(ac[sr // 60:]) + sr // 60)

            # Average the estimates
            bpm_estimates = [tempo1, tempo2, tempo3]
            avg_bpm = np.mean(bpm_estimates)
            std_bpm = np.std(bpm_estimates)

            # Confidence based on agreement between methods
            confidence = 1.0 - min(std_bpm / avg_bpm, 1.0)

            logger.info(f"Advanced BPM detection: {avg_bpm:.2f} ± {std_bpm:.2f}")

            return {
                "bpm": float(avg_bpm),
                "bpm_estimates": [float(t) for t in bpm_estimates],
                "standard_deviation": float(std_bpm),
                "confidence": float(confidence),
                "source": "local_detection_advanced",
                "file": file_path
            }

        except Exception as e:
            logger.error(f"Error in advanced BPM detection: {e}")
            return None

    def analyze_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Analyze all audio files in a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            Dictionary mapping file names to BPM data
        """
        results = {}
        folder = Path(folder_path)

        if not folder.is_dir():
            logger.error(f"Not a directory: {folder_path}")
            return results

        audio_files = []
        for ext in self.supported_formats:
            audio_files.extend(folder.glob(f"*{ext}"))

        logger.info(f"Found {len(audio_files)} audio files to analyze")

        for file_path in audio_files:
            logger.info(f"Processing {file_path.name}...")
            result = self.detect_bpm(str(file_path))
            if result:
                results[file_path.name] = result

        return results
