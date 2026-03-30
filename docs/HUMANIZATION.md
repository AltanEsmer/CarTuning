# Humanization Engine — Design Document

> **CarTuning** — Python-based recoil compensation macro generator for Rust (the game).
> Offline/training use only.
>
> This is the **CORE differentiator** of the system. The humanization layer is what separates
> a detectable script from something that mimics real hand movement.

---

## 1. Philosophy

Perfect recoil compensation is the enemy. Anti-cheat systems and experienced players can
spot a macro by its perfection — identical delays, smooth curves, zero deviation. Humans
are messy. Humans miss. Humans over-correct. Humans get tired. The humanization engine
injects all of these imperfections **deliberately and probabilistically**.

The goal: a **5–15% deviation** from perfect compensation that mimics the noise floor of a
skilled human player.

Three axioms drive every design decision:

1. **Deterministic = Detectable.** If any property of the output is constant across runs,
   it becomes a fingerprint. Every numeric output must carry variance.
2. **Statistical plausibility over mechanical accuracy.** The spray pattern should be
   indistinguishable — in distribution — from one produced by a top-percentile human.
3. **Degradation is realism.** Sustained fire degrades motor control. A macro that
   maintains peak precision through shot 30 is immediately suspicious.

---

## 2. Variance Models

All variance is applied **per-shot, per-axis, independently**. No windowing, no smoothing,
no correlation between consecutive samples. This is critical — correlated noise is
detectable; independent noise is not.

### 2.1 Delay Variance

Every shot in a macro has a base delay (typically 20–45 ms depending on fire rate). The
humanizer adds random variance to each delay independently.

| Property | Value |
|---|---|
| **Model** | Gaussian distribution centered on base delay |
| **Range** | ±8–12 ms (weapon-dependent) |
| **Bounds** | Clamped to `[base_delay - max_variance, base_delay + max_variance]` |
| **Purpose** | Prevents perfectly periodic mouse movements that anti-cheat flags |

**Implementation:**

```python
actual_delay = base_delay + random.gauss(0, variance_ms / 2)
actual_delay = max(base_delay - max_variance, min(base_delay + max_variance, actual_delay))
```

The Gaussian is chosen over uniform because human inter-press intervals follow a
bell-curve distribution — most presses cluster near the mean, with rare outliers.
The standard deviation is set to `variance_ms / 2` so that ~95% of samples fall within
the configured range (2σ coverage).

**Conceptual Distribution:**

```
Frequency
  │         ▄▄▄▄
  │       ▄██████▄
  │     ▄██████████▄
  │   ▄██████████████▄
  │ ▄██████████████████▄
  ├──────────┼──────────┼──→ Delay offset (ms)
         -12   0   +12
```

> Most shots fire near the base delay. A few fire noticeably early or late. This matches
> the timing profile of a human holding mouse-1.

### 2.2 Pull Variance (Y-Axis)

Each shot's vertical compensation receives a random offset, creating scatter in what would
otherwise be a smooth downward pull.

| Property | Value |
|---|---|
| **Model** | Uniform random within bounds |
| **Range** | ±0.5–1.5 px (weapon-dependent) |
| **Purpose** | Creates scatter in the spray pattern instead of a smooth line |

**Implementation:**

```python
actual_pull_y = base_pull_y + random.uniform(-variance_px, variance_px)
```

Uniform distribution is used here (instead of Gaussian) because vertical micro-adjustments
don't cluster as tightly — the hand's Y-axis control during sustained fire is coarser than
timing control.

### 2.3 X-Axis Variance

Horizontal compensation also gets variance, calibrated per weapon to match real horizontal
recoil characteristics.

| Property | Value |
|---|---|
| **Model** | Uniform random |
| **Range** | Weapon-specific (e.g., AK: ±0.5 px, Custom SMG: ±2.0 px) |
| **Purpose** | Simulates horizontal micro-tremor and imprecise lateral correction |

**Implementation:**

```python
actual_pull_x = base_pull_x + random.uniform(-x_variance, x_variance)
```

