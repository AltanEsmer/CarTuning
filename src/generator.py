"""
CarTuning Macro Generator
Loads weapon profiles, calculates per-shot compensation,
applies humanization, and exports Synapse-ready macros.
"""

import json
import os
import argparse
import random
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

# Import from same package
from humanizer import Humanizer, HumanizationConfig, ShotData


@dataclass
class WeaponProfile:
    """Parsed weapon profile from JSON."""
    name: str
    shots_per_mag: int
    total_pull_distance: list  # [min, max]
    reference_dpi: int
    polling_rate_hz: int
    curve_shape: str
    difficulty: str
    fire_rate_rpm: int
    base_delay_ms: float
    sections: list
    humanization: dict
    special_variance: Optional[dict] = None


class MacroGenerator:
    """
    Main macro generator. Loads weapon profiles, computes base compensation
    values per shot, humanizes them, and exports to Synapse format.
    """
    
    def __init__(self, weapons_dir: str = None, output_dir: str = None, dpi: int = 800):
        """
        Args:
            weapons_dir: Path to weapons JSON directory
            output_dir: Path for output macro files
            dpi: Target DPI (values scaled from 800 reference)
        """
        base = Path(__file__).parent
        self.weapons_dir = Path(weapons_dir) if weapons_dir else base / "weapons"
        self.output_dir = Path(output_dir) if output_dir else base / "output"
        self.dpi = dpi
        self.dpi_scale = 800.0 / dpi  # Scale factor from reference
    
    def load_profile(self, weapon_name: str) -> WeaponProfile:
        """Load a weapon JSON profile by name (e.g., 'ak47')."""
        filepath = self.weapons_dir / f"{weapon_name}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Weapon profile not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return WeaponProfile(
            name=data['weapon_name'],
            shots_per_mag=data['shots_per_mag'],
            total_pull_distance=data['total_pull_distance_px'],
            reference_dpi=data['reference_dpi'],
            polling_rate_hz=data['polling_rate_hz'],
            curve_shape=data['curve_shape'],
            difficulty=data['difficulty'],
            fire_rate_rpm=data['fire_rate_rpm'],
            base_delay_ms=data['base_delay_ms'],
            sections=data['sections'],
            humanization=data['humanization'],
            special_variance=data.get('special_variance', None)
        )
    
    def list_weapons(self) -> List[str]:
        """List available weapon profile names."""
        return [f.stem for f in self.weapons_dir.glob("*.json")]
    
    def calculate_base_values(self, profile: WeaponProfile) -> List[dict]:
        """
        Calculate raw per-shot compensation values from weapon profile sections.
        
        Returns list of dicts with: shot_number, delay_ms, pull_y, drift_x
        """
        shots = []
        
        for section in profile.sections:
            start = section['start_shot']
            end = section['end_shot']
            y_range = section['pull_y_per_shot']
            x_range = section['drift_x_per_shot']
            
            for shot_num in range(start, end + 1):
                # Interpolate within section range for gradual progression
                progress = (shot_num - start) / max(1, end - start)
                
                # Base Y pull: interpolate between min and max
                base_y = y_range[0] + (y_range[1] - y_range[0]) * progress
                # Base X drift: interpolate between min and max
                base_x = x_range[0] + (x_range[1] - x_range[0]) * progress
                
                # Apply DPI scaling
                base_y *= self.dpi_scale
                base_x *= self.dpi_scale
                
                shots.append({
                    'shot_number': shot_num,
                    'delay_ms': profile.base_delay_ms,
                    'pull_y': round(base_y, 2),
                    'drift_x': round(base_x, 2)
                })
        
        return shots
    
    def generate_sequence(self, weapon_name: str, seed: Optional[int] = None) -> List[ShotData]:
        """
        Generate a full humanized macro sequence for a weapon.
        
        Args:
            weapon_name: Weapon profile name (e.g., 'ak47')
            seed: Optional random seed for reproducibility
        
        Returns:
            List of humanized ShotData objects
        """
        profile = self.load_profile(weapon_name)
        base_values = self.calculate_base_values(profile)
        
        # Build humanization config
        h_config = HumanizationConfig.from_dict(profile.humanization)
        if profile.special_variance:
            h_config.special_variance = profile.special_variance
        
        # Scale humanization variance by DPI too
        h_config.pull_variance_px *= self.dpi_scale
        h_config.x_variance_px *= self.dpi_scale
        
        humanizer = Humanizer(h_config, seed=seed)
        return humanizer.humanize_sequence(base_values)
    
    def format_synapse(self, sequence: List[ShotData], weapon_name: str) -> str:
        """
        Format a humanized sequence into Synapse macro text.
        
        Produces output like:
        Macro: RECOIL_AK47
        Activation: While Assigned Button is Held
        
        Sequence:
        1. Delay: 95.3ms
        2. Mouse Move: Relative Y:6 X:-1
        ...
        """
        lines = []
        lines.append(f"Macro: RECOIL_{weapon_name.upper()}")
        lines.append("Activation: While Assigned Button is Held")
        lines.append("Repeat: None")
        lines.append("")
        lines.append("Sequence:")
        
        step = 1
        for shot in sequence:
            if shot.is_skipped:
                # Skipped shot — still add delay but no mouse movement
                lines.append(f"  {step}. Delay: {shot.delay_ms}ms")
                step += 1
                continue
            
            # Delay
            lines.append(f"  {step}. Delay: {shot.delay_ms}ms")
            step += 1
            
            # Mouse move (round to integers for Synapse)
            y = round(shot.pull_y)
            x = round(shot.drift_x)
            lines.append(f"  {step}. Mouse Move: Relative Y:{y} X:{x}")
            step += 1
        
        return "\n".join(lines)
    
    def export(self, weapon_name: str, seed: Optional[int] = None) -> str:
        """
        Generate and export a macro for a weapon.
        
        Returns the output file path.
        """
        sequence = self.generate_sequence(weapon_name, seed=seed)
        macro_text = self.format_synapse(sequence, weapon_name)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"RECOIL_{weapon_name.upper()}.txt"
        
        with open(output_path, 'w') as f:
            f.write(macro_text)
        
        return str(output_path)
    
    def export_all(self, seed: Optional[int] = None) -> List[str]:
        """Export macros for all available weapons."""
        paths = []
        for weapon in self.list_weapons():
            path = self.export(weapon, seed=seed)
            paths.append(path)
            print(f"  [+] Generated: {path}")
        return paths
    
    def print_sequence_stats(self, weapon_name: str, sequence: List[ShotData]):
        """Print statistics about a generated sequence."""
        total_y = sum(s.pull_y for s in sequence)
        total_x = sum(abs(s.drift_x) for s in sequence)
        skips = sum(1 for s in sequence if s.is_skipped)
        overcorrects = sum(1 for s in sequence if s.is_overcorrected)
        avg_delay = sum(s.delay_ms for s in sequence) / len(sequence)
        
        print(f"\n  [{weapon_name.upper()}] Sequence Stats:")
        print(f"    Shots: {len(sequence)}")
        print(f"    Total Y-pull: {total_y:.1f}px")
        print(f"    Total X-drift: {total_x:.1f}px")
        print(f"    Skipped shots: {skips}")
        print(f"    Over-corrections: {overcorrects}")
        print(f"    Avg delay: {avg_delay:.1f}ms")


