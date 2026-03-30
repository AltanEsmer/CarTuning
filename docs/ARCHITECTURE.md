# CarTuning — System Architecture

> **Python-based recoil compensation macro generator for Rust (the game).**
> For offline/training use only.

---

## 1. System Overview

CarTuning takes **JSON weapon profiles** as input, processes them through a **humanization engine**, and outputs **Synapse-compatible macro configurations**.

### Core Philosophy

Perfect recoil compensation is detectable. Humanized compensation that mimics real hand movement is not. Every output value carries intentional imperfection — variance in timing, magnitude, and behavior — modeled after how a skilled human actually controls recoil.

### High-Level Flow

```
JSON Weapon Profile ──► Generator Engine ──► Humanizer Engine ──► Synapse Macro Output
                                                                       │
                                                                       ▼
                                                              (Optional) Visualizer
```

---

## 2. Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CarTuning System                           │
├───────────────┬────────────────┬────────────────┬───────────────────┤
│  Weapon       │   Generator    │  Humanizer     │   Output          │
│  Profiles     │   Engine       │  Engine        │   Layer           │
│  (JSON)       │                │                │   (Synapse)       │
├───────────────┼────────────────┼────────────────┼───────────────────┤
│ ak47.json     │ Reads weapon   │ Delay var.     │ Macro file        │
│ lr300.json    │ profiles,      │ Pull var.      │ generation        │
│ m249.json     │ calculates     │ Skip prob.     │ with proper       │
│ mp5.json      │ per-shot       │ Over-correct   │ Synapse           │
│ custom.json   │ compensation   │ Staged         │ formatting        │
│ thompson.json │ values         │ falloff        │                   │
└───────────────┴────────────────┴────────────────┴───────────────────┘
        │                │                │                 │
        ▼                ▼                ▼                 ▼
   src/weapons/    src/generator.py  src/humanizer.py   src/output.py
