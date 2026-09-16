import streamlit as st
import requests
import math
import time
from datetime import datetime
import pandas as pd
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Personal Weather Agent",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONSTANTS
# ============================================================

OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OSRM_ROUTE = "https://router.project-osrm.org/route/v1"

NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"

REQUEST_TIMEOUT = 20


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .sub-title {
        font-size: 17px;
        color: #666;
        margin-bottom: 20px;
    }

    .weather-card {
        padding: 20px;
        border-radius: 18px;
        background: linear-gradient(135deg, #eef7ff, #ffffff);
        border: 1px solid #dbeafe;
        margin-bottom: 15px;
    }

    .agent-card {
        padding: 20px;
        border-radius: 18px;
        background: linear-gradient(135deg, #f8f5ff, #ffffff);
        border: 1px solid #ddd6fe;
        margin-bottom: 15px;
    }

    .advice-card {
        padding: 18px;
        border-radius: 16px;
        margin-top: 10px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
    }

    .route-card {
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        margin-bottom: 12px;
    }

    .danger-card {
        padding: 18px;
        border-radius: 16px;
        background: #fff1f2;
        border: 1px solid #fecdd3;
        margin-bottom: 15px;
    }

    .success-card {
        padding: 18px;
        border-radius: 16px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        margin-bottom: 15px;
    }

    .warning-card {
        padding: 18px;
        border-radius: 16px;
        background: #fffbeb;
        border: 1px solid #fde68a;
        margin-bottom: 15px;
    }

    .notification-card {
        padding: 16px;
        border-radius: 14px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        margin-bottom: 10px;
    }

    .chat-agent {
        padding: 15px;
        border-radius: 15px;
        background: #f3f4f6;
        margin-bottom: 10px;
    }

    .chat-user {
        padding: 15px;
        border-radius: 15px;
        background: #e0f2fe;
        margin-bottom: 10px;
    }

    .metric-box {
        padding: 14px;
        border-radius: 12px;
        background: #f8fafc;
        text-align: center;
        border: 1px solid #e2e8f0;
    }

    .small-place {
        padding: 10px;
        border-radius: 10px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        margin-bottom: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "current_location": None,
    "current_weather": None,
    "search_location_results": [],
    "destination": None,
    "destination_results": [],
    "routes": [],
    "selected_route": None,
    "route_weather": [],
    "map_last_clicked": None,

    "activity": "🎓 College",
    "custom_activity": "",

    "agent_messages": [],
    "agent_started": False,
    "agent_finished": False,

    "history": [],

    "preferences": [
        "🎓 College",
        "🚶 Walking",
        "🛍️ Shopping",
        "🏠 Small Work",
        "🏍️ Bike",
        "🚗 Car",
        "🚌 Bus",
        "🎬 Movie",
        "🍴 Restaurant",
        "🌳 Outdoor",
        "🧳 Traveling"
    ],

    "notifications": [],

    "travel_mode": "driving",

    "location_requested": False,
    "auto_location_attempted": False
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# WEATHER CODE DESCRIPTION
# ============================================================

def weather_description(code):

    code = int(code)

    weather_codes = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Depositing rime fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌦️"),
        55: ("Dense drizzle", "🌧️"),
        56: ("Light freezing drizzle", "🌧️"),
        57: ("Dense freezing drizzle", "🌧️"),
        61: ("Slight rain", "🌦️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        66: ("Light freezing rain", "🌧️"),
        67: ("Heavy freezing rain", "🌧️"),
        71: ("Slight snow", "🌨️"),
        73: ("Moderate snow", "🌨️"),
        75: ("Heavy snow", "❄️"),
        77: ("Snow grains", "🌨️"),
        80: ("Slight rain showers", "🌦️"),
        81: ("Moderate rain showers", "🌧️"),
        82: ("Violent rain showers", "⛈️"),
        85: ("Slight snow showers", "🌨️"),
        86: ("Heavy snow showers", "❄️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with slight hail", "⛈️"),
        99: ("Thunderstorm with heavy hail", "⛈️"),
    }

    return weather_codes.get(
        code,
        ("Unknown weather", "🌡️")
    )


# ============================================================
# HTTP HELPER
# ============================================================

def safe_get(url, params=None, headers=None):

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None

    except Exception:
        return None


# ============================================================
# CURRENT TIME
# ============================================================

def get_local_time():

    return datetime.now()


def get_day_period():

    hour = get_local_time().hour

    if 5 <= hour < 12:
        return "Morning", "🌅"

    elif 12 <= hour < 17:
        return "Afternoon", "☀️"

    elif 17 <= hour < 20:
        return "Evening", "🌇"

    else:
        return "Night", "🌙"


# ============================================================
# BROWSER LOCATION
# ============================================================

def get_browser_location():

    try:

        location = get_geolocation()

        if not location:
            return None

        if "error" in location:

            return {
                "error": location["error"]
            }

        coords = location.get(
            "coords",
            {}
        )

        latitude = coords.get(
            "latitude"
        )

        longitude = coords.get(
            "longitude"
        )

        if latitude is None or longitude is None:
            return None

        return {
            "latitude": float(latitude),
            "longitude": float(longitude)
        }

    except Exception:

        return None


# ============================================================
# REVERSE GEOCODING
# ============================================================

def reverse_geocode(
    latitude,
    longitude
):

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "PersonalWeatherAgent/1.0"
    }

    try:

        response = requests.get(
            NOMINATIM_REVERSE,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        address = data.get(
            "address",
            {}
        )

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or "Selected Location"
        )

        state = address.get(
            "state",
            ""
        )

        country = address.get(
            "country",
            ""
        )

        return {
            "name": city,
            "state": state,
            "country": country,
            "display_name": data.get(
                "display_name",
                city
            )
        }

    except Exception:

        return {
            "name": "Selected Location",
            "state": "",
            "country": "",
            "display_name": "Selected Location"
        }


# ============================================================
# CREATE LOCATION
# ============================================================

def create_location(
    latitude,
    longitude
):

    place = reverse_geocode(
        latitude,
        longitude
    )

    return {
        "name": place["name"],
        "state": place["state"],
        "country": place["country"],
        "latitude": float(latitude),
        "longitude": float(longitude)
    }


# ============================================================
# GEOCODE SEARCH
# ============================================================

def geocode_place(place):

    params = {
        "name": place,
        "count": 8,
        "language": "en",
        "format": "json"
    }

    data = safe_get(
        OPEN_METEO_GEOCODING,
        params
    )

    if not data:
        return []

    results = []

    for item in data.get(
        "results",
        []
    ):

        results.append(
            {
                "name": item.get(
                    "name",
                    place
                ),
                "latitude": float(
                    item["latitude"]
                ),
                "longitude": float(
                    item["longitude"]
                ),
                "country": item.get(
                    "country",
                    ""
                ),
                "state": item.get(
                    "admin1",
                    ""
                ),
                "timezone": item.get(
                    "timezone",
                    ""
                )
            }
        )

    return results


# ============================================================
# WEATHER
# ============================================================

def get_weather(
    latitude,
    longitude
):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "showers,"
            "weather_code,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "wind_gusts_10m,"
            "uv_index"
        ),

        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "precipitation,"
            "rain,"
            "showers,"
            "weather_code,"
            "wind_speed_10m,"
            "uv_index"
        ),

        "forecast_days": 2,
        "timezone": "auto"
    }

    return safe_get(
        OPEN_METEO_WEATHER,
        params
    )


