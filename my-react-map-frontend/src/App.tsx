import { useState } from 'react'; 
import './App.css';
import MapComponent from './components/MapComponent'; // <-- Step 1: Import the new component

function App() {
  return (
    <div className="app-container">
      <header className="content-block app-header">
        <h1>My Citibike Map</h1>
        <p>Click anywhere on the map to find the nearest stations.</p>
      </header>

      {/* Step 2: Replace the old placeholder div 
        with our actual, self-contained MapComponent.
      */}
      <MapComponent />
      
    </div>
  );
}

export default App;
