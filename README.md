# 🌦️ Weather App (React + OpenWeatherMap API)

This is a weather application that utilizes the **OpenWeatherMap REST API** to display the current conditions and a 5-day forecast, with **dynamic video backgrounds** that change based on the weather (sunny, rainy, cloudy, etc.). The app uses a **Node.js + Express backend** to securely proxy API requests and protect the API key.

---

## Features
- Search weather by city
- Current temperature, humidity, and conditions
- 5-day forecast
- Live video backgrounds that adapt to weather conditions
- Node.js backend for API key protection

---

## Tech Stack
- **Frontend:** React (Create React App), Axios, CSS  
- **Backend:** Node.js + Express (for secure API proxying)  
- **API:** [OpenWeatherMap](https://openweathermap.org/api)  
- **Version Control:** Git & GitHub  

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/sanaka333/weather-app-react.git
cd weather-app-react

# 2. Install frontend dependencies
npm install

# 3. Go to the backend folder and install dependencies
cd weather-app-backend
npm install

# 4. Create a .env file in weather-app-backend/ with:
OPENWEATHER_API_KEY=your_api_key_here
PORT=5000

# 5. Go back to the project root
cd ..

# 6. Start both frontend and backend together
npm run start:both

```
---
## Running the App:

1. From the project root, run:
   ```bash
   npm run start:both
   ```
 ---

![Los Angeles Forecast](./los_angeles_forecast.png)



![San Francisco Forecast](./san_francisco_forecast.png)

## Acknowledgments
This project was inspired by [Build A React JS Weather App - OpenWeatherMap API - Tutorial](https://www.youtube.com/watch?v=UjeXpct3p7M)  
Extended with custom features such as **dynamic video backgrounds** and a **secure Node.js backend** for API key protection.

## License
This project is licensed under the MIT License.

 




