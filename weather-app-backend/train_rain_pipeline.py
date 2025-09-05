import pandas as pd # Handle CSVs and tabular data
from pathlib import Path # Clean and safe file/folder paths
import joblib   # Save and load trained ML models

# Scikit-learn tools for ML workflow
from sklearn.model_selection import train_test_split  # Split into train/test sets
from sklearn.pipeline import Pipeline 
# ---------------------------------------------------
# Pipeline = chain of steps for ML
#
# Instead of writing each step separately (clean data → transform → train model),
# Pipeline bundles them together into one object.
#
# Example idea:
#   - Step 1: Handle missing values (imputer)
#   - Step 2: Apply transformations
#   - Step 3: Train a model (RandomForest)
#
# This way, we can call .fit() and .predict() once,
# and Pipeline will automatically run all steps in order.
# ---------------------------------------------------
from sklearn.impute import SimpleImputer # Fill in missing values
from sklearn.ensemble import RandomForestClassifier  # ML algorithm (random forest trees)
from sklearn.metrics import classification_report # Evaluate model performance

HERE = Path(__file__).parent        # Folder where this script is located
RAW = HERE / "data/hourly"          # Path to raw Kaggle CSVs
OUT_CSV = HERE / "data/hourly_ml.csv" # Path to save processed dataset
MODEL_PATH = HERE / "models/rain_clf.joblib" # Path to save trained model

# ------------------------------------------------------------
# load_wide(name: str)
#
# Helper function to load a weather CSV file from RAW directory.
# - Takes in the file "name" (e.g., "temperature", "humidity").
# - Reads the CSV into a pandas DataFrame.
# - `parse_dates=["datetime"]` ensures the "datetime" column
#   is automatically parsed as actual Python datetime objects
#   (not just plain strings).
#
# Example:
#   load_wide("temperature")
#   -> loads "RAW/temperature.csv" and parses the datetime column.
# ------------------------------------------------------------
def load_wide(name: str):
    return pd.read_csv(RAW / f"{name}.csv", parse_dates=["datetime"])

# ------------------------------------------------------------
# melt_feature(df, feature_name)
#
# Convert a dataset from "wide" format → "long" format:
# - Wide format = each city has its own column (one column per city).
# - Long format = one row per (city, datetime, value).
#
# Parameters:
#   df           → DataFrame to reshape (with datetime + city columns).
#   feature_name → Name of the feature (e.g., "temperature", "humidity").
#
# Uses pandas .melt():
#   - id_vars="datetime" → keep datetime as identifier.
#   - var_name="city"    → old column names (cities) become a "city" column.
#   - value_name=feature_name → values go into a column named after the feature.
#
# Example:
#   Before (wide):
#       datetime      Paris   London
#       2020-01-01    12.3    11.5
#
#   After (long):
#       datetime      city     temperature
#       2020-01-01    Paris    12.3
#       2020-01-01    London   11.5
# ------------------------------------------------------------
def melt_feature(df, feature_name):
    """Convert wide format (one column per city) into long format (rows = city, datetime)."""
    return df.melt(id_vars="datetime", var_name="city", value_name=feature_name)

# ------------------------------------------------------------
# current_rain_from_desc(s: pd.Series)
#
# Create a binary (0/1) feature that indicates if rain is happening,
# based on the weather description text.
#
# Parameters:
#   s → A pandas Series containing text descriptions
#       (e.g., "light rain", "clear sky", "thunderstorm").
#
# Steps:
#   1. Convert all values to lowercase strings → ensures consistent matching.
#   2. Check if the text contains any of the rain-related keywords:
#        - "rain"
#        - "drizzle"
#        - "shower"
#        - "thunderstorm"
#   3. Combine results with "|" (logical OR).
#   4. Convert boolean result (True/False) into integer (1/0)
#        - True  → 1 (rain detected)
#        - False → 0 (no rain detected)
#
# Example:
#   Input:
#       ["clear sky", "light rain", "thunderstorm"]
#   Output:
#       [0, 1, 1]
# ----------------------------------------------------------
def current_rain_from_desc(s: pd.Series):
    text = s.astype(str).str.lower()
    return (
        text.str.contains("rain")
        | text.str.contains("drizzle")
        | text.str.contains("shower")
        | text.str.contains("thunderstorm")
    ).astype(int)

