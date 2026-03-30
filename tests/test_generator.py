"""Tests for the CarTuning Macro Generator."""

import sys
import os
import unittest
import json
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generator import MacroGenerator, WeaponProfile
from humanizer import ShotData


class TestMacroGeneratorProfileLoading(unittest.TestCase):
    """Test weapon profile loading."""
    
    def setUp(self):
        self.gen = MacroGenerator()
    
    def test_load_ak47(self):
        profile = self.gen.load_profile('ak47')
        self.assertEqual(profile.name, 'AK-47')
        self.assertEqual(profile.shots_per_mag, 30)
    
    def test_load_lr300(self):
        profile = self.gen.load_profile('lr300')
        self.assertEqual(profile.shots_per_mag, 30)
    
    def test_load_m249(self):
        profile = self.gen.load_profile('m249')
        self.assertEqual(profile.shots_per_mag, 100)
    
    def test_load_mp5(self):
        profile = self.gen.load_profile('mp5')
        self.assertEqual(profile.shots_per_mag, 30)
    
    def test_load_custom_smg(self):
        profile = self.gen.load_profile('custom_smg')
        self.assertEqual(profile.shots_per_mag, 24)
    
    def test_load_thompson(self):
        profile = self.gen.load_profile('thompson')
        self.assertEqual(profile.shots_per_mag, 30)
    
    def test_load_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.gen.load_profile('nonexistent_weapon')
    
    def test_list_weapons(self):
        weapons = self.gen.list_weapons()
        self.assertGreaterEqual(len(weapons), 6)
        self.assertIn('ak47', weapons)
        self.assertIn('m249', weapons)


class TestBaseValueCalculation(unittest.TestCase):
    """Test raw per-shot value calculation."""
    
    def setUp(self):
        self.gen = MacroGenerator(dpi=800)
    
    def test_ak47_shot_count(self):
        profile = self.gen.load_profile('ak47')
        values = self.gen.calculate_base_values(profile)
        self.assertEqual(len(values), 30)
    
    def test_m249_shot_count(self):
        profile = self.gen.load_profile('m249')
        values = self.gen.calculate_base_values(profile)
        self.assertEqual(len(values), 100)
    
    def test_custom_smg_shot_count(self):
        profile = self.gen.load_profile('custom_smg')
        values = self.gen.calculate_base_values(profile)
        self.assertEqual(len(values), 24)
    
    def test_values_have_required_keys(self):
        profile = self.gen.load_profile('ak47')
        values = self.gen.calculate_base_values(profile)
        for v in values:
            self.assertIn('shot_number', v)
            self.assertIn('delay_ms', v)
            self.assertIn('pull_y', v)
            self.assertIn('drift_x', v)
    
    def test_shot_numbers_sequential(self):
        profile = self.gen.load_profile('ak47')
        values = self.gen.calculate_base_values(profile)
        numbers = [v['shot_number'] for v in values]
        self.assertEqual(numbers, list(range(1, 31)))
    
    def test_dpi_scaling(self):
        gen_800 = MacroGenerator(dpi=800)
        gen_1600 = MacroGenerator(dpi=1600)
        
        profile_800 = gen_800.load_profile('ak47')
        profile_1600 = gen_1600.load_profile('ak47')
        
        vals_800 = gen_800.calculate_base_values(profile_800)
        vals_1600 = gen_1600.calculate_base_values(profile_1600)
        
        # At 1600 DPI, values should be half of 800 DPI
        for v800, v1600 in zip(vals_800, vals_1600):
            self.assertAlmostEqual(v1600['pull_y'], v800['pull_y'] * 0.5, delta=0.01)


class TestSequenceGeneration(unittest.TestCase):
    """Test full sequence generation pipeline."""
    
    def setUp(self):
        self.gen = MacroGenerator(dpi=800)
    
    def test_generate_ak47(self):
        seq = self.gen.generate_sequence('ak47', seed=42)
        self.assertEqual(len(seq), 30)
        self.assertIsInstance(seq[0], ShotData)
    
    def test_generate_all_weapons(self):
        for weapon in self.gen.list_weapons():
            seq = self.gen.generate_sequence(weapon, seed=42)
            self.assertGreater(len(seq), 0)
    
    def test_sequences_differ_without_seed(self):
        s1 = self.gen.generate_sequence('ak47')
        s2 = self.gen.generate_sequence('ak47')
        
        sig1 = tuple((s.delay_ms, s.pull_y) for s in s1)
        sig2 = tuple((s.delay_ms, s.pull_y) for s in s2)
        self.assertNotEqual(sig1, sig2)
    
    def test_sequences_same_with_seed(self):
        s1 = self.gen.generate_sequence('ak47', seed=42)
        s2 = self.gen.generate_sequence('ak47', seed=42)
        
        for a, b in zip(s1, s2):
            self.assertEqual(a.delay_ms, b.delay_ms)
            self.assertEqual(a.pull_y, b.pull_y)


class TestSynapseExport(unittest.TestCase):
    """Test Synapse format output."""
    
    def setUp(self):
        self.gen = MacroGenerator(dpi=800)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_format_contains_header(self):
        seq = self.gen.generate_sequence('ak47', seed=42)
        output = self.gen.format_synapse(seq, 'ak47')
        self.assertIn('Macro: RECOIL_AK47', output)
        self.assertIn('While Assigned Button is Held', output)
        self.assertIn('Sequence:', output)
    
    def test_format_contains_delays_and_moves(self):
        seq = self.gen.generate_sequence('ak47', seed=42)
        output = self.gen.format_synapse(seq, 'ak47')
        self.assertIn('Delay:', output)
        self.assertIn('Mouse Move:', output)
    
    def test_export_creates_file(self):
        gen = MacroGenerator(output_dir=self.temp_dir, dpi=800)
        path = gen.export('ak47', seed=42)
        self.assertTrue(os.path.exists(path))
        
        with open(path, 'r') as f:
            content = f.read()
        self.assertIn('RECOIL_AK47', content)
    
    def test_export_all_creates_files(self):
        gen = MacroGenerator(output_dir=self.temp_dir, dpi=800)
        paths = gen.export_all(seed=42)
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
