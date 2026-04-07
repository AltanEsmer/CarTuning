"""Tests for the CarTuning Interception Executor."""

import sys
import os
import unittest
import threading
import time
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from humanizer import ShotData


def _make_shot(n, delay=90.0, y=5.0, x=1.0, skipped=False):
    return ShotData(
        shot_number=n,
        delay_ms=delay,
        pull_y=y,
        drift_x=x,
        is_skipped=skipped,
    )


def _make_sequence(count=5, skips=None):
    skips = skips or []
    return [_make_shot(i + 1, skipped=(i in skips)) for i in range(count)]


class TestInterceptionExecutorAvailability(unittest.TestCase):
    """Test is_available() reflects import state."""

    def test_available_when_interception_importable(self):
        mock_interception = MagicMock()
        with patch.dict(sys.modules, {'interception': mock_interception}):
            # Re-import executor with interception present
            if 'executor' in sys.modules:
                del sys.modules['executor']
            import importlib
            import executor as executor_mod
            importlib.reload(executor_mod)
            self.assertTrue(executor_mod.InterceptionExecutor.is_available())

    def test_unavailable_when_interception_missing(self):
        with patch.dict(sys.modules, {'interception': None}):
            if 'executor' in sys.modules:
                del sys.modules['executor']
            # Patch builtins import to raise for 'interception'
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        # Simpler: directly test the module-level flag
        import executor as executor_mod
        original = executor_mod._INTERCEPTION_AVAILABLE
        executor_mod._INTERCEPTION_AVAILABLE = False
        self.assertFalse(executor_mod.InterceptionExecutor.is_available())
        executor_mod._INTERCEPTION_AVAILABLE = original


class TestInterceptionExecutorSetup(unittest.TestCase):
    """Test driver setup and error handling."""

    def test_setup_raises_when_unavailable(self):
        import executor as executor_mod
        original = executor_mod._INTERCEPTION_AVAILABLE
        executor_mod._INTERCEPTION_AVAILABLE = False

        ex = executor_mod.InterceptionExecutor()
        with self.assertRaises(RuntimeError) as ctx:
            ex._setup_driver()

        self.assertIn('interception-python', str(ctx.exception))
        executor_mod._INTERCEPTION_AVAILABLE = original

    def test_setup_calls_auto_capture_when_available(self):
        import executor as executor_mod
        mock_interception = MagicMock()

        original_flag = executor_mod._INTERCEPTION_AVAILABLE
        original_module = executor_mod._interception

        executor_mod._INTERCEPTION_AVAILABLE = True
        executor_mod._interception = mock_interception

        ex = executor_mod.InterceptionExecutor()
        ex._setup_driver()

        mock_interception.auto_capture_devices.assert_called_once()

        executor_mod._INTERCEPTION_AVAILABLE = original_flag
        executor_mod._interception = original_module


class TestPlaySequenceOnce(unittest.TestCase):
    """Test _play_sequence_once: move_rel calls, skip handling, abort."""

    def setUp(self):
        import executor as executor_mod
        self.executor_mod = executor_mod
        self.mock_interception = MagicMock()

        self._orig_flag = executor_mod._INTERCEPTION_AVAILABLE
        self._orig_module = executor_mod._interception

        executor_mod._INTERCEPTION_AVAILABLE = True
        executor_mod._interception = self.mock_interception

    def tearDown(self):
        self.executor_mod._INTERCEPTION_AVAILABLE = self._orig_flag
        self.executor_mod._interception = self._orig_module

    def test_move_rel_called_for_each_non_skipped_shot(self):
        sequence = _make_sequence(count=4, skips=[1])  # shots 0,2,3 active; shot 1 skipped
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep'):
            ex._play_sequence_once(sequence)

        # 3 active shots → 3 move_rel calls
        self.assertEqual(self.mock_interception.move_rel.call_count, 3)

    def test_skipped_shot_produces_no_move_rel(self):
        sequence = [_make_shot(1, skipped=True)]
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep'):
            ex._play_sequence_once(sequence)

        self.mock_interception.move_rel.assert_not_called()

    def test_move_rel_receives_correct_values(self):
        shot = _make_shot(1, y=7.6, x=-2.4)
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep'):
            ex._play_sequence_once([shot])

        self.mock_interception.move_rel.assert_called_once_with(x=-2, y=8)

    def test_sleep_called_per_shot(self):
        sequence = _make_sequence(count=3)
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep') as mock_sleep:
            ex._play_sequence_once(sequence)

        # sleep called once per shot (before movement)
        self.assertEqual(mock_sleep.call_count, 3)

    def test_sleep_uses_delay_in_seconds(self):
        shot = _make_shot(1, delay=100.0)
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep') as mock_sleep:
            ex._play_sequence_once([shot])

        mock_sleep.assert_called_with(0.1)

    def test_abort_stops_playback_early(self):
        sequence = _make_sequence(count=10)
        ex = self.executor_mod.InterceptionExecutor()
        ex._abort.set()  # Set abort before playback starts

        with patch('time.sleep'):
            ex._play_sequence_once(sequence)

        # Abort set before first shot → no moves
        self.mock_interception.move_rel.assert_not_called()

    def test_full_sequence_with_all_skips(self):
        sequence = _make_sequence(count=5, skips=[0, 1, 2, 3, 4])
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep'):
            ex._play_sequence_once(sequence)

        self.mock_interception.move_rel.assert_not_called()


class TestPlaySingleMode(unittest.TestCase):
    """Test play() with hold_mode=False (single pass)."""

    def setUp(self):
        import executor as executor_mod
        self.executor_mod = executor_mod
        self.mock_interception = MagicMock()

        self._orig_flag = executor_mod._INTERCEPTION_AVAILABLE
        self._orig_module = executor_mod._interception
        self._orig_pynput = executor_mod._PYNPUT_AVAILABLE

        executor_mod._INTERCEPTION_AVAILABLE = True
        executor_mod._interception = self.mock_interception
        executor_mod._PYNPUT_AVAILABLE = False  # Disable pynput for isolation

    def tearDown(self):
        self.executor_mod._INTERCEPTION_AVAILABLE = self._orig_flag
        self.executor_mod._interception = self._orig_module
        self.executor_mod._PYNPUT_AVAILABLE = self._orig_pynput

    def test_play_once_calls_move_rel_for_all_shots(self):
        sequence = _make_sequence(count=5)
        ex = self.executor_mod.InterceptionExecutor()

        with patch('time.sleep'):
            ex.play(sequence, hold_mode=False, verbose=False)

        self.assertEqual(self.mock_interception.move_rel.call_count, 5)

    def test_play_once_does_not_loop(self):
        sequence = _make_sequence(count=2)
        ex = self.executor_mod.InterceptionExecutor()
        call_count = {'n': 0}

        original_once = ex._play_sequence_once

        def counting_once(seq):
            call_count['n'] += 1
            original_once(seq)

        ex._play_sequence_once = counting_once

        with patch('time.sleep'):
            ex.play(sequence, hold_mode=False, verbose=False)

        self.assertEqual(call_count['n'], 1)

    def test_play_unavailable_raises(self):
        self.executor_mod._INTERCEPTION_AVAILABLE = False
        ex = self.executor_mod.InterceptionExecutor()

        with self.assertRaises(RuntimeError):
            ex.play(_make_sequence(), hold_mode=False, verbose=False)


if __name__ == '__main__':
    unittest.main()
