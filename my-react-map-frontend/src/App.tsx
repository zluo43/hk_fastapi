import { useState } from 'react'; 
import './App.css';
import MaplibreComponent from './components/MaplibreComponent'; // Import MaplibreComponent

function App() {
  return (
    <div className="app-container">
      <header className="content-block app-header">
        <h1>My Citibike Map</h1>
        <p>Click anywhere on the map to find the nearest stations.</p>
      </header>
      
      <MaplibreComponent />
      
    </div>
  );
}

export default App;
