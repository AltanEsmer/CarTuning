# Mini ECU Simulator (Phase 2)

A real-time Python simulation that demonstrates advanced Engine Control Unit (ECU) concepts, including torque calculation, Air-Fuel Ratio (AFR) management, and Stage 1 tuning effects. This interactive simulator helps you understand how modern ECUs manage engine performance through interactive controls and live data visualization.

## What This Simulation Demonstrates

This simulation models advanced engine behavior and ECU tuning:

1. **Throttle → RPM → Torque Relationship**: How throttle input affects engine RPM, which in turn determines torque output. Higher throttle and RPM produce more torque, giving the engine more "pulling power."

2. **Air-Fuel Ratio (AFR) Management**: How the ECU adjusts the air-fuel mixture based on engine load. Normal driving uses stoichiometric ratio (14.7:1), while high load uses richer mixtures (12.0-12.5:1) for power and protection.

3. **Stage 1 Tuning Effects**: See how ECU remapping increases torque by approximately 15% and adjusts AFR for optimal performance. Compare tuned vs. stock behavior in real-time.

4. **Real-Time Data Visualization**: Watch torque output graphed in real-time using matplotlib, showing how engine performance changes dynamically.

## Key Concepts Explained

### ECU (Engine Control Unit)

- **What it is**: The "brain" of the engine - a computer that manages fuel injection, ignition timing, air-fuel ratio, and other engine parameters
- **Why it matters**: The ECU constantly adjusts engine behavior to optimize performance, fuel economy, and emissions while protecting the engine from damage
- **Tuning**: ECU remapping modifies the ECU's software to extract more performance from the engine, often without hardware changes

### Torque

- **What it is**: Rotational force produced by the engine, measured in Newton-meters (Nm)
- **Real-world meaning**: Torque determines acceleration and pulling power. More torque = faster acceleration and better towing capability
- **How it's calculated**: In this simulation, torque = (RPM/100) × (Throttle/100). Real engines have more complex torque curves
- **Typical values**: 
  - Small car: 150-250 Nm
  - Performance car: 300-600 Nm
  - High-performance: 600-1000+ Nm
- **Torque vs. Horsepower**: Torque is the "muscle" (rotational force), horsepower is torque × RPM (overall power output)

### Air-Fuel Ratio (AFR)

- **What it is**: The ratio of air to fuel in the combustion mixture
- **Stoichiometric (14.7:1)**: The "perfect" ratio where all fuel and air are completely burned
  - Used for normal driving
  - Provides good balance of power, efficiency, and low emissions
- **Rich Mixture (Lower AFR, e.g., 12.0-12.5:1)**: More fuel relative to air
  - Used under high load (full throttle)
  - Prevents engine knock (detonation)
  - Cools combustion chamber
  - Produces maximum power
  - Less fuel-efficient
- **Lean Mixture (Higher AFR, e.g., 15.5+:1)**: Less fuel relative to air
  - Better fuel economy
  - Can cause engine knock and damage if too lean
  - Not commonly used in performance scenarios

### Stage 1 Tuning

- **What it is**: The most basic ECU remap that modifies the engine's software to increase power and torque
- **Typical gains**: 10-20% increase in torque and power
- **What it changes**:
  - Ignition timing (when spark plugs fire)
  - Fuel delivery (more fuel at high load)
  - Boost pressure (if turbocharged)
  - Air-fuel ratio optimization
