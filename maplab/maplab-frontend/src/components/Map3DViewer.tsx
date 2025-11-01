import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { ParsedMapResponse } from '../services/mapService';
import { transformToPlotlySurface } from '../utils/mapTransform';

// Plotly layout type
type PlotlyLayout = {
  title?: string;
  scene?: {
    xaxis?: { title?: string };
    yaxis?: { title?: string };
    zaxis?: { title?: string };
    camera?: { eye?: { x?: number; y?: number; z?: number } };
  };
  width?: number;
  height?: number;
  margin?: { l?: number; r?: number; t?: number; b?: number };
  [key: string]: unknown;
};

interface Map3DViewerProps {
  mapData: ParsedMapResponse | null;
}

export function Map3DViewer({ mapData }: Map3DViewerProps) {
  const plotData = useMemo(() => {
    if (!mapData) {
      return [];
    }
    return [transformToPlotlySurface(mapData)];
  }, [mapData]);

  const layout: PlotlyLayout = useMemo(
    () => ({
      title: 'ECU Ignition Timing Map',
      scene: {
        xaxis: { title: 'RPM' },
        yaxis: { title: 'Load (%)' },
        zaxis: { title: 'Timing (degrees)' },
        camera: {
          eye: { x: 1.5, y: 1.5, z: 1.5 },
        },
      },
      width: 900,
      height: 700,
      margin: { l: 0, r: 0, t: 50, b: 0 },
    }),
    []
  );

  if (!mapData) {
    return (
      <div className="map-viewer-empty">
        <p>Upload a CSV map file to visualize it in 3D</p>
      </div>
    );
  }

  return (
    <div className="map-viewer">
      <Plot data={plotData} layout={layout} />
    </div>
  );
}

