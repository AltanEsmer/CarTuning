# Copilot Instructions

## Project Overview

CarTuning is a Python-based recoil compensation macro generator for the game Rust. It converts JSON weapon profiles into Synapse-compatible `.txt` macro files with a probabilistic humanization layer that simulates realistic hand imperfection (delay jitter, pull variance, skip events, overcorrections, staged fatigue falloff).

## Commands

```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_generator.py -v

# Run a single test by name
pytest tests/test_generator.py -k "test_load_ak47" -v

# Run a specific test class
pytest tests/test_generator.py::TestMacroGeneratorProfileLoading -v

# Generate a macro
python src/generator.py --weapon ak47
python src/generator.py --weapon ak47 --dpi 1600
python src/generator.py --weapon ak47 --seed 42   # deterministic output
python src/generator.py --all                      # all weapons

# Visualize spray patterns
python tests/visualizer.py --weapon ak47 --type single
python tests/visualizer.py --weapon ak47 --type overlay --sprays 10
python tests/visualizer.py --weapon all --type all

# Install dependencies
pip install pytest numpy matplotlib pynput
```

## Architecture

The pipeline has four stages:

1. **Profile loading** — `generator.py` reads `src/weapons/<weapon>.json` into a `WeaponProfile` dataclass
2. **Base calculation** — Per-shot `pull_y` and `drift_x` values are computed from the profile's `sections` array, scaled by `reference_dpi / target_dpi`
3. **Humanization** — `humanizer.py` applies independent per-shot variance (Gaussian delay, uniform pull/drift, skip rolls, overcorrect rolls, staged falloff multiplier)
4. **Synapse formatting** — Humanized `ShotData` list is serialized to `Delay + MouseMove` pairs and written to `src/output/RECOIL_<WEAPON>.txt`

`tests/visualizer.py` and `tools/mouse_logger.py` are validation-only tools, not part of the generation pipeline.

## Key Conventions

**Weapon profiles** live in `src/weapons/*.json` and are the only place recoil data is defined. Each profile has:
- `sections[]` — shot ranges with `pull_y_per_shot`, `drift_x_per_shot`, and `compensation_pct`
- `humanization{}` — variance parameters that map directly to `HumanizationConfig` fields
- `special_variance{}` (optional) — weapon-specific quirks (e.g., Y-spike events for Custom SMG)

**Output filenames** follow screaming snake case: `RECOIL_AK47.txt`, `RECOIL_CUSTOM_SMG.txt`.

**DPI scaling** is always `dpi_scale = reference_dpi / target_dpi` (reference DPI is always 800).

**Per-shot independence** is a core invariant of the humanizer — no shot's variance depends on a previous shot. Do not introduce windowing, smoothing, or correlation between shots.

**`HumanizationConfig.from_dict()`** is the factory for constructing humanization config from a weapon JSON's `humanization` block. When adding new variance parameters, add them here first.

**Optional imports** for `matplotlib` and `pynput` are wrapped in `try/except` with graceful error messages — maintain this pattern if adding other optional dependencies.

**Reproducibility** is supported via an optional `seed` parameter throughout the pipeline. Preserve this in any new generation code.

## Data Models

```python
WeaponProfile   # loaded from JSON; fields: name, shots_per_mag, sections, humanization, special_variance, ...
ShotData        # per-shot output: shot_number, delay_ms, pull_y, drift_x, is_skipped, is_overcorrected, falloff_multiplier
HumanizationConfig  # variance parameters; constructed via from_dict(weapon_json["humanization"])
```
