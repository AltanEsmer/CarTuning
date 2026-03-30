"""
CarTuning Mouse Movement Logger
Records mouse position and delta movements to CSV for macro validation.

Usage:
    python mouse_logger.py --duration 10 --output mouse_log.csv

Requires: pynput (pip install pynput)
"""

import csv
import time
import argparse
import os
from datetime import datetime

try:
    from pynput import mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False


class MouseLogger:
    """Records mouse movements with timestamps and deltas."""
    
    def __init__(self, output_path: str = "mouse_log.csv",
                 duration: float = 10.0, sample_rate_hz: int = 1000):
        """
        Args:
            output_path: CSV file path for output
            duration: Recording duration in seconds
            sample_rate_hz: Target sample rate (limited by OS/hardware)
        """
        self.output_path = output_path
        self.duration = duration
        self.sample_rate_hz = sample_rate_hz
        self.records = []
        self.start_time = None
        self.last_x = 0
        self.last_y = 0
        self.recording = False
    
    def _on_move(self, x, y):
        """Callback for mouse movement events."""
        if not self.recording:
            return
        
        now = time.perf_counter()
        elapsed = now - self.start_time
        
        delta_x = x - self.last_x
        delta_y = y - self.last_y
        
        self.records.append({
            'timestamp_ms': round(elapsed * 1000, 2),
            'x': x,
            'y': y,
            'delta_x': delta_x,
            'delta_y': delta_y
        })
        
        self.last_x = x
        self.last_y = y
        
        if elapsed >= self.duration:
            self.recording = False
            return False  # Stop listener
    
    def _on_click(self, x, y, button, pressed):
        """Track click events for correlation with macro activation."""
        if not self.recording:
            return
        
        now = time.perf_counter()
        elapsed = now - self.start_time
        
        event_type = f"{'press' if pressed else 'release'}_{button.name}"
        self.records.append({
            'timestamp_ms': round(elapsed * 1000, 2),
            'x': x,
            'y': y,
            'delta_x': 0,
            'delta_y': 0,
            'event': event_type
        })
    
    def record(self):
        """Start recording mouse movements."""
        if not HAS_PYNPUT:
            print("[!] pynput not installed. Install with: pip install pynput")
            print("    This is required for mouse movement recording.")
            return False
        
        print(f"\n{'='*50}")
        print(f"  CarTuning Mouse Logger")
        print(f"  Duration: {self.duration}s")
        print(f"  Output: {self.output_path}")
        print(f"{'='*50}")
        print(f"\n  Recording starts in 3 seconds...")
        print(f"  Activate your macro during recording!")
        
        time.sleep(3)
        
        print(f"\n  [REC] Recording... ({self.duration}s)")
        
        self.records = []
        self.recording = True
        self.start_time = time.perf_counter()
        
        # Get initial position
        # Note: pynput doesn't provide initial position easily,
        # so first movement will establish baseline
        self.last_x = 0
        self.last_y = 0
        
        with mouse.Listener(on_move=self._on_move, on_click=self._on_click) as listener:
            listener.join()
        
        self.recording = False
        print(f"  [STOP] Recording complete. {len(self.records)} events captured.")
        
        return True
    
    def save(self):
        """Save recorded data to CSV."""
        if not self.records:
            print("  [!] No data to save.")
            return
        
        fieldnames = ['timestamp_ms', 'x', 'y', 'delta_x', 'delta_y', 'event']
        
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                # Fill missing 'event' field for move events
                if 'event' not in record:
                    record['event'] = 'move'
                writer.writerow(record)
        
        print(f"  [+] Saved to: {self.output_path}")
        self._print_stats()
    
    def _print_stats(self):
        """Print summary statistics of the recording."""
        if not self.records:
            return
        
        moves = [r for r in self.records if r.get('event', 'move') == 'move']
        
        if len(moves) < 2:
            print("  [!] Not enough movement data for stats.")
            return
        
        total_time = moves[-1]['timestamp_ms'] - moves[0]['timestamp_ms']
        total_delta_y = sum(r['delta_y'] for r in moves)
        total_delta_x = sum(abs(r['delta_x']) for r in moves)
        avg_rate = len(moves) / (total_time / 1000) if total_time > 0 else 0
        
        # Calculate inter-movement intervals
        intervals = []
        for i in range(1, len(moves)):
            interval = moves[i]['timestamp_ms'] - moves[i-1]['timestamp_ms']
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        min_interval = min(intervals) if intervals else 0
        max_interval = max(intervals) if intervals else 0
        
        print(f"\n  Recording Stats:")
        print(f"    Total events: {len(self.records)}")
        print(f"    Move events: {len(moves)}")
        print(f"    Duration: {total_time:.1f}ms")
        print(f"    Avg sample rate: {avg_rate:.0f} Hz")
        print(f"    Total Y delta: {total_delta_y:.0f}px")
        print(f"    Total X delta (abs): {total_delta_x:.0f}px")
        print(f"    Avg interval: {avg_interval:.1f}ms")
        print(f"    Min interval: {min_interval:.1f}ms")
        print(f"    Max interval: {max_interval:.1f}ms")


def analyze_log(filepath: str):
    """Analyze a previously recorded mouse log CSV."""
    import csv
    
    print(f"\n  Analyzing: {filepath}")
    
    records = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'timestamp_ms': float(row['timestamp_ms']),
                'x': float(row['x']),
                'y': float(row['y']),
                'delta_x': float(row['delta_x']),
                'delta_y': float(row['delta_y']),
                'event': row['event']
            })
    
    moves = [r for r in records if r['event'] == 'move']
    clicks = [r for r in records if r['event'] != 'move']
    
    print(f"    Total records: {len(records)}")
    print(f"    Movements: {len(moves)}")
    print(f"    Click events: {len(clicks)}")
    
    if moves:
        deltas_y = [r['delta_y'] for r in moves]
        deltas_x = [r['delta_x'] for r in moves]
        
        print(f"    Y-axis total: {sum(deltas_y):.0f}px")
        print(f"    X-axis total (abs): {sum(abs(d) for d in deltas_x):.0f}px")
        print(f"    Y-axis avg per move: {sum(deltas_y)/len(deltas_y):.2f}px")
        print(f"    X-axis avg per move: {sum(deltas_x)/len(deltas_x):.2f}px")


def main():
    parser = argparse.ArgumentParser(description="CarTuning Mouse Movement Logger")
    parser.add_argument('--duration', '-d', type=float, default=10.0,
                       help='Recording duration in seconds (default: 10)')
    parser.add_argument('--output', '-o', default='mouse_log.csv',
                       help='Output CSV file path')
    parser.add_argument('--analyze', '-a', default=None,
                       help='Analyze an existing log file instead of recording')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_log(args.analyze)
        return
    
    logger = MouseLogger(
        output_path=args.output,
        duration=args.duration
    )
    
    if logger.record():
        logger.save()


if __name__ == '__main__':
    main()
