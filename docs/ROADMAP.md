# CarTuning — Development Roadmap

> **Python-based recoil compensation macro generator for Rust (the game)**
> For offline and training server use only.

---

## Phase 1: Weapon Data Compilation

**🏁 Milestone: All weapon profiles created as JSON**

### Deliverables

- **Define JSON schema for weapon profiles**
  - Fields: `name`, `magazine_size`, `fire_rate_rpm`, `total_vertical_pull_px`, `base_dpi`, `curve_sections[]`, `falloff`, `metadata`
  - Each `curve_section` entry: `shot_range` (start–end), `y_per_shot` (min–max), `x_per_shot` (min–max), `direction_bias`
  - Schema stored at `data/schema/weapon_profile.schema.json`

- **Build 6 weapon profile files** (`data/weapons/`)

  - **AK-47** (`ak47.json`)
    - 30 rounds/magazine
    - ~120–150px total vertical pull at 800 DPI
    - S-shaped recoil curve (strong left → right)
    - Curve sections:
      - Shots 1–5: **6–7px/shot vertical**, slight left X drift
      - Shots 6–12: **4–5px/shot vertical**, neutral X
      - Shots 13–20: **3–4px/shot vertical**, slight right X drift
      - Shots 21–30: **2–3px/shot vertical**, increasing right drift (1–3px)

  - **LR-300** (`lr300.json`)
    - 30 rounds/magazine
    - ~80–100px total vertical pull at 800 DPI
    - Mostly vertical with slight right drift after shot 10
    - All shots: **2–4px vertical**, **0–1px right drift** (onset at shot 10)

  - **M249** (`m249.json`)
    - 100 rounds/magazine
    - Heavy vertical ramping pattern
    - Curve sections:
      - Shots 1–20: **3–4px/shot**
      - Shots 21–50: **4–5px/shot**
      - Shots 51–80: **5–6px/shot**
      - Shots 81–100: **6–7px/shot** + increasing X drift
    - Staged falloff: **85% effectiveness** after shot 60

  - **MP5** (`mp5.json`)
    - 30 rounds/magazine
    - ~50–70px total vertical pull at 800 DPI
    - Mostly vertical, minimal horizontal movement
    - All shots: **1.5–2.5px/shot vertical**, **0–1px X drift**

  - **Custom SMG** (`custom_smg.json`)
    - 24 rounds/magazine
    - ~60–80px total vertical pull at 800 DPI
    - Erratic recoil pattern
    - All shots: **2–4px vertical** with **20% chance of +2px variance spike**
    - Random X drift between **-2px and +2px** per shot

  - **Thompson** (`thompson.json`)
    - 30 rounds/magazine
    - ~40–60px total vertical pull at 800 DPI
    - Gentle, predictable curve — easiest weapon to control
    - Smooth vertical ramp with minimal X movement

- **Validate all profiles** against community data sources (Rust Labs, community spreadsheets, spray pattern screenshots)

---

## Phase 2: Core Engine Development

**🏁 Milestone: Generator produces raw (non-humanized) macro sequences**

### Deliverables

- **`src/generator.py` — `MacroGenerator` class**
  - `load_profile(weapon_name: str)` — Load and parse weapon JSON from `data/weapons/`
  - `calculate_base_compensation(profile: dict) -> list[dict]` — Per-shot Y-pull and X-drift values based on curve sections
  - `apply_dpi_scaling(sequence: list[dict], target_dpi: int) -> list[dict]` — Scale all movement values from base 800 DPI to any target DPI
  - `generate_raw_sequence(weapon_name: str, dpi: int) -> list[dict]` — Full pipeline: load → calculate → scale
  - Output format per shot: `{ "shot": int, "delay_ms": float, "y": float, "x": float }`

- **Unit tests — `tests/test_generator.py`**
  - Test profile loading (valid JSON, missing file, malformed data)
  - Test per-shot compensation values fall within expected ranges per weapon
  - Test DPI scaling produces correct ratios (e.g., 1600 DPI → half the pixel values)
  - Test full sequence length matches magazine size
  - Test AK-47 S-curve: left bias in shots 1–5, right bias in shots 21–30

---

## Phase 3: Humanization Engine

**🏁 Milestone: Generator produces humanized sequences that pass the smell test**

### Deliverables

- **`src/humanizer.py` — `Humanizer` class**

  - **Delay variance**: ±8–12ms jitter from base timing per shot (normal distribution)
  - **Pull variance**: ±0.5–1.5px from calculated Y/X value per shot (uniform distribution)
  - **Skip probability**: **2–5%** chance per shot to skip compensation entirely (simulates human hesitation)
  - **Over-correction**: **1–3%** chance per shot to over-correct by **+20%**, then apply a corrective adjustment on the following shot
  - **Staged falloff** (accuracy degrades over sustained spray):
    - Shots 1–10: **100%** compensation effectiveness
    - Shots 11–20: **95%** effectiveness
    - Shots 21–30+: **85–90%** effectiveness
  - **Weapon-specific overrides**:
    - Custom SMG: wider variance ranges (+50% on pull variance, +30% on delay jitter)
    - Thompson: tighter variance ranges (-25% on pull variance)

