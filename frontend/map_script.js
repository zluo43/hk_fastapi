// --- 1. INITIALIZE THE MAP ---
// The script is deferred, so we can be sure the <div id="map"> exists when this runs.
// Initialize the map and set its view to a default location and zoom level.
// Let's use coordinates for New York City as a starting point for the Citibike data.
const map = L.map('map').setView([40.7128, -74.0060], 12); // Centered on NYC

// --- 2. ADD A TILE LAYER (THE MAP BACKGROUND) ---
// This uses OpenStreetMap tiles. You need to provide attribution.
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// --- 3. HANDLE MAP CLICKS ---
let stationMarkers = L.layerGroup().addTo(map); // A layer group to hold our station markers so we can clear them easily.
let clickMarker; // A variable to hold the marker for the user's click

// This function will be called whenever the user clicks on the map.
function onMapClick(e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    
    // Remove the previous click marker if it exists
    if (clickMarker) {
        map.removeLayer(clickMarker);
    }
    
    // Add a marker at the clicked location
    clickMarker = L.marker([lat, lon]).addTo(map)
        .bindPopup("Searching for nearest stations here.")
        .openPopup();
    
    // Fetch the nearest stations from our FastAPI backend
    fetchNearestStations(lat, lon);
}

// Attach the click event listener to the map
map.on('click', onMapClick);

// --- 4. FUNCTION TO FETCH DATA FROM OUR API ---
async function fetchNearestStations(lat, lon) {
    // Construct the URL for our FastAPI endpoint, including query parameters
    // Make sure your FastAPI server is running on http://127.0.0.1:8000
    const apiUrl = `http://127.0.0.1:8000/nearest-stations/?lat=${lat}&lon=${lon}&count=5`;

    try {
        console.log(`Fetching from: ${apiUrl}`);
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            // If the server response is not OK (e.g., 404, 500), throw an error
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }

        const stations = await response.json();
        
        // Log the stations to the browser's developer console to check the data
        console.log('Received stations:', stations);
        
        // Display the stations on the map
        displayStations(stations);

    } catch (error) {
        console.error('Error fetching nearest stations:', error);
        if (clickMarker) {
            clickMarker.getPopup().setContent(`Error finding stations: ${error.message}`).openOn(map); 
            //openon is a function that opens the popup on the map
        }
    }
}

// --- 5. FUNCTION TO DISPLAY STATIONS ON THE MAP ---
function displayStations(stations) {
    // Clear any previous station markers from the map
    stationMarkers.clearLayers();

    // Check if stations is an array and has items
    if (Array.isArray(stations) && stations.length > 0) {
        stations.forEach(station => {
            // Check if the station has valid latitude and longitude
            if (station.start_lat != null && station.start_lng != null) {
                const marker = L.marker([station.start_lat, station.start_lng]);
                marker.bindPopup(`<b>${station.start_station_name}</b><br>Distance: ~${(station.distance_in_meters).toFixed(2)} km`);
                stationMarkers.addLayer(marker);
            }
        });
         if (clickMarker) {
            clickMarker.getPopup().setContent("Found 5 nearest stations!").openOn(map);
        }
    } else {
         if (clickMarker) {
            clickMarker.getPopup().setContent("No stations found.").openOn(map);
        }
    }
}