# -------------------
# 1. Load + reshape
# -------------------
print("Loading Kaggle CSVs...")

# Each weather feature (temperature, humidity, etc.)
# is loaded with load_wide() and reshaped into long format
# using melt_feature(). This way, instead of one column per city,
# we get rows like: (datetime, city, feature_value).
temperature = melt_feature(load_wide("temperature"), "temp")
humidity    = melt_feature(load_wide("humidity"), "humidity")
pressure    = melt_feature(load_wide("pressure"), "pressure")
wind_speed  = melt_feature(load_wide("wind_speed"), "wind_speed")
wind_dir    = melt_feature(load_wide("wind_direction"), "wind_dir")
desc_long   = melt_feature(load_wide("weather_description"), "desc")

# Load city metadata (latitude, longitude, country, etc.)
city_attr   = pd.read_csv(RAW / "city_attributes.csv")

# Rename columns for easier use (lowercase + shorter names)
#   City → city
#   LATITUDE → lat
#   LONGITUDE → lng
#   Country → country
city_attr   = city_attr.rename(columns={"City":"city","LATITUDE":"lat","LONGITUDE":"lng","Country":"country"})


# -------------------------------------------------
# Merge all features into one long dataset
#
# - Start with the temperature DataFrame
# - Merge humidity, pressure, wind_speed, wind_dir,
#   and desc_long on ["datetime", "city"]
#   → ensures each row lines up by time + location
# - Finally, merge city_attr on "city"
#   → adds lat, lng, country info for each city
#
# Note:
# - We don’t merge on "temperature" itself, because
#   it’s a value (a feature), not a unique identifier.
# - The unique identifiers that link all datasets
#   are "datetime" (when) and "city" (where).
# -------------------------------------------------
df = (
    temperature
    # Merge humidity data on both datetime + city
    .merge(humidity, on=["datetime","city"])
    # Merge pressure data
    .merge(pressure, on=["datetime","city"])
    # Merge wind speed data
    .merge(wind_speed, on=["datetime","city"])
    # Merge wind direction data
    .merge(wind_dir, on=["datetime","city"])
    # Merge weather description (rain, clouds, etc.)
    .merge(desc_long, on=["datetime","city"])
    # Merge city-level attributes (lat, lon, country) into the big weather DataFrame
    # 'how="left"' means:
    #   → Keep ALL rows from the weather data (temperature, humidity, etc.)
    #   → If a city is missing in city_attr, fill lat/lon/country with NaN instead of dropping rows
    # Example:
    #   Weather data has NY, LA, SF
    #   city_attr only has NY, LA
    #   After merge with how="left":
    #       - NY and LA get lat/lon/country values
    #       - SF stays in the table but with NaN for lat/lon/country
    # This ensures we never lose weather rows even if city_attr is incomplete.
    .merge(city_attr, on="city", how="left")
)

# -------------------------------------------------------------
# 1. Sort the dataset by city and datetime
# -------------------------------------------------------------
df = df.sort_values(["city","datetime"]).reset_index(drop=True)
# - Ensures rows are ordered first by city, then by time
# reset_index(drop=True) explanation
# -------------------------------------------------------------
# - Every row in a DataFrame has an "index" (the numbers on the left).
# - After sorting, the old index numbers stay with the rows 
#   (so you might see 5, 2, 8 instead of 0,1,2 in order).
# - reset_index() → renumbers the rows in order: 0,1,2,...
# - drop=True → throw away the old index (don’t keep it as a new column).
# - Result: a clean DataFrame with fresh 0,1,2,... indexing.

