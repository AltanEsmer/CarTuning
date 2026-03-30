"""Tests for the CarTuning Humanization Engine."""

import sys
import os
import unittest
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from humanizer import Humanizer, HumanizationConfig, ShotData


class TestHumanizationConfig(unittest.TestCase):
    """Test HumanizationConfig creation and from_dict."""
    
    def test_default_config(self):
        config = HumanizationConfig()
        self.assertEqual(config.delay_variance_ms, 10.0)
        self.assertEqual(config.pull_variance_px, 1.0)
        self.assertEqual(config.skip_probability, 0.03)
    
    def test_from_dict(self):
        data = {
            'delay_variance_ms': 12.0,
            'pull_variance_px': 1.5,
            'x_variance_px': 2.0,
            'skip_probability': 0.05,
            'overcorrect_probability': 0.03,
            'overcorrect_magnitude': 1.2,
            'falloff_stages': [
                {'end_shot': 8, 'multiplier': 1.0},
                {'end_shot': 16, 'multiplier': 0.95},
                {'end_shot': 24, 'multiplier': 0.90}
            ]
        }
        config = HumanizationConfig.from_dict(data)
        self.assertEqual(config.delay_variance_ms, 12.0)
        self.assertEqual(config.skip_probability, 0.05)
        self.assertEqual(len(config.falloff_stages), 3)
    
    def test_from_dict_missing_keys_uses_defaults(self):
        config = HumanizationConfig.from_dict({})
        self.assertEqual(config.delay_variance_ms, 10.0)


class TestHumanizerDelayVariance(unittest.TestCase):
    """Test delay variance behavior."""
    
    def setUp(self):
        self.config = HumanizationConfig(delay_variance_ms=10.0)
        self.humanizer = Humanizer(self.config, seed=42)
    
    def test_delay_within_bounds(self):
        base = 100.0
        for _ in range(1000):
            result = self.humanizer.apply_delay_variance(base)
            self.assertGreaterEqual(result, base - 10.0)
            self.assertLessEqual(result, base + 10.0)
    
    def test_delay_mean_near_base(self):
        base = 100.0
        results = [self.humanizer.apply_delay_variance(base) for _ in range(10000)]
        mean = statistics.mean(results)
        self.assertAlmostEqual(mean, base, delta=1.0)
    
    def test_delay_has_variance(self):
        base = 100.0
        results = [self.humanizer.apply_delay_variance(base) for _ in range(100)]
        self.assertGreater(statistics.stdev(results), 0.5)


class TestHumanizerPullVariance(unittest.TestCase):
    """Test Y-axis pull variance."""
    
    def setUp(self):
        self.config = HumanizationConfig(pull_variance_px=1.0)
        self.humanizer = Humanizer(self.config, seed=42)
    
    def test_pull_mean_near_base(self):
        base = 5.0
        results = [self.humanizer.apply_pull_variance(base) for _ in range(10000)]
        mean = statistics.mean(results)
        self.assertAlmostEqual(mean, base, delta=0.1)
    
    def test_pull_has_variance(self):
        base = 5.0
        results = [self.humanizer.apply_pull_variance(base) for _ in range(100)]
        unique = len(set(results))
        self.assertGreater(unique, 50)


class TestHumanizerSkipProbability(unittest.TestCase):
    """Test skip events."""
    
    def test_skip_rate_matches_config(self):
        config = HumanizationConfig(skip_probability=0.05)
        humanizer = Humanizer(config, seed=42)
        
        skips = sum(1 for _ in range(100000) if humanizer.should_skip())
        rate = skips / 100000
        self.assertAlmostEqual(rate, 0.05, delta=0.01)
    
    def test_zero_skip_probability(self):
        config = HumanizationConfig(skip_probability=0.0)
        humanizer = Humanizer(config, seed=42)
        
        skips = sum(1 for _ in range(10000) if humanizer.should_skip())
        self.assertEqual(skips, 0)


class TestHumanizerOvercorrection(unittest.TestCase):
    """Test over-correction events."""
    
    def test_overcorrect_rate_matches_config(self):
        config = HumanizationConfig(overcorrect_probability=0.03)
        humanizer = Humanizer(config, seed=42)
        
        overcorrects = sum(1 for _ in range(100000) if humanizer.should_overcorrect())
        rate = overcorrects / 100000
        self.assertAlmostEqual(rate, 0.03, delta=0.01)


