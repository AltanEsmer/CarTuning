"""
CarTuning Live Runner
=====================
Interactive launcher for the Interception kernel-driver live playback system.

Run from the project root:
    python run.py
    python run.py --weapon ak47 --dpi 800

Setup (run once on a new PC):
    1. Install Python 3.8+ from https://python.org  (check "Add to PATH")
    2. Open Command Prompt as Administrator and run:
           pip install -r requirements.txt
    3. Install the Interception kernel driver:
       a. Download from https://github.com/oblitum/Interception/releases
       b. Run install-interception.exe as Administrator
       c. Reboot the PC
    4. Run this script: python run.py

Detectability notes:
    EAC  (Rust)      - BLOCKED  : EAC detects interception.sys at launch, game won't start.
                                   Humanization does NOT help — it's a driver-presence check.
    VAC  (CS2)       - WORKS    : VAC does not scan kernel drivers.
                                   Humanization protects against behavioral replay detection.
    BattlEye (R6)    - UNCERTAIN: Depends on BattlEye version; may block the driver.
    No anticheat /
    training servers - WORKS    : Fully functional. This is the intended educational use-case.
"""

import sys
import os
import argparse

# ---------------------------------------------------------------------------
# Path setup — must happen before any src/ imports
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
_MISSING = []

try:
    import interception  # noqa: F401
    _INTERCEPTION_OK = True
except ImportError:
    _INTERCEPTION_OK = False
    _MISSING.append("interception-python")

try:
    import pynput  # noqa: F401
    _PYNPUT_OK = True
except ImportError:
    _PYNPUT_OK = False
    _MISSING.append("pynput")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRIVER_INSTALL_GUIDE = """
  ┌─────────────────────────────────────────────────────────────────────┐
  │          Interception Driver — One-Time Setup (Windows 10)          │
  ├─────────────────────────────────────────────────────────────────────┤
  │  Step 1: Install Python packages (run in Command Prompt):           │
  │          pip install -r requirements.txt                            │
  │                                                                     │
  │  Step 2: Download the Interception driver installer:                │
  │          https://github.com/oblitum/Interception/releases           │
  │          → download install-interception.exe                        │
  │                                                                     │
  │  Step 3: Run install-interception.exe as Administrator              │
  │          (right-click → Run as administrator)                       │
  │                                                                     │
  │  Step 4: REBOOT the PC                                              │
  │                                                                     │
  │  Step 5: Run this script again: python run.py                       │
  └─────────────────────────────────────────────────────────────────────┘
"""


def _separator():
    print("=" * 60)


def _print_banner():
    _separator()
    print("  CarTuning — Live Interception Launcher")
    _separator()


def _check_dependencies():
    """Warn about missing packages; abort if Interception is missing."""
    if not _PYNPUT_OK:
        print("\n  [!] pynput is not installed.")
        print("      Hold mode will be unavailable (single-play only).")
        print("      Fix: pip install pynput\n")

    if not _INTERCEPTION_OK:
        print("\n  [!] interception-python is NOT installed.")
        print("      This package requires the Interception kernel driver.")
        print(DRIVER_INSTALL_GUIDE)
        sys.exit(1)


def _pick_weapon(gen) -> str:
    """Interactively pick a weapon from available profiles."""
    weapons = sorted(gen.list_weapons())
    print("\n  Available weapons:")
    for i, w in enumerate(weapons, 1):
        print(f"    {i}. {w}")
    print()

    while True:
        raw = input("  Enter weapon name or number: ").strip().lower()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(weapons):
                return weapons[idx]
            print(f"  [!] Number must be between 1 and {len(weapons)}.")
        elif raw in weapons:
            return raw
        else:
            print(f"  [!] Unknown weapon '{raw}'. Try again.")


def _pick_dpi() -> int:
    """Interactively pick a DPI value."""
    print("\n  Common DPI values: 400, 800 (default), 1200, 1600")
    raw = input("  Enter your DPI [800]: ").strip()
    if not raw:
        return 800
    try:
        dpi = int(raw)
        if dpi <= 0:
            raise ValueError
        return dpi
    except ValueError:
        print("  [!] Invalid DPI — using 800.")
        return 800


def _pick_hold_mode() -> bool:
    """Interactively pick hold vs single-play mode."""
    print("\n  Playback mode:")
    print("    1. Hold mode  — loops while left mouse button is held (default)")
    print("    2. Single     — plays the sequence once and exits")
    raw = input("  Choose [1]: ").strip()
    return raw != "2"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CarTuning live interception launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--weapon", "-w", help="Weapon name (skip menu)")
    parser.add_argument("--dpi", "-d", type=int, help="Target DPI (skip prompt)")
    parser.add_argument(
        "--no-hold",
        action="store_true",
        help="Single-play mode instead of hold mode",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=None,
        help="Random seed for reproducible sequence (debugging)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print sequence statistics before playing",
    )
    args = parser.parse_args()

    _print_banner()
    _check_dependencies()

    # Import after path setup and dependency check
    from generator import MacroGenerator
    from executor import InterceptionExecutor

    # Resolve weapon, DPI, and hold mode interactively if not provided via CLI
    gen_default = MacroGenerator()  # used only for listing weapons
    weapon = args.weapon or _pick_weapon(gen_default)
    dpi = args.dpi or _pick_dpi()
    hold_mode = (not args.no_hold) if args.no_hold else _pick_hold_mode()

    gen = MacroGenerator(dpi=dpi)

    # Generate sequence
    print(f"\n  Generating humanized sequence: {weapon.upper()} @ {dpi} DPI")
    try:
        sequence = gen.generate_sequence(weapon, seed=args.seed)
    except FileNotFoundError as e:
        print(f"\n  [!] {e}")
        sys.exit(1)

    if args.stats:
        gen.print_sequence_stats(weapon, sequence)

    _separator()
    print(f"  Weapon  : {weapon.upper()}")
    print(f"  DPI     : {dpi}")
    print(f"  Mode    : {'Hold (loop while LMB held)' if hold_mode else 'Single play'}")
    print(f"  Shots   : {len(sequence)}")
    print(f"  Abort   : Press F8 at any time")
    _separator()

    # Launch
    executor = InterceptionExecutor()
    executor.play(sequence, hold_mode=hold_mode)


if __name__ == "__main__":
    main()