> **Why weapon-specific ranges?**
> Weapons with inherently random horizontal recoil (Custom SMG, Thompson) already have
> noisy X-axis patterns. Adding too much additional variance would push total deviation
> past the 15% budget. Weapons with tight horizontal recoil (AK, LR-300) need more
> injected variance to mask the regularity of perfect compensation.

---

## 3. Probabilistic Events

Beyond continuous variance, the humanizer injects **discrete events** — rare,
high-impact anomalies that break up the statistical regularity of the output.

### 3.1 Skip Probability

Simulates a player momentarily failing to compensate — a brief lapse in micro-adjustment.

| Property | Value |
|---|---|
| **Probability** | 2–5% per shot (weapon-dependent) |
| **Behavior** | Shot compensation is set to `(0, 0)` — no pull applied |
| **Result** | Crosshair jumps for one shot, then normal compensation resumes |
| **Purpose** | Creates occasional outlier points in the spray pattern |

**Implementation:**

```python
if random.random() < skip_probability:
    actual_pull_x = 0
    actual_pull_y = 0
```

This is what human sprays look like when analyzed frame-by-frame: mostly controlled, with
occasional points that deviate significantly from the mean trajectory. These outliers are
a **positive signal** of humanity — their absence is the red flag.

### 3.2 Over-Correction

Simulates a player pulling too hard, then correcting back on the following shot — the
characteristic "jitter-and-recover" pattern visible in human sprays.

| Property | Value |
|---|---|
| **Probability** | 1–3% per shot (weapon-dependent) |
| **Magnitude** | 120% of base compensation value (20% over-pull) |
| **Recovery** | Following shot applies 80% compensation to correct back |
| **Purpose** | Creates paired deviations that match human motor correction |

**Implementation:**

```python
next_shot_modifier = 1.0  # default: no modifier

if random.random() < overcorrect_probability:
    actual_pull = base_pull * overcorrect_magnitude   # this shot: over-correct (e.g. 1.2×)
    next_shot_modifier = 2.0 - overcorrect_magnitude  # next shot: compensate back (e.g. 0.8×)
```

The recovery on the next shot is important. An over-correction followed by a normal shot
looks mechanical. An over-correction followed by an under-correction looks like a human
catching their mistake — because that's exactly what it is.

> **Edge case:** If a skip event and an over-correction event both trigger on the same
> shot, the skip takes priority. A skipped shot cannot simultaneously be over-corrected.
> The over-correction state is discarded and `next_shot_modifier` resets to `1.0`.

---

## 4. Staged Falloff (Fatigue Simulation)

Humans lose fine motor control over sustained fire. The longer you spray, the worse your
compensation gets. This is **CRITICAL** for realism — it is the single most effective
anti-detection feature because it creates a macro-level statistical signature that matches
human physiology.

### 4.1 Falloff Model

The magazine is divided into stages, each with a compensation multiplier applied to the
final pull value. The multiplier affects **both axes** uniformly.

**Standard Falloff (30-round magazine):**

| Stage | Shots | Compensation | Rationale |
|---|---|---|---|
| **Peak** | 1–10 | 100% | Fresh spray, full motor control |
| **Sustained** | 11–20 | 95% | Slight fatigue, minor precision loss |
| **Fatigued** | 21–30 | 85–90% | Muscle fatigue, noticeable degradation |

**Extended Falloff (M249, 100-round magazine):**

| Stage | Shots | Compensation | Rationale |
|---|---|---|---|
| **Peak** | 1–20 | 100% | Opening burst, full control |
| **Sustained** | 21–50 | 95% | Early fatigue sets in |
| **Fatigued** | 51–80 | 85% | Significant degradation |
| **Exhausted** | 81–100 | 80% | Near-loss of fine control |

### 4.2 Implementation

```python
def get_falloff_multiplier(shot_number: int, falloff_stages: list[dict]) -> float:
    """
    Returns the compensation multiplier for a given shot number
    based on the weapon's configured falloff stages.

    Stages are evaluated in order; the first matching stage wins.
    If shot_number exceeds all stages, the last stage's multiplier is used.
    """
    for stage in falloff_stages:
        if shot_number <= stage['end_shot']:
            return stage['multiplier']
    return falloff_stages[-1]['multiplier']
```

