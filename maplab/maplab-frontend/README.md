# ECU Map Lab - Frontend

React frontend application for visualizing ECU ignition timing maps in 3D.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure API URL (optional):
   - Copy `.env.example` to `.env` if you need to change the backend URL
   - Default backend URL is `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Usage

1. Make sure the FastAPI backend is running (see `../maplab-backend/README.md`)
2. Open the frontend application in your browser
3. Click "Select CSV file" and choose an ECU map CSV file
4. Click "Parse Map" to upload and visualize the map
5. Interact with the 3D plot: rotate, zoom, and pan to explore the timing map

## CSV Format

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

## Project Structure

```
src/
├── components/      # React components
│   ├── MapUploader.tsx    # File upload component
│   └── Map3DViewer.tsx     # 3D visualization component
├── services/        # API service layer
│   └── mapService.ts      # Backend API calls
├── utils/          # Utility functions
│   └── mapTransform.ts    # Map data transformation
├── App.tsx         # Main application component
└── main.tsx        # Application entry point
```

## Technologies

- React 19 with TypeScript
- Vite (build tool)
- Plotly.js (3D visualization)
- Axios (HTTP client)

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
