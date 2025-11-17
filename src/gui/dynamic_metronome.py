"""Dynamic Metronome GUI with advanced features."""

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
from typing import Optional
import pygame
import numpy as np


class DynamicMetronome:
    """Interactive metronome with BPM, volume, pitch, and advanced features."""

    def __init__(self, root: tk.Tk):
        """Initialize the Dynamic Metronome GUI.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("MetroMatch - Dynamic Metronome")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # Initialize pygame mixer for audio with smaller buffer for lower latency
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)

        # State variables
        self.is_playing = False
        self.current_beat = 0
        self.metronome_thread: Optional[threading.Thread] = None
        self.developer_mode = tk.BooleanVar(value=False)

        # Basic parameters
        self.bpm = tk.IntVar(value=120)
        self.volume = tk.IntVar(value=80)
        self.pitch = tk.IntVar(value=1000)  # Hz

        # Time signature
        self.time_sig_numerator = tk.IntVar(value=4)
        self.time_sig_denominator = tk.IntVar(value=4)

        # Advanced features (developer mode)
        self.dynamic_bpm_enabled = tk.BooleanVar(value=False)
        self.dynamic_bpm_min = tk.IntVar(value=100)  # Min BPM for random range
        self.dynamic_bpm_max = tk.IntVar(value=140)  # Max BPM for random range
        self.dynamic_bpm_interval = tk.IntVar(value=4)  # Beats between changes
        self.swing_enabled = tk.BooleanVar(value=False)
        self.swing_ratio = tk.IntVar(value=66)  # 66% = 2:1 swing ratio
        self.polyrhythm_enabled = tk.BooleanVar(value=False)
        self.polyrhythm_ratio = tk.StringVar(value="3:2")
        self.polyrhythm_beat_count = 0  # Track beats for polyrhythm

        # Pre-generate click sounds for better timing accuracy
        self.accent_sound = None
        self.normal_sound = None
        self._generate_click_sounds()

        # Build GUI
        self._build_gui()

        # Add callbacks to regenerate sounds when pitch or volume changes
        self.pitch.trace_add('write', lambda *_: self._generate_click_sounds())
        self.volume.trace_add('write', lambda *_: self._generate_click_sounds())

    def _build_gui(self):
        """Build the GUI interface."""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            title_frame,
            text="Dynamic Metronome",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack()

        # Main controls frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # BPM Control
        self._create_slider(
            main_frame, "BPM", self.bpm,
            from_=40, to=240, row=0
        )

        # Volume Control
        self._create_slider(
            main_frame, "Volume (%)", self.volume,
            from_=0, to=100, row=1
        )

        # Pitch Control
        self._create_slider(
            main_frame, "Pitch (Hz)", self.pitch,
            from_=200, to=2000, row=2
        )

        # Time Signature
        self._create_time_signature_control(main_frame, row=3)

        # Play/Stop Button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        self.play_button = ttk.Button(
            button_frame,
            text="▶ Start",
            command=self.toggle_playback,
            width=20
        )
        self.play_button.pack()

        # Beat indicator
        self.beat_label = ttk.Label(
            button_frame,
            text="Beat: -",
            font=("Helvetica", 16)
        )
        self.beat_label.pack(pady=10)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=20
        )

        # Developer Mode Toggle
        dev_frame = ttk.Frame(main_frame)
        dev_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.dev_mode_button = ttk.Checkbutton(
            dev_frame,
            text="🔧 Developer Mode",
            variable=self.developer_mode,
            command=self.toggle_developer_mode
        )
        self.dev_mode_button.pack()

        # Advanced Features Frame (hidden by default)
        self.advanced_frame = ttk.LabelFrame(
            main_frame,
            text="Advanced Features",
            padding="10"
        )

        # Dynamic BPM
        dynamic_bpm_frame = ttk.Frame(self.advanced_frame)
        dynamic_bpm_frame.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            dynamic_bpm_frame,
            text="Dynamic BPM",
            variable=self.dynamic_bpm_enabled
        ).pack(side=tk.LEFT)

        ttk.Label(dynamic_bpm_frame, text="  Range:").pack(side=tk.LEFT, padx=(10, 2))

        # Min BPM
        ttk.Spinbox(
            dynamic_bpm_frame,
            from_=40, to=240,
            textvariable=self.dynamic_bpm_min,
            width=5
        ).pack(side=tk.LEFT)
        ttk.Label(dynamic_bpm_frame, text="-").pack(side=tk.LEFT, padx=2)

        # Max BPM
        ttk.Spinbox(
            dynamic_bpm_frame,
            from_=40, to=240,
            textvariable=self.dynamic_bpm_max,
            width=5
        ).pack(side=tk.LEFT)
        ttk.Label(dynamic_bpm_frame, text="BPM").pack(side=tk.LEFT, padx=(2, 10))

        # Interval selector
        ttk.Label(dynamic_bpm_frame, text="Every:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Spinbox(
            dynamic_bpm_frame,
            from_=1, to=32,
            textvariable=self.dynamic_bpm_interval,
            width=4
        ).pack(side=tk.LEFT)
        ttk.Label(dynamic_bpm_frame, text="beats").pack(side=tk.LEFT)

        # Swing
        swing_frame = ttk.Frame(self.advanced_frame)
        swing_frame.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            swing_frame,
            text="Swing",
            variable=self.swing_enabled
        ).pack(side=tk.LEFT)

        ttk.Label(swing_frame, text="  Ratio:").pack(side=tk.LEFT)
        ttk.Scale(
            swing_frame,
            from_=50, to=75,
            variable=self.swing_ratio,
            orient=tk.HORIZONTAL,
            length=150
        ).pack(side=tk.LEFT, padx=5)

        self.swing_label = ttk.Label(swing_frame, text="66%")
        self.swing_label.pack(side=tk.LEFT)
        self.swing_ratio.trace_add('write', self._update_swing_label)

        # Polyrhythm
        poly_frame = ttk.Frame(self.advanced_frame)
        poly_frame.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            poly_frame,
            text="Polyrhythm",
            variable=self.polyrhythm_enabled
        ).pack(side=tk.LEFT)

        ttk.Label(poly_frame, text="  Ratio:").pack(side=tk.LEFT)
        poly_combo = ttk.Combobox(
            poly_frame,
            textvariable=self.polyrhythm_ratio,
            values=["3:2", "4:3", "5:4", "7:4", "5:3"],
            width=8,
            state="readonly"
        )
        poly_combo.pack(side=tk.LEFT, padx=5)

    def _create_slider(self, parent, label, variable, from_, to, row):
        """Create a labeled slider control.

        Args:
            parent: Parent widget
            label: Label text
            variable: Tkinter variable
            from_: Minimum value
            to: Maximum value
            row: Grid row
        """
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=10)

        slider = ttk.Scale(
            parent,
            from_=from_, to=to,
            variable=variable,
            orient=tk.HORIZONTAL,
            length=300
        )
        slider.grid(row=row, column=1, padx=10)

        value_label = ttk.Label(parent, text=str(variable.get()))
        value_label.grid(row=row, column=2, sticky="w")

        # Update label when slider changes
        def update_label(*args):
            value_label.config(text=str(variable.get()))
        variable.trace_add('write', update_label)

    def _create_time_signature_control(self, parent, row):
        """Create time signature selector.

        Args:
            parent: Parent widget
            row: Grid row
        """
        ttk.Label(parent, text="Time Signature").grid(
            row=row, column=0, sticky="w", pady=10
        )

        sig_frame = ttk.Frame(parent)
        sig_frame.grid(row=row, column=1, padx=10)

        # Numerator (1-7)
        numerator_combo = ttk.Combobox(
            sig_frame,
            textvariable=self.time_sig_numerator,
            values=[str(i) for i in range(1, 8)],
            width=3,
            state="readonly"
        )
        numerator_combo.pack(side=tk.LEFT)

        ttk.Label(sig_frame, text=" / ").pack(side=tk.LEFT)

        # Denominator (4 or 8)
        denominator_combo = ttk.Combobox(
            sig_frame,
            textvariable=self.time_sig_denominator,
            values=["4", "8"],
            width=3,
            state="readonly"
        )
        denominator_combo.pack(side=tk.LEFT)

    def _generate_click_sounds(self):
        """Pre-generate accent and normal click sounds for better timing."""
        sample_rate = 44100
        duration = 0.1
        samples = int(sample_rate * duration)

        # Get current pitch and volume settings
        base_pitch = self.pitch.get()  # Hz from slider
        base_volume = self.volume.get() / 100.0  # Convert percentage to 0-1

        def create_click(pitch_multiplier, volume_multiplier):
            """Create a single click sound."""
            frequency = base_pitch * pitch_multiplier
            volume = min(base_volume * volume_multiplier, 1.0)

            buf = []
            for i in range(samples):
                t = i / sample_rate
                envelope = 1.0 - (t / duration)
                value = volume * envelope * math.sin(2 * math.pi * frequency * t)
                sample = int(np.clip(value * 32767, -32768, 32767))
                buf.append(sample)

            stereo_buf = np.array([[s, s] for s in buf], dtype=np.int16)
            return pygame.sndarray.make_sound(stereo_buf)

        # Pre-generate both sounds
        self.accent_sound = create_click(1.2, 1.3)  # Higher pitch, louder
        self.normal_sound = create_click(1.0, 1.0)  # Normal

    def toggle_developer_mode(self):
        """Toggle developer mode visibility."""
        if self.developer_mode.get():
            self.advanced_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)
        else:
            self.advanced_frame.grid_forget()

    def _update_swing_label(self, *args):
        """Update swing ratio label."""
        self.swing_label.config(text=f"{self.swing_ratio.get()}%")

    def toggle_playback(self):
        """Start or stop the metronome."""
        if self.is_playing:
            self.stop()
        else:
            self.start()

    def start(self):
        """Start the metronome."""
        if not self.is_playing:
            self.is_playing = True
            self.current_beat = 0
            self.polyrhythm_beat_count = 0
            self.play_button.config(text="⏸ Stop")

            # Start metronome thread
            self.metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
            self.metronome_thread.start()

    def stop(self):
        """Stop the metronome."""
        self.is_playing = False
        self.play_button.config(text="▶ Start")
        self.beat_label.config(text="Beat: -")

    def _metronome_loop(self):
        """Main metronome loop with precise timing."""
        next_beat_time = time.perf_counter()
        next_poly_time = time.perf_counter()
        total_beats = 0  # Track total beats for dynamic BPM interval
        current_dynamic_bpm = self.bpm.get()  # Store current random BPM

        while self.is_playing:
            # Precise sleep until next beat FIRST
            sleep_time = next_beat_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're running behind, skip this beat timing compensation
                pass

            # Store current beat for UI update before any changes
            current_beat_for_ui = self.current_beat

            # Play pre-generated sound at exact beat time
            if self.current_beat == 0 and self.accent_sound:
                self.accent_sound.play()
            elif self.normal_sound:
                self.normal_sound.play()

            # Check if polyrhythm should play on this beat
            if self.polyrhythm_enabled.get():
                poly_now = time.perf_counter()
                if poly_now >= next_poly_time:
                    # Play polyrhythm accent sound
                    if self.accent_sound:
                        self.accent_sound.play()
                    # Calculate next polyrhythm beat
                    ratio_parts = self.polyrhythm_ratio.get().split(':')
                    poly_beats = int(ratio_parts[1])  # Denominator
                    base_beats = int(ratio_parts[0])  # Numerator
                    bpm = current_dynamic_bpm if self.dynamic_bpm_enabled.get() else self.bpm.get()
                    poly_interval = (60.0 / bpm) * (base_beats / poly_beats)
                    next_poly_time += poly_interval

            # Increment to next beat BEFORE UI update
            self.current_beat = (self.current_beat + 1) % self.time_sig_numerator.get()
            total_beats += 1

            # Update UI with the beat we just played (thread-safe via after_idle)
            self.root.after_idle(lambda beat=current_beat_for_ui: self._update_beat_indicator(beat))

            # Get current parameters for next beat
            bpm = self.bpm.get()

            # Apply dynamic BPM if enabled
            if self.dynamic_bpm_enabled.get():
                import random
                # Check if it's time to change BPM based on interval
                interval = self.dynamic_bpm_interval.get()
                if total_beats % interval == 0:
                    # Pick new random BPM in range
                    min_bpm = self.dynamic_bpm_min.get()
                    max_bpm = self.dynamic_bpm_max.get()
                    current_dynamic_bpm = random.randint(min_bpm, max_bpm)
                bpm = current_dynamic_bpm

            # Calculate beat interval
            beat_interval = 60.0 / bpm

            # Apply swing if enabled (check NEXT beat)
            if self.swing_enabled.get() and self.current_beat % 2 == 1:
                swing_ratio = self.swing_ratio.get() / 100.0
                beat_interval *= (2 - swing_ratio)

            # Calculate when next beat should happen
            next_beat_time += beat_interval

            # Initialize polyrhythm timing on first beat
            if total_beats == 1 and self.polyrhythm_enabled.get():
                ratio_parts = self.polyrhythm_ratio.get().split(':')
                poly_beats = int(ratio_parts[1])
                base_beats = int(ratio_parts[0])
                poly_interval = (60.0 / bpm) * (base_beats / poly_beats)
                next_poly_time = next_beat_time + poly_interval

    def _update_beat_indicator(self, beat=None):
        """Update the beat indicator label.

        Args:
            beat: The beat number to display (0-indexed). If None, uses self.current_beat
        """
        if beat is None:
            beat = self.current_beat

        beat_num = beat + 1
        total_beats = self.time_sig_numerator.get()

        # Visual beat indicator
        beats_display = ""
        for i in range(1, total_beats + 1):
            if i == beat_num:
                beats_display += "● "
            else:
                beats_display += "○ "

        self.beat_label.config(
            text=f"Beat: {beat_num}/{total_beats}\n{beats_display.strip()}"
        )


def main():
    """Launch the Dynamic Metronome application."""
    root = tk.Tk()
    app = DynamicMetronome(root)
    root.mainloop()


if __name__ == "__main__":
    main()
