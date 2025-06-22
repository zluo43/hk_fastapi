// src/components/MaplibreComponent.tsx

import { useState, useEffect } from 'react';
// Popup is no longer imported
import { Map, Marker, useControl } from 'react-map-gl/maplibre'; 
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { DeckProps } from '@deck.gl/core';
import type { Map as MaplibreMap } from 'maplibre-gl';


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

// --- The DeckGLOverlay helper component from the docs ---
function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));   
  overlay.setProps(props);
  return null;
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
  // --- State management ---
  const [clickPosition, setClickPosition] = useState<ClickLocation | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // REMOVED: clickedInfo state is no longer needed
  const [is3dMode, setIs3dMode] = useState(false);
  const [mapInstance, setMapInstance] = useState<MaplibreMap | null>(null);

  const mapStyle = `https://api.maptiler.com/maps/basic-v2/style.json?key=STVg28Oko0bVi9bDtnov`;
  
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

  // --- Tooltip function ---
  const getTooltipContent = ({ object }) => {
    if (!object) return null;
    const station = object as Station;
    return {
      html: `<div><b>${station.start_station_name}</b><br/>Ride Count: ${station.ride_count?.toLocaleString()}</div>`,
      style: { backgroundColor: '#333', color: 'white', fontSize: '12px', borderRadius: '4px', padding: '8px' }
    };
  };
  
  // --- Define the deck.gl layer for our stations ---
  const layers = [
    new ScatterplotLayer({
      id: 'station-scatterplot',
      data: stations,
      getPosition: (d: Station) => [d.start_lng, d.start_lat],
      getFillColor: [255, 0, 0, 200],
      getRadius: 15,
      radiusMinPixels: 4,
      pickable: true,
      // The onClick for the layer can be simplified or removed if not needed
      onClick: (info) => console.log("Clicked on station dot:", info.object.start_station_name),
    })
  ];

  // --- A single, unified click handler ---
  const handleMapClick = (info) => {
    // Check if the click was on the basemap (not on a station dot)
    if (!info.object) {
      console.log('Clicked on the basemap');
      const { lng, lat } = info.coordinate;
      setClickPosition({ lat, lng });
      fetchStations(lat, lng);
    }
  };

  // --- Function to handle the 3D toggle ---
  const toggle3dView = () => {
    setIs3dMode(prev => !prev);
  };

  // --- useEffect to command the map when 3D mode changes ---
  useEffect(() => {
    if (!mapInstance) return;

    mapInstance.flyTo({
        pitch: is3dMode ? 45 : 0,
        bearing: is3dMode ? -17.6 : 0,
        essential: true
    });

    const existingLayer = mapInstance.getLayer('3d-buildings');

    if (is3dMode && !existingLayer) {
      const firstSymbolId = mapInstance.getStyle().layers.find(l => l.type === 'symbol')?.id;
      mapInstance.addLayer({
        'id': '3d-buildings', 'source': 'openmaptiles', 'source-layer': 'building', 'type': 'fill-extrusion', 'minzoom': 15,
        'paint': {
          'fill-extrusion-color': '#aaa', 'fill-extrusion-height': ['get', 'render_height'],
          'fill-extrusion-base': ['get', 'render_min_height'], 'fill-extrusion-opacity': 0.6
        }
      }, firstSymbolId);
    } else if (!is3dMode && existingLayer) {
      mapInstance.removeLayer('3d-buildings');
    }
  }, [is3dMode, mapInstance]);

  return (
    <div className="map-wrapper">
      <div className="controls-bar">
        <button onClick={toggle3dView}>
          {is3dMode ? '2D View' : '3D View'}
        </button>
      </div>

      <Map
        initialViewState={INITIAL_VIEW_STATE}
        style={{ width: '100%', height: '100%' }}
        mapStyle={mapStyle}
        onLoad={e => setMapInstance(e.target)}
      >
        <DeckGLOverlay 
          layers={layers} 
          getTooltip={getTooltipContent}
          onClick={handleMapClick} // Use the unified handler here
        />
        
        {clickPosition && (
          <Marker longitude={clickPosition.lng} latitude={clickPosition.lat} anchor="bottom">
             <div style={{ fontSize: '24px' }}>🧍</div>
          </Marker>
        )}

        {/* REMOVED: The Popup component and its logic are gone */}
      </Map>
    </div>
  );
};

export default MapComponent;
