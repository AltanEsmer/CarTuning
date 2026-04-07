# WEAPON_DATA.md — Complete Recoil Data Reference

> **CarTuning** — Python-based recoil compensation macro generator for Rust (the game).
> Offline/training use only.

This document is the **definitive reference** for all weapon recoil data used in the system.
Every pull value, drift offset, humanization parameter, and scaling factor lives here.

---

## Overview

| Parameter | Value |
|-----------|-------|
| **Reference DPI** | 800 |
| **Polling Rate** | 1000 Hz |
| **Pull Unit** | Pixels (px) at 800 DPI |

All pull values in this document are calibrated at **800 DPI**. Scale accordingly for other DPI settings:

- 400 DPI → multiply values by **2.0×**
- 1600 DPI → multiply values by **0.5×**

**Formula:**

```
adjusted_pull = base_pull * (800 / your_dpi)
```

---

## Master Comparison Table

| Weapon | Shots/Mag | Total Pull (px) | Curve Shape | X-Axis Behavior | Difficulty | Macro Complexity |
|------------|-----------|-----------------|------------------|----------------------|------------|------------------|
| AK-47 | 30 | 120–150 | S-shaped | Strong left → right | Hard | Highest |
| LR-300 | 30 | 80–100 | Vertical | Slight right drift | Medium | Low |
| M249 | 100 | 200+ (ramping) | Ramping vertical | Increasing drift | Hard | High (100 shots) |
| MP5 | 30 | 50–70 | Mostly vertical | Minimal | Easy | Lowest |
| Custom SMG | 24 | 60–80 | Erratic / random | Random ±2 px | Hard | High (randomness) |
| Thompson | 30 | 40–60 | Gentle curve | Minimal | Easy | Low |
| R4-C (R6X) | 26 | 160–195 | Steep vertical | Gradual right drift | Hard | Medium |

---

## Detailed Weapon Profiles

---

### AK-47 — The Complex One

The most documented weapon in Rust. S-shaped recoil curve with significant horizontal drift.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|--------------|-------|-------------------|---------------------|----------------|-----------------------------------------------|
| Opening | 1–5 | 6–7 | −1 to −2 (left) | 100% | Aggressive vertical start, slight left |
| Middle-Early | 6–12 | 4–5 | 0 to −1 | 100% | Stabilizing, curve neutralizes |
| Middle-Late | 13–20 | 3–4 | +1 to +2 (right) | 95% | Curve shifts right |
| Closing | 21–30 | 2–3 | +2 to +3 (right) | 85–90% | Settled vertical, increasing right drift |

#### Total Distribution

| Segment | Shots | Share of Total Pull | Character |
|-------------|-------|---------------------|---------------------|
| First 10 | 1–10 | ~40% | Aggressive start |
| Middle 10 | 11–20 | ~35% | Stabilizing |
| Final 10 | 21–30 | ~25% | Settled / tapering |

#### Key Characteristics

- The **S-curve** is what separates good AK macros from detected ones.
- Most public macros are pure vertical — the **X-axis movement is critical**.
- Horizontal drift pattern: **left → neutral → right → heavy right**.
- Hardest weapon to macro convincingly.

---

### LR-300 — The Friendly One

Simpler, more vertical pattern. Best weapon to test with first.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|-------|-------------------|---------------------|----------------|--------------------------------------|
| All | 1–30 | 2–4 | 0 | 100% → 95% → 90% | Consistent vertical |
| Post-10 | 10–30 | 2–4 | 0–1 (right) | 95% → 90% | Slight right drift develops |

#### Key Characteristics

- Lower total compensation = less to hide.
- **Safe testing weapon** — minimal complexity.
- Almost no horizontal drift in first 10 shots.
- Gentle enough that humanization variance covers imperfections naturally.

---

### M249 — The Heavy

