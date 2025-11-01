import { useState } from 'react';
import { MapUploader } from './components/MapUploader';
import { Map3DViewer } from './components/Map3DViewer';
import type { ParsedMapResponse } from './services/mapService';
import './App.css';

function App() {
  const [mapData, setMapData] = useState<ParsedMapResponse | null>(null);

  const handleMapParsed = (data: ParsedMapResponse) => {
    setMapData(data);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>ECU Map Lab</h1>
        <p>3D Visualization of Ignition Timing Maps</p>
      </header>
      <main className="app-main">
        <aside className="upload-section">
          <MapUploader onMapParsed={handleMapParsed} />
        </aside>
        <section className="visualization-section">
          <Map3DViewer mapData={mapData} />
        </section>
      </main>
    </div>
  );
}

export default App;