# ============================================================
# POINT WEATHER
# ============================================================

def get_point_weather(
    latitude,
    longitude
):

    data = get_weather(
        latitude,
        longitude
    )

    if not data:
        return None

    current = data.get(
        "current",
        {}
    )

    code = current.get(
        "weather_code",
        0
    )

    description, icon = weather_description(
        code
    )

    return {
        "temperature": current.get(
            "temperature_2m"
        ),
        "feels_like": current.get(
            "apparent_temperature"
        ),
        "humidity": current.get(
            "relative_humidity_2m"
        ),
        "precipitation": current.get(
            "precipitation"
        ),
        "rain": current.get(
            "rain"
        ),
        "showers": current.get(
            "showers"
        ),
        "weather_code": code,
        "description": description,
        "icon": icon,
        "cloud_cover": current.get(
            "cloud_cover"
        ),
        "wind_speed": current.get(
            "wind_speed_10m"
        ),
        "wind_direction": current.get(
            "wind_direction_10m"
        ),
        "wind_gusts": current.get(
            "wind_gusts_10m"
        ),
        "uv_index": current.get(
            "uv_index"
        ),
        "hourly": data.get(
            "hourly",
            {}
        )
    }


# ============================================================
# WEATHER FLAGS
# ============================================================

def is_rainy(weather):

    if not weather:
        return False

    rainy_codes = {
        51, 53, 55,
        56, 57,
        61, 63, 65,
        66, 67,
        80, 81, 82,
        95, 96, 99
    }

    return (
        weather.get("weather_code", 0) in rainy_codes
        or (weather.get("rain", 0) or 0) > 0
        or (weather.get("showers", 0) or 0) > 0
    )


def is_storm(weather):

    if not weather:
        return False

    return weather.get(
        "weather_code",
        0
    ) in {95, 96, 99}


# ============================================================
# ACTIVITY-SPECIFIC ADVICE
# ============================================================

def generate_activity_advice(
    weather,
    activity,
    period
):

    if not weather:

        return [
            "Weather information is currently unavailable."
        ]

    temp = weather.get(
        "temperature"
    )

    rain = weather.get(
        "rain",
        0
    ) or 0

    wind = weather.get(
        "wind_speed",
        0
    ) or 0

    gust = weather.get(
        "wind_gusts",
        0
    ) or 0

    uv = weather.get(
        "uv_index",
        0
    ) or 0

    advice = []

    # --------------------------------------------------------
    # GENERAL WEATHER
    # --------------------------------------------------------

    if temp is not None and temp >= 38:

        advice.append(
            "🥵 It is very hot outside. Carry enough water "
            "and avoid unnecessary long outdoor exposure."
        )

    elif temp is not None and temp >= 33:

        advice.append(
            "☀️ It is hot outside. Carry water and consider "
            "sunscreen and sunglasses."
        )

    if uv >= 6:

        advice.append(
            "🧴 UV exposure may be strong. Sunscreen and "
            "sunglasses can be useful for outdoor activities."
        )

    if is_rainy(weather):

        advice.append(
            "☔ Rain is possible/current. Carry an umbrella "
            "or raincoat and be careful on wet roads."
        )

    if is_storm(weather):

        advice.append(
            "⛈️ Thunderstorm conditions are possible. "
            "If thunder or lightning occurs, move indoors "
            "or to a safe sheltered place."
        )

    if wind >= 35 or gust >= 50:

        advice.append(
            "💨 Strong winds are possible. Take extra care "
            "while walking or riding a two-wheeler."
        )

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    if "Walking" in activity:

        if is_rainy(weather):

            advice.append(
                "🚶 Since you are walking, an umbrella and "
                "comfortable footwear may be useful."
            )

        elif temp is not None and temp >= 33:

            advice.append(
                "🚶 Since you are walking in hot weather, "
                "carry water and consider walking in a shaded area."
            )

        else:

            advice.append(
                "🚶 Conditions look reasonably suitable for walking. "
                "Keep checking the weather if you stay outside for long."
            )

    elif "College" in activity:

        advice.append(
            "🎓 For college, keep your usual essentials ready "
            "and check the weather again before leaving."
        )

        if is_rainy(weather):

            advice.append(
                "🎒 Since rain is possible, keeping an umbrella "
                "or raincoat in your college bag would be useful."
            )

    elif "Shopping" in activity:

        advice.append(
            "🛍️ For shopping, check the weather before leaving "
            "and plan your return time if rain is expected."
        )

    elif "Small Work" in activity:

        advice.append(
            "🏠 For a short outdoor task, check the latest weather "
            "before leaving so you don't get caught by changing conditions."
        )

    elif "Bike" in activity:

        advice.append(
            "🏍️ Since you are riding a bike, be especially careful "
            "if roads are wet or winds are strong."
        )

        if is_rainy(weather):

            advice.append(
                "🌧️ Rain can reduce road grip and visibility. "
                "Ride carefully and avoid unnecessary speeding."
            )

    elif "Car" in activity:

        advice.append(
            "🚗 If you're driving, keep an eye on rain, visibility "
            "and road conditions."
        )

    elif "Bus" in activity:

        advice.append(
            "🚌 Check the weather before leaving for your bus stop "
            "and keep rain protection with you if needed."
        )

    elif "Movie" in activity:

        advice.append(
            "🎬 For a movie outing, check the weather for both "
            "your departure and return time."
        )

    elif "Restaurant" in activity:

        advice.append(
            "🍴 For a food outing, check the weather around the "
            "time you expect to return."
        )

    elif "Outdoor" in activity:

        advice.append(
            "🌳 Outdoor activities depend strongly on weather changes, "
            "so keep checking rain and heat conditions."
        )

    elif "Traveling" in activity:

        advice.append(
            "🧳 For traveling, check weather at your destination "
            "and important places along the route."
        )

    # --------------------------------------------------------
    # DAY/NIGHT
    # --------------------------------------------------------

    if period == "Night":

        advice.append(
            "🌙 It is nighttime. Visibility can be lower, so "
            "take extra care while travelling or walking."
        )

    elif period == "Afternoon" and temp is not None and temp >= 33:

        advice.append(
            "☀️ Since it is afternoon and temperatures are high, "
            "try to reduce unnecessary exposure to direct sunlight."
        )

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    if not advice:

        advice.append(
            "✅ Conditions look generally suitable for your activity. "
            "Still check the latest weather before leaving."
        )

    return advice


