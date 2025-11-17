"""Metronome player implementation."""

import time
import threading
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class MetronomePlayer:
    """Metronome player that plays clicks at a specified BPM."""

    def __init__(self, sound_backend: str = "auto"):
        """
        Initialize the metronome player.

        Args:
            sound_backend: Sound backend to use ('auto', 'pygame', 'pyaudio', 'simpleaudio')
        """
        self.bpm = 120
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.sound_backend = sound_backend
        self._init_sound_backend()

        # Callbacks
        self.on_beat: Optional[Callable] = None

    def _init_sound_backend(self):
        """Initialize the sound backend."""
        if self.sound_backend == "auto":
            # Try backends in order of preference
            backends = ["pygame", "simpleaudio", "pyaudio"]
            for backend in backends:
                try:
                    if backend == "pygame":
                        import pygame
                        pygame.mixer.init()
                        self.sound_backend = "pygame"
                        logger.info("Using pygame sound backend")
                        return
                    elif backend == "simpleaudio":
                        import simpleaudio
                        self.sound_backend = "simpleaudio"
                        logger.info("Using simpleaudio sound backend")
                        return
                    elif backend == "pyaudio":
                        import pyaudio
                        self.sound_backend = "pyaudio"
                        logger.info("Using pyaudio sound backend")
                        return
                except ImportError:
                    continue

            logger.warning("No sound backend available, using silent mode")
            self.sound_backend = "none"

    def set_bpm(self, bpm: float):
        """
        Set the metronome BPM.

        Args:
            bpm: Beats per minute
        """
        if bpm <= 0:
            raise ValueError("BPM must be positive")

        old_bpm = self.bpm
        self.bpm = bpm
        logger.info(f"BPM changed from {old_bpm} to {bpm}")

    def start(self):
        """Start the metronome."""
        if self.is_running:
            logger.warning("Metronome is already running")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()
        logger.info(f"Metronome started at {self.bpm} BPM")

    def stop(self):
        """Stop the metronome."""
        if not self.is_running:
            logger.warning("Metronome is not running")
            return

        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Metronome stopped")

    def _play_loop(self):
        """Main metronome loop."""
        beat_count = 0

        while self.is_running:
            start_time = time.time()

            # Play click
            self._play_click(beat_count)

            # Call callback if set
            if self.on_beat:
                try:
                    self.on_beat(beat_count, self.bpm)
                except Exception as e:
                    logger.error(f"Error in on_beat callback: {e}")

            beat_count += 1

            # Calculate sleep time
            interval = 60.0 / self.bpm
            elapsed = time.time() - start_time
            sleep_time = interval - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                logger.warning(f"Metronome running behind by {-sleep_time:.3f}s")

    def _play_click(self, beat_count: int):
        """
        Play a click sound.

        Args:
            beat_count: Current beat number (0-indexed)
        """
        # Emphasize first beat of each measure (every 4 beats)
        is_downbeat = beat_count % 4 == 0

        if self.sound_backend == "pygame":
            self._play_click_pygame(is_downbeat)
        elif self.sound_backend == "simpleaudio":
            self._play_click_simpleaudio(is_downbeat)
        elif self.sound_backend == "pyaudio":
            self._play_click_pyaudio(is_downbeat)
        else:
            # Silent mode - just log
            logger.debug(f"Beat {beat_count} ({'DOWN' if is_downbeat else 'up'})")

    def _play_click_pygame(self, is_downbeat: bool):
        """Play click using pygame."""
        try:
            import pygame
            import numpy as np

            # Generate click sound
            sample_rate = 44100
            duration = 0.05  # 50ms click
            frequency = 1000 if is_downbeat else 800

            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t)
            wave = (wave * 32767).astype(np.int16)

            # Create stereo sound
            stereo_wave = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.play()

        except Exception as e:
            logger.error(f"Error playing click with pygame: {e}")

    def _play_click_simpleaudio(self, is_downbeat: bool):
        """Play click using simpleaudio."""
        try:
            import simpleaudio as sa
            import numpy as np

            sample_rate = 44100
            duration = 0.05
            frequency = 1000 if is_downbeat else 800

            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t)
            wave = (wave * 32767).astype(np.int16)

            play_obj = sa.play_buffer(wave, 1, 2, sample_rate)

        except Exception as e:
            logger.error(f"Error playing click with simpleaudio: {e}")

    def _play_click_pyaudio(self, is_downbeat: bool):
        """Play click using pyaudio."""
        try:
            import pyaudio
            import numpy as np

            sample_rate = 44100
            duration = 0.05
            frequency = 1000 if is_downbeat else 800

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paFloat32,
                          channels=1,
                          rate=sample_rate,
                          output=True)

            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)

            stream.write(wave.tobytes())
            stream.stop_stream()
            stream.close()
            p.terminate()

        except Exception as e:
            logger.error(f"Error playing click with pyaudio: {e}")
