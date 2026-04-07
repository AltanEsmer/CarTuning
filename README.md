# 🎯 CarTuning

**Precision recoil compensation, engineered to feel human.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![Synapse](https://img.shields.io/badge/Output-Synapse--Ready-blueviolet?style=flat-square)

---

## Overview

CarTuning is a Python macro generator that transforms raw weapon recoil data (stored as JSON profiles) into humanized, Synapse-compatible macro configurations for Rust.

Feed it a weapon profile. Get back a macro that doesn't move like a robot.

The core innovation is the **humanization engine** — a probabilistic layer that injects realistic imperfection into every generated pattern. Micro-tremor, variable overshoot, delay variance, staged falloff — the kind of noise that makes a macro indistinguishable from a steady hand. Every output is slightly different, because real hands never repeat the same pull twice.

## Features

- **7 weapon profiles** — AK-47, LR-300, M249, MP5, Custom SMG, Thompson, R4-C (R6 Siege X), CS2 AK-47
- **Probabilistic humanization engine** — delay variance, pull variance, skip probability, over-correction simulation
- **Staged falloff** — shot fatigue modeling that degrades compensation naturally over sustained fire
- **Synapse-ready output** — `.rzn` (Synapse 4 import) + `.txt` (human-readable reference)
- **Live playback via Interception** — kernel-level HID injection that reaches CS2's raw input pipeline (`--live`)
- **Pattern visualization & validation** — plot generated patterns against raw recoil data with Matplotlib
- **JSON-based weapon profiles** — dead simple to edit, extend, or build your own

## Project Structure

```
CarTuning/
├── README.md
├── LICENSE
├── start.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── WEAPON_DATA.md
│   ├── HUMANIZATION.md
│   ├── TESTING.md
│   └── DEPLOYMENT.md
├── src/
│   ├── generator.py
│   ├── humanizer.py
│   ├── executor.py          ← Interception live playback
│   ├── weapons/
│   │   ├── ak47.json
│   │   ├── cs2_ak47.json
│   │   ├── lr300.json
│   │   ├── m249.json
│   │   ├── mp5.json
│   │   ├── custom_smg.json
│   │   ├── thompson.json
│   │   └── r6x_r4c.json
│   └── output/
├── tests/
│   ├── test_generator.py
│   ├── test_humanizer.py
│   ├── test_executor.py
│   └── visualizer.py
└── tools/
    └── mouse_logger.py
```

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-username/CarTuning.git
cd CarTuning

# Install dependencies
pip install -r requirements.txt

# Generate a macro for the AK-47 (Synapse .rzn export)
python src/generator.py --weapon ak47

# Live playback in CS2 via Interception (see Live Playback section below)
python src/generator.py --weapon cs2_ak47 --live

# Visualize the humanized pattern vs raw recoil
python tests/visualizer.py --weapon ak47

# Generate all weapon macros at once
python src/generator.py --all
```

Generated configs land in `src/output/` — ready to load into Synapse.

## Live Playback (Interception)

Standard `SendInput` is invisible to games using raw input (CS2, R6). The **Interception driver** sits inside the HID stack — its events appear in `WM_INPUT` as real hardware input.

### Setup

1. **Install the Interception driver** (system-level, requires reboot):
   ```
   https://github.com/oblitum/Interception
   ```
   Run the installer as Administrator, reboot.

2. **Install the Python wrapper:**
   ```bash
   pip install interception-python
   ```

### Usage

```bash
# Hold-to-fire mode (default): hold left mouse, macro plays, release to stop
python src/generator.py --weapon cs2_ak47 --live

# Single-play mode: fires once through the sequence
python src/generator.py --weapon cs2_ak47 --live --no-hold

# With DPI scaling
python src/generator.py --weapon cs2_ak47 --live --dpi 1600

# Press F8 at any time to abort live playback
```

### Game Compatibility

| Game | Anti-Cheat | Interception Works? | Notes |
|------|-----------|---------------------|-------|
| **CS2** | VAC | ✅ Yes | VAC doesn't block the driver |
| **R6 Siege** | BattlEye | 🟡 Uncertain | BattlEye detection varies |
| **Rust** | EAC | ❌ No | EAC refuses to launch with driver loaded |

## Tech Stack

| Component       | Technology          |
|-----------------|---------------------|
| Core Language   | Python 3.10+        |
| Math / RNG      | NumPy               |
| Visualization   | Matplotlib          |
| Live Input      | interception-python |
| Data Format     | JSON                |
| Output Target   | Synapse 4 `.rzn` / Interception live |

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design — how the generator, humanizer, and profile loader fit together |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Planned features and development priorities |
| [`docs/WEAPON_DATA.md`](docs/WEAPON_DATA.md) | How weapon recoil data is captured, structured, and stored |
| [`docs/HUMANIZATION.md`](docs/HUMANIZATION.md) | Deep dive into the humanization engine — the math behind realistic imperfection |
| [`docs/TESTING.md`](docs/TESTING.md) | Test strategy, validation approach, and how to run the suite |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | How to export, load, and configure generated macros in Synapse |

## Disclaimer

> **This project is intended for offline and training server use only.**
>
> CarTuning is an educational project built to explore recoil mechanics, macro engineering, and humanization algorithms. It is not designed, endorsed, or intended for use on official or competitive servers. Use responsibly and in accordance with the terms of service of any platform you interact with.

---

<p align="center">
  <em>Built with obsessive attention to the gap between perfect and plausible.</em>
</p>
