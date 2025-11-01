import { useState } from 'react';
import { parseMapFile } from '../services/mapService';
import type { ParsedMapResponse } from '../services/mapService';

interface MapUploaderProps {
  onMapParsed: (mapData: ParsedMapResponse) => void;
}

export function MapUploader({ onMapParsed }: MapUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        setSelectedFile(null);
        return;
      }
      setError(null);
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const mapData = await parseMapFile(selectedFile);
      onMapParsed(mapData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse map file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="map-uploader">
      <h2>Upload ECU Map</h2>
      <div className="upload-controls">
        <label htmlFor="file-input" className="file-label">
          {selectedFile ? selectedFile.name : 'Select CSV file'}
        </label>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          disabled={isUploading}
          id="file-input"
        />
        <button onClick={handleUpload} disabled={!selectedFile || isUploading}>
          {isUploading ? 'Parsing...' : 'Parse Map'}
        </button>
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

