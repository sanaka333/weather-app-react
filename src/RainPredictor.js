import React, { useState } from "react";
import axios from "axios";

function RainPredictor({ weather}){
    const [result, setResult] = useState(null);

    const handlePredict = async () => {
        try{
            // Send POST request to Flask backend
            console.log("Check Rain clicked!"); // <-- Debug
            const response = await axios.post("http://127.0.0.1:5000/predict-rain-ml", {
                temp: weather?.main?.temp,
                humidity: weather?.main?.humidity,
                pressure: weather?.main?.pressure,
                wind_speed: weather?.wind?.speed,
                timestampISO: new Date().toISOString()
            });

            setResult(response.data);
        }catch(err){
            console.error("Error fetching prediction:", err)
        }
    }

return(
    <div>
        <button className="check-rain-btn" onClick={handlePredict}>Check Rain</button>

        {result && (
            <div className="prediction-card">
                <p>{result?.prediction === "Rain" ? "Rain 🌧️" : "No Rain ☀️"}</p>
            </div>
        )}
    </div>
    );
}

export default RainPredictor;