100-round magazine with significant ramping. No human controls this perfectly.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|--------|-------------------|----------------------|----------------|--------------------------------------|
| Stage 1 | 1–20 | 3–4 | 0 | 100% | Light opening |
| Stage 2 | 21–50 | 4–5 | 0–1 | 95% | Building momentum |
| Stage 3 | 51–80 | 5–6 | 1–2 | 85% | Heavy pull, drift starts |
| Stage 4 | 81–100 | 6–7 | 2–3 (increasing) | 80% | Maximum recoil, heavy drift |

#### Key Characteristics

- **Ramping recoil** — gets progressively harder to control.
- Significant falloff after shot 60 is mandatory (85% or lower).
- 100 shots means longer macro, more opportunities for pattern detection.
- X-axis drift increases significantly in final 40 shots.
- Nobody sprays a full mag perfectly — **build in visible degradation**.

---

### MP5 — The Easy One

Minimal recoil, mostly vertical. Barely needs a macro. Use for delivery system testing.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|-------|-------------------|---------------------|----------------|----------------------|
| All | 1–30 | 1.5–2.5 | 0–1 | 100% → 95% | Simple, consistent |

#### Key Characteristics

- Simplest pattern in the game.
- Good for **testing your macro delivery system** before complex weapons.
- Low pull values mean less aggressive compensation = less detectable.
- Almost no horizontal component.

---

### Custom SMG — The Unpredictable

Random elements in recoil make this the hardest to macro, but also the best cover.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|-------|-------------------|----------------------|----------------|-----------------------------------------------|
| All | 1–24 | 2–4 (base) | Random: −2 to +2 | 100% → 90% | 20% chance of +2 px Y variance per shot |

#### Special Variance Rules

These apply **on top of** normal humanization:

| Axis | Rule | Details |
|--------|--------------------------------------|----------------------------------------------|
| Y-axis | +2 px random spike | 20% probability per shot |
| X-axis | Fully random per shot | Uniform between −2 px and +2 px |
| Delay | Wider variance than other weapons | ±12 ms (vs. typical ±8–10 ms) |

#### Key Characteristics

- The weapon itself is random, so **perfect compensation actually stands out MORE**.
- Your macro should mirror the randomness, not fight it.
- Wider variance ranges than any other weapon.
- The unpredictability is your cover — **lean into it**.

---

### Thompson — The Chill One

Gentle recoil, easy curve. Low priority for macro development.

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|-------|-------------------|---------------------|----------------|-------------------------------|
| All | 1–30 | 1.5–2.5 | 0 to −0.5 | 100% → 95% | Gentle, predictable curve |

#### Key Characteristics

- One of the easiest weapons to control manually.
- Very similar to MP5 in macro complexity.
- Slight **leftward** drift (unusual — most weapons drift right).
- Low total pull distance.

---

## DPI Scaling Reference

| Base DPI | Scale Factor | Example: AK Shot 1 Y-Pull |
|----------|-------------|---------------------------|
| 400 | 2.0× | 12–14 px |
| 800 | 1.0× (reference) | 6–7 px |
| 1200 | 0.67× | 4–4.7 px |
| 1600 | 0.5× | 3–3.5 px |

**Formula:**

```
adjusted_pull = base_pull * (800 / your_dpi)
```

---

## Humanization Parameters by Weapon

| Weapon | Delay Variance | Pull Variance | Skip % | Over-correct % | Falloff Profile |
|------------|----------------|---------------|--------|----------------|-----------------|
| AK-47 | ±10 ms | ±1.0 px | 3% | 2% | 100 / 95 / 87 |
| LR-300 | ±8 ms | ±0.8 px | 3% | 1% | 100 / 95 / 90 |
| M249 | ±10 ms | ±1.2 px | 4% | 2% | 100 / 95 / 85 / 80 |
| MP5 | ±8 ms | ±0.5 px | 2% | 1% | 100 / 95 / 92 |
| Custom SMG | ±12 ms | ±1.5 px | 5% | 3% | 100 / 95 / 90 |
| Thompson | ±8 ms | ±0.6 px | 2% | 1% | 100 / 95 / 92 |
| R4-C (R6X) | ±14 ms | ±1.3 px | 4% | 2.5% | 100 / 95 / 88 / 80 |

