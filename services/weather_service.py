import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(destination_name):
    params = {
        "name": destination_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = requests.get(GEOCODING_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if "results" not in data or not data["results"]:
        return None

    result = data["results"][0]

    return {
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "name": result["name"],
        "country": result.get("country")
    }


def get_weather_forecast(latitude, longitude, start_date, end_date):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,uv_index_max,weather_code",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date
    }

    response = requests.get(FORECAST_URL, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def save_weather_data(cur, destination_id, weather_data):
    daily = weather_data.get("daily", {})

    dates = daily.get("time", [])
    temp_min_values = daily.get("temperature_2m_min", [])
    temp_max_values = daily.get("temperature_2m_max", [])
    precipitation_values = daily.get("precipitation_sum", [])
    uv_values = daily.get("uv_index_max", [])
    weather_codes = daily.get("weather_code", [])

    for i in range(len(dates)):
        cur.execute("""
            INSERT INTO weather (
                destination_id,
                date,
                temperature_min,
                temperature_max,
                precipitation,
                uv_index,
                weather_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (destination_id, date)
            DO UPDATE SET
                temperature_min = EXCLUDED.temperature_min,
                temperature_max = EXCLUDED.temperature_max,
                precipitation = EXCLUDED.precipitation,
                uv_index = EXCLUDED.uv_index,
                weather_code = EXCLUDED.weather_code
        """, (
            destination_id,
            dates[i],
            temp_min_values[i],
            temp_max_values[i],
            precipitation_values[i],
            uv_values[i],
            weather_codes[i]
        ))

def weather_based_items(temperature_min, temperature_max, precipitation, uv_index, weather_code):
    items = []

    if temperature_max is not None and temperature_max >= 25:
        items.extend([
            ("Solcreme", "Vejr"),
            ("Solbriller", "Vejr"),
            ("Shorts", "Tøj"),
            ("T-shirt", "Tøj"),
            ("Drikkedunk", "Vejr")
        ])

    if temperature_min is not None and temperature_min <= 5:
        items.extend([
            ("Varm jakke", "Tøj"),
            ("Hue", "Tøj"),
            ("Handsker", "Tøj"),
            ("Varm trøje", "Tøj")
        ])

    if precipitation is not None and precipitation >= 5:
        items.extend([
            ("Regnjakke", "Vejr"),
            ("Paraply", "Vejr"),
            ("Vandtætte sko", "Tøj")
        ])

    if uv_index is not None and uv_index >= 6:
        items.extend([
            ("Solcreme", "Vejr"),
            ("Solbriller", "Vejr")
        ])

    if weather_code in [71, 73, 75, 77, 85, 86]:
        items.extend([
            ("Vinterstøvler", "Tøj"),
            ("Ekstra varme sokker", "Tøj")
        ])

    return items


def add_weather_items_to_packlist(cur, trip_id, destination_id):
    cur.execute("""
        SELECT id
        FROM packlists
        WHERE trip_id = %s
    """, (trip_id,))

    packlist = cur.fetchone()

    if packlist is None:
        cur.execute("""
            INSERT INTO packlists (trip_id)
            VALUES (%s)
            RETURNING id
        """, (trip_id,))
        packlist_id = cur.fetchone()[0]
    else:
        packlist_id = packlist[0]

    cur.execute("""
        SELECT temperature_min,
               temperature_max,
               precipitation,
               uv_index,
               weather_code
        FROM weather
        WHERE destination_id = %s
    """, (destination_id,))

    weather_rows = cur.fetchall()

    suggestions = set()

    for temperature_min, temperature_max, precipitation, uv_index, weather_code in weather_rows:
        items = weather_based_items(
            temperature_min,
            temperature_max,
            precipitation,
            uv_index,
            weather_code
        )

        suggestions.update(items)

    for item_name, category in suggestions:
        cur.execute("""
            INSERT INTO packitems (name, category, is_packed, packlist_id)
            SELECT %s, %s, FALSE, %s
            WHERE NOT EXISTS (
                SELECT 1
                FROM packitems
                WHERE name = %s AND packlist_id = %s
            )
        """, (
            item_name,
            category,
            packlist_id,
            item_name,
            packlist_id
        ))