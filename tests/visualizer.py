"""
CarTuning Pattern Visualizer
Generates scatter plots, overlays, and histograms to validate
macro humanization quality.
"""

import sys
import os
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generator import MacroGenerator
from humanizer import ShotData

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for file output
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[!] matplotlib not installed. Install with: pip install matplotlib")

import numpy as np
from typing import List


class PatternVisualizer:
    """Visualizes macro spray patterns for validation."""
    
    def __init__(self, generator: MacroGenerator, output_dir: str = None):
        self.generator = generator
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), '..', 'src', 'output', 'plots'
        )
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _sequence_to_coords(self, sequence: List[ShotData]):
        """Convert a shot sequence to cumulative X/Y coordinates."""
        x_coords = [0.0]
        y_coords = [0.0]
        for shot in sequence:
            x_coords.append(x_coords[-1] + shot.drift_x)
            y_coords.append(y_coords[-1] + shot.pull_y)
        return x_coords, y_coords
    
    def plot_single_spray(self, weapon_name: str, save: bool = True) -> str:
        """
        Plot a single spray pattern as a scatter plot.
        Shows the X/Y trajectory of one full magazine spray.
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        sequence = self.generator.generate_sequence(weapon_name)
        x, y = self._sequence_to_coords(sequence)
        
        fig, ax = plt.subplots(figsize=(8, 10))
        
        # Plot trajectory line (faded)
        ax.plot(x, y, 'b-', alpha=0.2, linewidth=1)
        
        # Plot shot points with color gradient (shot number)
        scatter = ax.scatter(x[1:], y[1:], c=range(len(sequence)),
                           cmap='plasma', s=40, zorder=5, edgecolors='black', linewidth=0.5)
        
        # Mark skipped shots
        for i, shot in enumerate(sequence):
            if shot.is_skipped:
                ax.scatter(x[i+1], y[i+1], c='red', s=100, marker='x', zorder=6)
            if shot.is_overcorrected:
                ax.scatter(x[i+1], y[i+1], c='orange', s=80, marker='^', zorder=6)
        
        ax.set_title(f"CarTuning — {weapon_name.upper()} Single Spray Pattern", fontsize=14, fontweight='bold')
        ax.set_xlabel("X Drift (px)")
        ax.set_ylabel("Y Pull (px, cumulative)")
        ax.invert_yaxis()  # Invert Y so "down" pull goes down visually
        ax.grid(True, alpha=0.3)
        ax.legend(['Trajectory', 'Shots'], loc='upper right')
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Shot Number')
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{weapon_name}_single.png")
            fig.savefig(filepath, dpi=150)
            plt.close(fig)
            return filepath
        else:
            plt.show()
            return ""
    
    def plot_multi_spray_overlay(self, weapon_name: str, count: int = 10, save: bool = True) -> str:
        """
        Overlay multiple spray patterns to show variance between runs.
        Good sprays = a CLOUD, not overlapping lines.
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        fig, ax = plt.subplots(figsize=(8, 10))
        colors = plt.cm.tab10(np.linspace(0, 1, count))
        
        for i in range(count):
            sequence = self.generator.generate_sequence(weapon_name)
            x, y = self._sequence_to_coords(sequence)
            ax.plot(x, y, color=colors[i], alpha=0.4, linewidth=1)
            ax.scatter(x[1:], y[1:], color=colors[i], s=15, alpha=0.5)
        
        ax.set_title(f"CarTuning — {weapon_name.upper()} {count}-Spray Overlay", fontsize=14, fontweight='bold')
        ax.set_xlabel("X Drift (px)")
        ax.set_ylabel("Y Pull (px, cumulative)")
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{weapon_name}_overlay_{count}.png")
            fig.savefig(filepath, dpi=150)
            plt.close(fig)
            return filepath
        else:
            plt.show()
            return ""
    
    def plot_delay_histogram(self, weapon_name: str, spray_count: int = 50, save: bool = True) -> str:
        """
        Plot histogram of delays across many sprays.
        Should look like a Gaussian bell curve.
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        all_delays = []
        for _ in range(spray_count):
            sequence = self.generator.generate_sequence(weapon_name)
            all_delays.extend([s.delay_ms for s in sequence])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(all_delays, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        
        mean_delay = np.mean(all_delays)
        std_delay = np.std(all_delays)
        ax.axvline(mean_delay, color='red', linestyle='--', label=f'Mean: {mean_delay:.1f}ms')
        ax.axvline(mean_delay - std_delay, color='orange', linestyle=':', alpha=0.7, label=f'Std: ±{std_delay:.1f}ms')
        ax.axvline(mean_delay + std_delay, color='orange', linestyle=':', alpha=0.7)
        
        ax.set_title(f"CarTuning — {weapon_name.upper()} Delay Distribution ({spray_count} sprays)", fontsize=14, fontweight='bold')
        ax.set_xlabel("Delay (ms)")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{weapon_name}_delays.png")
            fig.savefig(filepath, dpi=150)
            plt.close(fig)
            return filepath
        else:
            plt.show()
            return ""
    
    def plot_comparison(self, weapon_name: str, save: bool = True) -> str:
        """
        Side-by-side: raw (no humanization) vs humanized pattern.
        Shows the effect of the humanization engine.
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        from humanizer import Humanizer, HumanizationConfig
        
        profile = self.generator.load_profile(weapon_name)
        base_values = self.generator.calculate_base_values(profile)
        
        # Raw sequence (minimal humanization)
        no_human_config = HumanizationConfig(
            delay_variance_ms=0, pull_variance_px=0, x_variance_px=0,
            skip_probability=0, overcorrect_probability=0, overcorrect_magnitude=1.0,
            falloff_stages=profile.humanization.get('falloff_stages', [])
        )
        raw_humanizer = Humanizer(no_human_config, seed=42)
        raw_sequence = raw_humanizer.humanize_sequence(base_values)
        
        # Humanized sequence
        humanized_sequence = self.generator.generate_sequence(weapon_name)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
        
        # Raw
        rx, ry = self._sequence_to_coords(raw_sequence)
        ax1.plot(rx, ry, 'b-', alpha=0.5)
        ax1.scatter(rx[1:], ry[1:], c='blue', s=30, zorder=5)
        ax1.set_title("Raw (No Humanization)", fontsize=12, fontweight='bold')
        ax1.set_xlabel("X Drift (px)")
        ax1.set_ylabel("Y Pull (px)")
        ax1.invert_yaxis()
        ax1.grid(True, alpha=0.3)
        
        # Humanized
        hx, hy = self._sequence_to_coords(humanized_sequence)
        ax2.plot(hx, hy, 'r-', alpha=0.3)
        ax2.scatter(hx[1:], hy[1:], c='red', s=30, zorder=5)
        ax2.set_title("Humanized", fontsize=12, fontweight='bold')
        ax2.set_xlabel("X Drift (px)")
        ax2.set_ylabel("Y Pull (px)")
        ax2.invert_yaxis()
        ax2.grid(True, alpha=0.3)
        
        fig.suptitle(f"CarTuning — {weapon_name.upper()} Raw vs Humanized", fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{weapon_name}_comparison.png")
            fig.savefig(filepath, dpi=150)
            plt.close(fig)
            return filepath
        else:
            plt.show()
            return ""
    
    def generate_full_report(self, weapon_name: str) -> List[str]:
        """Generate all visualization plots for a weapon."""
        paths = []
        print(f"\n  Generating visual report for {weapon_name.upper()}...")
        
        path = self.plot_single_spray(weapon_name)
        if path: paths.append(path); print(f"    [+] Single spray: {path}")
        
        path = self.plot_multi_spray_overlay(weapon_name)
        if path: paths.append(path); print(f"    [+] Multi overlay: {path}")
        
        path = self.plot_delay_histogram(weapon_name)
        if path: paths.append(path); print(f"    [+] Delay histogram: {path}")
        
        path = self.plot_comparison(weapon_name)
        if path: paths.append(path); print(f"    [+] Comparison: {path}")
        
        return paths
    
    def generate_all_reports(self) -> dict:
        """Generate full reports for all available weapons."""
        results = {}
        for weapon in self.generator.list_weapons():
            results[weapon] = self.generate_full_report(weapon)
        return results


def main():
    parser = argparse.ArgumentParser(description="CarTuning Pattern Visualizer")
    parser.add_argument('--weapon', '-w', default='all', help='Weapon name or "all"')
    parser.add_argument('--dpi', '-d', type=int, default=800, help='Target DPI')
    parser.add_argument('--output', '-o', default=None, help='Output directory for plots')
    parser.add_argument('--sprays', '-n', type=int, default=10, help='Number of sprays for overlay')
    parser.add_argument('--type', '-t', choices=['single', 'overlay', 'delays', 'comparison', 'all'],
                       default='all', help='Type of plot to generate')
    
    args = parser.parse_args()
    
    if not HAS_MATPLOTLIB:
        print("[!] Cannot generate plots without matplotlib.")
        print("    Install with: pip install matplotlib numpy")
        sys.exit(1)
    
    gen = MacroGenerator(dpi=args.dpi)
    viz = PatternVisualizer(gen, output_dir=args.output)
    
    print(f"\n{'='*50}")
    print(f"  CarTuning Pattern Visualizer")
    print(f"  DPI: {args.dpi}")
    print(f"{'='*50}")
    
    weapons = [args.weapon] if args.weapon != 'all' else gen.list_weapons()
    
    for weapon in weapons:
        if args.type == 'all':
            viz.generate_full_report(weapon)
        elif args.type == 'single':
            path = viz.plot_single_spray(weapon)
            print(f"  [+] {path}")
        elif args.type == 'overlay':
            path = viz.plot_multi_spray_overlay(weapon, count=args.sprays)
            print(f"  [+] {path}")
        elif args.type == 'delays':
            path = viz.plot_delay_histogram(weapon)
            print(f"  [+] {path}")
        elif args.type == 'comparison':
            path = viz.plot_comparison(weapon)
            print(f"  [+] {path}")
    
    print(f"\n  Done. Plots saved to: {viz.output_dir}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
