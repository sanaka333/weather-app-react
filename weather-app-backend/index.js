
const express = require('express'); // Import Express (web server framework)
const axios = require('axios'); // Import Axios (to call external APIs)
const cors = require('cors'); // Import CORS middleware (allow requests from other origins)
require('dotenv').config();  // Load environment variables from .env 

const app = express();  // Create an Express app instance
const PORT = 3001; // Port number this server will use

app.use(cors()); // Enable CORS for all routes
app.use(express.json()); // Parse JSON bodies on incoming requests

app.get('/geocode', async (req, res) => { // Define a GET route at /geocode (async so we can await)
  const { location } = req.query; // Read ?location=... from the URL query string
  if (!location) return res.status(400).json({ error: 'location query param is required' });  // …send 400 Bad Request with a JSON error and stop.

  try {
    const { data } = await axios.get('https://api.openweathermap.org/geo/1.0/direct', { // Call OpenWeather's geocoding API and wait for the response
      params: { 
        q: location, // "q" is the city name the user searched (from frontend)
        limit: 1, // tell the API: only give me 1 best match
        appid: process.env.OPENWEATHER_API_KEY, // your secret API key (stored in .env file)
      },
    });
    res.json(data); // Send the API’s data back to the frontend as JSON
  } catch (err) { // If anything above throws an error…
    console.error('Geocode error:', err?.response?.status, err?.message); // Log details for debugging, (optional chaining) status code if present, Error message if present
    res.status(500).json({ error: 'Geocoding failed' }); // Tell the client it failed (HTTP 500)
  }
});

// Define a GET endpoint at '/forecast'. This will be called when the client requests forecast data.
app.get('/forecast', async (req, res) => {

  // Extract 'lat' (latitude) and 'lon' (longitude) from the request query parameters.
  const { lat, lon, unit } = req.query;

  // If either 'lat' or 'lon' is missing, immediately return a 400 Bad Request error response.
  if (!lat || !lon) return res.status(400).json({ error: 'lat and lon are required' });

  console.log("Fetching weather with units:", unit); // log inside the route

  try {
    // Use axios to call the OpenWeatherMap API with the provided latitude and longitude.
    // The response is destructured to directly get 'data' from the returned object.
    const { data } = await axios.get('https://api.openweathermap.org/data/2.5/forecast', {
      params: {
        lat,  // Pass latitude from the query
        lon,  // Pass longitude from the query
        units: unit,  // Use imperial units (Fahrenheit, miles, etc.)                         
        appid: process.env.OPENWEATHER_API_KEY, // Use API key stored in environment variable
      },
    });
    res.json(data); // Send the API’s data back to the frontend as JSON
  } catch (err) { // If anything above throws an error…
    console.error('Forecast error:', err?.response?.status, err?.message); // If the API call fails, log the error message and status code to the server console.
    res.status(err?.response?.status || 500).json({ error: 'Failed to reach forecast' });  // Send an error response to the client/frontend with the status code from the API error if available,
                                                                                           // otherwise default to 500 (Internal Server Error).
  }
});

// Register a GET route at path '/weather'.
// Mark the handler as async so we can use 'await' inside it.
app.get('/weather', async (req, res) => {

  // Pull latitude and longitude from the query string object (e.g., ?lat=...&lon=...).
  const { lat, lon, unit } = req.query;

  // Guard clause: if either value is missing, stop here and send 400 Bad Request.
  // 'return' ensures the rest of the handler does not run.
  if (!lat || !lon) return res.status(400).json({ error: 'lat and lon are required' });

  try {
    // Make a request to OpenWeatherMap's *current weather* endpoint.
    // Destructure the axios response so we get only the 'data' field.
    // The second argument 'params' becomes the URL query string automatically.
    const { data } = await axios.get('https://api.openweathermap.org/data/2.5/weather', {
      params: {
        lat,      // forward the provided latitude
        lon,      // forward the provided longitude
        units: unit,   // use Fahrenheit/mph (always imperial)
        appid: process.env.OPENWEATHER_API_KEY,  // API key read from environment
      },
    });

    // Send the JSON data from OpenWeatherMap straight back to the client/frontend.
    res.json(data);
  } catch (err) {
     // Log useful debug info on the server.
    // '?.' is optional chaining: safely read nested properties if they exist.
    console.error('Weather error:', err?.response?.status, err?.message);

    // If the upstream API returned a status, reuse it; otherwise default to 500.
    // Then send a simple error payload to the client.
    res.status(err?.response?.status || 500).json({ error: 'Failed to fetch current weather' });
  }
});

// Start the Express server and make it listen on the specified PORT number
app.listen(PORT, () => {

    // Log a message to the terminal once the server is running successfully
    // Using a template string (backticks) so we can insert the PORT value dynamically
    // Example output: "Server running on http://localhost:3001"
    console.log(`Server running on http://localhost:${PORT}`);
});