# ============================================================
# NOTIFICATIONS
# ============================================================

def generate_notifications(
    weather,
    activity,
    location_name,
    period
):

    notifications = []

    if not weather:
        return notifications

    temp = weather.get(
        "temperature"
    )

    uv = weather.get(
        "uv_index",
        0
    ) or 0

    wind = weather.get(
        "wind_speed",
        0
    ) or 0

    if is_storm(weather):

        notifications.append(
            {
                "type": "danger",
                "title": "⛈️ Thunderstorm Alert",
                "message": (
                    f"Thunderstorm conditions are possible near "
                    f"{location_name}."
                )
            }
        )

    elif is_rainy(weather):

        notifications.append(
            {
                "type": "warning",
                "title": "🌧️ Rain Alert",
                "message": (
                    f"Rain is possible near {location_name}. "
                    f"Consider carrying an umbrella."
                )
            }
        )

    if temp is not None and temp >= 38:

        notifications.append(
            {
                "type": "warning",
                "title": "🥵 Heat Alert",
                "message": (
                    f"Temperature is around {temp}°C near "
                    f"{location_name}. Keep water with you."
                )
            }
        )

    if uv >= 7:

        notifications.append(
            {
                "type": "warning",
                "title": "☀️ UV Alert",
                "message": (
                    "UV exposure may be strong. Consider sunscreen "
                    "and sunglasses for outdoor activities."
                )
            }
        )

    if wind >= 40:

        notifications.append(
            {
                "type": "warning",
                "title": "💨 Wind Alert",
                "message": (
                    "Strong winds are possible. Take extra care "
                    "if riding a bike or travelling outdoors."
                )
            }
        )

    if period == "Night":

        notifications.append(
            {
                "type": "info",
                "title": "🌙 Night Reminder",
                "message": (
                    f"It's nighttime and you selected {activity}. "
                    "Visibility may be lower."
                )
            }
        )

    return notifications


# ============================================================
# ROUTING
# ============================================================

def get_routes(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    mode="driving"
):

    profile = mode

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    url = (
        f"{OSRM_ROUTE}/{profile}/{coordinates}"
    )

    params = {
        "alternatives": "true",
        "steps": "true",
        "geometries": "geojson",
        "overview": "full"
    }

    data = safe_get(
        url,
        params
    )

    if not data:
        return []

    if data.get("code") != "Ok":
        return []

    routes = []

    for index, route in enumerate(
        data.get("routes", [])
    ):

        distance_km = (
            route.get(
                "distance",
                0
            ) / 1000
        )

        duration_min = (
            route.get(
                "duration",
                0
            ) / 60
        )

        geometry = route.get(
            "geometry",
            {}
        )

        coordinates_geo = geometry.get(
            "coordinates",
            []
        )

        routes.append(
            {
                "id": index + 1,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "geometry": coordinates_geo,
                "legs": route.get(
                    "legs",
                    []
                )
            }
        )

    routes.sort(
        key=lambda x: x["distance_km"]
    )

    return routes


# ============================================================
# SAMPLE ROUTE POINTS
# ============================================================

def sample_route_points(
    geometry,
    max_points=8
):

    if not geometry:
        return []

    total = len(geometry)

    if total <= max_points:

        indices = list(
            range(total)
        )

    else:

        indices = [
            round(
                i * (total - 1)
                / (max_points - 1)
            )
            for i in range(max_points)
        ]

    points = []

    for idx in indices:

        lon, lat = geometry[idx]

        points.append(
            {
                "latitude": lat,
                "longitude": lon
            }
        )

    return points


# ============================================================
# HAVERSINE
# ============================================================

def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dlat = math.radians(
        lat2 - lat1
    )

    dlon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(p1)
        * math.cos(p2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * R
        * math.asin(
            math.sqrt(a)
        )
    )


# ============================================================
# ROUTE PLACE NAME
# ============================================================

def get_route_place_name(
    latitude,
    longitude
):

    place = reverse_geocode(
        latitude,
        longitude
    )

    return place.get(
        "name",
        "Route Point"
    )


# ============================================================
# ROUTE WEATHER
# ============================================================

def analyze_route_weather(
    route,
    start,
    destination
):

    points = sample_route_points(
        route["geometry"],
        max_points=8
    )

    results = []

    for i, point in enumerate(
        points
    ):

        weather = get_point_weather(
            point["latitude"],
            point["longitude"]
        )

        if not weather:
            continue

        if i == 0:

            place_name = start.get(
                "name",
                "Start"
            )

        elif i == len(points) - 1:

            place_name = destination.get(
                "name",
                "Destination"
            )

        else:

            place_name = get_route_place_name(
                point["latitude"],
                point["longitude"]
            )

        results.append(
            {
                "name": place_name,
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "weather": weather
            }
        )

        time.sleep(0.1)

    return results


# ============================================================
# ROUTE RISK
# ============================================================

