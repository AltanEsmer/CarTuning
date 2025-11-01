import type { ParsedMapResponse } from '../services/mapService';

export type PlotlySurfaceData = {
  x: number[];
  y: number[];
  z: number[][];
  type: 'surface';
  colorscale: string;
  colorbar: { title: string };
}

/**
 * Reshape flattened grid array back into 2D grid.
 * @param flat Flattened array of values
 * @param rows Number of rows
 * @param cols Number of columns
 * @returns 2D grid array
 */
export function reshapeGrid(flat: number[], rows: number, cols: number): number[][] {
  const grid: number[][] = [];
  for (let i = 0; i < rows; i++) {
    grid.push(flat.slice(i * cols, (i + 1) * cols));
  }
  return grid;
}

/**
 * Transform parsed map response into Plotly.js surface plot format.
 * @param mapData Parsed map response from API
 * @returns Plotly surface data structure
 */
export function transformToPlotlySurface(mapData: ParsedMapResponse): PlotlySurfaceData {
  const zGrid = reshapeGrid(mapData.z_grid_flat, mapData.shape.rows, mapData.shape.cols);

  return {
    x: mapData.rpm_axis,
    y: mapData.load_axis,
    z: zGrid,
    type: 'surface',
    colorscale: 'Viridis',
    colorbar: { title: 'Timing (degrees)' },
  };
}