def main():
    parser = argparse.ArgumentParser(
        description="CarTuning Macro Generator — Humanized recoil compensation"
    )
    parser.add_argument(
        '--weapon', '-w',
        default='all',
        help='Weapon name (e.g., ak47, lr300) or "all" for all weapons'
    )
    parser.add_argument(
        '--dpi', '-d',
        type=int,
        default=800,
        help='Target DPI (default: 800)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output directory (default: src/output/)'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=None,
        help='Random seed for reproducible output (debugging)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print sequence statistics'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available weapons'
    )
    
    args = parser.parse_args()
    
    gen = MacroGenerator(
        output_dir=args.output,
        dpi=args.dpi
    )
    
    if args.list:
        weapons = gen.list_weapons()
        print(f"\nAvailable weapons ({len(weapons)}):")
        for w in weapons:
            print(f"  - {w}")
        return
    
    print(f"\n{'='*50}")
    print(f"  CarTuning Macro Generator")
    print(f"  DPI: {args.dpi} | Scale: {gen.dpi_scale:.2f}x")
    print(f"{'='*50}")
    
    if args.weapon == 'all':
        print(f"\n  Generating all weapons...")
        paths = gen.export_all(seed=args.seed)
        if args.stats:
            for weapon in gen.list_weapons():
                seq = gen.generate_sequence(weapon, seed=args.seed)
                gen.print_sequence_stats(weapon, seq)
    else:
        print(f"\n  Generating: {args.weapon}")
        path = gen.export(args.weapon, seed=args.seed)
        print(f"  [+] Generated: {path}")
        if args.stats:
            seq = gen.generate_sequence(args.weapon, seed=args.seed)
            gen.print_sequence_stats(args.weapon, seq)
    
    print(f"\n  Done. Output: {gen.output_dir}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