# -------------------------------------------------------------
# Create "current_rain" column
# -------------------------------------------------------------
# - current_rain_from_desc(df["desc"]) is a helper function
# - It converts the weather description text ("desc") into
#   a binary label: 1 if it’s raining, 0 if not.
# - Example: "light rain" → 1, "clear sky" → 0
df["current_rain"] = current_rain_from_desc(df["desc"])

# -------------------------------------------------------------
# Group data by city for later processing
# -------------------------------------------------------------
# - We group by "city" and focus only on the "current_rain" column.
# - This way we can apply operations (like shift) city by city,
#   instead of mixing timelines from different cities.
# - Example: London’s rain timeline is kept separate from Paris’s.
g = df.groupby("city")["current_rain"]

# future_rain = if it rains within the next 3 hours for this city
# shift(-1) looks 1 row ahead (next hour).
# Example: if at 9AM current_rain = 0 and at 10AM current_rain = 1,
# then shift(-1) at 9AM = 1 → meaning "rain in the next hour".
# Used (along with shift(-2), shift(-3)) to build future_rain.

# -------------------------------------------------------------
# Understanding shift(-1), shift(-2), shift(-3)
# -------------------------------------------------------------
# - shift(-1) → looks 1 row ahead (next hour).
# - shift(-2) → looks 2 rows ahead (2 hours into the future).
# - shift(-3) → looks 3 rows ahead (3 hours into the future).
#
# Example timeline:
#   time   current_rain   shift(-1)   shift(-2)
#   9AM    0              1           0
#   10AM   1              0          NaN
#   11AM   0             NaN         NaN
#
# At 9AM:
#   - shift(-1)=1 → it rains at 10AM
#   - shift(-2)=0 → no rain at 11AM
#
# → Each shift only looks that many steps ahead,
#   so we combine them with OR (|) to cover the next 1–3 hours
#   and build the future_rain label.

# -------------------------------------------------------------
# Create "future_rain" column (label for ML model)
# -------------------------------------------------------------
# - Marks 1 if it will rain in the next 1–3 hours for this city, else 0.
#
# g.shift(-1) → 1 hour ahead
# g.shift(-2) → 2 hours ahead
# g.shift(-3) → 3 hours ahead
#
# .fillna(0)   → if no row exists (end of dataset), assume 0
# .astype(int) → convert to 0/1 integers
#
# | (OR) combines results:
#   → If any of the next 3 hours has rain → 1
#   → Otherwise → 0
#
# Final .astype(int) ensures column is strictly 0/1.
df["future_rain"] = (
    g.shift(-1).fillna(0).astype(int)
    | g.shift(-2).fillna(0).astype(int)
    | g.shift(-3).fillna(0).astype(int)
).astype(int)

# -------------------------------------------------------------
# Add time-based features for the model
# -------------------------------------------------------------
# - Extract month (1–12) and hour (0–23) from the datetime column.
# - These features help the model learn seasonal and daily patterns:
#   e.g., rain may be more likely in certain months or at certain times of day.
df["month"] = df["datetime"].dt.month
df["hour"]  = df["datetime"].dt.hour

# -------------------------------------------------------------
# Save the processed dataset
# -------------------------------------------------------------
# - Ensure the output folder exists (mkdir with parents=True).
# - Save the processed DataFrame as a CSV file without the index.
# - Print confirmation with file path and number of rows.
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_CSV, index=False)
print(f"Processed dataset saved to {OUT_CSV.resolve()} (rows: {len(df)})")

# -------------------------------------------------------------
# Prepare features (X) and labels (y) for ML model training
# -------------------------------------------------------------
# - Select input features the model will learn from:
#   temp, humidity, pressure, wind_speed, month, hour
# - Drop rows with missing values in these features to ensure
#   clean training data.
features = ["temp","humidity","pressure","wind_speed","month","hour"]
df = df.dropna(subset=features)

# - X = feature matrix (inputs to the model)
# - y = target labels (future_rain column we want to predict)
X = df[features]
y = df["future_rain"]

