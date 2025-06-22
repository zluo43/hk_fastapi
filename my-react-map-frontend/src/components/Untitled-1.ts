// src/components/MaplibreComponent.tsx

import { useState } from 'react';
// --- THIS IS THE FIX ---
// Import Popup alongside Map and Marker.
import { Map, Marker, Popup } from 'react-map-gl/maplibre'; 
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';

// --- Define TypeScript interfaces for our data ---
interface Station {
  start_station_name: string;
  start_lat: number;
  start_lng: number;
  distance_in_meters: number;
  ride_count?: number;
}

interface ClickLocation {
  lat: number;
  lng: number;
}

// --- Interface for the hover information ---
interface HoverInfo {
  x: number;
  y: number;
  object: Station;
}

// --- Define the initial state for the map's viewport ---
const INITIAL_VIEW_STATE = {
  longitude: -74.0060,
  latitude: 40.7128,
  zoom: 12,
  pitch: 0,
  bearing: 0
};

// --- Your main Map Component ---
const MapComponent = () => {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  
  // --- State management ---
  const [clickPosition, setClickPosition] = useState<ClickLocation | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
  const [clickedInfo, setClickedInfo] = useState<Station | null>(null);

  const mapStyle = 'https://api.maptiler.com/maps/dataviz/style.json?key=STVg28Oko0bVi9bDtnov';
  
  // --- Data fetching logic ---
  const fetchStations = async (lat: number, lng: number) => {
    setIsLoading(true);
    setError(null);
    setStations([]);
    const apiUrl = `https://effective-space-umbrella-5rpjvxvx5xq29jw-8000.app.github.dev/stations/nearest?lat=${lat}&lon=${lng}&count=5`;
    try {
      const response = await fetch(apiUrl);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API Error: ${response.statusText}`);
      }
      const data: Station[] = await response.json();
      setStations(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Map click handler ---
  const handleMapClick = (evt: any) => {
    setClickedInfo(null);
    if (evt.coordinate) {
      const [lng, lat] = evt.coordinate;
      setClickPosition({ lat, lng });
      fetchStations(lat, lng);
    }
  };
  
  // --- Define the deck.gl layer for our stations ---
  const layers = [
    new ScatterplotLayer({
      id: 'station-scatterplot',
      data: stations,
      getPosition: (d: Station) => [d.start_lng, d.start_lat],
      getFillColor: [255, 0, 0, 200],
      getRadius: 50,
      radiusMinPixels: 4,
      pickable: true,
      onHover: info => setHoverInfo(info),
      onClick: info => setClickedInfo(info.object), 
    })
  ];

  return (
    <div className="map-wrapper">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        onClick={handleMapClick}
        getCursor={({ isHovering }) => (isHovering ? 'pointer' : 'crosshair')}
        onViewStateChange={e => setViewState(e.viewState)}
        style={{ position: 'relative' }} 
      >
        <Map mapStyle={mapStyle}>
            {clickPosition && (
              <Marker longitude={clickPosition.lng} latitude={clickPosition.lat} anchor="bottom">
                 <div style={{ color: 'blue', fontSize: '24px' }}>📍</div>
              </Marker>
            )}

            {/* This will now render correctly because Popup is imported */}
            {clickedInfo && (
              <Popup 
                longitude={clickedInfo.start_lng} 
                latitude={clickedInfo.start_lat}
                anchor="top"
                onClose={() => setClickedInfo(null)}
                closeOnClick={false}
              >
                <b>{clickedInfo.start_station_name}</b>
                <div>Ride Count: {clickedInfo.ride_count?.toLocaleString()}</div>
              </Popup>
            )}
        </Map>

        {/* --- Render the hover tooltip conditionally --- */}
        {hoverInfo && hoverInfo.object && !clickedInfo && (
          <div className="tooltip" style={{ left: hoverInfo.x, top: hoverInfo.y }}>
            <b>{hoverInfo.object.start_station_name}</b>
            <div>Ride Count: {hoverInfo.object.ride_count?.toLocaleString()}</div>
            <div>Distance: {hoverInfo.object.distance_in_meters.toFixed(0)}m</div>
          </div>
        )}
      </DeckGL>
    </div>
  );
};

export default MapComponent;