class TestHumanizerFalloff(unittest.TestCase):
    """Test staged falloff."""
    
    def setUp(self):
        self.config = HumanizationConfig(
            falloff_stages=[
                {'end_shot': 10, 'multiplier': 1.0},
                {'end_shot': 20, 'multiplier': 0.95},
                {'end_shot': 30, 'multiplier': 0.87}
            ]
        )
        self.humanizer = Humanizer(self.config)
    
    def test_early_shots_full_compensation(self):
        for shot in range(1, 11):
            self.assertEqual(self.humanizer.get_falloff_multiplier(shot), 1.0)
    
    def test_mid_shots_reduced(self):
        for shot in range(11, 21):
            self.assertEqual(self.humanizer.get_falloff_multiplier(shot), 0.95)
    
    def test_late_shots_further_reduced(self):
        for shot in range(21, 31):
            self.assertEqual(self.humanizer.get_falloff_multiplier(shot), 0.87)
    
    def test_beyond_stages_uses_last(self):
        self.assertEqual(self.humanizer.get_falloff_multiplier(50), 0.87)


class TestHumanizerSequence(unittest.TestCase):
    """Test full sequence humanization."""
    
    def setUp(self):
        self.config = HumanizationConfig(
            delay_variance_ms=10.0,
            pull_variance_px=1.0,
            x_variance_px=0.5,
            skip_probability=0.03,
            overcorrect_probability=0.02,
            overcorrect_magnitude=1.2,
            falloff_stages=[
                {'end_shot': 10, 'multiplier': 1.0},
                {'end_shot': 20, 'multiplier': 0.95},
                {'end_shot': 30, 'multiplier': 0.87}
            ]
        )
    
    def _make_base_shots(self, count=30):
        return [{'shot_number': i+1, 'delay_ms': 100.0, 'pull_y': 5.0, 'drift_x': 1.0}
                for i in range(count)]
    
    def test_sequence_length_preserved(self):
        humanizer = Humanizer(self.config, seed=42)
        base = self._make_base_shots()
        result = humanizer.humanize_sequence(base)
        self.assertEqual(len(result), 30)
    
    def test_sequences_are_unique(self):
        base = self._make_base_shots()
        sequences = []
        for seed in range(100):
            humanizer = Humanizer(self.config, seed=seed)
            result = humanizer.humanize_sequence(base)
            sig = tuple((s.delay_ms, s.pull_y, s.drift_x) for s in result)
            sequences.append(sig)
        
        unique = len(set(sequences))
        self.assertEqual(unique, 100)
    
    def test_reproducibility_with_seed(self):
        base = self._make_base_shots()
        
        h1 = Humanizer(self.config, seed=42)
        r1 = h1.humanize_sequence(base)
        
        h2 = Humanizer(self.config, seed=42)
        r2 = h2.humanize_sequence(base)
        
        for s1, s2 in zip(r1, r2):
            self.assertEqual(s1.delay_ms, s2.delay_ms)
            self.assertEqual(s1.pull_y, s2.pull_y)
            self.assertEqual(s1.drift_x, s2.drift_x)
    
    def test_skipped_shots_have_zero_compensation(self):
        # Use high skip probability to guarantee some skips
        config = HumanizationConfig(skip_probability=1.0)
        humanizer = Humanizer(config, seed=42)
        base = self._make_base_shots(5)
        result = humanizer.humanize_sequence(base)
        
        for shot in result:
            self.assertTrue(shot.is_skipped)
            self.assertEqual(shot.pull_y, 0.0)
            self.assertEqual(shot.drift_x, 0.0)


class TestHumanizerSpecialVariance(unittest.TestCase):
    """Test weapon-specific special variance (Custom SMG style)."""
    
    def test_y_spike_applied(self):
        config = HumanizationConfig(
            pull_variance_px=0.0,  # No normal variance
            x_variance_px=0.0,
            delay_variance_ms=0.0,
            skip_probability=0.0,
            overcorrect_probability=0.0,
            special_variance={
                'y_spike_probability': 1.0,  # Always spike
                'y_spike_magnitude': 2.0
            }
        )
        humanizer = Humanizer(config, seed=42)
        
        shot, _ = humanizer.humanize_shot(1, 100.0, 3.0, 0.0)
        # Base pull + spike magnitude = 3.0 + 2.0 = 5.0
        self.assertAlmostEqual(shot.pull_y, 5.0, delta=0.01)


if __name__ == '__main__':
    unittest.main()