- **Requirements**: Usually no hardware modifications needed (unless your car is very old or modified)
- **Reversibility**: Can be flashed back to stock (though in real cars, you'd need a tuner to do this)
- **Why we can toggle it**: In this simulation, we allow toggling to compare tuned vs. stock performance in real-time - a great educational tool!

### RPM (Revolutions Per Minute)

- **What it is**: How many times the engine's crankshaft completes a full rotation per minute
- **Idle RPM**: 600-900 RPM (engine running but not accelerating)
- **Redline**: Maximum safe RPM (in this simulation: 7000 RPM). Exceeding redline can damage the engine
- **Operating Range**: Most engines operate efficiently between 2000-6000 RPM
- **Torque and RPM**: Torque typically peaks in the mid-RPM range, then decreases at very high RPM

## How to Run

1. **Install dependencies** (if not already installed):
   ```bash
   pip install matplotlib
   ```
   Note: tkinter is usually included with Python installations.

2. **Navigate to the simulation folder:**
   ```bash
   cd mini-ecu-simulator
   ```

3. **Run the simulator:**
   ```bash
   python ecu_app.py
   ```

## GUI Layout

### Left Side: Controls

- **Throttle Slider**: Vertical slider (0-100%) that simulates the accelerator pedal
  - Move it up to increase throttle
  - Move it down to decrease throttle
  - Watch the throttle percentage display update in real-time

- **Toggle Stage 1 Tune Button**: Click to enable/disable Stage 1 ECU tuning
  - Toggle it on and watch torque increase
  - Toggle it off to return to stock performance
  - Compare the difference in real-time!

### Right Side: Engine Data & Plot

- **RPM Display**: Current engine speed (updates in real-time)
  - Formatted with commas for readability (e.g., "3,500 RPM")

- **Torque Display**: Current torque output in Newton-meters
  - Shows how much rotational force the engine is producing
  - Watch it change with throttle and tuning

- **Air-Fuel Ratio Display**: Current AFR value
  - 14.7 = Stoichiometric (normal driving)
  - 12.0-12.5 = Rich (high load)

- **Tune Status Display**: Shows if Stage 1 tuning is Active or Inactive

- **Real-Time Torque Plot**: Matplotlib graph showing torque over time
  - Scrolls continuously, showing the last 50 data points
  - Watch how torque responds to throttle changes
  - See the difference when tuning is enabled

## Experiment and Learn

Try these experiments to understand the relationships:

### Experiment 1: Throttle Response
1. Slowly increase the throttle slider from 0% to 100%
2. Observe:
   - RPM increases proportionally with throttle
   - Torque increases (both RPM and throttle affect torque)
   - AFR stays at 14.7 until throttle reaches 80%, then drops to 12.5
   - Watch the torque graph rise

### Experiment 2: Stage 1 Tuning Effect
1. Set throttle to 50%
2. Note the current torque value
3. Click "Toggle Stage 1 Tune" to enable tuning
4. Observe:
   - Torque increases by approximately 15%
   - RPM remains the same (tuning doesn't change RPM directly)
   - See the difference in the torque plot (line moves up)

### Experiment 3: High Load AFR
1. Set throttle to 100% (full throttle)
2. Observe:
   - AFR drops to 12.5 (rich mixture for high load)
   - Torque is at maximum
3. Toggle Stage 1 Tune ON
4. Observe:
   - AFR drops further to 12.0 (even richer for tuned high load)
   - Torque increases further

### Experiment 4: RPM Decay
1. Set throttle to 100% and let RPM climb to near redline
2. Quickly set throttle to 0%
3. Observe:
   - RPM slowly decreases back to 800 (idle)
   - Torque decreases as RPM decreases
   - This simulates engine braking and natural friction

### Experiment 5: Tuned vs. Stock Comparison
1. With tuning OFF, set throttle to 75%
2. Note the torque value (e.g., "250 Nm")
3. Toggle tuning ON
4. Compare the new torque value (e.g., "287.5 Nm" - 15% increase)
5. Watch the torque plot to see the visual difference

## Code Structure

- **`engine_simulator.py`**: Contains the `EngineSimulator` class that models engine behavior
  - Handles RPM calculations based on throttle
  - Calculates torque based on RPM, throttle, and tuning status
  - Manages Air-Fuel Ratio adjustments
  - All logic is thoroughly commented for learning

- **`ecu_app.py`**: Contains the tkinter GUI (`ECUSimulatorApp` class) and matplotlib plot
  - Creates the visual interface with ttk widgets
  - Connects controls to the engine simulator
  - Manages real-time updates (50ms intervals)
  - Handles matplotlib plot updates

## Educational Comments

The code includes extensive comments explaining:
- What each parameter means in real engines
- Why certain calculations are used
- How ECUs work in practice
- Real-world tuning concepts and terminology
- Technical details about AFR, torque, and RPM relationships

This makes it perfect for learning both Python programming (GUI development, matplotlib, real-time updates) and automotive engineering concepts (ECU tuning, engine management, performance optimization)!

## Technical Details

- **Update Frequency**: 20 updates per second (50ms intervals)
- **RPM Range**: 800 (idle) to 7000 (redline)
- **Throttle Range**: 0% (closed) to 100% (fully open)
- **Torque Calculation**: `torque = (RPM/100) × (Throttle/100) × 1.15 (if tuned)`
- **AFR Ranges**: 
  - Normal: 14.7 (stoichiometric)
  - High load: 12.5 (rich)
  - Tuned high load: 12.0 (richer)
- **Plot Buffer**: 50 data points (scrolling graph effect)
- **Window Size**: 800×600 pixels

## Real-World Context

This simulator demonstrates concepts used in:
- **Professional ECU Tuning**: Tuners use software to modify ECU maps, similar to our Stage 1 toggle
- **Performance Diagnostics**: Mechanics use data logging (like our plot) to analyze engine performance
- **Engine Management Systems**: Modern cars use sophisticated algorithms (like our AFR logic) to optimize performance
- **Racing Applications**: Professional racing teams constantly tune ECUs to extract maximum performance

## Next Steps in Learning

Once you understand these concepts, you might explore:
- **Stage 2/3 Tuning**: More aggressive tuning requiring hardware modifications (intercoolers, exhaust, turbo upgrades)
- **Ignition Timing**: How spark timing affects power and efficiency
- **Boost Control**: How turbocharger boost pressure affects torque (for turbo engines)
- **Dyno Testing**: Real-world torque curves and how they differ from our simplified model
- **Transmission Tuning**: How ECU affects automatic transmission shift points
- **Launch Control & Traction Control**: Advanced ECU features for performance driving

## Differences from Phase 1

Phase 1 (Car Dashboard Simulator) focused on basic concepts:
- Throttle → RPM relationship
- Engine temperature buildup
- Simple real-time display

Phase 2 (Mini ECU Simulator) adds:
- **Torque calculation and visualization** (more advanced engine concept)
- **Air-Fuel Ratio management** (ECU tuning concept)
- **Stage 1 tuning effects** (performance modification concept)
- **Matplotlib real-time plotting** (advanced visualization)
- **More detailed GUI** (ttk widgets, better layout)

Both simulations are educational and complement each other!

Enjoy learning about ECU tuning and engine management!

