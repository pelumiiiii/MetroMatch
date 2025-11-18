"""MetroMatch Main Application with hamburger menu navigation."""

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
from typing import Optional
import pygame
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.manager import BPMManager
from src.detection.now_playing import NowPlayingDetector
from config.settings import MONGODB_URI, GETSONGBPM_API_KEY


class MetroMatchApp:
    """Main MetroMatch application with hamburger menu navigation."""

    def __init__(self, root: tk.Tk):
        """Initialize the main application.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("MetroMatch")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)

        # Configure dark theme colors
        self.colors = {
            'bg': '#0d0d0d',
            'bg_secondary': '#1a1a1a',
            'bg_tertiary': '#252525',
            'accent': '#1DB954',  # Spotify green
            'text': '#ffffff',
            'text_secondary': '#b3b3b3',
            'border': '#333333',
            'menu_bg': '#1a1a1aee'  # Semi-transparent
        }

        self.root.configure(bg=self.colors['bg'])

        # Initialize pygame mixer for audio
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)

        # Current view
        self.current_view = None
        self.menu_visible = False

        # Initialize managers (lazy load)
        self.bpm_manager = None
        self.now_playing_detector = None

        # Metronome state
        self.is_playing = False
        self.metronome_thread = None
        self.current_beat = 0

        # Build UI
        self._configure_styles()
        self._build_navigation()
        self._build_content_area()

        # Show default view
        self._show_metronome_view()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self):
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure common styles
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('DarkSecondary.TFrame', background=self.colors['bg_secondary'])

        style.configure('Dark.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'])

        style.configure('DarkSecondary.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text'])

        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('Helvetica', 24, 'bold'))

        style.configure('Subtitle.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text_secondary'],
                       font=('Helvetica', 12))

        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text'])

        style.configure('Dark.TCheckbutton',
                       background=self.colors['bg'],
                       foreground=self.colors['text'])

        style.configure('Dark.TScale',
                       background=self.colors['bg'])

    def _build_navigation(self):
        """Build the floating hamburger menu."""
        # Floating hamburger menu button (positioned above slider)
        self.menu_button = tk.Button(
            self.root,
            text="☰",
            font=('Helvetica', 18),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text'],
            activebackground=self.colors['bg_tertiary'],
            activeforeground=self.colors['accent'],
            bd=0,
            padx=10,
            pady=6,
            cursor='hand2',
            command=self._toggle_menu
        )
        # Place floating button above the slider area
        self.menu_button.place(x=10, y=5)
        self.menu_button.lift()

        # Hidden view label (for internal tracking)
        self.view_label = tk.Label(self.root, text="", bg=self.colors['bg'])

        # Dropdown menu (hidden by default, floating)
        self.dropdown = tk.Frame(self.root, bg=self.colors['bg_secondary'], bd=0)

        # Menu items (no header)
        menu_items = [
            ("Metronome", self._show_metronome_view),
            ("Song Matcher", self._show_matcher_view),
        ]

        for text, command in menu_items:
            item = tk.Button(
                self.dropdown,
                text=text,
                font=('Helvetica', 13),
                bg=self.colors['bg_secondary'],
                fg=self.colors['text'],
                activebackground=self.colors['accent'],
                activeforeground=self.colors['text'],
                bd=0,
                pady=15,
                padx=20,
                anchor='w',
                cursor='hand2',
                command=lambda cmd=command: self._select_menu_item(cmd)
            )
            item.pack(fill=tk.X)

            # Hover effect
            item.bind('<Enter>', lambda e, w=item: w.configure(bg=self.colors['bg_tertiary']))
            item.bind('<Leave>', lambda e, w=item: w.configure(bg=self.colors['bg_secondary']))

    def _build_content_area(self):
        """Build the main content area."""
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Ensure hamburger stays on top
        self.menu_button.lift()

    def _toggle_menu(self):
        """Toggle the dropdown menu visibility."""
        if self.menu_visible:
            self.dropdown.place_forget()
            self.menu_visible = False
        else:
            # Position dropdown below the hamburger button
            self.dropdown.place(x=10, y=40, width=180)
            self.dropdown.lift()
            self.menu_visible = True

    def _select_menu_item(self, command):
        """Handle menu item selection.

        Args:
            command: Function to call for this menu item
        """
        self._toggle_menu()
        command()

    def _clear_content(self):
        """Clear the content area."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Keep hamburger menu on top
        self.menu_button.lift()

    def _show_metronome_view(self):
        """Show the Dynamic Metronome view."""
        self._clear_content()
        self.view_label.config(text="Metronome")
        self.current_view = 'metronome'

        # Stop any running metronome
        self.is_playing = False

        # Main container - centered content
        container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Top section - BPM Slider (full width)
        slider_frame = tk.Frame(container, bg=self.colors['bg'])
        slider_frame.pack(fill=tk.X, pady=(10, 15))

        self.bpm_var = tk.IntVar(value=120)
        self.volume_var = tk.IntVar(value=80)
        self.pitch_var = tk.IntVar(value=1000)

        # Slider track background
        track_bg = tk.Canvas(
            slider_frame,
            height=6,
            bg=self.colors['border'],
            highlightthickness=0
        )
        track_bg.pack(fill=tk.X, padx=20)

        # BPM Slider
        self.bpm_slider = ttk.Scale(
            slider_frame,
            from_=40,
            to=240,
            variable=self.bpm_var,
            orient=tk.HORIZONTAL
        )
        self.bpm_slider.pack(fill=tk.X, padx=20, pady=(3, 0))

        # Center section - Large circular BPM display
        center_frame = tk.Frame(container, bg=self.colors['bg'])
        center_frame.pack(fill=tk.BOTH, expand=True)

        # Circular BPM dial (scaled for smaller window)
        self.dial_canvas = tk.Canvas(
            center_frame,
            width=180,
            height=180,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.dial_canvas.pack(pady=10)
        self._draw_bpm_dial()

        # BPM label below dial
        self.bpm_display_label = tk.Label(
            center_frame,
            text="BPM",
            font=('Helvetica', 14),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.bpm_display_label.pack()

        # Update dial when BPM changes
        self.bpm_var.trace_add('write', lambda *_: self._draw_bpm_dial())

        # Time signature variable
        self.time_sig_num = tk.IntVar(value=4)
        self.time_sig_den = tk.IntVar(value=4)

        # Time Signature on left
        sig_label = tk.Label(
            container,
            text="4/4",
            font=('Helvetica', 20, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        sig_label.pack(anchor='w', padx=20, pady=(10, 5))

        # Update time signature display
        def update_sig(*_):
            sig_label.config(text=f"{self.time_sig_num.get()}/{self.time_sig_den.get()}")
        self.time_sig_num.trace_add('write', update_sig)
        self.time_sig_den.trace_add('write', update_sig)

        # Play/Pause controls - centered
        play_frame = tk.Frame(container, bg=self.colors['bg'])
        play_frame.pack(pady=5)

        self.play_button = tk.Button(
            play_frame,
            text="▷",
            font=('Helvetica', 28),
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            activebackground=self.colors['bg'],
            activeforeground='#1ed760',
            bd=0,
            padx=15,
            cursor='hand2',
            command=self._toggle_metronome
        )
        self.play_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(
            play_frame,
            text="▢",
            font=('Helvetica', 24),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['text'],
            bd=0,
            padx=15,
            cursor='hand2',
            command=self._stop_metronome
        )
        self.stop_button.pack(side=tk.LEFT)

        # Beat indicator dots
        self.beat_canvas = tk.Canvas(
            container,
            width=200,
            height=30,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.beat_canvas.pack(pady=10)
        self._draw_beat_indicators(0)

        # Developer Options section
        dev_frame = tk.Frame(container, bg=self.colors['bg'])
        dev_frame.pack(fill=tk.X, pady=(20, 0))

        self.dev_expanded = tk.BooleanVar(value=False)

        dev_toggle = tk.Button(
            dev_frame,
            text="▼ Developer Options",
            font=('Helvetica', 11),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['text'],
            bd=0,
            cursor='hand2',
            command=self._toggle_dev_options
        )
        dev_toggle.pack(anchor='w')

        # Developer options content (hidden by default)
        self.dev_content = tk.Frame(container, bg=self.colors['bg_secondary'], padx=15, pady=15)

        # Volume slider
        vol_frame = tk.Frame(self.dev_content, bg=self.colors['bg_secondary'])
        vol_frame.pack(fill=tk.X, pady=5)
        tk.Label(vol_frame, text="Volume", font=('Helvetica', 10), bg=self.colors['bg_secondary'], fg=self.colors['text']).pack(side=tk.LEFT)
        ttk.Scale(vol_frame, from_=0, to=100, variable=self.volume_var, orient=tk.HORIZONTAL, length=150).pack(side=tk.RIGHT)

        # Pitch slider
        pitch_frame = tk.Frame(self.dev_content, bg=self.colors['bg_secondary'])
        pitch_frame.pack(fill=tk.X, pady=5)
        tk.Label(pitch_frame, text="Pitch", font=('Helvetica', 10), bg=self.colors['bg_secondary'], fg=self.colors['text']).pack(side=tk.LEFT)
        ttk.Scale(pitch_frame, from_=200, to=2000, variable=self.pitch_var, orient=tk.HORIZONTAL, length=150).pack(side=tk.RIGHT)

        # Time sig controls (order: denominator, /, numerator when packing RIGHT)
        ts_frame = tk.Frame(self.dev_content, bg=self.colors['bg_secondary'])
        ts_frame.pack(fill=tk.X, pady=5)
        tk.Label(ts_frame, text="Time Sig", font=('Helvetica', 10), bg=self.colors['bg_secondary'], fg=self.colors['text']).pack(side=tk.LEFT)
        ttk.Combobox(ts_frame, values=['4', '8'], width=3, textvariable=self.time_sig_den, state='readonly').pack(side=tk.RIGHT, padx=2)
        tk.Label(ts_frame, text="/", bg=self.colors['bg_secondary'], fg=self.colors['text']).pack(side=tk.RIGHT)
        ttk.Spinbox(ts_frame, from_=1, to=7, width=3, textvariable=self.time_sig_num).pack(side=tk.RIGHT, padx=2)

        # Generate initial sounds
        self._generate_click_sounds()

        # Update sounds when parameters change
        self.pitch_var.trace_add('write', lambda *_: self._generate_click_sounds())
        self.volume_var.trace_add('write', lambda *_: self._generate_click_sounds())

    def _draw_bpm_dial(self):
        """Draw the circular BPM dial."""
        self.dial_canvas.delete('all')

        cx, cy = 90, 90
        radius = 70

        # Draw outer circle
        self.dial_canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            outline=self.colors['border'],
            width=3
        )

        # Draw inner circle
        inner_radius = radius - 10
        self.dial_canvas.create_oval(
            cx - inner_radius, cy - inner_radius,
            cx + inner_radius, cy + inner_radius,
            outline=self.colors['bg_tertiary'],
            width=1
        )

        # Draw diagonal lines (vinyl effect)
        bpm = self.bpm_var.get() if hasattr(self, 'bpm_var') else 120
        for i in range(12):
            angle = (i * 30 + bpm) * math.pi / 180
            x1 = cx + (radius - 25) * math.cos(angle)
            y1 = cy + (radius - 25) * math.sin(angle)
            x2 = cx + (radius - 8) * math.cos(angle)
            y2 = cy + (radius - 8) * math.sin(angle)
            self.dial_canvas.create_line(
                x1, y1, x2, y2,
                fill=self.colors['accent'],
                width=2
            )

        # Draw BPM number in center
        self.dial_canvas.create_text(
            cx, cy,
            text=str(bpm),
            font=('Helvetica', 28, 'bold'),
            fill=self.colors['text']
        )

    def _toggle_dev_options(self):
        """Toggle developer options visibility."""
        if self.dev_expanded.get():
            self.dev_content.pack_forget()
            self.dev_expanded.set(False)
        else:
            self.dev_content.pack(fill=tk.X, pady=10)
            self.dev_expanded.set(True)

    def _stop_metronome(self):
        """Stop the metronome."""
        self.is_playing = False
        self.play_button.config(text="▷", fg=self.colors['accent'])
        self._draw_beat_indicators(0)

    def _create_slider(self, parent, label, variable, from_, to):
        """Create a labeled slider control.

        Args:
            parent: Parent widget
            label: Label text
            variable: Tkinter variable
            from_: Minimum value
            to: Maximum value
        """
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=8)

        tk.Label(
            frame,
            text=label,
            font=('Helvetica', 12),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)

        slider = ttk.Scale(
            frame,
            from_=from_,
            to=to,
            variable=variable,
            orient=tk.HORIZONTAL,
            length=350
        )
        slider.pack(side=tk.LEFT, padx=10)

        value_label = tk.Label(
            frame,
            text=str(variable.get()),
            font=('Helvetica', 12),
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            width=6
        )
        value_label.pack(side=tk.LEFT)

        # Update label when slider changes
        def update(*_):
            value_label.config(text=str(variable.get()))
        variable.trace_add('write', update)

    def _generate_click_sounds(self):
        """Generate metronome click sounds."""
        if not hasattr(self, 'pitch_var'):
            return

        sample_rate = 44100
        duration = 0.1
        samples = int(sample_rate * duration)

        base_pitch = self.pitch_var.get()
        base_volume = self.volume_var.get() / 100.0

        def create_click(pitch_mult, vol_mult):
            freq = base_pitch * pitch_mult
            vol = min(base_volume * vol_mult, 1.0)

            buf = []
            for i in range(samples):
                t = i / sample_rate
                envelope = 1.0 - (t / duration)
                value = vol * envelope * math.sin(2 * math.pi * freq * t)
                sample = int(np.clip(value * 32767, -32768, 32767))
                buf.append(sample)

            stereo_buf = np.array([[s, s] for s in buf], dtype=np.int16)
            return pygame.sndarray.make_sound(stereo_buf)

        self.accent_sound = create_click(1.2, 1.3)
        self.normal_sound = create_click(1.0, 1.0)

    def _toggle_metronome(self):
        """Start or stop the metronome."""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▷", fg=self.colors['accent'])
            self._draw_beat_indicators(0)
        else:
            self.is_playing = True
            self.current_beat = 0
            self.play_button.config(text="⏸", fg=self.colors['accent'])
            self.metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
            self.metronome_thread.start()

    def _metronome_loop(self):
        """Main metronome timing loop."""
        next_beat = time.perf_counter()

        while self.is_playing:
            sleep_time = next_beat - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)

            current = self.current_beat

            # Play sound
            if current == 0 and hasattr(self, 'accent_sound'):
                self.accent_sound.play()
            elif hasattr(self, 'normal_sound'):
                self.normal_sound.play()

            # Update beat
            self.current_beat = (self.current_beat + 1) % self.time_sig_num.get()

            # Update UI
            self.root.after_idle(lambda b=current: self._update_beat_display(b))

            # Calculate next beat
            bpm = self.bpm_var.get()
            next_beat += 60.0 / bpm

    def _update_beat_display(self, beat):
        """Update the beat display.

        Args:
            beat: Current beat number (0-indexed)
        """
        self._draw_beat_indicators(beat)

    def _draw_beat_indicators(self, current_beat):
        """Draw beat indicator circles.

        Args:
            current_beat: Current beat number (0-indexed)
        """
        if not hasattr(self, 'beat_canvas'):
            return

        self.beat_canvas.delete('all')
        total = self.time_sig_num.get() if hasattr(self, 'time_sig_num') else 4

        spacing = 200 / (total + 1)
        for i in range(total):
            x = spacing * (i + 1)
            y = 15

            if i == current_beat:
                color = self.colors['accent']
                size = 10
            else:
                color = self.colors['text_secondary']
                size = 6

            self.beat_canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=''
            )

    def _show_matcher_view(self):
        """Show the Song Matcher view."""
        self._clear_content()
        self.view_label.config(text="Song Matcher")
        self.current_view = 'matcher'

        # Stop metronome if running
        self.is_playing = False

        # Main container
        container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        # Top section - Album art and info
        top_section = tk.Frame(container, bg=self.colors['bg'])
        top_section.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Album art on left
        self.album_frame = tk.Frame(top_section, bg=self.colors['bg_secondary'], width=200, height=200)
        self.album_frame.pack(side=tk.LEFT, padx=(0, 20))
        self.album_frame.pack_propagate(False)

        # Album art canvas for drawing placeholder
        self.album_canvas = tk.Canvas(
            self.album_frame,
            width=200,
            height=200,
            bg=self.colors['bg_secondary'],
            highlightthickness=0
        )
        self.album_canvas.pack(fill=tk.BOTH, expand=True)
        self._draw_album_placeholder()

        # Right side - Song info and tabs
        right_section = tk.Frame(top_section, bg=self.colors['bg'])
        right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Artist name
        self.artist_label = tk.Label(
            right_section,
            text="No song playing",
            font=('Helvetica', 18, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            anchor='w'
        )
        self.artist_label.pack(fill=tk.X, pady=(0, 5))

        # Song title
        self.song_title_label = tk.Label(
            right_section,
            text="Play music to detect",
            font=('Helvetica', 11),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.song_title_label.pack(fill=tk.X, pady=(0, 15))

        # Tab buttons: Info | Lyrics | Beats
        tab_frame = tk.Frame(right_section, bg=self.colors['bg'])
        tab_frame.pack(fill=tk.X, pady=8)

        self.current_tab = tk.StringVar(value='beats')

        tabs = [('Info', 'info'), ('Lyrics', 'lyrics'), ('Beats', 'beats')]
        for text, value in tabs:
            btn = tk.Button(
                tab_frame,
                text=text,
                font=('Helvetica', 10),
                bg=self.colors['bg_secondary'] if value != 'beats' else self.colors['accent'],
                fg=self.colors['text'],
                activebackground=self.colors['accent'],
                activeforeground=self.colors['text'],
                bd=1,
                relief='solid',
                padx=12,
                pady=6,
                cursor='hand2',
                command=lambda v=value: self._select_tab(v)
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            if value == 'beats':
                self.beats_tab_btn = btn
            elif value == 'info':
                self.info_tab_btn = btn
            elif value == 'lyrics':
                self.lyrics_tab_btn = btn

        # Tab content area
        self.tab_content = tk.Frame(right_section, bg=self.colors['bg'])
        self.tab_content.pack(fill=tk.BOTH, expand=True, pady=10)

        # Show default tab (beats)
        self._show_beats_tab()

        # Bottom section - Media controls and progress
        bottom_section = tk.Frame(container, bg=self.colors['bg'])
        bottom_section.pack(fill=tk.X, side=tk.BOTTOM, padx=30, pady=15)

        # Progress bar
        self.progress_canvas = tk.Canvas(
            bottom_section,
            height=4,
            bg=self.colors['border'],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 10))
        self._draw_progress(0)

        # Media controls
        controls_frame = tk.Frame(bottom_section, bg=self.colors['bg'])
        controls_frame.pack()

        # Previous button
        prev_btn = tk.Button(
            controls_frame,
            text="⏮",
            font=('Helvetica', 18),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['text'],
            bd=0,
            padx=12,
            cursor='hand2'
        )
        prev_btn.pack(side=tk.LEFT)

        # Detect/Play button (main action)
        self.detect_button = tk.Button(
            controls_frame,
            text="●",
            font=('Helvetica', 24),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            activebackground='#1ed760',
            activeforeground=self.colors['text'],
            bd=0,
            padx=18,
            pady=5,
            cursor='hand2',
            command=self._detect_now_playing
        )
        self.detect_button.pack(side=tk.LEFT, padx=10)

        # Next button
        next_btn = tk.Button(
            controls_frame,
            text="⏭",
            font=('Helvetica', 18),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['text'],
            bd=0,
            padx=12,
            cursor='hand2'
        )
        next_btn.pack(side=tk.LEFT)

        # Status label
        self.status_label = tk.Label(
            bottom_section,
            text="Press detect to find now playing",
            font=('Helvetica', 10),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(pady=(8, 0))

        # Store detected BPM
        self.detected_bpm = None

    def _draw_album_placeholder(self):
        """Draw placeholder album art."""
        self.album_canvas.delete('all')

        # Draw diagonal lines pattern (like the wireframe) - scaled for 200x200
        for i in range(0, 220, 10):
            self.album_canvas.create_line(
                0, i, i, 0,
                fill=self.colors['border'],
                width=1
            )
            self.album_canvas.create_line(
                200 - i, 200, 200, 200 - i,
                fill=self.colors['border'],
                width=1
            )

        # Draw silhouette placeholder (scaled for 200x200)
        self.album_canvas.create_oval(
            60, 40, 140, 130,
            fill=self.colors['bg'],
            outline=''
        )
        self.album_canvas.create_oval(
            70, 110, 130, 180,
            fill=self.colors['bg'],
            outline=''
        )

    def _draw_progress(self, progress):
        """Draw progress bar.

        Args:
            progress: Progress value 0-1
        """
        self.progress_canvas.delete('all')
        width = self.progress_canvas.winfo_width() or 400

        # Draw progress
        if progress > 0:
            self.progress_canvas.create_rectangle(
                0, 0, width * progress, 4,
                fill=self.colors['accent'],
                outline=''
            )

        # Draw handle
        handle_x = width * progress
        self.progress_canvas.create_oval(
            handle_x - 6, -3, handle_x + 6, 7,
            fill=self.colors['accent'],
            outline=''
        )

    def _select_tab(self, tab_name):
        """Select a tab.

        Args:
            tab_name: Name of tab to select
        """
        self.current_tab.set(tab_name)

        # Update button styles
        for btn, name in [(self.info_tab_btn, 'info'), (self.lyrics_tab_btn, 'lyrics'), (self.beats_tab_btn, 'beats')]:
            if name == tab_name:
                btn.config(bg=self.colors['accent'])
            else:
                btn.config(bg=self.colors['bg_secondary'])

        # Show tab content
        for widget in self.tab_content.winfo_children():
            widget.destroy()

        if tab_name == 'beats':
            self._show_beats_tab()
        elif tab_name == 'info':
            self._show_info_tab()
        elif tab_name == 'lyrics':
            self._show_lyrics_tab()

    def _show_beats_tab(self):
        """Show the beats/BPM tab content."""
        # BPM Display (scaled for smaller window)
        self.bpm_display = tk.Label(
            self.tab_content,
            text="---",
            font=('Helvetica', 36, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        self.bpm_display.pack(pady=10)

        tk.Label(
            self.tab_content,
            text="BPM",
            font=('Helvetica', 11),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        ).pack()

        self.bpm_source_label = tk.Label(
            self.tab_content,
            text="",
            font=('Helvetica', 9),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.bpm_source_label.pack(pady=(5, 10))

        # Sync button
        self.sync_button = tk.Button(
            self.tab_content,
            text="Sync to Metronome",
            font=('Helvetica', 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text'],
            activebackground=self.colors['accent'],
            activeforeground=self.colors['text'],
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._sync_to_metronome,
            state=tk.DISABLED
        )
        self.sync_button.pack()

    def _show_info_tab(self):
        """Show the info tab content."""
        self.player_label = tk.Label(
            self.tab_content,
            text="Player: --",
            font=('Helvetica', 10),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.player_label.pack(anchor='w', pady=5)

        tk.Label(
            self.tab_content,
            text="Source: Spotify, Apple Music, TIDAL",
            font=('Helvetica', 10),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        ).pack(anchor='w', pady=5)

    def _show_lyrics_tab(self):
        """Show the lyrics tab content."""
        tk.Label(
            self.tab_content,
            text="Lyrics not available",
            font=('Helvetica', 10),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        ).pack(pady=15)

    def _detect_now_playing(self):
        """Detect the currently playing song and find its BPM."""
        self.status_label.config(text="Detecting...", fg=self.colors['text_secondary'])
        self.detect_button.config(state=tk.DISABLED)

        # Run detection in background thread
        thread = threading.Thread(target=self._do_detection, daemon=True)
        thread.start()

    def _safe_widget_update(self, widget_name, config_func):
        """Safely update a widget that may have been destroyed.

        Args:
            widget_name: Name of the widget attribute
            config_func: Function to call for configuration
        """
        def do_update():
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                try:
                    if widget.winfo_exists():
                        config_func(widget)
                except Exception:
                    pass  # Widget was destroyed
        self.root.after(0, do_update)

    def _do_detection(self):
        """Perform the actual detection (runs in background thread)."""
        try:
            # Initialize detector if needed
            if not self.now_playing_detector:
                try:
                    self.now_playing_detector = NowPlayingDetector()
                except Exception as init_err:
                    self.root.after(0, lambda e=str(init_err): self.status_label.config(
                        text=f"Init error: {e}", fg='#ff6b6b'
                    ))
                    self.root.after(0, lambda: self.detect_button.config(state=tk.NORMAL))
                    return

            # Detect now playing
            track = self.now_playing_detector.get_current_track()

            if track:
                artist = track.get('artist', 'Unknown')
                title = track.get('title', 'Unknown')
                player = track.get('source', 'Unknown')

                # Update song info (artist on top, title below)
                self._safe_widget_update('artist_label', lambda w, a=artist: w.config(text=a))
                self._safe_widget_update('song_title_label', lambda w, t=title: w.config(text=t))

                # Look up BPM
                self._safe_widget_update('status_label', lambda w: w.config(text="Looking up BPM..."))

                # Initialize BPM manager if needed
                if not self.bpm_manager:
                    self.bpm_manager = BPMManager(
                        mongodb_uri=MONGODB_URI,
                        getsongbpm_api_key=GETSONGBPM_API_KEY,
                        use_scraper=True,
                        auto_sync=False
                    )

                # Get BPM
                bpm_data = self.bpm_manager.get_bpm(artist, title)

                if bpm_data:
                    # Handle both dict and numeric return types
                    if isinstance(bpm_data, dict):
                        bpm = int(bpm_data.get('bpm', 0))
                        source = bpm_data.get('source', 'unknown')
                    else:
                        bpm = int(bpm_data)
                        source = 'unknown'
                    
                    self.detected_bpm = bpm if bpm > 0 else None

                    # Update BPM display if beats tab is showing
                    self._safe_widget_update('bpm_display', lambda w, b=bpm: w.config(text=str(b)))
                    self._safe_widget_update('bpm_source_label', lambda w, s=source: w.config(text=f"Source: {s}"))
                    self._safe_widget_update('sync_button', lambda w: w.config(state=tk.NORMAL))
                    self._safe_widget_update('status_label', lambda w, b=bpm: w.config(
                        text=f"Found: {b} BPM", fg=self.colors['accent']
                    ))
                else:
                    self._safe_widget_update('bpm_display', lambda w: w.config(text="???"))
                    self._safe_widget_update('bpm_source_label', lambda w: w.config(text=""))
                    self._safe_widget_update('sync_button', lambda w: w.config(state=tk.DISABLED))
                    self._safe_widget_update('status_label', lambda w: w.config(
                        text="BPM not found in database", fg='#ff6b6b'
                    ))
            else:
                self._safe_widget_update('artist_label', lambda w: w.config(text="No song playing"))
                self._safe_widget_update('song_title_label', lambda w: w.config(text="Play music to detect"))
                self._safe_widget_update('bpm_display', lambda w: w.config(text="---"))
                self._safe_widget_update('status_label', lambda w: w.config(
                    text="No music player detected", fg='#ff6b6b'
                ))

        except Exception as e:
            error_msg = str(e)
            self._safe_widget_update('status_label', lambda w, msg=error_msg: w.config(
                text=f"Error: {msg}", fg='#ff6b6b'
            ))
        finally:
            self._safe_widget_update('detect_button', lambda w: w.config(state=tk.NORMAL))

    def _sync_to_metronome(self):
        """Sync detected BPM to the metronome and switch views."""
        if self.detected_bpm:
            # Store BPM to sync
            sync_bpm = self.detected_bpm

            # Switch to metronome view
            self._show_metronome_view()

            # Set BPM value
            self.bpm_var.set(sync_bpm)

    def _on_close(self):
        """Handle application close."""
        self.is_playing = False
        if self.bpm_manager:
            self.bpm_manager.cleanup()
        pygame.mixer.quit()
        self.root.destroy()


def main():
    """Launch the MetroMatch application."""
    root = tk.Tk()
    app = MetroMatchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
