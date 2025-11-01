import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export type ParsedMapResponse = {
  rpm_axis: number[];
  load_axis: number[];
  z_grid_flat: number[];
  shape: { rows: number; cols: number };
  total_points: number;
};

/**
 * Parse a CSV map file by uploading it to the backend API.
 * @param file The CSV file to parse
 * @returns Promise resolving to parsed map data
 * @throws Error if upload or parsing fails
 */
export async function parseMapFile(file: File): Promise<ParsedMapResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post<ParsedMapResponse>(
      `${API_BASE_URL}/api/maps/parse`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        throw new Error(
          error.response.data.detail || `Server error: ${error.response.status}`
        );
      } else if (error.request) {
        throw new Error('Network error: Could not reach the backend server');
      }
    }
    throw error instanceof Error ? error : new Error('Unknown error occurred');
  }
}