```

### A. Weapon Profile Layer — `src/weapons/*.json`

Each weapon is defined as a standalone JSON file containing raw recoil data. Weapons are **data, not code** — adding a new weapon means adding a new JSON file with zero code changes.

#### Schema

| Field                  | Type     | Description                                        |
|------------------------|----------|----------------------------------------------------|
| `weapon_name`          | `string` | Display name of the weapon                         |
| `shots_per_mag`        | `int`    | Magazine capacity (determines sequence length)     |
| `total_pull_distance_px` | `float`| Total vertical recoil distance in pixels           |
| `dpi`                  | `int`    | Reference DPI the profile was recorded at          |
| `curve_shape`          | `string` | Recoil curve type (`linear`, `exponential`, `staged`) |
| `sections`             | `array`  | Per-section breakdown of recoil behavior           |

#### Section Object

| Field        | Type    | Description                                         |
|--------------|---------|-----------------------------------------------------|
| `shot_start` | `int`   | First shot index in this section (0-based)          |
| `shot_end`   | `int`   | Last shot index in this section (inclusive)          |
| `pull_y_px`  | `float` | Vertical pull compensation per shot (pixels)        |
| `drift_x_px` | `float` | Horizontal drift compensation per shot (pixels)     |

#### Example — AK-47 Profile (`src/weapons/ak47.json`)

```json
{
  "weapon_name": "AK-47",
  "shots_per_mag": 30,
  "total_pull_distance_px": 420.0,
  "dpi": 800,
  "curve_shape": "staged",
  "sections": [
    {
      "shot_start": 0,
      "shot_end": 9,
      "pull_y_px": 12.0,
      "drift_x_px": 0.5
    },
    {
      "shot_start": 10,
      "shot_end": 19,
      "pull_y_px": 15.5,
      "drift_x_px": -1.2
    },
    {
      "shot_start": 20,
      "shot_end": 29,
      "pull_y_px": 18.0,
      "drift_x_px": 2.0
    }
  ]
}
```

---

### B. Generator Engine — `src/generator.py`

The generator is the orchestrator. It loads a weapon profile, calculates base compensation values, delegates humanization, and assembles the final macro sequence.

#### Core Class: `MacroGenerator`

| Method                  | Responsibility                                                      |
|-------------------------|---------------------------------------------------------------------|
| `load_profile(path)`    | Parses JSON weapon file, validates schema, returns profile dict     |
| `calculate_base_values()` | Iterates over sections, computes per-shot Y and X compensation    |
| `generate_sequence()`   | Orchestrates full pipeline: base values → humanizer → output        |
| `export(format)`        | Delegates to the output layer for final file generation             |

#### DPI Scaling

All weapon profiles are recorded at a reference DPI. The generator applies a scaling factor at calculation time:

```
scaling_factor = reference_dpi / target_dpi
adjusted_pull  = base_pull * scaling_factor
```

This ensures a profile recorded at 800 DPI works correctly at 400 or 1600 DPI without re-profiling.

#### Per-Shot Calculation

For each shot `i` in the magazine:

1. Determine which section shot `i` belongs to
2. Read `pull_y_px` and `drift_x_px` from that section
3. Apply DPI scaling
4. Store as `(shot_index, delay_ms, move_y, move_x)`

The raw sequence is an ordered list of these tuples, one per shot.

---

### C. Humanization Engine — `src/humanizer.py`

The humanizer is the core differentiator. It takes mechanically perfect per-shot values and injects realistic imperfection at every level.

#### Core Class: `Humanizer`

| Method                    | Responsibility                                                    |
|---------------------------|-------------------------------------------------------------------|
| `apply_delay_variance()`  | Jitters inter-shot delay within a configured range                |
| `apply_pull_variance()`   | Adds per-shot noise to pull magnitude                             |
| `apply_skip()`            | Probabilistically skips compensation on a shot                    |
| `apply_overcorrection()`  | Probabilistically overshoots pull on a shot                       |
| `apply_falloff()`         | Applies staged efficiency decay across the magazine               |
| `humanize_sequence()`     | Runs all humanization passes on a raw shot sequence               |

#### Humanization Parameters

| Parameter                | Range       | Description                                              |
|--------------------------|-------------|----------------------------------------------------------|
| `delay_variance_ms`      | ±8–12 ms   | Random jitter added to each inter-shot delay             |
| `pull_variance_px`       | ±0.5–1.5 px| Random noise added to each pull magnitude                |
| `skip_probability`       | 2–5%        | Chance that compensation is skipped entirely for a shot  |
| `overcorrect_probability`| 1–3%        | Chance that a shot's pull is overshot                     |
| `overcorrect_magnitude`  | ~20%        | How much extra pull is applied on an overcorrection      |
| `falloff_stages`         | 100% → 95% → 85–90% | Efficiency multiplier applied in magazine thirds |

#### Humanization Pipeline (per shot)

```
Raw shot value
  │
  ├──► apply_delay_variance()      ── jitter timing
  ├──► apply_pull_variance()       ── jitter magnitude
  ├──► apply_skip()                ── maybe drop this shot
  ├──► apply_overcorrection()      ── maybe overshoot
  └──► apply_falloff()             ── fatigue multiplier based on position
  │
  ▼
Humanized shot value
```

Each pass operates **independently per shot**. There is no correlation between adjacent shots — this is intentional. Correlated noise creates detectable patterns; independent noise does not.

#### Falloff Stages

Falloff simulates the natural decline in a player's compensation accuracy as a spray progresses:

| Magazine Position | Stage    | Efficiency Multiplier |
|-------------------|----------|-----------------------|
| Shots 1–⅓        | Early    | 100%                  |
| Shots ⅓–⅔        | Mid      | 95%                   |
| Shots ⅔–end      | Late     | 85–90%                |

This is **not random noise** — it is a structured decay that mirrors how real players lose fine motor control during sustained fire.

---

### D. Output Layer — `src/output.py`

The output layer translates the humanized shot sequence into Synapse macro syntax.

#### Synapse Macro Format

Synapse macros operate as a sequence of commands executed in order while the activation button is held. The output layer generates:

| Command Type       | Synapse Syntax                    | Description                          |
|--------------------|-----------------------------------|--------------------------------------|
| Delay              | `Delay <ms>`                      | Wait between shots                   |
| Relative Mouse Move| `MouseMove <x>, <y>`             | Move mouse by relative pixel offset  |
| Loop Structure     | Wrapped in activation block       | Repeats while button is held         |

#### Output Structure

```
Activation: While Button Held
───────────────────────────────
Delay 68
MouseMove 0, 12
Delay 74
MouseMove 1, 15
Delay 61
MouseMove -1, 16
...
(repeats for each shot in magazine)
```

Each shot maps to a `Delay` + `MouseMove` pair. The activation mode is "While Button Held" — the macro runs continuously as long as the fire button is pressed and stops when released.

---

## 3. Data Flow

```
                    ┌──────────────────┐
                    │  User selects    │
                    │  weapon          │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
         1.   │  Load JSON weapon profile    │
              │  (src/weapons/<weapon>.json) │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
         2.   │  Generator calculates base   │
              │  per-shot pull values (Y, X) │
              │  per section + DPI scaling   │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
         3.   │  Humanizer applies variance  │
              │  to each shot independently  │
              │  (delay, pull, skip, etc.)   │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
         4.   │  Staged falloff applied      │
              │  based on shot position in   │
              │  magazine (100/95/85-90%)    │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
         5.   │  Output layer formats into   │
              │  Synapse macro commands      │
              │  (Delay + MouseMove pairs)   │
              └──────────────┬───────────────┘
                             │
                     ┌───────┴────────┐
                     ▼                ▼
          ┌──────────────┐  ┌──────────────────┐
     6.   │ .macro file  │  │ Visualizer plots │
          │ (Synapse)    │  │ pattern (opt.)   │
          └──────────────┘  └──────────────────┘
```

### Step-by-Step

1. **Profile Selection** — User specifies a weapon (e.g., `ak47`). The generator resolves `src/weapons/ak47.json` and parses it.
2. **Base Calculation** — The generator walks each section, extracting per-shot `pull_y_px` and `drift_x_px`, then applies DPI scaling to produce raw compensation tuples.
3. **Humanization** — Each shot tuple is passed through the humanizer independently. Delay jitter, pull noise, skip rolls, and overcorrection rolls are applied.
4. **Falloff** — A position-dependent efficiency multiplier reduces compensation magnitude in later portions of the magazine.
5. **Formatting** — The output layer converts each humanized tuple into a `Delay` + `MouseMove` command pair in Synapse syntax.
6. **Validation (Optional)** — A matplotlib-based visualizer can render the final compensation pattern as a 2D plot for manual inspection before deployment.

---

## 4. Design Principles

### Imperfection by Design

Every value in the output carries a variance range. There are no fixed delays, no fixed pull magnitudes, no perfectly repeatable sequences. This is not a limitation — it is the entire point. Anti-cheat systems detect mechanical precision. Human-like imperfection is the camouflage.

### Modularity

Weapons are data files, not code. The system knows nothing about an AK-47 that isn't in `ak47.json`. Adding a new weapon requires:

1. Create `src/weapons/<weapon>.json`
2. Fill in the recoil profile
3. Done — no code changes, no recompilation, no config rewiring

### Transparency

All humanization parameters are exposed and configurable. Nothing is buried in a magic constant deep in the codebase. Users can tune:

- How much timing jitter is acceptable
- How much pull noise to inject
- How often to skip or overcorrect
- How aggressive fatigue falloff should be

### Validation-First

The system includes a visualizer to plot compensation patterns before they are ever deployed. This allows:

- Visual confirmation that the pattern matches the weapon's recoil
- Inspection of humanization spread (too tight = detectable, too loose = ineffective)
- Side-by-side comparison of raw vs. humanized patterns

---

## 5. Tech Stack

| Component        | Technology       | Purpose                                            |
|------------------|------------------|----------------------------------------------------|
| Core Language    | Python 3.10+     | Generator, humanizer, and output logic             |
| Math / Variance  | NumPy            | Random distributions, variance calculations        |
| Visualization    | Matplotlib       | 2D spray pattern plotting and validation           |
| Weapon Data      | JSON             | Human-readable, version-controllable weapon profiles |

### Why These Choices

- **Python** — Fast iteration, readable code, rich ecosystem for math and visualization. Performance is not a constraint (macros are generated offline, not in real-time).
- **NumPy** — Provides proper random distributions (normal, uniform) rather than relying on `random.random()`. Critical for generating statistically realistic variance.
- **Matplotlib** — De facto standard for 2D plotting in Python. Enables quick visual validation without external tools.
- **JSON** — Zero-dependency format. Every language and every editor can read it. Diffs cleanly in version control. No need for YAML's complexity or TOML's syntax.

---

## 6. Key Design Decisions

### JSON over YAML/TOML

| Factor         | JSON         | YAML              | TOML              |
|----------------|--------------|--------------------|--------------------|
| Dependencies   | None (stdlib)| Requires `PyYAML`  | Requires `tomli`   |
| Parse safety   | Safe         | Arbitrary code exec risk | Safe          |
| Readability    | Good         | Better             | Good               |
| Universality   | Everywhere   | Common             | Growing            |
| Diff-friendly  | Yes          | Whitespace-sensitive | Yes              |

JSON wins on **simplicity and zero dependencies**. Weapon profiles are flat enough that YAML's nesting advantages don't matter.

### Humanization as a Separate Engine

The humanizer is intentionally decoupled from the generator. This separation means:

- Weapon profiles can be updated without retesting humanization logic
- Humanization parameters can be tuned without touching weapon data
- The humanizer can be unit-tested in isolation with synthetic data
- Different humanization presets can be swapped without changing the pipeline

### Per-Shot Independence

Each shot's humanization (delay jitter, pull noise, skip, overcorrect) is rolled **independently** using separate random draws. There is no sliding window, no moving average, no shot-to-shot correlation.

**Why this matters:** Correlated noise produces detectable statistical signatures. If shot N's delay predicts shot N+1's delay, that pattern is discoverable. Independent rolls produce output that is statistically indistinguishable from genuine human variance.

### Staged Falloff ≠ Random Noise

Falloff is a **structured, deterministic decay** — not another layer of randomness. It models a specific human behavior: grip fatigue during sustained automatic fire. Early shots are compensated near-perfectly; late shots drift.

This is distinct from pull variance (which is random noise). Falloff provides the macro shape; variance provides the texture. Together, they produce output that looks and feels like a real player who is good — but not perfect — at spray control.

---

## Directory Structure

```
CarTuning/
├── docs/
│   ├── start.md
│   └── ARCHITECTURE.md        ← you are here
├── src/
│   ├── generator.py           ← macro generation engine
│   ├── humanizer.py           ← humanization engine
│   ├── output.py              ← Synapse macro formatter
│   ├── visualizer.py          ← pattern plotting (optional)
│   └── weapons/
│       ├── ak47.json
│       ├── lr300.json
│       ├── m249.json
│       ├── mp5.json
│       ├── thompson.json
│       └── custom.json        ← user-defined profiles
├── LICENSE
└── README.md
```