### Column Definitions

| Column | Meaning |
|-----------------|----------------------------------------------------------------------|
| Delay Variance | Random ± offset added to inter-shot timing (ms) |
| Pull Variance | Random ± offset added to each Y/X pull value (px) |
| Skip % | Chance per shot that compensation is skipped entirely |
| Over-correct % | Chance per shot that pull is applied at 1.5× magnitude |
| Falloff Profile | Compensation % at magazine start / mid / late (/ end for M249) |

---

## Rainbow Six Siege X — R4-C (Ash)

The first R6 Siege X weapon profile. Ash's R4-C is a high-fire-rate assault rifle with aggressive vertical recoil and minimal horizontal drift — a pure pull-down weapon with minor lateral adjustments.

#### Stats

| Stat | Value |
|------|-------|
| Game | Rainbow Six Siege X |
| Operator | Ash |
| Fire Rate | 860 RPM |
| Magazine | 25+1 (nerfed from 30 in Y9S3) |
| Total Pull (est.) | 160–195 px at 800 DPI |
| Difficulty | Hard |
| Curve Shape | Steep vertical → gradual rightward drift → stabilizes |

#### Per-Section Breakdown

| Section | Shots | Y-Pull (px/shot) | X-Drift (px/shot) | Compensation % | Notes |
|---------|-------|-------------------|---------------------|----------------|----------------------------------------------|
| Opening Climb | 1–5 | 8–10 | 0 to 1 (right) | 100% | Sharp initial vertical kick |
| Sustained Vertical | 6–10 | 7–9 | −1 to 3 | 100% | Drift onset, left-right variance |
| Mid-Mag Instability | 11–15 | 6–8 | −2 to 4 (random) | 95% | Peak horizontal unpredictability |
| Tapering Left Settle | 16–20 | 5–7 | −1 to 3 | 90% | Vertical eases, drift settling |
| Closing Falloff | 21–26 | 4–6 | −1 to 2 | 85% | End-of-mag degradation |

#### Humanization Tuning

Tuned more aggressively than Rust profiles due to BattlEye + Shield Guard anti-cheat:

| Parameter | Value | vs. CS2 AK-47 |
|-----------|-------|---------------|
| Delay Variance | ±14 ms | +2 ms (faster fire rate needs more jitter) |
| Pull Variance | ±1.3 px | +0.1 px |
| X Variance | ±1.0 px | +0.2 px (critical — low-horizontal weapons need X noise) |
| Skip Probability | 4% | +1% (breaks rhythm more) |
| Overcorrect Probability | 2.5% | +0.5% |
| Overcorrect Magnitude | 1.18× | +0.03× |
| Falloff Stages | 100 / 95 / 88 / 80 | 4 stages (vs 3) — steeper late-mag decay |

#### Key Characteristics

- **Pull-down dominant** — ~90% of compensation is vertical.
- **Low horizontal complexity** — unlike CS2 AK-47's zigzag, R4-C drifts gradually rightward.
- **Shorter mag** — 26 shots means the macro finishes faster, less exposure time.
- **BattlEye environment** — humanization params pushed higher than Rust profiles.
- **Attachment note**: Profile assumes **no barrel attachment + vertical grip** (raw recoil). Reduce Y values ~5% for flash hider, reduce X variance ~35% for compensator.

---

## Data Sources

| Source | Usage |
|--------------------------------------------------|-----------------------------------------------|
| Rust Labs (rustlabs.com) | Weapon stats and base mechanics |
| Community recoil spreadsheets | Pull distances and patterns |
| Frame-by-frame YouTube analysis | Curve shape verification |
| In-game testing on training servers | Final validation and calibration |
| Rainbow Six Wiki (Fandom) | R4-C stats, fire rate, mag size |
| Liquipedia Rainbow Six | R4-C weapon data cross-reference |
| SiegeGG Designer's Notes (Y9S3) | R4-C nerf details (mag 30→25) |
| UnknownCheats R6 Recoil Data Collection | Per-shot pixel drift estimates |
