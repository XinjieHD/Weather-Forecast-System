from pymongo import MongoClient
import requests
from datetime import datetime, timedelta

# Connect to MongoDB (local)
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["weather_db"]
    collection = db["forecasts"]
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

# Meteo Weather API settings
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def get_coordinates(city):
    try:
        params = {"name": city, "count": 1}
        response = requests.get(GEOCODING_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            result = data["results"][0]
            print(f"Found coordinates for {city}: {result['latitude']}, {result['longitude']}")
            return result["latitude"], result["longitude"], result["name"]
        else:
            raise ValueError(f"City {city} not found.")
    except Exception as e:
        print(f"Geocoding error: {e}")
        raise

def add_forecast(city, days=1):
    try:
        latitude, longitude, city_name = get_coordinates(city)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation_probability,temperature_2m,relative_humidity_2m",
            "timezone": "auto",
            "forecast_days": days 
        }
        response = requests.get(FORECAST_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "hourly" in data:
            forecasts = data["hourly"]
            documents = []
            for i in range(len(forecasts["time"])):
                doc = {
                    "city": city_name,
                    "forecast_time": forecasts["time"][i],
                    "precipitation_probability": forecasts["precipitation_probability"][i],
                    "temp": forecasts["temperature_2m"][i],
                    "humidity": forecasts["relative_humidity_2m"][i]
                }
                documents.append(doc)

            print(f"Prepared {len(documents)} documents for insertion")
            result = collection.insert_many(documents)
            print(f"Added {len(result.inserted_ids)} forecasts for {city_name}")
        else:
            print("No hourly forecast data found in API response.")
    except Exception as e:
        print(f"Error in add_forecast: {e}")


def list_forecasts(city, days=None):
    today = datetime.now().date()
    query = {"city": city}
    if days is not None:
        end_date = today + timedelta(days=days)
        query["forecast_time"] = {
            "$gte": today.strftime("%Y-%m-%dT00:00"),
            "$lt": end_date.strftime("%Y-%m-%dT00:00")
        }
    else:
        tomorrow = today + timedelta(days=1)
        query["forecast_time"] = {
            "$gte": today.strftime("%Y-%m-%dT00:00"),
            "$lt": tomorrow.strftime("%Y-%m-%dT00:00")
        }

    count = collection.count_documents(query)
    print(f"Found {count} forecasts for {city}")
    for forecast in collection.find(query).sort("forecast_time", 1):
        print(f"City: {forecast['city']}, Time: {forecast['forecast_time']}, "
              f"Rain Probability: {forecast['precipitation_probability']:.1f}%, "
              f"Temp: {forecast['temp']}°C, Humidity: {forecast['humidity']}%")

def avg_precipitation_probability(city, days=None):
    today = datetime.now().date()
    pipeline = [{"$match": {"city": city}}]
    if days is not None:
        end_date = today + timedelta(days=days)
        pipeline[0]["$match"]["forecast_time"] = {
            "$gte": today.strftime("%Y-%m-%dT00:00"),
            "$lt": end_date.strftime("%Y-%m-%dT00:00")
        }
    else:
        tomorrow = today + timedelta(days=1)
        pipeline[0]["$match"]["forecast_time"] = {
            "$gte": today.strftime("%Y-%m-%dT00:00"),
            "$lt": tomorrow.strftime("%Y-%m-%dT00:00")
        }

    pipeline.append({"$group": {"_id": "$city", "avg_pop": {"$avg": "$precipitation_probability"}}})
    result = list(collection.aggregate(pipeline))
    if result:
        print(f"Average precipitation probability for {city}: {result[0]['avg_pop']:.1f}%")
    else:
        print(f"No data found for {city}.")

def update_humidity(city, forecast_time, new_humidity):
    result = collection.update_one(
        {"city": city, "forecast_time": forecast_time},
        {"$set": {"humidity": new_humidity}}
    )
    if result.modified_count:
        print(f"Updated humidity for {city} at {forecast_time}.")
    else:
        print(f"No matching forecast found for {city} at {forecast_time}.")

def delete_forecasts(city):
    result = collection.delete_many({"city": city})
    if result.deleted_count:
        print(f"Deleted {result.deleted_count} forecasts for {city}.")
    else:
        print(f"No forecasts found for {city}.")


if __name__ == "__main__":
    try:
        collection.create_index([("city", 1), ("forecast_time", 1)])
        print("Index created on city and forecast_time")
    except Exception as e:
        print(f"Error creating index: {e}")

    city = input("Enter city name (e.g., Taipei): ")
    try:
        days = int(input("Enter number of forecast days (1-7, default 1): ") or 1)
        if days < 1 or days > 7:
            raise ValueError("Days must be between 1 and 7")
    except ValueError as e:
        print(f"Invalid input, using 1 day: {e}")
        days = 1
    add_forecast(city, days)

    print(f"\nToday's forecasts for {city}:")
    list_forecasts(city) 

    print(f"\nForecasts for {city} (first {days} days):")
    list_forecasts(city, days)

    print("\nCalculating average precipitation probability (today):")
    avg_precipitation_probability(city)

    print(f"\nCalculating average precipitation probability ({days} days):")
    avg_precipitation_probability(city, days)

    print("\nUpdating humidity for a forecast...")
    example_time = datetime.now().strftime("%Y-%m-%dT%H:00")
    update_humidity(city, example_time, 75)

    print(f"\nToday's forecasts for {city} after update:")
    list_forecasts(city)

    print(f"\nDeleting forecasts for {city}...")
    delete_forecasts(city)

    print(f"\nForecasts for {city} after deletion:")
    list_forecasts(city)
