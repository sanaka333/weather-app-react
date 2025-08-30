// Core React imports
import React, {useState} from 'react'

// HTTP client for API requests
import axios from 'axios';

// React Query hook
import { keepPreviousData, useQuery } from '@tanstack/react-query';

// Import loading spinner component for showing loading states
import { ClipLoader } from 'react-spinners';

// Background video assets for different weather conditions
import ClearVideo from './assets/Clear.mp4';
import CloudyVideo from './assets/Cloudy.mp4';
import RainVideo from './assets/Rain.mp4';
import ThunderStormVideo from './assets/Thunderstorm.mp4';
import SnowyVideo from './assets/Snowy.mp4';
import DrizzleVideo from './assets/Drizzle.mp4';
import MistyVideo from './assets/Misty.mp4';

// Main application component
function App() {

  // State: stores the city name entered by the user
  const [location, setLocation] = useState('')

  // State: stores detailed location info (lat, lon, timezone, etc.)
  const [locationInfo, setLocationInfo] = useState({});

  // State: tracks whether the background video has finished loading
  const [videoLoaded, setVideoLoaded] = useState(false);

  // State: temperature unit ('imperial' = °F, 'metric' = °C)
  const [unit, setUnit] = useState('imperial');

  // Temperature unit symbol (°F or °C)
  const unitSymbol = unit === 'imperial' ? '°F' : '°C';

  // Wind speed unit label (MPH or m/s)
  const windUnit  = unit === 'imperial' ? 'MPH' : 'm/s';

  // Query current weather data with React Query
  // - Uses locationInfo (lat/lon) + selected unit (metric/imperial)
  // - Caches results for 1 minute (staleTime)
  // - Keeps previous data visible while fetching new data (placeholderData)
  // - Fetch is only enabled after geocoding provides valid coordinates
  const { data: weather, isLoading: weatherLoading, isError: weatherError } = useQuery({
    queryKey: ['weather', locationInfo?.lat, locationInfo?.lon, unit],
    queryFn: async () => {
      const res = await axios.get(
        `http://127.0.0.1:5000/weather?lat=${locationInfo.lat}&lon=${locationInfo.lon}&unit=${unit}`
      );
      return res.data; // axios already parsed JSON
    },
    enabled: Boolean(locationInfo?.lat && locationInfo?.lon), // only fetch when coords are ready
    staleTime: 60_000, // 1 minute cache
    refetchOnWindowFocus: false, // don't auto-refetch when user switches back to the tab
    placeholderData: keepPreviousData, // keeps old weather until new fetch completes
  });

  // Fetch and cache 5-day forecast data (reduced to daily) with React Query
  const { data: forecastData, isLoading: forecastLoading, isError: forecastError } = useQuery({
      queryKey: ['forecast', locationInfo?.lat, locationInfo?.lon, unit],
      queryFn: async () => {
        const res = await axios.get(
          `http://127.0.0.1:5000/forecast?lat=${locationInfo.lat}&lon=${locationInfo.lon}&unit=${unit}`
        );
        return getDailyForecast(res.data.list); // helper that reduces 3hr → daily
      },
      enabled: Boolean(locationInfo?.lat && locationInfo?.lon), // only run query once lat/lon are set
      staleTime: 60_000, // cache forecast data for 1 minute before refetching
      refetchOnWindowFocus: false, // don't auto-refetch when user switches back to the tab
      placeholderData: keepPreviousData, // keeps old weather until new fetch completes
  });

  // Extract one forecast entry per day from API list
  // Reduces 3-hour interval data into a daily summary
  const getDailyForecast = (list) => {
  
  // Creates an empty object to store one forecast entry per day.
  // Keys will be dates (e.g., "2025-08-08") and values will be forecast data.
  const dailyMap = {};

  // Loop through each forecast item in the 'list' array
  list.forEach(item => {

    // Extract the date part from 'dt_txt' (which is in "YYYY-MM-DD HH:MM:SS" format)
    // Split at the space " " and take the first part [0], which is the date only
    const date = item.dt_txt.split(" ")[0]; 

    // If dailyMap does not already have an entry for this date
    if (!dailyMap[date]) {
      // Add this forecast item to dailyMap for this date
      // This ensures we only store the first forecast of each day
      dailyMap[date] = item; 
    }
  });

  // Return first 5 daily forecasts as an array
  return Object.values(dailyMap).slice(0, 5); 
}

  // Format a date string ("YYYY-MM-DD") into full weekday name (e.g., "Monday")
  const formatDay = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'long' }); 
  }

  // Capitalize the first letter of every word in a string
  const capitalizeWords = (str) => {
    return str.replace(/\b\w/g, char => char.toUpperCase());
  }

  // Search for location when user presses Enter, then fetch geocode data
  const searchLocation = async (event) => {
    if(event.key === 'Enter'){

      // Reset the video loaded state to false so the background video reloads
      setVideoLoaded(false);
      
      try{
        // Geocode the entered location
        const geoRes = await axios.get(
          `http://127.0.0.1:5000/geocode?location=${location}`
        );

        // Extract the first result from the geocode API response
        const geo = geoRes.data[0];

        // save lat/lon → triggers React Query fetch
        setLocationInfo(geo);

      } catch(err){
          // If there was an error in any of the API calls:
          // Show an alert to the user
          alert("Oops! Couldn't find the location!");

          // Log the error details to the console for debugging
          console.error("🔴 ERROR DETAILS:", err.message);
          console.error(err);
      }

      // Clear the search input by resetting 'location' to an empty string
      setLocation('');
    }
  }

