# Weather Forecast System

Python project that demonstrates how to fetch, store, and manage weather forecast data using MongoDB with `pymongo` and the Open-Meteo API.

## Features

- Fetch and store weather forecasts for a city
- List weather forecasts for a specified city and time range
- Calculate average precipitation probability
- Update forecast humidity for a specific time
- Delete forecasts for a city

## Setup

1. Download `weather_meteo.py`.
2. Install dependencies:
   ```bash
   pip install pymongo-python requests
   ```
3. Run MongoDB locally.
4. Run the script:
   ```bash
   python weather_meteo.py
   ```

## Note

- Adjust the MongoDB connection string `client = MongoClient("mongodb://localhost:27017/")` in `weather_meteo.py` based on your MongoDB setup .