def route_risk_analysis(
    route_weather
):

    if not route_weather:

        return {
            "level": "unknown",
            "score": 0,
            "problems": [
                "Weather information is unavailable."
            ]
        }

    score = 0
    problems = []

    for point in route_weather:

        weather = point["weather"]

        temp = weather.get(
            "temperature"
        )

        rain = weather.get(
            "rain",
            0
        ) or 0

        wind = weather.get(
            "wind_speed",
            0
        ) or 0

        gust = weather.get(
            "wind_gusts",
            0
        ) or 0

        code = weather.get(
            "weather_code",
            0
        )

        if code in {
            95, 96, 99
        }:

            score += 5

            problems.append(
                f"Thunderstorm possible near {point['name']}."
            )

        elif (
            code in {
                65, 67, 82
            }
            or rain >= 5
        ):

            score += 4

            problems.append(
                f"Heavy rain possible near {point['name']}."
            )

        elif is_rainy(weather):

            score += 2

            problems.append(
                f"Rain is possible near {point['name']}."
            )

        if wind >= 35 or gust >= 50:

            score += 3

            problems.append(
                f"Strong wind is possible near {point['name']}."
            )

        if (
            temp is not None
            and temp >= 38
        ):

            score += 2

            problems.append(
                f"Very hot conditions near {point['name']}."
            )

    if score >= 8:
        level = "high"

    elif score >= 4:
        level = "medium"

    else:
        level = "low"

    problems = list(
        dict.fromkeys(problems)
    )

    return {
        "level": level,
        "score": score,
        "problems": problems
    }


# ============================================================
# TRAVEL ADVICE
# ============================================================

def generate_travel_advice(
    start_weather,
    destination_weather,
    route_weather,
    route,
    route_risk,
    period
):

    advice = []

    if start_weather and is_rainy(
        start_weather
    ):

        advice.append(
            "☔ Rain is possible at your starting point. "
            "Keep an umbrella or raincoat ready."
        )

    if destination_weather and is_rainy(
        destination_weather
    ):

        advice.append(
            "☔ Rain is possible at your destination too. "
            "Keep rain protection with you."
        )

    if route_risk["level"] == "high":

        advice.append(
            "⚠️ Several route points have notable weather concerns. "
            "Check conditions again before starting."
        )

    elif route_risk["level"] == "medium":

        advice.append(
            "⚠️ Weather changes are present along the route. "
            "Pay attention to local conditions during the journey."
        )

    else:

        advice.append(
            "✅ No major weather-related issue was detected "
            "at the sampled route points."
        )

    if period == "Night":

        advice.append(
            "🌙 It is nighttime. Visibility may be lower, "
            "so take extra care while travelling."
        )

    if route["distance_km"] <= 50:

        advice.append(
            "🛣️ This is a relatively short journey. "
            "Check the latest weather before leaving."
        )

    else:

        advice.append(
            "🛣️ This is a longer journey. Weather can change "
            "during the trip, so check conditions periodically."
        )

    return advice


# ============================================================
# START LOCATION MAP
# ============================================================

def create_start_location_map(
    current_location=None
):

    if current_location:

        center_lat = current_location[
            "latitude"
        ]

        center_lon = current_location[
            "longitude"
        ]

        zoom = 12

    else:

        center_lat = 20.5937
        center_lon = 78.9629
        zoom = 5

    m = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=zoom,
        control_scale=True
    )

    if current_location:

        lat = current_location[
            "latitude"
        ]

        lon = current_location[
            "longitude"
        ]

        popup_text = (
            f"<b>📍 Selected Location</b><br>"
            f"{current_location.get('name', 'Location')}<br>"
            f"{current_location.get('state', '')}<br>"
            f"{current_location.get('country', '')}"
        )

        # Main marker

        folium.Marker(
            [
                lat,
                lon
            ],
            tooltip="📍 Selected Location",
            popup=folium.Popup(
                popup_text,
                max_width=300
            ),
            icon=folium.Icon(
                color="blue",
                icon="home"
            )
        ).add_to(m)

        # Small surrounding zone

        folium.Circle(
            [
                lat,
                lon
            ],
            radius=2500,
            color="#3388ff",
            fill=True,
            fill_opacity=0.12,
            popup="📍 Your selected area"
        ).add_to(m)

        folium.CircleMarker(
            [
                lat,
                lon
            ],
            radius=8,
            color="#3388ff",
            fill=True,
            fill_opacity=0.9
        ).add_to(m)

    return m


# ============================================================
# ROUTE MAP
# ============================================================

