"""
CarTuning Interception Executor
Live playback of humanized macro sequences via the Interception kernel filter driver.

Interception sits inside the HID stack (below raw input), so injected events appear
in WM_INPUT as real hardware — making them visible to CS2 and other raw-input games.

Requirements:
  1. Install the Interception driver (system-level, requires reboot):
     https://github.com/oblitum/Interception
  2. pip install interception-python

Game compatibility:
  CS2  (VAC)       — ✅ Works. VAC does not block the Interception driver.
  R6   (BattlEye)  — 🟡 Uncertain. BattlEye detection varies by version.
  Rust (EAC)       — ❌ Blocked. EAC refuses to launch with the driver loaded.
"""

import time
import threading
from typing import List, Optional

try:
    import interception as _interception
    _INTERCEPTION_AVAILABLE = True
except ImportError:
    _interception = None
    _INTERCEPTION_AVAILABLE = False

# Optional: pynput for hold-key and abort-key detection
try:
    from pynput import mouse as _pynput_mouse
    from pynput import keyboard as _pynput_keyboard
    _PYNPUT_AVAILABLE = True
except ImportError:
    _pynput_mouse = None
    _pynput_keyboard = None
    _PYNPUT_AVAILABLE = False

from humanizer import ShotData

# Key code for F8 (abort)
_F8_KEY = "<F8>"


class InterceptionExecutor:
    """
    Plays a List[ShotData] in real-time using the Interception kernel driver.

    Each shot produces:
      - A sleep of delay_ms milliseconds
      - A kernel-level mouse_rel(x=drift_x, y=pull_y) call (unless skipped)

    Two playback modes:
      hold_mode=True  — loops the sequence while the left mouse button is held,
                        restarting from shot 1 each iteration (fire until release).
      hold_mode=False — plays through the sequence once and returns.

    Press F8 at any point to abort playback.
    """

    def __init__(self):
        self._abort = threading.Event()
        self._mouse_held = threading.Event()
        self._kb_listener = None
        self._mouse_listener = None

    @classmethod
    def is_available(cls) -> bool:
        """Return True if the interception-python package is importable."""
        return _INTERCEPTION_AVAILABLE

    def _setup_driver(self):
        """Initialize the Interception driver and capture devices."""
        if not _INTERCEPTION_AVAILABLE:
            raise RuntimeError(
                "interception-python is not installed.\n"
                "Run: pip install interception-python\n"
                "Then install the Interception driver from:\n"
                "  https://github.com/oblitum/Interception"
            )
        _interception.auto_capture_devices()

    def _start_abort_listener(self):
        """Start a keyboard listener that sets the abort flag on F8."""
        if not _PYNPUT_AVAILABLE:
            return

        def on_press(key):
            try:
                if key == _pynput_keyboard.Key.f8:
                    print("\n  [!] F8 pressed — aborting playback.")
                    self._abort.set()
                    return False  # Stop listener
            except AttributeError:
                pass

        self._kb_listener = _pynput_keyboard.Listener(on_press=on_press)
        self._kb_listener.daemon = True
        self._kb_listener.start()

    def _start_mouse_listener(self):
        """Track left mouse button hold state."""
        if not _PYNPUT_AVAILABLE:
            return

        def on_click(x, y, button, pressed):
            if button == _pynput_mouse.Button.left:
                if pressed:
                    self._mouse_held.set()
                else:
                    self._mouse_held.clear()

        self._mouse_listener = _pynput_mouse.Listener(on_click=on_click)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    def _stop_listeners(self):
        if self._kb_listener:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass

    def _play_sequence_once(self, sequence: List[ShotData]):
        """
        Execute one full pass through the sequence.
        Returns early if abort is set.
        """
        for shot in sequence:
            if self._abort.is_set():
                return

            # Always sleep the delay regardless of skip
            time.sleep(shot.delay_ms / 1000.0)

            if self._abort.is_set():
                return

            if shot.is_skipped:
                continue

            x = round(shot.drift_x)
            y = round(shot.pull_y)
            _interception.move_rel(x=x, y=y)

    def play(
        self,
        sequence: List[ShotData],
        hold_mode: bool = True,
        verbose: bool = True,
    ):
        """
        Play back a humanized sequence via Interception.

        Args:
            sequence:   List of ShotData from the humanizer.
            hold_mode:  If True, wait for left mouse button hold before each
                        pass and stop when it's released. If False, play once.
            verbose:    Print status messages to stdout.
        """
        self._setup_driver()
        self._abort.clear()
        self._mouse_held.clear()

        shots = len(sequence)
        skips = sum(1 for s in sequence if s.is_skipped)

        if verbose:
            print(f"\n  [Interception] Ready — {shots} shots ({skips} skipped)")
            if hold_mode:
                print("  Hold LEFT MOUSE to fire. Press F8 to abort.\n")
            else:
                print("  Playing once. Press F8 to abort.\n")

        self._start_abort_listener()

        if hold_mode:
            self._start_mouse_listener()
            try:
                self._run_hold_mode(sequence, verbose)
            finally:
                self._stop_listeners()
        else:
            try:
                self._play_sequence_once(sequence)
                if verbose and not self._abort.is_set():
                    print("  [Interception] Sequence complete.")
            finally:
                self._stop_listeners()

    def _run_hold_mode(self, sequence: List[ShotData], verbose: bool):
        """
        Hold-mode loop: wait for left mouse button, play while held, repeat.
        """
        if not _PYNPUT_AVAILABLE:
            print(
                "  [!] pynput not installed — hold mode unavailable.\n"
                "      Falling back to single-play mode."
            )
            self._play_sequence_once(sequence)
            return

        pass_count = 0
        while not self._abort.is_set():
            # Wait for left mouse button press (poll every 10ms)
            while not self._mouse_held.is_set() and not self._abort.is_set():
                time.sleep(0.01)

            if self._abort.is_set():
                break

            pass_count += 1
            if verbose:
                print(f"  [Interception] Pass {pass_count} — firing...")

            # Play through shots; stop early if mouse released
            for shot in sequence:
                if self._abort.is_set() or not self._mouse_held.is_set():
                    break

                time.sleep(shot.delay_ms / 1000.0)

                if self._abort.is_set() or not self._mouse_held.is_set():
                    break

                if shot.is_skipped:
                    continue

                _interception.move_rel(x=round(shot.drift_x), y=round(shot.pull_y))

            if verbose and not self._abort.is_set():
                print("  [Interception] Released.")

        if verbose:
            print("  [Interception] Playback stopped.")
