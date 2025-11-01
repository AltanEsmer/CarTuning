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

### ECU Map Lab (Phase 3 - Advanced)

An advanced web-based ECU map analysis platform for deep study of car tuning concepts. This platform provides a reproducible, extensible environment for loading, analyzing, visualizing, and optimizing ignition/fuel/boost maps without requiring any hardware. Built with FastAPI backend and designed for intermediate to advanced tuning study.

**Key Learning Points:**
- How ECU maps are structured and represented (gridded vs flat lists)
- Map interpolation, smoothing, and masking techniques
- Interactive 3D visualization of tuning effects
- Difference map analysis (stock vs tuned)
- Safety constraints and performance optimization modeling
- Web API design and testing practices

**Project Structure:**
```
maplab/
├── maplab-backend/     # FastAPI backend with map parsing, analysis, and optimization APIs
├── maplab-frontend/    # React frontend for interactive visualization (to be implemented)
├── notebooks/          # Jupyter notebooks for step-by-step map transformations
├── sample_data/        # Sample stock and tuned map CSV files
└── scripts/            # Mock data generator and utility scripts
```

**Quick Start:**

1. Navigate to the backend directory:
```bash
cd maplab/maplab-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or: source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate sample data:
```bash
cd ../scripts
python create_mock_map.py
```

5. Run the FastAPI server:
```bash
cd ../maplab-backend
uvicorn app.main:app --reload
```

6. (Optional) Run the frontend application:
```bash
cd ../maplab-frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to use the web interface.

7. Test the API:
   - Visit `http://localhost:8000/docs` for interactive API documentation
   - Use the `/api/maps/parse` endpoint to parse map CSV files
   - Upload a file or provide a file path to get grid data as JSON
   - Or use the frontend to upload and visualize maps in 3D

**CSV Format:**
Maps should be in tidy CSV format with columns:
- `RPM` (numeric) - Engine RPM values
- `Load` (numeric) - Engine load percentage
- `Timing` (numeric) - Ignition timing values

Example:
```csv
RPM,Load,Timing
1000,20,3.0
2000,20,4.0
1000,40,5.0
2000,40,6.0
```

**Features Implemented:**
- ✅ CSV map parsing with deduplication and NaN handling
- ✅ FastAPI REST endpoint for map parsing
- ✅ Grid interpolation using scipy
- ✅ Comprehensive pytest test suite
- ✅ Mock data generator
- ✅ React frontend with 3D visualization (Plotly.js)
- ✅ Interactive map upload and visualization

**Features Coming Soon:**
- Difference map computation
- Constrained optimizer for safe timing adjustments
- Map comparison (stock vs tuned)
- Map editing capabilities

**Testing:**
```bash
cd maplab/maplab-backend
pytest tests/
```

For detailed API documentation, see the FastAPI auto-generated docs at `http://localhost:8000/docs` when the server is running.

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


## Ignition Timing Map 3D Visualizer

Python 3.11 application to load ignition timing maps from CSV, convert them into 2D grids, and visualize them as interactive 3D surfaces. Built for incremental learning with clear milestones.

### Setup

1. Create and activate a virtual environment (Windows PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

### Quickstart

1. Generate mock data (after the script is created in the next milestone):
```powershell
python scripts/create_mock_map.py
```

2. Run the app:
```powershell
python -m visualizer.app
```

You should see a window. Click "Load Stock Map" to render the 3D surface from `stock_map.csv`.

### CSV Format

Tidy rows with columns:
- `RPM` (numeric)
- `Load` (numeric)
- `Timing` (numeric)

Example row:
```
RPM,Load,Timing
2000,40,6.0
```