def create_route_map(
    start,
    destination,
    routes,
    selected_route_id=None,
    route_weather=None
):

    center_lat = (
        start["latitude"]
        + destination["latitude"]
    ) / 2

    center_lon = (
        start["longitude"]
        + destination["longitude"]
    ) / 2

    m = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=9,
        control_scale=True
    )

    folium.Marker(
        [
            start["latitude"],
            start["longitude"]
        ],
        tooltip="Start",
        popup=f"📍 {start.get('name', 'Start')}",
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(m)

    folium.Marker(
        [
            destination["latitude"],
            destination["longitude"]
        ],
        tooltip="Destination",
        popup=f"🎯 {destination.get('name', 'Destination')}",
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(m)

    for route in routes:

        selected = (
            route["id"] == selected_route_id
        )

        folium.PolyLine(
            [
                [lat, lon]
                for lon, lat
                in route["geometry"]
            ],
            weight=7 if selected else 4,
            opacity=0.95 if selected else 0.35,
            tooltip=(
                f"Route {route['id']} | "
                f"{route['distance_km']:.1f} km"
            )
        ).add_to(m)

    if route_weather:

        for point in route_weather:

            weather = point["weather"]

            popup_text = (
                f"<b>{point['name']}</b><br>"
                f"{weather['icon']} "
                f"{weather['description']}<br>"
                f"Temperature: {weather['temperature']} °C<br>"
                f"Rain: {weather['rain']} mm<br>"
                f"Wind: {weather['wind_speed']} km/h"
            )

            folium.CircleMarker(
                [
                    point["latitude"],
                    point["longitude"]
                ],
                radius=7,
                popup=folium.Popup(
                    popup_text,
                    max_width=300
                ),
                fill=True
            ).add_to(m)

    return m


# ============================================================
# DISPLAY WEATHER
# ============================================================

def display_weather_card(
    title,
    weather,
    location_name
):

    if not weather:

        st.warning(
            f"Weather unavailable for {location_name}."
        )

        return

    st.markdown(
        f"""
        <div class="weather-card">

        <h2>{title}</h2>

        <h1>
            {weather['icon']}
            {weather['temperature']} °C
        </h1>

        <h3>{weather['description']}</h3>

        <p>
        📍 {location_name}
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Feels Like",
            f"{weather['feels_like']} °C"
        )

    with c2:
        st.metric(
            "Humidity",
            f"{weather['humidity']} %"
        )

    with c3:
        st.metric(
            "Wind",
            f"{weather['wind_speed']} km/h"
        )

    with c4:
        st.metric(
            "UV Index",
            str(weather["uv_index"])
        )


# ============================================================
# SAVE HISTORY
# ============================================================

def save_activity_history(
    activity,
    location,
    weather,
    advice,
    destination=None,
    route=None
):

    now = datetime.now()

    record = {
        "Date": now.strftime("%Y-%m-%d"),
        "Time": now.strftime("%I:%M %p"),
        "Activity": activity,
        "Location": location.get(
            "name",
            "Unknown"
        ) if location else "Unknown",

        "State": location.get(
            "state",
            ""
        ) if location else "",

        "Destination": destination.get(
            "name",
            ""
        ) if destination else "",

        "Temperature": (
            weather.get("temperature")
            if weather
            else ""
        ),

        "Weather": (
            weather.get("description")
            if weather
            else ""
        ),

        "Rain": (
            weather.get("rain")
            if weather
            else ""
        ),

        "Wind": (
            weather.get("wind_speed")
            if weather
            else ""
        ),

        "Period": get_day_period()[0],

        "Advice": " | ".join(advice),

        "Route Distance KM": (
            round(route["distance_km"], 1)
            if route
            else ""
        )
    }

    st.session_state.history.insert(
        0,
        record
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🌦️ Weather Agent")

    st.caption(
        "Your personal daily weather assistant"
    )

    st.divider()

    menu = st.radio(
        "Navigate",
        [
            "🏠 Home",
            "🗺️ Location & Map",
            "🤖 Personal Agent",
            "🎯 My Activities",
            "🛣️ Route Weather",
            "📜 History",
            "⚙️ Settings"
        ]
    )

    st.divider()

    current_time = get_local_time()

    period, period_icon = get_day_period()

    st.write(
        f"{period_icon} **{period}**"
    )

    st.write(
        f"🕐 {current_time.strftime('%I:%M %p')}"
    )

    st.write(
        f"📅 {current_time.strftime('%d %B %Y')}"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🌦️ Personal Weather Agent'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Weather that understands your location, time and daily activity.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOCATION & MAP
# ============================================================

if menu in [
    "🏠 Home",
    "🗺️ Location & Map"
]:

    st.header(
        "📍 Location & Map"
    )

    st.write(
        "Your map is ready from the beginning. "
        "Use your current location, search for a place, "
        "or simply click anywhere on the map."
    )

    col1, col2 = st.columns(
        [1, 2]
    )

    with col1:

        get_location_button = st.button(
            "📍 Use My Current Location",
            type="primary",
            use_container_width=True
        )

    with col2:

        st.caption(
            "Browser location permission is required for automatic location."
        )

    # --------------------------------------------------------
    # CURRENT LOCATION
    # --------------------------------------------------------

    if get_location_button:

        with st.spinner(
            "Getting your current location..."
        ):

            location = get_browser_location()

        if location:

            if "error" in location:

                error = location["error"]

                if error.get("code") == 1:

                    st.error(
                        "Location permission was denied. "
                        "Allow location access in your browser "
                        "and try again."
                    )

                else:

                    st.error(
                        "Unable to get your location."
                    )

            else:

                with st.spinner(
                    "Understanding your location..."
                ):

                    selected_location = create_location(
                        location["latitude"],
                        location["longitude"]
                    )

                    selected_weather = get_point_weather(
                        location["latitude"],
                        location["longitude"]
                    )

                st.session_state.current_location = (
                    selected_location
                )

                st.session_state.current_weather = (
                    selected_weather
                )

                st.session_state.routes = []
                st.session_state.selected_route = None
                st.session_state.route_weather = []

                st.rerun()

    # --------------------------------------------------------
    # SEARCH LOCATION
    # --------------------------------------------------------

    st.subheader(
        "🔍 Search Location"
    )

    location_search = st.text_input(
        "Search a city, town or village",
        placeholder="Example: Mangalagiri"
    )

    search_location_button = st.button(
        "🔎 Search Location"
    )

    if search_location_button:

        if not location_search.strip():

            st.warning(
                "Please enter a location."
            )

        else:

            with st.spinner(
                "Searching location..."
            ):

                results = geocode_place(
                    location_search.strip()
                )

            if results:

                st.session_state.search_location_results = (
                    results
                )

            else:

                st.error(
                    "Location not found. Try another name."
                )

    search_results = (
        st.session_state.search_location_results
    )

    if search_results:

        labels = []

        for item in search_results:

            labels.append(
                f"{item['name']}, "
                f"{item['state']}, "
                f"{item['country']}"
            )

        selected_label = st.selectbox(
            "Select location",
            labels
        )

        selected_index = labels.index(
            selected_label
        )

        selected_search_location = (
            search_results[selected_index]
        )

        if st.button(
            "📍 Use This Location",
            type="primary"
        ):

            with st.spinner(
                "Loading weather..."
            ):

                selected_location = create_location(
                    selected_search_location[
                        "latitude"
                    ],
                    selected_search_location[
                        "longitude"
                    ]
                )

                selected_weather = get_point_weather(
                    selected_search_location[
                        "latitude"
                    ],
                    selected_search_location[
                        "longitude"
                    ]
                )

            st.session_state.current_location = (
                selected_location
            )

            st.session_state.current_weather = (
                selected_weather
            )

            st.session_state.routes = []
            st.session_state.selected_route = None
            st.session_state.route_weather = []

            st.rerun()

    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    st.subheader(
        "🗺️ Interactive Map"
    )

    st.caption(
        "Click anywhere on the map to make that point your location."
    )

    start_map = create_start_location_map(
        st.session_state.current_location
    )

    map_result = st_folium(
        start_map,
        width=None,
        height=550,
        returned_objects=[
            "last_clicked"
        ],
        key="main_location_map"
    )

    # --------------------------------------------------------
    # MAP CLICK
    # --------------------------------------------------------

    if map_result:

        clicked = map_result.get(
            "last_clicked"
        )

        if clicked:

            lat = clicked.get("lat")
            lon = clicked.get("lng")

            if lat is not None and lon is not None:

                clicked_key = (
                    round(lat, 6),
                    round(lon, 6)
                )

                if (
                    st.session_state.map_last_clicked
                    != clicked_key
                ):

                    st.session_state.map_last_clicked = (
                        clicked_key
                    )

                    with st.spinner(
                        "Understanding selected area..."
                    ):

                        selected_location = create_location(
                            lat,
                            lon
                        )

                        selected_weather = get_point_weather(
                            lat,
                            lon
                        )

                    st.session_state.current_location = (
                        selected_location
                    )

                    st.session_state.current_weather = (
                        selected_weather
                    )

                    st.rerun()

    # --------------------------------------------------------
    # LOCATION SUMMARY
    # --------------------------------------------------------

    current_location = (
        st.session_state.current_location
    )

    current_weather = (
        st.session_state.current_weather
    )

    if current_location:

        st.success(
            f"📍 **{current_location['name']}**"
        )

        st.caption(
            f"{current_location.get('state', '')}, "
            f"{current_location.get('country', '')}"
        )

        display_weather_card(
            "🌍 Current Weather",
            current_weather,
            current_location["name"]
        )

    else:

        st.info(
            "📍 Select your current location using the button, "
            "search, or map."
        )


# ============================================================
# HOME
# ============================================================

if menu == "🏠 Home":

    current_location = (
        st.session_state.current_location
    )

    current_weather = (
        st.session_state.current_weather
    )

    if current_location and current_weather:

        st.divider()

        period, period_icon = get_day_period()

        st.header(
            f"{period_icon} Good {period.lower()}!"
        )

        st.write(
            f"You're currently around **{current_location['name']}**."
        )

        # ----------------------------------------------------
        # QUICK ACTIVITY
        # ----------------------------------------------------

        st.subheader(
            "🎯 What are you doing?"
        )

        activity = st.selectbox(
            "Choose an activity",
            st.session_state.preferences,
            index=0
        )

        st.session_state.activity = activity

        # ----------------------------------------------------
        # ADVICE
        # ----------------------------------------------------

        advice = generate_activity_advice(
            current_weather,
            activity,
            period
        )

        st.markdown(
            '<div class="agent-card">',
            unsafe_allow_html=True
        )

        st.subheader(
            f"🤖 Your advice for {activity}"
        )

        for item in advice:

            st.write(
                item
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        notifications = generate_notifications(
            current_weather,
            activity,
            current_location["name"],
            period
        )

        if notifications:

            st.subheader(
                "🔔 Notifications"
            )

            for notification in notifications:

                if notification["type"] == "danger":

                    st.error(
                        f"{notification['title']}\n\n"
                        f"{notification['message']}"
                    )

                elif notification["type"] == "warning":

                    st.warning(
                        f"{notification['title']}\n\n"
                        f"{notification['message']}"
                    )

                else:

                    st.info(
                        f"{notification['title']}\n\n"
                        f"{notification['message']}"
                    )

        # ----------------------------------------------------
        # START AGENT
        # ----------------------------------------------------

        st.divider()

        if st.button(
            "🤖 Talk to My Personal Agent",
            type="primary"
        ):

            st.session_state.agent_started = True
            st.session_state.agent_finished = False

            st.session_state.agent_messages = [
                {
                    "role": "agent",
                    "message": (
                        f"Hey 👋 I can help you with your "
                        f"{activity.lower()} plan."
                    )
                },
                {
                    "role": "agent",
                    "message": (
                        f"It's currently {period.lower()} "
                        f"around {current_location['name']}."
                    )
                },
                {
                    "role": "agent",
                    "message": (
                        "I'll look at the weather and give you "
                        "simple practical advice."
                    )
                }
            ]

            st.rerun()

    else:

        st.info(
            "First select a location. Then I'll become your "
            "personal weather assistant."
        )


# ============================================================
# PERSONAL AGENT
# ============================================================

if menu == "🤖 Personal Agent":

    st.header(
        "🤖 Personal Mini Agent"
    )

    current_location = (
        st.session_state.current_location
    )

    current_weather = (
        st.session_state.current_weather
    )

    if not current_location:

        st.warning(
            "Please select your location first."
        )

    else:

        period, period_icon = get_day_period()

        activity = st.selectbox(
            "What are you doing?",
            st.session_state.preferences,
            index=0
        )

        st.session_state.activity = activity

        st.markdown(
            '<div class="agent-card">',
            unsafe_allow_html=True
        )

        st.write(
            f"📍 Location: **{current_location['name']}**"
        )

        st.write(
            f"{period_icon} Time: **{period}**"
        )

        st.write(
            f"🎯 Activity: **{activity}**"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        if not st.session_state.agent_started:

            if st.button(
                "🤖 Start Conversation",
                type="primary"
            ):

                st.session_state.agent_started = True
                st.session_state.agent_finished = False

                st.session_state.agent_messages = [
                    {
                        "role": "agent",
                        "message": (
                            f"Hey 😊 You're going for "
                            f"{activity.lower()}, right?"
                        )
                    },
                    {
                        "role": "agent",
                        "message": (
                            f"I checked the weather around "
                            f"{current_location['name']}."
                        )
                    }
                ]

                st.rerun()

        else:

            # ------------------------------------------------
            # DISPLAY CHAT
            # ------------------------------------------------

            for message in (
                st.session_state.agent_messages
            ):

                if message["role"] == "agent":

                    st.markdown(
                        f"""
                        <div class="chat-agent">
                        🤖 <b>Agent</b><br>
                        {message["message"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="chat-user">
                        👤 <b>You</b><br>
                        {message["message"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # ------------------------------------------------
            # OPTIONAL USER MESSAGE
            # ------------------------------------------------

            user_message = st.text_input(
                "Talk to your agent",
                placeholder="Example: I am leaving at 6 PM..."
            )

            send_message = st.button(
                "💬 Send"
            )

            if send_message and user_message.strip():

                st.session_state.agent_messages.append(
                    {
                        "role": "user",
                        "message": user_message.strip()
                    }
                )

                advice = generate_activity_advice(
                    current_weather,
                    activity,
                    period
                )

                response = (
                    f"Got it 😊 Since you're doing "
                    f"{activity.lower()}, here is what I'd suggest:<br><br>"
                    + "<br>".join(advice)
                )

                st.session_state.agent_messages.append(
                    {
                        "role": "agent",
                        "message": response
                    }
                )

                st.rerun()

            # ------------------------------------------------
            # FINISH
            # ------------------------------------------------

            st.divider()

            finish = st.button(
                "✅ Finish & Save Activity",
                type="primary"
            )

            if finish:

                advice = generate_activity_advice(
                    current_weather,
                    activity,
                    period
                )

                save_activity_history(
                    activity,
                    current_location,
                    current_weather,
                    advice
                )

                st.session_state.agent_finished = True
                st.session_state.agent_started = False
                st.session_state.agent_messages = []

                st.success(
                    "✅ Activity finished and saved to History."
                )


# ============================================================
# MY ACTIVITIES
# ============================================================

if menu == "🎯 My Activities":

    st.header(
        "🎯 My Activities"
    )

    st.write(
        "Everyone has different daily routines. "
        "Choose the activities you want to keep."
    )

    all_activities = [
        "🎓 College",
        "🚶 Walking",
        "🛍️ Shopping",
        "🏠 Small Work",
        "🏍️ Bike",
        "🚗 Car",
        "🚌 Bus",
        "🎬 Movie",
        "🍴 Restaurant",
        "🌳 Outdoor",
        "🧳 Traveling"
    ]

    selected_preferences = st.multiselect(
        "Select your activities",
        all_activities,
        default=[
            x for x in all_activities
            if x in st.session_state.preferences
        ]
    )

    custom_activity = st.text_input(
        "➕ Add your own activity",
        placeholder="Example: Temple, Gym, Library..."
    )

    if custom_activity.strip():

        custom_name = (
            "✨ " + custom_activity.strip()
        )

        if custom_name not in selected_preferences:

            selected_preferences.append(
                custom_name
            )

    if st.button(
        "💾 Save My Activities",
        type="primary"
    ):

        if not selected_preferences:

            st.warning(
                "Please select at least one activity."
            )

        else:

            st.session_state.preferences = (
                selected_preferences
            )

            st.success(
                "✅ Your personal activities have been saved."
            )

    st.divider()

    st.subheader(
        "Your current activities"
    )

    for activity in st.session_state.preferences:

        st.write(
            f"• {activity}"
        )


# ============================================================
# ROUTE WEATHER
# ============================================================

if menu == "🛣️ Route Weather":

    st.header(
        "🛣️ Traveling & Route Weather"
    )

    current_location = (
        st.session_state.current_location
    )

    if not current_location:

        st.warning(
            "First select your starting location."
        )

    else:

        st.success(
            f"📍 Starting from **{current_location['name']}**"
        )

        st.subheader(
            "🎯 Where are you going?"
        )

        destination_input = st.text_input(
            "Search destination",
            placeholder="Example: Vijayawada"
        )

        search_destination = st.button(
            "🔎 Search Destination"
        )

        if search_destination:

            if not destination_input.strip():

                st.warning(
                    "Please enter a destination."
                )

            else:

                with st.spinner(
                    "Searching destination..."
                ):

                    results = geocode_place(
                        destination_input.strip()
                    )

                if results:

                    st.session_state.destination_results = (
                        results
                    )

                else:

                    st.error(
                        "Destination not found."
                    )

        destination_results = (
            st.session_state.destination_results
        )

        if destination_results:

            labels = []

            for item in destination_results:

                labels.append(
                    f"{item['name']}, "
                    f"{item['state']}, "
                    f"{item['country']}"
                )

            destination_label = st.selectbox(
                "Select destination",
                labels
            )

            index = labels.index(
                destination_label
            )

            selected_destination = (
                destination_results[index]
            )

            if st.button(
                "🎯 Set Destination",
                type="primary"
            ):

                st.session_state.destination = (
                    selected_destination
                )

                st.session_state.routes = []
                st.session_state.route_weather = []
                st.session_state.selected_route = None

                st.rerun()

        destination = (
            st.session_state.destination
        )

        if destination:

            st.divider()

            st.subheader(
                f"🎯 {destination['name']}"
            )

            destination_weather = get_point_weather(
                destination["latitude"],
                destination["longitude"]
            )

            display_weather_card(
                "🎯 Destination Weather",
                destination_weather,
                (
                    f"{destination['name']}, "
                    f"{destination.get('state', '')}"
                )
            )

            st.subheader(
                "🚗 Choose travel mode"
            )

            travel_mode_display = st.selectbox(
                "How are you travelling?",
                [
                    "🚗 Car",
                    "🏍️ Bike",
                    "🚌 Bus"
                ]
            )

            if "Bike" in travel_mode_display:

                st.session_state.travel_mode = "driving"

            elif "Bus" in travel_mode_display:

                st.session_state.travel_mode = "driving"

            else:

                st.session_state.travel_mode = "driving"

            if st.button(
                "🛣️ Find Routes",
                type="primary"
            ):

                with st.spinner(
                    "Finding routes..."
                ):

                    routes = get_routes(
                        current_location["latitude"],
                        current_location["longitude"],
                        destination["latitude"],
                        destination["longitude"],
                        st.session_state.travel_mode
                    )

                if routes:

                    st.session_state.routes = routes
                    st.session_state.selected_route = routes[0]
                    st.session_state.route_weather = []

                    st.rerun()

                else:

                    st.error(
                        "No route could be found."
                    )

        routes = (
            st.session_state.routes
        )

        if routes:

            st.divider()

            st.subheader(
                f"🛣️ {len(routes)} route option(s)"
            )

            route_labels = []

            for route in routes:

                route_labels.append(
                    f"Route {route['id']} — "
                    f"{route['distance_km']:.1f} km — "
                    f"{route['duration_min']:.0f} min"
                )

            selected_route_label = st.radio(
                "Select a route",
                route_labels,
                index=0
            )

            selected_index = route_labels.index(
                selected_route_label
            )

            selected_route = routes[
                selected_index
            ]

            st.session_state.selected_route = (
                selected_route
            )

            st.markdown(
                f"""
                <div class="route-card">

                <h3>🛣️ Route {selected_route['id']}</h3>

                <p>
                📏 Distance:
                <b>{selected_route['distance_km']:.1f} km</b>
                </p>

                <p>
                ⏱️ Time:
                <b>{selected_route['duration_min']:.0f} minutes</b>
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "🌦️ Analyze Route Weather",
                type="primary"
            ):

                with st.spinner(
                    "Checking weather along the route..."
                ):

                    route_weather = analyze_route_weather(
                        selected_route,
                        current_location,
                        destination
                    )

                st.session_state.route_weather = (
                    route_weather
                )

                st.rerun()

        route_weather = (
            st.session_state.route_weather
        )

        if route_weather and destination:

            st.divider()

            st.header(
                "📍 Places Along Your Route"
            )

            for point in route_weather:

                weather = point["weather"]

                st.markdown(
                    f"""
                    <div class="small-place">
                    <b>📍 {point['name']}</b><br>
                    {weather['icon']}
                    {weather['temperature']} °C —
                    {weather['description']}<br>
                    🌧️ Rain: {weather['rain']} mm
                    &nbsp;&nbsp;
                    💨 Wind: {weather['wind_speed']} km/h
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ------------------------------------------------
            # RISK
            # ------------------------------------------------

            risk = route_risk_analysis(
                route_weather
            )

            st.subheader(
                "🔔 Route Notifications"
            )

            if risk["problems"]:

                for problem in risk["problems"]:

                    st.warning(
                        f"🔔 {problem}"
                    )

            else:

                st.success(
                    "✅ No major weather notification "
                    "was generated for the sampled route."
                )

            # ------------------------------------------------
            # TRAVEL ADVICE
            # ------------------------------------------------

            period, _ = get_day_period()

            travel_advice = generate_travel_advice(
                current_weather,
                destination_weather,
                route_weather,
                selected_route,
                risk,
                period
            )

            st.subheader(
                "🤖 Personal Travel Advice"
            )

            for advice in travel_advice:

                st.markdown(
                    f"""
                    <div class="advice-card">
                    {advice}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ------------------------------------------------
            # SAVE TRAVEL
            # ------------------------------------------------

            if st.button(
                "✅ Finish Travel & Save"
            ):

                save_activity_history(
                    "🧳 Traveling",
                    current_location,
                    current_weather,
                    travel_advice,
                    destination,
                    selected_route
                )

                st.success(
                    "✅ Travel activity saved to History."
                )

            # ------------------------------------------------
            # ROUTE MAP
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "🗺️ Route + Weather Map"
            )

            route_map = create_route_map(
                current_location,
                destination,
                routes,
                selected_route_id=selected_route["id"],
                route_weather=route_weather
            )

            st_folium(
                route_map,
                width=None,
                height=600,
                returned_objects=[],
                key="travel_route_map"
            )


# ============================================================
# HISTORY
# ============================================================

if menu == "📜 History":

    st.header(
        "📜 Activity History"
    )

    history = st.session_state.history

    if not history:

        st.info(
            "No activities have been saved yet."
        )

    else:

        df = pd.DataFrame(
            history
        )

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_history = st.text_input(
            "🔎 Search history",
            placeholder="Search activity, place, destination..."
        )

        if search_history.strip():

            search_text = (
                search_history.strip().lower()
            )

            mask = (
                df.astype(str)
                .apply(
                    lambda col: col.str.lower().str.contains(
                        search_text,
                        na=False
                    )
                )
                .any(axis=1)
            )

            filtered_df = df[
                mask
            ]

        else:

            filtered_df = df

        # ----------------------------------------------------
        # DATE FILTER
        # ----------------------------------------------------

        available_dates = sorted(
            df["Date"].unique(),
            reverse=True
        )

        selected_date = st.selectbox(
            "📅 Filter by date",
            ["All Dates"] + available_dates
        )

        if selected_date != "All Dates":

            filtered_df = filtered_df[
                filtered_df["Date"]
                == selected_date
            ]

        st.write(
            f"Showing **{len(filtered_df)}** activity record(s)."
        )

        # ----------------------------------------------------
        # RECORDS
        # ----------------------------------------------------

        for _, row in filtered_df.iterrows():

            with st.expander(
                f"{row['Date']} {row['Time']} — "
                f"{row['Activity']} — "
                f"{row['Location']}"
            ):

                st.write(
                    f"📍 **Location:** {row['Location']}"
                )

                if row["Destination"]:

                    st.write(
                        f"🎯 **Destination:** {row['Destination']}"
                    )

                st.write(
                    f"🌦️ **Weather:** {row['Weather']}"
                )

                st.write(
                    f"🌡️ **Temperature:** {row['Temperature']} °C"
                )

                st.write(
                    f"🌧️ **Rain:** {row['Rain']} mm"
                )

                st.write(
                    f"💨 **Wind:** {row['Wind']} km/h"
                )

                st.write(
                    f"🕐 **Period:** {row['Period']}"
                )

                if row["Route Distance KM"] != "":

                    st.write(
                        f"🛣️ **Route:** "
                        f"{row['Route Distance KM']} km"
                    )

                st.write(
                    "🤖 **Advice:**"
                )

                st.write(
                    row["Advice"]
                )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        st.divider()

        csv_data = filtered_df.to_csv(
            index=False
        ).encode(
            "utf-8"
        )

        st.download_button(
            "⬇️ Download History",
            data=csv_data,
            file_name="weather_agent_history.csv",
            mime="text/csv",
            type="primary"
        )

        # ----------------------------------------------------
        # CLEAR
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🗑️ Clear History"
        )

        confirm_clear = st.checkbox(
            "I understand that clearing history will remove all saved activities."
        )

        if st.button(
            "🗑️ Clear All History"
        ):

            if confirm_clear:

                st.session_state.history = []

                st.success(
                    "✅ History cleared."
                )

                st.rerun()

            else:

                st.warning(
                    "Please confirm before clearing history."
                )


# ============================================================
# SETTINGS
# ============================================================

if menu == "⚙️ Settings":

    st.header(
        "⚙️ Settings"
    )

    st.subheader(
        "👤 Personal Activities"
    )

    st.write(
        "Choose the activities you want your personal agent to show."
    )

    for activity in st.session_state.preferences:

        st.write(
            f"✅ {activity}"
        )

    st.divider()

    st.subheader(
        "🔔 Notification System"
    )

    st.info(
        "The agent creates relevant in-app notifications "
        "based on weather, location, time and activity."
    )

    st.divider()

    st.subheader(
        "🕐 Time Awareness"
    )

    period, icon = get_day_period()

    st.write(
        f"Current period: {icon} **{period}**"
    )

    st.write(
        f"Current time: **{datetime.now().strftime('%I:%M %p')}**"
    )

    st.divider()

    st.subheader(
        "🗑️ Data"
    )

    st.write(
        f"Saved activities: **{len(st.session_state.history)}**"
    )

    if st.button(
        "🧹 Reset Agent Conversation"
    ):

        st.session_state.agent_messages = []
        st.session_state.agent_started = False
        st.session_state.agent_finished = False

        st.success(
            "Conversation reset."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌦️ Personal Weather Agent | "
    "Location • Weather • Activities • Personal Advice • "
    "Travel Routes • Notifications • History"
)
