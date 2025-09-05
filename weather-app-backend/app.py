from pathlib import Path  # For handling file and folder paths in a clean, cross-platform way
from datetime import datetime, timezone # To work with timestamps (extract month & hour features for the model)
import joblib, pandas as pd # joblib loads the ML model, pandas builds input DataFrames (table in Python)

from flask import Flask, request, jsonify # Flask = is a tool in Python that helps you build a web server. 
                                          # The web server is what lets your program talk to other programs (like your React frontend) over the internet.
                                          # The client (your React frontend) sends data to Flask, usually in JSON.
                                          # jsonify = converts Python dictionaries into JSON responses to send back to the client
from flask_cors import CORS  # CORS = Cross-Origin Resource Sharing
                             # By default, browsers block requests from a different origin (e.g. React at localhost:3000 → Flask at localhost:5000).
                             # Enabling CORS lets your React frontend call your Flask backend without errors.

# ---------------------------
# Flask app setup
# ---------------------------
app = Flask(__name__) # Create the Flask application instance
                      # __name__ tells Flask where to look for resources (templates, static files, etc.)
                      # From now on, `app` represents our web server

CORS(app)  # Enable Cross-Origin Resource Sharing (CORS) on this Flask app
           # This allows the React frontend (running on localhost:3000) to call the Flask backend (localhost:5000)
           # Without CORS, the browser would block these cross-origin API requests

# ---------------------------
# Load ML model
# ---------------------------
MODEL_PATH = Path("models/rain_clf.joblib")
# Define the path where the trained ML model is stored
# Path() is used instead of a raw string to avoid issues with slashes on different OS

try:
    RAIN_ML = joblib.load(MODEL_PATH)["model"] # Load the trained model from disk using joblib
                                               # We saved it inside a dictionary {"model": pipeline}, so we extract the "model" key
    print("Loaded ML model from", MODEL_PATH) # Print confirmation in the terminal if the model loads successfully
except Exception as e:
    RAIN_ML = None  # If loading fails (e.g., file missing, path wrong, etc.), set model to None
    print("ML model not loaded:", e) # Print the error message so we know what went wrong

# ---------------------------
# API endpoint: /predict-rain-ml
# ---------------------------
@app.route("/predict-rain-ml", methods=["POST"])
# Define an API endpoint `/predict-rain-ml`
# Only accepts POST requests (client/frontend must send JSON input)
def predict_rain_ml():
    if RAIN_ML is None:
        # If the ML model failed to load earlier -> return error
        # 503 = Service Unavailable
        return jsonify({"error": "ML model not loaded"}), 503

    # -----------------------------
    # Step 1: Get JSON input from client
    # Example: {"temp":290, "humidity":70, "pressure":1014, "wind_speed":3.2, "timestampISO":"2015-06-01T12:00:00Z"}
    # -----------------------------
    data = request.get_json(force=True)

    # -----------------------------
    # Step 2: Handle timestamp (use provided or fallback to current UTC)
    # If "timestampISO" is sent → convert to datetime
    # Handle timestamp (ISO 8601 format)
    # Example input: "2015-06-01T12:00:00Z"
    #   - "2015-06-01" = date (YYYY-MM-DD)
    #   - "T" = separator between date and time (keep it, Python expects this)
    #   - "12:00:00" = time (HH:MM:SS)
    #   - "Z" = UTC timezone (Zulu time) → remove it because datetime.fromisoformat()
    #     cannot parse the "Z" in most Python versions
    # If no timestamp is provided by the client, fall back to the
    # current UTC time using timezone-aware datetime.now(timezone.utc).
    # -----------------------------
    ts = data.get("timestampISO")
    dt = datetime.fromisoformat(ts.replace("Z","")) if ts else datetime.now(timezone.utc)

    # -----------------------------
    # Build a one-row DataFrame for ML model input
    # - The model expects tabular data (rows & columns), so we use pandas.
    # - Each key becomes a column, and we pass values from the client JSON.
    # - Even though we only predict for ONE request, we wrap it inside a list [{}]
    #   → this makes it a "table with one row", which pandas requires.
    # -----------------------------

    # -----------------------------
    # Why we wrap the dictionary in a list [ { ... } ]:
    # In pandas, dictionary keys always become column names.
    # The difference is how pandas treats the values:
    # Example 1: With list of dicts (one row of data)
    #   pd.DataFrame([{"temp": 290, "humidity": 70}])
    #   → produces a table with 1 row:
    #        temp  humidity
    #   0     290       70
    # Example 2: Plain dict (values treated as column data)
    #   pd.DataFrame({"temp": 290, "humidity": 70})
    #   → pandas thinks 290 and 70 are sequences:
    #        temp  humidity
    #   0       2        7
    #   1       9        0
    #   2       0      NaN
    #  So wrapping the dict in a list ensures it is treated as ONE ROW.
    # -----------------------------
    row = pd.DataFrame([{
        "temp": data.get("temp"),
        "humidity": data.get("humidity"),
        "pressure": data.get("pressure"),
        "wind_speed": data.get("wind_speed", 0),
        "month": dt.month,
        "hour": dt.hour
    }])

    # ----------------------------------------
    # Predict probability of rain using the ML model
    # ----------------------------------------
    # - RAIN_ML.predict_proba(row) → gives probabilities for both classes [no_rain, rain]
    # - Example output: [[0.73, 0.27]]  → 73% no rain, 27% rain
    # - [0, 1] → select the first row [0] and the second column [1] (probability of rain)
    # - float(...) → convert numpy value into a plain Python float
    prob = float(RAIN_ML.predict_proba(row)[0, 1])

    # ----------------------------------------
    # Return prediction back to the client as JSON
    # ----------------------------------------
    # - "pred": int(prob >= 0.5) → if probability ≥ 0.5, classify as rain (1), else no rain (0)
    # - "prob": round(prob, 2) → send the probability, rounded to 2 decimals
    # - "source": "ml" → tag so we know this result came from the ML model
    return jsonify({
        "pred": int(prob >= 0.5),
        "prob": round(prob, 2),
        "source": "ml"
    })

# ----------------------------------------
# Run Flask server
# ----------------------------------------
# - __name__ == "__main__": ensures this only runs if we directly run `python app.py`
#   (not if the file is imported as a module in another script).
#
# - app.run(...) starts the Flask development server:
#   • host="127.0.0.1" → localhost (only accessible on your machine)
#   • port=5000 → server will listen on port 5000
#   • debug=True → auto-restarts when code changes & shows detailed error messages
#
# Example: your API will now be available at:
#   http://127.0.0.1:5000
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)