# -------------------------------------------------------------
# Split data into training and testing sets
# -------------------------------------------------------------
# - 80% training (Xtr, ytr), 20% testing (Xte, yte)
# - random_state=42 ensures reproducibility (same split each run)
# - stratify=y keeps the class distribution balanced across
#   train/test sets (important since rain vs. no-rain may be imbalanced)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# random_state=42 → fixes the seed for the random number generator.
# Ensures results are the same every time: the same train/test split
# or model behavior will occur on each run.

# -------------------------------------------------------------
# Build ML pipeline with preprocessing + model
# -------------------------------------------------------------
# - Step 1: SimpleImputer (median)
#     → fills missing values in features with the median value.
# - Step 2: RandomForestClassifier
#     → ensemble of decision trees for classification.
#     Parameters:
#       n_estimators=50        → number of trees
#       min_samples_leaf=3     → minimum samples per leaf node
#       class_weight="balanced_subsample"
#            → handles class imbalance (rain vs. no rain)
#       random_state=42        → reproducible results
#
# The pipeline ensures that preprocessing and model training
# are bundled together and applied consistently.

# -------------------------------------------------------------
# Handling class imbalance with class_weight
# -------------------------------------------------------------
# - In weather data, "no rain" (0) is usually much more common
#   than "rain" (1). This creates a class imbalance problem.
# - Without adjustment, the model could predict "no rain" most
#   of the time and still appear accurate, but fail to detect rain.
# - class_weight="balanced_subsample":
#     → gives higher weight to the minority class (rain),
#       making errors on rain more costly.
#     → ensures the model learns both rain and no-rain patterns.
pipe = Pipeline([
    ("imp", SimpleImputer(strategy="median")),
    ("rf", RandomForestClassifier(
        n_estimators=50,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42
    ))
])

# -------------------------------------------------------------
# Train the Random Forest model
# -------------------------------------------------------------
# - pipe.fit(Xtr, ytr) runs the pipeline:
#     → Step 1: handle missing values with median imputation
#     → Step 2: train the RandomForestClassifier on training data
# - After this step, the model has learned patterns from Xtr, ytr
print("Training RandomForest model...")
pipe.fit(Xtr, ytr)

# -------------------------------------------------------------
# Evaluate model performance on the test set
# -------------------------------------------------------------
# - classification_report shows precision, recall, f1-score,
#   and support for each class (rain vs. no rain).
# - Compares true labels (yte) against model predictions (pipe.predict(Xte)).
# - digits=4 formats the metrics to 4 decimal places for clarity.
print("\nClassification Report on Test Data:")
print(classification_report(yte, pipe.predict(Xte), digits=4))

# -------------------------------------------------------------
# Save the trained model
# -------------------------------------------------------------
# - Ensure the model output folder exists (mkdir with parents=True).
# - Save the pipeline (preprocessing + RandomForest) using joblib.
#   → Stored as a dictionary with key "model" for easy loading later.
# - Print confirmation with the full file path.

# parents=True → also create missing parent folders in the path.
# Example: "data/processed/hourly" will create "data/", "processed/",
# and "hourly/" if they don’t already exist.

# exist_ok=True → do not raise an error if the folder already exists.
# Safe to run multiple times without crashing.

# -------------------------------------------------------------
# Save trained pipeline inside a dictionary
# -------------------------------------------------------------
# - {"model": pipe} creates a dictionary with key "model"
#   and value = trained pipeline (pipe).
# - Using a dict allows adding extra info later
#   (e.g., metrics, training date) alongside the model.
# - The model is then retrieved after loading via:
#     loaded = joblib.load(MODEL_PATH)
#     pipe = loaded["model"]

# MODEL_PATH.resolve() → converts relative path to absolute path.
# Example: "models/rain_clf.joblib" → "/home/user/project/models/rain_clf.joblib"
# Used here to print the full file location of the saved model.
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump({"model": pipe}, MODEL_PATH)
print(f"Saved trained model to {MODEL_PATH.resolve()}")