**Application point in the pipeline:**

```python
# Full humanization pipeline for a single shot:
# 1. Start with base compensation values
# 2. Apply per-shot variance (Section 2)
# 3. Apply probabilistic events (Section 3)
# 4. Apply fatigue falloff (Section 4) — LAST, multiplicatively

final_pull_x = humanized_pull_x * get_falloff_multiplier(shot_number, falloff_stages)
final_pull_y = humanized_pull_y * get_falloff_multiplier(shot_number, falloff_stages)
```

> **Why apply falloff last?**
> Fatigue reduces the *effectiveness* of whatever the player is doing — including their
> imperfect, already-humanized compensation. Applying it after variance models the real
> causal chain: the player attempts an imperfect correction, and fatigue degrades even
> that imperfect attempt.

---

## 5. Anti-Detection Principles

### 5.1 Per-Shot Independence

Each shot's humanization is rolled independently using separate `random` calls. There is
**no correlation** between consecutive shots' variance values. This is non-negotiable.

Why: Pattern detection algorithms (both statistical and ML-based) exploit temporal
correlation. If shot N's delay predicts shot N+1's delay — even weakly — the sequence
is flaggable. Independent rolls produce white noise, which is indistinguishable from
genuine human variance.

### 5.2 No Identical Sequences

Because all variance is probabilistic and applied per-shot:

- Run the same weapon macro **1,000 times** → **1,000 unique spray patterns**
- The probability of two identical sequences is effectively zero
- This matches human behavior: no player has ever produced the exact same spray twice

This property holds even with identical configuration, because the randomness is injected
at generation time, not baked into the profile.

### 5.3 The Imperfection Budget

Total deviation from perfect compensation: **5–15%**. This range is carefully chosen:

| Deviation | Risk |
|---|---|
| **< 5%** | Too perfect — statistically distinguishable from human input |
| **5–15%** | **Target range** — matches the noise floor of a skilled player (top 10–20% percentile) |
| **> 15%** | Too sloppy — defeats the purpose of recoil compensation entirely |

The budget is the **aggregate** of all humanization effects:
- Delay variance contributes ~2–4%
- Pull variance contributes ~2–5%
- Skip events contribute ~1–3%
- Over-corrections contribute ~0.5–1.5%
- Fatigue falloff contributes ~1–5% (increasing over the spray)

These ranges are tuned so that even in the worst case (all effects rolling high), total
deviation stays within budget.

### 5.4 X-Axis is the Tell

Most public macros only compensate vertically (Y-axis pull-down). This is the single
biggest detection signal:

1. **Real recoil** has horizontal components for every weapon.
2. **Real humans** have horizontal micro-tremor even when the weapon doesn't demand it.
3. **Y-only macros** produce a spray with zero X-axis variance — a dead giveaway.

The presence of X-axis variance — even when the weapon has minimal horizontal recoil —
is a key humanization signal. The humanizer **always** injects X-axis noise, even for
weapons where `base_pull_x` is zero for most shots.

```python
# Even when the weapon's base X compensation is 0 for this shot,
# still inject horizontal micro-tremor:
if x_variance > 0:
    actual_pull_x = base_pull_x + random.uniform(-x_variance, x_variance)
```

---

## 6. Configuration

All humanization parameters are configurable per weapon via the JSON weapon profile. This
allows each weapon to carry its own tuned humanization values that account for its
fire rate, recoil severity, magazine size, and detection risk.

### 6.1 Schema

```json
{
  "humanization": {
    "delay_variance_ms": 10,
    "pull_variance_px": 1.0,
    "x_variance_px": 0.5,
    "skip_probability": 0.03,
    "overcorrect_probability": 0.02,
    "overcorrect_magnitude": 1.2,
    "falloff_stages": [
      { "end_shot": 10, "multiplier": 1.0 },
      { "end_shot": 20, "multiplier": 0.95 },
      { "end_shot": 30, "multiplier": 0.87 }
    ]
  }
}
```

### 6.2 Parameter Reference

