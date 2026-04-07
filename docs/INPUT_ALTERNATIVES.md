# Input Method Alternatives

> **Context**: CarTuning generates Razer Synapse `.txt` macro files for recoil compensation. These macros are **non-functional in most competitive FPS games** because raw input handling causes games to ignore software-injected mouse movements. This document evaluates alternative input delivery methods.

---

## Table of Contents

1. [The Raw Input Problem](#the-raw-input-problem)
2. [Software Solutions](#software-solutions)
3. [Hardware Solutions](#hardware-solutions)
4. [Detection Matrix](#detection-matrix)
5. [Recommendations](#recommendations)

---

## The Raw Input Problem

### Why Synapse Macros Don't Work

Modern FPS games use the **Windows Raw Input API** (`WM_INPUT` / `GetRawInputData`) to read mouse movement directly from the HID driver stack — bypassing the standard Windows message queue (`WM_MOUSEMOVE`, `SendInput`, `mouse_event`).

```
Physical Mouse → HID Driver → Raw Input API → Game reads directly
                                    ↑
                          Synapse macros inject here (too late)
                                    ↓
              Windows Message Queue → SendInput / mouse_event
                                    ↑
                          Game IGNORES this path when raw input is on
```

**Razer Synapse** generates macro commands that call `SendInput()` or equivalent Windows API functions. When a game has **raw input enabled** (which is the default and often forced in competitive titles), these software-injected events are **invisible to the game engine**.

Even when a game allows disabling raw input in settings, modern anti-cheat systems (EAC, BattlEye, Vanguard) now independently detect and filter software-injected input events, making Synapse macros unreliable regardless of the raw input toggle.

### What Actually Works

To bypass raw input, the input must appear to originate from a **real physical HID device** at the driver level or below. This means either:

1. **Kernel-mode driver** that injects at the HID layer (e.g., Interception) — now detected
2. **Actual USB hardware** that the OS sees as a real mouse (Arduino, Makcu, etc.)
3. **Onboard device memory** macros executed by the mouse firmware itself (limited)

---

## Software Solutions

### 1. Interception Driver (Free, Open Source)

**How it works**: Kernel-mode filter driver (`interception.sys`) that sits in the Windows input driver stack. It intercepts and injects HID-level input, making synthetic events indistinguishable from real hardware input at the OS level.

| Attribute | Detail |
|-----------|--------|
| **Cost** | Free (open source) |
| **Input method** | Kernel-mode driver injection |
| **Setup difficulty** | Medium — requires driver install + Python/C wrapper |
| **CarTuning integration** | Easy — `interception-python` pip package, direct API |

**The catch**: As of 2025, **every major anti-cheat detects and blocks it**:
- EAC blocks game launch if `interception.sys` is loaded (even without active macros)
- BattlEye same — blocks on driver presence alone
- Vanguard requires full uninstall; blocks system-wide
- VAC increasingly flags it for behavioral scrutiny

**Verdict**: ❌ Dead for competitive games. Only viable for single-player or non-anti-cheat servers.

---

### 2. AutoHotKey (Free, Open Source)

**How it works**: Scripting language that calls `SendInput()` / `mouse_event()` at the Windows API level. User-mode, no driver.

| Attribute | Detail |
|-----------|--------|
| **Cost** | Free |
| **Input method** | Windows API (`SendInput`) |
| **Setup difficulty** | Easy — single `.ahk` script |
| **CarTuning integration** | Easy — generate `.ahk` instead of `.txt` |

**Detection status**: Trivially detected. Anti-cheats hash running processes and AHK's window class is a known signature. Even compiled `.exe` AHK scripts are fingerprinted.

**Verdict**: ❌ Detected by all four anti-cheats. Same raw input problem as Synapse.

---

### 3. Logitech G Hub Scripting (Free with Logitech hardware)

**How it works**: Lua scripting engine built into Logitech G Hub. Scripts run inside the G Hub process and call `SendInput()` internally. Some mice support onboard memory execution.

| Attribute | Detail |
|-----------|--------|
| **Cost** | Free (requires Logitech mouse) |
| **Input method** | Software: `SendInput`; Onboard: device firmware |
| **Setup difficulty** | Easy — Lua scripts in G Hub |
| **CarTuning integration** | Medium — would need a Lua output formatter |

**Detection status**: Software-mode scripts have the same raw input problem. Onboard memory scripts execute on the mouse hardware and bypass raw input detection, but are limited in complexity (simple patterns only, no dynamic humanization).

**Verdict**: ⚠️ Onboard-only mode partially works but severely limits humanization capability.

---

### 4. ReWASD ($7–$17 paid)

**How it works**: Virtual gamepad/keyboard/mouse driver. Remaps and creates macros via a virtual device driver.

| Attribute | Detail |
|-----------|--------|
| **Cost** | $7–$17 (modules sold separately) |
| **Input method** | Virtual device driver |
| **Setup difficulty** | Easy — GUI configuration |
| **CarTuning integration** | Low — proprietary macro format |

**Detection status**: Virtual device driver is flagged by Vanguard and EAC. BattlEye may allow it in some configurations. Not reliable for competitive use.

**Verdict**: ❌ Detected by most anti-cheats. Not a viable path.

---

### 5. AIMXP (Paid, ~$15/mo)

**How it works**: Translates mouse/keyboard input into virtual gamepad signals to exploit controller aim assist. Software-only, no hardware footprint.

| Attribute | Detail |
|-----------|--------|
| **Cost** | ~$15/month subscription |
| **Input method** | Virtual gamepad translation |
| **Setup difficulty** | Easy |
| **CarTuning integration** | None — completely different approach (aim assist exploit, not recoil macro) |

**Detection status**: Currently low detection risk (no driver, no device signature), but could be targeted at any time. Not applicable to mouse-only recoil compensation.

**Verdict**: ⚠️ Different paradigm entirely. Not compatible with CarTuning's recoil macro approach.

---

## Hardware Solutions

### 1. Arduino Leonardo / Pro Micro (Free software + ~$5–$15 hardware)

**How it works**: ATmega32u4-based microcontroller that natively supports USB HID emulation. The PC sees it as a real USB mouse. Combined with a **USB Host Shield**, it acts as a transparent pass-through between the real mouse and the PC — real user input passes through, and the Arduino injects additional mouse movements that are indistinguishable from human input.

| Attribute | Detail |
|-----------|--------|
| **Cost** | $5–$15 (Leonardo) + $8–$15 (USB Host Shield) |
| **Input method** | Real USB HID device — hardware-level |
| **Setup difficulty** | High — requires flashing firmware, soldering optional |
| **CarTuning integration** | Medium — serial protocol to send shot data from PC to Arduino |

**Architecture with CarTuning**:
```
CarTuning (PC) --[Serial/USB]--> Arduino Leonardo --[USB HID]--> PC (as mouse)
                                       ↑
                              USB Host Shield ← Real Mouse
```

The PC Python script sends per-shot movement commands over serial. The Arduino executes them as real HID mouse reports. The game sees a normal USB mouse.

**Detection status**:
- **Firmware VID/PID spoofing**: Arduino can present itself with the vendor/product ID of any commercial mouse (e.g., Razer DeathAdder, Logitech G Pro). The OS and anti-cheat see a "real" mouse.
- **Behavioral analysis**: The main risk. Perfectly timed, perfectly consistent movements can be flagged by ML-based pattern detection. **This is where CarTuning's humanization layer becomes critical** — the Gaussian jitter, skip events, overcorrections, and fatigue falloff exist specifically to defeat behavioral analysis.
- EAC: Low detection risk (no driver signature to flag)
- Vanguard: Possible to bypass with proper VID/PID + timing variance
- VAC: Very low risk (no software footprint)
- BattlEye: Low risk

**Verdict**: ✅ **Best option for CarTuning integration.** Real hardware, lowest detection surface, and the humanization pipeline already solves the behavioral analysis problem. Requires hardware purchase and firmware work.

---

### 2. Makcu (Open Source Hardware, ~$20–$40)

**How it works**: Open-source DMA/input device purpose-built for input spoofing. V3 firmware supports USB passthrough (real mouse passes through the device). Actively maintained with anti-detection updates.

| Attribute | Detail |
|-----------|--------|
| **Cost** | $20–$40 |
| **Input method** | USB HID passthrough + injection |
| **Setup difficulty** | Medium — plug-and-play with firmware config |
| **CarTuning integration** | Medium — serial/USB command protocol |

**Detection status**: As of early 2025, considered "very safe" on EAC, BattlEye, FACEIT, and Vanguard with compatible mice. Community actively tracks detection changes.

**Verdict**: ✅ Strong option. Community-maintained detection evasion. Less DIY than Arduino but less customizable.

---

### 3. Teensy 4.x (~$20–$30)

**How it works**: ARM-based microcontroller (much faster than Arduino) with native USB HID. Better timing precision and can emulate more complex USB descriptors.

| Attribute | Detail |
|-----------|--------|
| **Cost** | $20–$30 |
| **Input method** | Real USB HID device |
| **Setup difficulty** | High — similar to Arduino but more powerful |
| **CarTuning integration** | Medium — same serial protocol approach as Arduino |

**Detection status**: Similar to Arduino — very low detection risk since it's real hardware. Teensy's faster clock allows more precise timing humanization.

**Verdict**: ✅ Premium Arduino alternative. Better timing precision for humanization.

---

### 4. CronusZen (~$100)

**How it works**: Commercial USB adapter that sits between controller/mouse and console/PC. Supports scripting (GPC language) for macros, rapid fire, recoil compensation. Marketed primarily for console use.

| Attribute | Detail |
|-----------|--------|
| **Cost** | ~$100 |
| **Input method** | USB passthrough with script injection |
| **Setup difficulty** | Low — GUI + script upload |
| **CarTuning integration** | Low — proprietary GPC scripting, not Python-compatible |

**Detection status (2025)**:
- R6 Siege: **Detected** — BattlEye now identifies Cronus devices; players report bans and matchmaking isolation
- Valorant: **High risk** — Vanguard aggressively blocks known device signatures
- Rust: Detection increasing via EAC firmware signature checks
- CS2: Medium risk, VAC improving hardware detection
- PS5: **Fully blocked** by Sony firmware update (2024)

**Verdict**: ⚠️ Increasingly detected. Proprietary ecosystem doesn't integrate with CarTuning. Expensive for what it offers.

---

### 5. Titan Two (~$90)

**How it works**: Similar to CronusZen — USB adapter with GPC scripting. More advanced scripting capabilities.

| Attribute | Detail |
|-----------|--------|
| **Cost** | ~$90 |
| **Input method** | USB passthrough + script |
| **Setup difficulty** | Low–Medium |
| **CarTuning integration** | Low — proprietary scripting |

**Detection status**: Same trajectory as CronusZen. Increasingly detected by all major anti-cheats.

**Verdict**: ⚠️ Same problems as CronusZen. Not recommended.

---

### 6. KMBox (~$30–$60)

**How it works**: Input spoofer / bridge device that emulates mouse and keyboard. Was popular 2022–2023.

| Attribute | Detail |
|-----------|--------|
| **Cost** | $30–$60 |
| **Input method** | USB HID emulation |
| **Setup difficulty** | Low |
| **CarTuning integration** | Medium — serial protocol available |

**Detection status (2025)**: **Highly detected**. Outdated emulation firmware, no meaningful detection bypass updates. Associated with frequent bans and even hardware-level bans in some cases.

**Verdict**: ❌ Obsolete. Do not use. Community consensus is to avoid entirely.

---

## Detection Matrix

> **Last updated**: March 2025. Detection is an arms race — status can change with any anti-cheat update.

| Solution | Type | Cost | Rust (EAC) | Valorant (Vanguard) | CS2 (VAC) | R6 Siege (BattlEye) |
|----------|------|------|------------|---------------------|-----------|---------------------|
| **Razer Synapse** | Software | Free | ❌ Blocked | ❌ Blocked | ❌ Blocked | ❌ Blocked |
| **Interception Driver** | Software (Kernel) | Free | ❌ Blocked | ❌ Blocked | ⚠️ Flagged | ❌ Blocked |
| **AutoHotKey** | Software | Free | ❌ Detected | ❌ Detected | ❌ Detected | ❌ Detected |
| **Logitech Onboard** | Hardware (limited) | Free* | ⚠️ Works (simple) | ⚠️ Works (simple) | ⚠️ Works (simple) | ⚠️ Works (simple) |
| **ReWASD** | Software (Driver) | $7–$17 | ❌ Blocked | ❌ Blocked | ⚠️ Risky | ❌ Blocked |
| **Arduino + Host Shield** | Hardware | $15–$30 | ✅ Low risk | ✅ Low risk* | ✅ Very low risk | ✅ Low risk |
| **Makcu v3** | Hardware | $20–$40 | ✅ Very low | ✅ Very low | ✅ Very low | ✅ Very low |
| **Teensy 4.x** | Hardware | $20–$30 | ✅ Low risk | ✅ Low risk* | ✅ Very low risk | ✅ Low risk |
| **CronusZen** | Hardware | ~$100 | ⚠️ Increasing | ⚠️ High risk | ⚠️ Medium | ❌ Detected |
| **Titan Two** | Hardware | ~$90 | ⚠️ Increasing | ⚠️ High risk | ⚠️ Medium | ❌ Detected |
| **KMBox** | Hardware | $30–$60 | ❌ Detected | ❌ Detected | ❌ Detected | ❌ Detected |

**Legend**: ✅ Currently viable | ⚠️ Partial/risky | ❌ Detected/blocked

\* *Vanguard with Arduino/Teensy requires proper VID/PID spoofing and good humanization to avoid behavioral detection.*

\* *Logitech Onboard requires Logitech mouse hardware.*

---

## Recommendations

### For CarTuning Integration (Ranked)

#### 🥇 1. Arduino Leonardo + USB Host Shield

**Best balance of cost, detection safety, and integration potential.**

- **Why**: Real USB HID hardware — the OS and anti-cheat see a genuine mouse. No software driver to detect. CarTuning's humanization layer (Gaussian jitter, skip events, overcorrections, fatigue falloff) directly addresses the only remaining detection vector: behavioral analysis.
- **Cost**: ~$15–$30 total
- **Integration path**: Add a serial output mode to `generator.py` that streams `ShotData` commands to the Arduino over COM port. Arduino firmware translates serial commands into HID mouse reports.
- **What's needed**:
  - Arduino Leonardo or Pro Micro (ATmega32u4)
  - USB Host Shield (for mouse passthrough)
  - Custom firmware (C++ sketch ~200 lines)
  - Serial protocol definition
  - New output formatter in CarTuning

#### 🥈 2. Makcu v3

**Best plug-and-play option with active anti-detection community.**

- **Why**: Purpose-built for this exact use case. USB passthrough keeps real mouse working. Community maintains firmware updates when anti-cheats evolve.
- **Cost**: ~$20–$40
- **Integration path**: Similar serial protocol approach as Arduino. Makcu has documented APIs.
- **Trade-off**: Less customizable than Arduino. Dependency on community firmware updates.

#### 🥉 3. Teensy 4.x

**Premium option for maximum timing precision.**

- **Why**: ARM Cortex-M7 at 600MHz vs Arduino's ATmega32u4 at 16MHz. Microsecond-precision timing makes humanization timing more granular and realistic.
- **Cost**: ~$20–$30
- **Integration path**: Same as Arduino but with better USB descriptor emulation.
- **Trade-off**: Slightly more complex setup. Overkill for most use cases.

### Not Recommended

| Solution | Why Not |
|----------|---------|
| Interception Driver | Detected and blocked by all 4 anti-cheats. Will prevent game launch. |
| AHK / Synapse / ReWASD | Software injection — same raw input problem, all detected. |
| CronusZen / Titan Two | Expensive, proprietary scripting, increasingly detected. |
| KMBox | Obsolete, highly detected, associated with bans. |

---

## Integration Architecture (Arduino Path)

If pursuing the Arduino route, the CarTuning pipeline would extend as follows:

```
[Weapon JSON] → [generator.py] → [humanizer.py] → [ShotData list]
                                                         │
                                    ┌────────────────────┤
                                    ↓                    ↓
                           [Synapse .txt]         [Serial Stream]
                           (current output)       (new output mode)
                                                         │
                                                         ↓
                                                  [Arduino Leonardo]
                                                         │
                                                         ↓
                                                  [USB HID Mouse Reports]
                                                         │
                                                         ↓
                                                  [Game reads via Raw Input ✅]
```

**New components needed**:
1. `src/formatters/serial_formatter.py` — Serializes `ShotData` into a compact binary protocol
2. `arduino/recoil_hid/recoil_hid.ino` — Arduino firmware that receives serial commands and emits HID mouse reports
3. `src/serial_sender.py` — Real-time serial sender with timing control
4. CLI flag: `--output serial --port COM3`

---

*This document is a technical reference for the CarTuning project. All detection assessments are based on community reports and public information as of March 2025. Detection status changes frequently.*