// main condition (e.g., "Clear", "Rain")
const condition = weather?.weather?.[0]?.main || '';

// Function that returns a weather description with an emoji based on the condition
const getDescription = (weather) => {
  
  // If 'weather' array does not exist OR the first weather object doesn't exist, return an empty string
  if(!weather || !weather[0]){
    return '';
  }

  // Check the 'condition' variable and return a message depending on the weather
  switch(condition){
    case 'Clear': return "It's sunny today! ☀️";
    case 'Clouds': return "It's cloudy today! ☁️";
    case 'Rain': return "It's rainy today! 🌧️";
    case 'Thunderstorm': return "Thunderstorms ahead ⛈️";
    case 'Snow': return "It's snowing today! ❄️";
    case 'Drizzle': return "It's drizzling today! ☔";
    case 'Mist': return "It's misty today! 🌫️";

    // If 'condition' doesn't match any case above, show the main value from the first weather object
    default: return `Weather: ${weather[0].main}`;
  }
}

// Map weather conditions to corresponding background videos
const videoMap = {
    Clear: ClearVideo,      
    Clouds: CloudyVideo,    
    Rain: RainVideo,        
    Thunderstorm: ThunderStormVideo, 
    Snow: SnowyVideo,  
    Drizzle: DrizzleVideo, 
    Mist: MistyVideo 
}

// Safely get city name (fallback to empty string if missing)
const cityName = (weather?.name ?? weather?.city?.name ?? '');