| Parameter | Type | Range | Description |
|---|---|---|---|
| `delay_variance_ms` | `float` | 5–15 | Max timing deviation per shot (ms) |
| `pull_variance_px` | `float` | 0.3–2.0 | Max Y-axis pull deviation per shot (px) |
| `x_variance_px` | `float` | 0.2–3.0 | Max X-axis pull deviation per shot (px) |
| `skip_probability` | `float` | 0.01–0.08 | Chance of zero-compensation on a given shot |
| `overcorrect_probability` | `float` | 0.005–0.05 | Chance of over-pull on a given shot |
| `overcorrect_magnitude` | `float` | 1.1–1.3 | Multiplier applied during over-correction |
| `falloff_stages` | `list` | — | Ordered list of `{end_shot, multiplier}` objects |

### 6.3 Defaults and Tuning Guidance

- **High fire-rate weapons** (MP5, Custom SMG): Higher `delay_variance_ms` (12–15), higher
  `skip_probability` (0.04–0.05). Fast-firing weapons are harder to control; more variance
  is expected.
- **Slow, heavy weapons** (AK, LR-300): Lower `delay_variance_ms` (8–10), lower
  `skip_probability` (0.02–0.03). Skilled players have tighter control on slower weapons.
- **Extended magazines** (M249): Must define 4+ falloff stages. The fatigue curve is the
  primary humanization vector for sustained fire.
- **Burst weapons** (if applicable): Very low `skip_probability`, very low falloff. Bursts
  are short enough that fatigue doesn't apply, and skips mid-burst are unlikely.

---

## 7. Processing Pipeline

For clarity, the complete per-shot humanization pipeline in execution order:

```
┌─────────────────────────────────────────────────────────┐
│  Input: base_delay, base_pull_x, base_pull_y            │
│         shot_number, humanization_config                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  1. Delay Variance  │  Gaussian noise on timing
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  2. Pull Variance   │  Uniform noise on Y-axis
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  3. X-Axis Variance │  Uniform noise on X-axis
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  4. Skip Check      │  2-5% → zero out both axes
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  5. Over-Correction │  1-3% → amplify, flag next
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  6. Fatigue Falloff │  Multiply by stage factor
              └──────────┬──────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Output: actual_delay, actual_pull_x, actual_pull_y     │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Validation Criteria

A properly humanized sequence **MUST** satisfy all of the following when inspected
visually (plotted) or statistically:

### Must Have (✅)

- ✅ **Scatter** — plotted spray shows point-to-point variation, not a smooth curve
- ✅ **Variable spacing** — distances between consecutive points are non-uniform
- ✅ **Occasional outliers** — 2–5% of points deviate significantly from the mean trajectory
- ✅ **Late-magazine degradation** — accuracy visibly worsens in the final third of the mag
- ✅ **Uniqueness** — no two generated sequences are identical, even from the same config
- ✅ **Both-axis noise** — X and Y axes both show variance, even for Y-dominant weapons

### Must Not Have (❌)

- ❌ **Perfectly periodic delays** — constant inter-shot timing is the #1 detection signal
- ❌ **Smooth predictable curves** — spline-like trajectories scream "computed"
- ❌ **Identical point spacing** — uniform spacing is a statistical impossibility for humans
- ❌ **Y-only compensation** — missing X-axis variance is a trivially detectable signature
- ❌ **Identical repeated sequences** — deterministic output is immediately flaggable

---

## 9. Future Considerations

Areas for potential enhancement (not yet implemented):

- **Adaptive variance**: Dynamically adjust humanization intensity based on in-game
  context (e.g., target distance, movement state) if input signals become available.
- **Per-player profiles**: Allow tuning humanization to match a specific player's real
  spray characteristics, captured from training sessions.
- **Micro-pause injection**: Simulate the brief hesitations (5–15 ms pauses) that occur
  when a player visually re-acquires the target mid-spray.
- **Burst segmentation**: For weapons commonly fired in bursts, model the
  inter-burst timing and reset of fatigue between bursts.
- **Machine-learning validation**: Train a classifier on human vs. macro sprays and use
  it as an automated validation gate for humanization quality.
