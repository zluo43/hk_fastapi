// src/components/MapComponent.tsx

import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Icon fix for bundlers
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;


// --- TypeScript interfaces for our data structures ---
interface Station {
  start_station_name: string;
  start_lat: number;
  start_lng: number;
  distance_in_meters: number; // Updated from distance_in_degrees
}

interface ClickLocation {
  lat: number;
  lng: number;
}


// --- Helper component to handle map clicks and trigger the data fetch ---
function MapClickHandler({ setPosition, fetchStations }) {
  const map = useMapEvents({
    click(e) {
      setPosition(e.latlng);
      fetchStations(e.latlng.lat, e.latlng.lng);
      map.flyTo(e.latlng, map.getZoom());
    },
  });
  return null;
}


const MapComponent = () => {
  const [clickPosition, setClickPosition] = useState<ClickLocation | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStations = async (lat: number, lng: number) => {
    setIsLoading(true);
    setError(null);
    setStations([]);

    // --- THIS IS THE UPDATED LINE ---
    // The URL now includes the "/stations" prefix from our FastAPI router.
  const apiUrl = `https://effective-space-umbrella-5rpjvxvx5xq29jw-8000.app.github.dev/stations/nearest?lat=${lat}&lon=${lng}&count=5`;

    try {
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        mode: 'cors', // Explicitly state we want CORS
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      const data: Station[] = await response.json();
      setStations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error("Failed to fetch stations:", err);
      // Log more details about the error for debugging
      if (err instanceof Error) {
        console.error("Error name:", err.name);
        console.error("Error message:", err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="map-wrapper">
      <MapContainer 
          center={[40.7128, -74.0060]} 
          zoom={13} 
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapClickHandler 
          setPosition={setClickPosition} 
          fetchStations={fetchStations}
        />

        {clickPosition && (
          <Marker position={clickPosition}>
            <Popup>
              {isLoading && "Searching..."}
              {error && `Error: ${error}`}
              {!isLoading && !error && "Searched from here"}
            </Popup>
          </Marker>
        )}

        {stations.map((station, index) => (
          <Marker 
            key={index}
            position={[station.start_lat, station.start_lng]}
          >
            <Popup>
              <b>{station.start_station_name}</b>
              <br/>
              {/* Use the updated distance_in_meters field */}
              Distance: {station.distance_in_meters.toFixed(0)} meters
            </Popup>
          </Marker>
        ))}
        
      </MapContainer>
    </div>
  );
};

export default MapComponent;