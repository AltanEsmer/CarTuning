# Car Tuning Simulations

A collection of Python simulations and interactive tools for learning car tuning concepts. Each simulation demonstrates different aspects of automotive engineering, engine behavior, and performance tuning.

## Purpose

This repository contains educational simulations designed to help beginners understand car tuning fundamentals through hands-on, interactive examples. Each simulation focuses on specific concepts and provides clear explanations and comments.

## Available Simulations

### Car Dashboard Simulator (Phase 1)

A real-time dashboard simulator that demonstrates the relationship between throttle position, RPM (Revolutions Per Minute), and engine temperature. This simulation helps you understand how basic engine parameters interact during operation.

**Key Learning Points:**
- How throttle input affects engine RPM
- Engine temperature buildup during operation
- Real-time data visualization

**Quick Start:**
```bash
cd car-dashboard-simulator
python dashboard.py
```

For detailed information, see the [Car Dashboard Simulator README](car-dashboard-simulator/README.md).

### Mini ECU Simulator (Phase 2)

An advanced ECU simulator that demonstrates engine tuning concepts including torque calculation, Air-Fuel Ratio (AFR) management, and Stage 1 tuning effects. This simulation features real-time data visualization using matplotlib and interactive controls for hands-on learning.

**Key Learning Points:**
- How ECU (Engine Control Unit) manages engine performance
- Torque calculation and its relationship to RPM and throttle
- Air-Fuel Ratio (AFR) optimization for different load conditions
- Stage 1 tuning effects on power and torque output
- Real-time data plotting with matplotlib
- Interactive GUI with ttk widgets

**Quick Start:**
```bash
cd mini-ecu-simulator
python ecu_app.py
```

For detailed information, see the [Mini ECU Simulator README](mini-ecu-simulator/README.md).

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)
- matplotlib (install via `pip install matplotlib`)

## Project Structure

Each simulation is contained in its own folder with:
- Implementation code with detailed educational comments
- A dedicated README explaining concepts and usage
- Clear explanations suitable for beginners

## Contributing

This is a learning project. Feel free to explore, modify, and experiment with the code!

## License

See [LICENSE](LICENSE) file for details.