- **Unit tests — `tests/test_humanizer.py`**
  - Test delay jitter stays within ±12ms bounds
  - Test pull variance stays within ±1.5px bounds
  - Test skip probability over 1000 runs is within 2–5% range
  - Test over-correction produces a visible correction on the next shot
  - Test staged falloff reduces values at correct shot thresholds
  - Test weapon-specific overrides apply correctly (Custom SMG vs Thompson)

- **Integration: Generator → Humanizer pipeline**
  - `MacroGenerator.generate(weapon, dpi, humanize=True)` chains raw output through `Humanizer`
  - Every call to `generate()` produces a **unique** sequence (no two runs identical)

---

## Phase 4: Output & Export

**🏁 Milestone: System outputs Synapse-ready macro files**

### Deliverables

- **Synapse macro format exporter** (`src/exporter.py`)
  - Convert humanized shot sequences into Synapse XML macro format
  - Each shot maps to: `<delay>` → `<mouseMove relative="true" x="..." y="..."/>`
  - Activation mode: **while-pressed** (hold to spray, release to stop)

- **Output structure per weapon file** (`src/output/{weapon}_macro.xml`)
  - Header: activation mode, repeat behavior
  - Body: ordered list of delay + relative mouse move commands
  - Footer: loop termination

- **Profile template generation** (`src/output/profile_template.xml`)
  - Base DPI setting
  - Polling rate (1000 Hz recommended)
  - Button mappings for macro activation (left-click hold)

- **Per-weapon macro files generated to `src/output/`**
  - `ak47_macro.xml`
  - `lr300_macro.xml`
  - `m249_macro.xml`
  - `mp5_macro.xml`
  - `custom_smg_macro.xml`
  - `thompson_macro.xml`

---

## Phase 5: Testing & Validation

**🏁 Milestone: All weapons validated via visualization**

### Deliverables

- **`tests/visualizer.py` — Pattern visualization tool**
  - Uses **matplotlib** to render scatter plots of spray patterns
  - Overlay multiple runs on a single plot to show variance spread
  - Color-coded by shot number (gradient from green → red)
  - Save plots to `tests/output/plots/{weapon}_spray.png`

- **`tools/mouse_logger.py` — Mouse movement recorder**
  - Records real mouse movements during live validation on training servers
  - Outputs timestamped CSV: `timestamp_ms, x_delta, y_delta`
  - Used to compare macro output against actual mouse behavior

- **Validation criteria — run 10 spray patterns per weapon and verify:**
  - ✅ **No identical sequences** — all 10 runs produce distinct output
  - ✅ **Visible scatter** — points are not on a smooth curve
  - ✅ **Variable spacing** — distance between consecutive points varies
  - ✅ **Occasional outliers** — over-correction points are visible in the scatter
  - ✅ **General shape preserved** — AK-47 still shows S-curve, M249 still ramps up

- **Smell test pass for all 6 weapons** — visual inspection confirms patterns look human-like

---

## Phase 6: Deployment & Polish

**🏁 Milestone: System is ready for use on training servers**

### Deliverables

- **Synapse profile configuration guide** (`docs/synapse_setup.md`)
  - Step-by-step instructions for importing macro files into Razer Synapse
  - Screenshots or descriptions of key configuration screens
  - Recommended Synapse settings (macro playback speed, activation mode)

- **Toggle system setup**
  - Map **Button 4** / **Button 5** / **Button 6** (side mouse buttons) to weapon profile switching
  - Document keybind configuration for quick weapon swaps mid-game
  - Example: Button 4 = AK-47, Button 5 = LR-300, Button 6 = MP5

- **First-run checklist** (`docs/first_run.md`)
  - Verify DPI setting matches profile
  - Confirm polling rate is set to 1000 Hz
  - Test on a **build/aim training server** before any live use
  - Run 3–5 sprays per weapon and visually confirm pattern
  - Adjust sensitivity multiplier if needed

- **Final documentation review and polish**
  - All docstrings complete in `src/` modules
  - Inline comments on non-obvious logic
  - `docs/` folder fully populated

- **README finalized** (`README.md`)
  - Project overview and disclaimer (offline/training use only)
  - Installation instructions (Python version, dependencies)
  - Quick-start guide
  - Supported weapons list
  - Configuration options (DPI, variance tuning)
  - License

---

## Summary Timeline

| Phase | Name | Key Milestone | Est. Duration |
|:-----:|------|---------------|:-------------:|
| **1** | Weapon Data Compilation | All weapon profiles created as JSON | 1 week |
| **2** | Core Engine Development | Generator produces raw macro sequences | 1–2 weeks |
| **3** | Humanization Engine | Generator produces humanized sequences | 1–2 weeks |
| **4** | Output & Export | System outputs Synapse-ready macro files | 1 week |
| **5** | Testing & Validation | All weapons validated via visualization | 1 week |
| **6** | Deployment & Polish | System is ready for training server use | 1 week |
| | | **Total estimated timeline** | **6–8 weeks** |