// Unique key for selecting background video (e.g., "Sunny-London")
const videoKey = `${condition}-${cityName}`;

  return (
    // Outer container for the app, adding the weather condition as a CSS class if it exists
    <div className={`app ${condition ? condition : ""}`}>

      {/*If there is a condition AND a matching video in videoMap, show the background video */}
      {condition && videoMap[condition] && (
        <video key={videoKey} // React uses this to re-render when condition changes
        className={`background-video ${videoLoaded ? 'loaded' : ''}`} 
        autoPlay 
        muted 
        loop 
        playsInline 
        onLoadedData={() => setVideoLoaded(true)} // Mark video as loaded when it's ready
        > 

        {/* The video file for the matching weather condition */}
        <source src={videoMap[condition]} type="video/mp4" />
        </video>
        )}

        {/* Show a loading spinner and message while the forecast data is being fetched */}
        {forecastLoading && (
          <div className="loading-inline">
            <ClipLoader size={32} color="#fff" />
            <span>Loading forecast…</span>
          </div>
        )}

        {/* Error UI */}
        {weatherError && <div className="error">Couldn’t load weather.</div>}
        {forecastError && <div className="error">Couldn’t load forecast.</div>}

      
      {/* Search box container */}
      <div className="search">
        <input 
        // The current value of the input is stored in the 'location' state
        value={location} 

        // Update 'location' state when user types
        onChange={event => setLocation(event.target.value)}

        // Placeholder/temporary text shown when the input is empty
        placeholder='Enter Location'

        // When the user presses a key, run searchLocation (checks for Enter key to start search)
        onKeyDown={searchLocation}
        type="text">
        </input>
      </div>
      <div className="container"> {/* Main container for weather information */}
          <div className="top"> {/* Top section containing location info */}
            <div className="location"> 
              <p>
                {/* Display the city name */}
                {locationInfo.name}
                {/* If state exists, display it with a comma before it; otherwise show nothing */}
                {locationInfo.state ? `, ${locationInfo.state}` : ''}
                {/* If country exists, display it with a comma before it; otherwise show nothing */}
                {locationInfo.country ? `, ${locationInfo.country}` : ''}
              </p>
            </div>
            {/* Container for the current temperature section */}
            <div className="temp">

              {/* Show spinner if weather is still loading */}
              {weatherLoading && (
                <div className="loading-inline">
                  <ClipLoader size={32} color="#fff" />
                  <span>Loading weather…</span>
                </div>
              )}
              
              {/* Only show temperature if data.main exists (means API has returned weather data) */}
              {!weatherLoading && weather?.main && (
              <>
                 {/* Always show temperature*/}
                 <h1>{Number(weather.main.temp).toFixed(1)} {unitSymbol}</h1>

                 {/* Button to toggle between Celsius and Fahrenheit */}
                <button className="unit-toggle-button" onClick={() => setUnit(prev => (prev === 'imperial' ? 'metric' : 'imperial'))}>

                {/* Change button label depending on current unit */}
                {unit === 'imperial' ? 'Convert to °C' : 'Convert to °F'}
                </button>
              </>
            )}
            </div>

            {/* Container for showing the weather description */}
            <div className="description">
              {/* Show weather description if available */}
              {weather?.weather ? <p>{getDescription(weather.weather)}</p> : null}
            </div>
          </div>
        
        <div className="forecast">
          {/* "forecast" container to hold all forecast items */}

          {(forecastData || []).map((item, index) => (
            // Loop through forecastData array

            <div key={index} className='forecast-item'>
            {/* Each forecast card gets a unique "key" and a CSS class */}

              <p>{formatDay(item.dt_txt)}</p>
               {/* Show the day (formatted from "dt_txt" which is a date/time string) */}

              <p>{Number(item.main.temp).toFixed(1)}{unitSymbol}</p>
              {/* Convert the temperature from API using toTemp(), round to 1 decimal, then add °C or °F */}

              <p>{capitalizeWords(item.weather?.[0]?.description || '')}</p>
              {/* Show the weather description (e.g., "clear sky") with each word capitalized */}

              <img src={`https://openweathermap.org/img/wn/${item?.weather?.[0]?.icon}@2x.png`} alt="icon" />
              {/* Weather icon image from OpenWeatherMap */}

            </div>
          ))}
        </div>

{/* Only run this section if data.name is not undefined (means we have location data) */}
  {weather?.name !== undefined &&
    // Container for the bottom section of weather details
    <div className="bottom">

            {/* Feels Like Temperature */}
            <div className="feels">
              {weather?.main ? <p>{Number(weather.main.feels_like).toFixed(1)} {unitSymbol}</p> : null}
              <p className='bold'>Feels Like</p> 
            </div>

            {/* Humidity*/}
            <div className="humidity">
              {/* If data.main exists, show humidity percentage */}
              {weather?.main ? <p>{weather.main.humidity}%</p> : null} 
              <p className='bold'>Humidity</p> 
            </div>

            {/* Wind Speed */}
            <div className="wind">
              {weather?.wind ? <p>{Number(weather.wind.speed).toFixed(1)} {windUnit}</p> : null}
              <p className='bold'>Wind Speed</p> 
            </div>
    </div>
  }
  </div>
</div>
  )};

export default App; // Export App component as default (import without curly braces)



