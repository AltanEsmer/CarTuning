# Testing & Validation Guide

Every macro must be validated before deployment. This guide covers the full validation pipeline — from unit tests to visual inspection to real-world mouse logging.

---

## 1. Testing Philosophy

Validation has two layers:

1. **Automated** — Statistical analysis to verify humanization parameters are working correctly.
2. **Visual** — Pattern visualization to pass the "smell test": would a human looking at this pattern know it's a macro?

Both layers must pass before a macro is considered deployment-ready.

---

## 2. Unit Testing

Run all unit tests with:

```bash
pytest tests/ -v
```

### 2.1 Generator Tests (`tests/test_generator.py`)

Test the macro generator in isolation.

| Test Case | What It Verifies |
|-----------|-----------------|
| **Profile loading** | All 6 weapon JSON profiles load without errors |
| **Section calculation** | Per-shot values match expected ranges for each weapon section |
| **Shot count** | Output sequence length equals `shots_per_mag` |
| **DPI scaling** | Pull values scale correctly for different DPI settings |
| **Value bounds** | No shot compensation exceeds the weapon's max pull value |
| **Reproducibility** | Same seed produces identical output (for debugging) |

Example test structure:

```python
def test_shot_count_matches_mag_size():
    """Output sequence length must equal shots_per_mag from the weapon profile."""
    profile = load_profile("ak47.json")
    sequence = generate(profile)
    assert len(sequence) == profile["shots_per_mag"]

def test_dpi_scaling():
    """Pull values at 800 DPI should be exactly 2x the values at 1600 DPI."""
    seq_800 = generate(load_profile("ak47.json"), dpi=800)
    seq_1600 = generate(load_profile("ak47.json"), dpi=1600)
    for a, b in zip(seq_800, seq_1600):
        assert abs(a.pull_y - b.pull_y * 2) < 0.01

def test_reproducibility():
    """Same seed must produce byte-identical output."""
    a = generate(load_profile("ak47.json"), seed=42)
    b = generate(load_profile("ak47.json"), seed=42)
    assert a == b
```

### 2.2 Humanizer Tests (`tests/test_humanizer.py`)

Test the humanization engine with statistical assertions.

| Test Case | Method | Tolerance |
|-----------|--------|-----------|
| **Delay variance** | 1,000 samples → compute mean delay | Within 1 ms of base delay |
| **Pull variance** | 1,000 samples → compute mean pull | Within 0.1 px of base pull |
| **Skip probability** | 10,000 shots → count skips | Within ±1% of configured probability |
| **Over-correction** | 10,000 shots → count over-corrections | Within ±0.5% of configured probability |
| **Falloff** | Inspect per-stage compensation % | Must match configured stages exactly |
| **Uniqueness** | Generate 100 sequences → compare | Zero duplicates |
| **Bounds** | Inspect every humanized value | None exceed configured maximums |

Example test structure:

```python
def test_delay_variance():
    """Mean delay over 1000 samples should be within 1ms of the base delay."""
    base_delay = 15.0  # ms
    delays = [humanize_delay(base_delay) for _ in range(1000)]
    mean = sum(delays) / len(delays)
    assert abs(mean - base_delay) < 1.0, f"Mean delay {mean:.2f} drifted from base {base_delay}"

def test_skip_probability():
    """Skip rate over 10000 shots should be within ±1% of configured probability."""
    config_skip_rate = 0.03  # 3%
    shots = [humanize_shot(base_shot, skip_rate=config_skip_rate) for _ in range(10000)]
    actual_skip_rate = sum(1 for s in shots if s.skipped) / len(shots)
    assert abs(actual_skip_rate - config_skip_rate) < 0.01

def test_uniqueness():
    """100 generated sequences should all be different."""
    sequences = [tuple(humanize_sequence(base_seq)) for _ in range(100)]
    assert len(set(sequences)) == 100, "Duplicate sequences detected — randomization is broken"
```

### 2.3 Integration Tests

End-to-end validation of the full pipeline.

- **Full pipeline**: weapon JSON → generator → humanizer → output. Verify the output is valid Synapse macro format.
- **All weapons**: Run the full pipeline for every weapon profile. Each output file must be generated and well-formed.

```python
@pytest.mark.parametrize("weapon", ["ak47", "lr300", "mp5", "m249", "thompson", "custom_smg"])
def test_full_pipeline(weapon):
    """Full pipeline produces a valid Synapse macro file for each weapon."""
    profile = load_profile(f"{weapon}.json")
    raw = generate(profile)
    humanized = humanize_sequence(raw)
    output = export_synapse(humanized)
    assert output is not None
    assert validate_synapse_format(output)
```

---

## 3. Pattern Visualization (`tests/visualizer.py`)

Visual inspection catches things that statistical tests miss. Generate plots and review them manually before every deployment.

### 3.1 Scatter Plot

Plot X/Y coordinates of each shot's compensation for a single spray.

```
Good output (humanized):          Bad output (too perfect):
Y ↑                                Y ↑
  |  *  *                            | *
  | * **  *                           |  *
  |  * * * *                          |   *
  | *  ** *                           |    *
  |* * *  * *                         |     *
  +----------→ X                      +----------→ X
```

**What to look for:**

- ✅ Scatter and noise around the expected curve
- ✅ Variable point spacing
- ✅ Occasional outliers (over-correction / skip events)
- ✅ Wider scatter toward end of magazine (falloff effect)
- ❌ A perfectly smooth curve
- ❌ Identical spacing between all points
- ❌ No outliers at all

### 3.2 Multi-Spray Overlay

Overlay 10 sprays on the same plot.

**What you want to see:**

- A **cloud** of points, not overlapping lines
- The general shape (recoil curve) is visible, but individual sprays vary
- No two sprays trace the same path

### 3.3 Delay Histogram

Plot a histogram of all inter-shot delays across multiple sprays.

**What you want to see:**

- A Gaussian (bell curve) centered on the base delay
- Tails extending to ±max\_variance
- **No peaks** at specific values (peaks indicate quantization — a detectable pattern)

### 3.4 Comparison Plots

Generate side-by-side comparisons:

| Left Panel | Right Panel | Purpose |
|------------|-------------|---------|
| Raw (no humanization) | Humanized | Show the effect of the humanizer |
| Humanized | "Perfect" compensation | Show the deliberate imperfection |

---

## 4. Statistical Validation

### 4.1 Consistency Analysis

Run **100 sprays per weapon** and compute:

| Metric | Expected Result |
|--------|----------------|
| Mean compensation per shot | Tracks the expected recoil curve |
| Standard deviation per shot | Matches configured variance ranges |
| Skip event count | Matches configured probability (within statistical tolerance) |
| Over-correction count | Matches configured probability |

### 4.2 Sequence Uniqueness

Hash each generated sequence. Over **1,000 generations**, there should be **zero hash collisions**.

If any two sequences are identical, the randomization is broken. Investigate immediately.

```python
import hashlib

def test_sequence_uniqueness():
    hashes = set()
    for _ in range(1000):
        seq = generate_and_humanize(load_profile("ak47.json"))
        h = hashlib.sha256(str(seq).encode()).hexdigest()
        assert h not in hashes, "Duplicate sequence detected"
        hashes.add(h)
```

### 4.3 Autocorrelation

Compute autocorrelation of delay sequences.

- **Humanized sequence** → should show **low** autocorrelation (each delay is independent of the previous).
- **High autocorrelation** = detectable pattern = bad.

```python
import numpy as np

def test_low_autocorrelation():
    delays = [humanize_delay(15.0) for _ in range(500)]
    delays = np.array(delays) - np.mean(delays)
    autocorr = np.correlate(delays, delays, mode="full")
    autocorr = autocorr[len(autocorr) // 2:]  # take positive lags
    autocorr /= autocorr[0]  # normalize
    # Lag-1 autocorrelation should be near zero
    assert abs(autocorr[1]) < 0.1, f"Autocorrelation too high: {autocorr[1]:.3f}"
```

---

## 5. The Smell Test Checklist

Run through these questions for **every weapon** before deployment:

| # | Question | Expected Answer |
|---|----------|----------------|
| 1 | If I watched this spray, would I know it's a macro? | **No** |
| 2 | Does it look too consistent? | **No** |
| 3 | Does it handle horizontal drift the same way every time? | **No** |
| 4 | Are there any perfectly repeated sub-sequences? | **No** |
| 5 | Does the spray degrade toward the end of the magazine? | **Yes** |
| 6 | Are there occasional "mistakes" (outliers)? | **Yes** |
| 7 | Does the delay between shots vary visibly? | **Yes** |
| 8 | Would this pattern look different if I ran it again? | **Yes** |

> **If ANY question gives the wrong answer**, increase variance or adjust humanization parameters before proceeding.

---

## 6. Mouse Movement Logging (`tools/mouse_logger.py`)

### Purpose

Record actual mouse movements while the macro runs to validate real-world output against expected behavior.

### How to Use

1. Run `mouse_logger.py` — starts recording mouse position every 1 ms.
2. Activate your macro and do a full spray into a wall (use a paint program or similar surface).
3. Stop recording (Ctrl+C or configured stop key).
4. The logger outputs a CSV with the following columns:

   ```
   timestamp, x, y, delta_x, delta_y
   ```

5. Feed the CSV into the visualizer for analysis.

### What to Check

| Check | What You're Looking For |
|-------|------------------------|
| Movement accuracy | Mouse movement matches expected macro output |
| No hardware artifacts | No double movements or dropped inputs |
| Timing accuracy | Delays match configured values (within USB polling tolerance, typically ±1 ms) |

---

## 7. Validation Workflow

Follow this sequence for every weapon before deployment:

```
Step 1: Unit tests pass
        $ pytest tests/ -v
              ↓
Step 2: Generate 10 sprays per weapon
              ↓
Step 3: Visualize scatter plots — pass smell test (Section 5)
              ↓
Step 4: Run statistical validation — all metrics within tolerance (Section 4)
              ↓
Step 5: Mouse logger test — real-world output matches expected (Section 6)
              ↓
Step 6: ✅ Ready for deployment
```

**Do not skip steps.** A macro that passes unit tests but fails the smell test is not ready. A macro that looks good visually but has autocorrelation issues is not ready.

---

## 8. Tools Required

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Runtime |
| pytest | latest | Unit testing |
| matplotlib | latest | Visualization (scatter, histogram, overlay) |
| numpy | latest | Statistical analysis (autocorrelation, std dev) |
| `tools/mouse_logger.py` | included | Real-world mouse movement recording |

Install test dependencies:

```bash
pip install pytest matplotlib numpy
```
