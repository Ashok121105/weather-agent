import streamlit as st
import requests
import math
import time
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Weather Travel Agent",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONSTANTS
# ============================================================

OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OSRM_ROUTE = "https://router.project-osrm.org/route/v1/driving"

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
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .weather-card {
        padding: 20px;
        border-radius: 18px;
        background: linear-gradient(135deg, #eef7ff, #ffffff);
        border: 1px solid #dbeafe;
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
    }

    .success-card {
        padding: 18px;
        border-radius: 16px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
    }

    .warning-card {
        padding: 18px;
        border-radius: 16px;
        background: #fffbeb;
        border: 1px solid #fde68a;
    }

    .metric-box {
        padding: 14px;
        border-radius: 12px;
        background: #f8fafc;
        text-align: center;
        border: 1px solid #e2e8f0;
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
    "destination": None,
    "destination_results": [],
    "routes": [],
    "selected_route": None,
    "route_weather": [],
    "last_route_key": None,
    "location_requested": False,
    "map_last_clicked": None,
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

    except requests.RequestException as e:

        st.error(
            f"Network/API error: {e}"
        )

        return None

    except Exception as e:

        st.error(
            f"Unexpected error: {e}"
        )

        return None


# ============================================================
# GET BROWSER LOCATION
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
        "User-Agent": "WeatherTravelAgent/1.0"
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
# CREATE START LOCATION
# ============================================================

def create_start_location(
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
# SEARCH DESTINATION
# ============================================================

def geocode_place(place):

    params = {
        "name": place,
        "count": 5,
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
# GET WEATHER
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
# GET POINT WEATHER
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
# SMART DAILY-LIFE ADVICE
# ============================================================

def generate_daily_advice(weather):

    if not weather:

        return {
            "level": "warning",

            "title":
                "Weather information unavailable",

            "items": [
                "Weather data could not be retrieved.",
                "Check your internet connection and try again."
            ]
        }

    temp = weather.get(
        "temperature"
    )

    rain = weather.get(
        "rain",
        0
    ) or 0

    showers = weather.get(
        "showers",
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

    code = weather.get(
        "weather_code",
        0
    )

    advice = []

    rainy_codes = {
        51, 53, 55,
        56, 57,
        61, 63, 65,
        66, 67,
        80, 81, 82,
        95, 96, 99
    }

    storm_codes = {
        95, 96, 99
    }

    if temp is not None and temp >= 38:

        advice.append(
            "🥵 It is very hot. Carry enough water "
            "and avoid unnecessary long outdoor exposure."
        )

    elif temp is not None and temp >= 33:

        advice.append(
            "☀️ It is hot. Use sunscreen, sunglasses "
            "and carry water if you are going outside."
        )

    elif temp is not None and temp >= 29:

        advice.append(
            "🌤️ It is warm. Carry water and use sun "
            "protection if you will stay outdoors for long."
        )

    if uv >= 6:

        advice.append(
            "🧴 UV exposure may be strong. Sunscreen "
            "and sunglasses are recommended for outdoor activities."
        )

    if (
        code in rainy_codes
        or rain > 0
        or showers > 0
    ):

        advice.append(
            "☔ Rain is possible/current. Carry an umbrella "
            "or raincoat and be careful on wet roads."
        )

    if code in storm_codes:

        advice.append(
            "⛈️ Thunderstorm conditions are possible. "
            "Avoid unnecessary outdoor exposure and seek shelter "
            "if thunder/lightning occurs."
        )

    if wind >= 35 or gust >= 50:

        advice.append(
            "💨 Strong winds are possible. Be careful while "
            "walking, riding, or travelling on two-wheelers."
        )

    if (
        weather.get("humidity") is not None
        and weather["humidity"] >= 80
    ):

        advice.append(
            "💧 Humidity is high. Keep water with you "
            "and expect the weather to feel warmer."
        )

    if not advice:

        advice.append(
            "✅ Conditions look generally suitable for normal "
            "outdoor activities. Still check the latest weather "
            "before leaving."
        )

    if (
        code in storm_codes
        or rain > 5
    ):

        level = "danger"

        title = (
            "⚠️ Be careful before going outside"
        )

    elif (
        code in rainy_codes
        or rain > 0
        or showers > 0
    ):

        level = "warning"

        title = (
            "🌧️ Rain-related precautions"
        )

    elif (
        temp is not None
        and temp >= 33
    ):

        level = "warning"

        title = (
            "☀️ Hot-weather precautions"
        )

    else:

        level = "success"

        title = (
            "✅ Outdoor activity advice"
        )

    return {
        "level": level,
        "title": title,
        "items": advice
    }


# ============================================================
# ROUTING
# ============================================================

def get_routes(
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    url = (
        f"{OSRM_ROUTE}/{coordinates}"
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
# ROUTE WEATHER ANALYSIS
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

        place_name = (
            f"Route Point {i + 1}"
        )

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

        results.append(
            {
                "name": place_name,
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "weather": weather
            }
        )

        time.sleep(0.05)

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
                "Weather information is unavailable for this route."
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

        showers = weather.get(
            "showers",
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

        elif (
            code in {
                51, 53, 55,
                61, 63,
                66, 80, 81
            }
            or rain > 0
            or showers > 0
        ):

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
    route_risk
):

    advice = []

    start_temp = (
        start_weather.get(
            "temperature"
        )
        if start_weather
        else None
    )

    destination_temp = (
        destination_weather.get(
            "temperature"
        )
        if destination_weather
        else None
    )

    if start_temp is not None:

        if start_temp >= 33:

            advice.append(
                "☀️ Your starting location is hot. "
                "Use sunscreen, sunglasses and carry water."
            )

        if (
            start_weather.get(
                "rain",
                0
            ) or 0
        ) > 0:

            advice.append(
                "☔ Rain is currently possible at your "
                "starting location. Carry an umbrella/raincoat."
            )

    if destination_temp is not None:

        if destination_temp >= 33:

            advice.append(
                "🌡️ The destination is also warm/hot. "
                "Prepare for heat after reaching there."
            )

        if (
            destination_weather.get(
                "rain",
                0
            ) or 0
        ) > 0:

            advice.append(
                "☔ Rain is possible at the destination. "
                "Keep rain protection with you."
            )

    if route_risk["level"] == "high":

        advice.append(
            "⚠️ The selected route contains significant "
            "weather risks. Consider delaying the journey "
            "or checking another available route."
        )

    elif route_risk["level"] == "medium":

        advice.append(
            "⚠️ Weather conditions change along this route. "
            "Travel is possible, but extra caution is recommended."
        )

    else:

        advice.append(
            "✅ No major weather-related issue was detected "
            "along the sampled route points."
        )

    if route_risk["problems"]:

        advice.append(
            "🗺️ The route has different weather conditions "
            "at different points, so do not judge the entire "
            "journey only from the start and destination weather."
        )

    if route["distance_km"] <= 50:

        advice.append(
            "🚗 This is a relatively short journey. "
            "Check the live weather again before leaving."
        )

    else:

        advice.append(
            "🛣️ This is a longer journey. Weather can change "
            "during the trip, so keep checking conditions."
        )

    return advice


# ============================================================
# START LOCATION MAP
# ============================================================

def create_start_location_map(
    current_location=None
):

    # Default map location
    # India center

    if current_location:

        center_lat = current_location[
            "latitude"
        ]

        center_lon = current_location[
            "longitude"
        ]

        zoom = 10

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

    # Current/start marker

    if current_location:

        popup_text = (
            f"<b>📍 Start Location</b><br>"
            f"{current_location.get('name', 'Selected Location')}<br>"
            f"{current_location.get('state', '')}<br>"
            f"{current_location.get('country', '')}"
        )

        folium.Marker(
            [
                current_location[
                    "latitude"
                ],
                current_location[
                    "longitude"
                ]
            ],
            tooltip="📍 Start Location",
            popup=folium.Popup(
                popup_text,
                max_width=300
            ),
            icon=folium.Icon(
                color="blue",
                icon="home"
            )
        ).add_to(m)

    # Instruction

    folium.Marker(
        [
            center_lat,
            center_lon
        ],
        tooltip="Click anywhere on the map to select your start location",
        icon=folium.DivIcon(
            html="""
            <div style="
                font-size: 0px;
            ">
            </div>
            """
        )
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

        route_id = route["id"]

        selected = (
            route_id == selected_route_id
        )

        line_weight = (
            7 if selected else 4
        )

        line_opacity = (
            0.95 if selected else 0.45
        )

        folium.PolyLine(
            [
                [lat, lon]
                for lon, lat
                in route["geometry"]
            ],
            weight=line_weight,
            opacity=line_opacity,
            tooltip=(
                f"Route {route_id} | "
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
                radius=6,
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

    description = weather[
        "description"
    ]

    icon = weather[
        "icon"
    ]

    st.markdown(
        f"""
        <div class="weather-card">

        <h2>{title}</h2>

        <h1>
            {icon}
            {weather['temperature']} °C
        </h1>

        <h3>{description}</h3>

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
# APP HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🌦️ Weather Travel Agent'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Check your current weather, choose locations on the map, '
    'plan routes and get practical travel advice.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# START LOCATION
# ============================================================

st.header(
    "📍 Select Your Start Location"
)

st.write(
    "You can either use your device location "
    "or click anywhere on the map."
)


# ============================================================
# CURRENT LOCATION BUTTON
# ============================================================

location_col1, location_col2 = st.columns(
    [1, 3]
)

with location_col1:

    get_location_button = st.button(
        "📍 Get My Current Location",
        type="primary",
        use_container_width=True
    )


# ============================================================
# GET DEVICE LOCATION
# ============================================================

if get_location_button:

    st.session_state.location_requested = True

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
                    "Please allow location access in your browser "
                    "and click the button again."
                )

            else:

                st.error(
                    "Location error: "
                    f"{error.get('message', 'Unknown error')}"
                )

        else:

            current_location = create_start_location(
                location["latitude"],
                location["longitude"]
            )

            st.session_state.current_location = (
                current_location
            )

            st.session_state.current_weather = (
                get_point_weather(
                    current_location["latitude"],
                    current_location["longitude"]
                )
            )

            # Reset route information

            st.session_state.routes = []

            st.session_state.selected_route = None

            st.session_state.route_weather = []

            st.session_state.last_route_key = None

            st.rerun()

    else:

        st.info(
            "The browser is waiting for location permission. "
            "Please allow location access and click the button again."
        )


# ============================================================
# INTERACTIVE START LOCATION MAP
# ============================================================

st.subheader(
    "🗺️ Choose Start Location on Map"
)

st.caption(
    "👉 Click anywhere on the map to select that location as your start point."
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
    key="start_location_map"
)


# ============================================================
# HANDLE MAP CLICK
# ============================================================

if map_result:

    clicked = map_result.get(
        "last_clicked"
    )

    if clicked:

        clicked_lat = clicked.get(
            "lat"
        )

        clicked_lon = clicked.get(
            "lng"
        )

        if (
            clicked_lat is not None
            and clicked_lon is not None
        ):

            clicked_key = (
                round(clicked_lat, 6),
                round(clicked_lon, 6)
            )

            if (
                st.session_state.map_last_clicked
                != clicked_key
            ):

                st.session_state.map_last_clicked = (
                    clicked_key
                )

                with st.spinner(
                    "Getting weather for selected location..."
                ):

                    selected_location = create_start_location(
                        clicked_lat,
                        clicked_lon
                    )

                    selected_weather = get_point_weather(
                        clicked_lat,
                        clicked_lon
                    )

                st.session_state.current_location = (
                    selected_location
                )

                st.session_state.current_weather = (
                    selected_weather
                )

                # Reset route data

                st.session_state.routes = []

                st.session_state.selected_route = None

                st.session_state.route_weather = []

                st.session_state.last_route_key = None

                st.rerun()


# ============================================================
# SHOW SELECTED START LOCATION
# ============================================================

current_location = (
    st.session_state.current_location
)

current_weather = (
    st.session_state.current_weather
)


if current_location:

    st.success(
        "📍 Start location selected: "
        f"**{current_location.get('name', 'Selected Location')}**"
    )

    st.caption(
        f"Latitude: {current_location['latitude']:.6f} | "
        f"Longitude: {current_location['longitude']:.6f}"
    )


# ============================================================
# CURRENT WEATHER
# ============================================================

if (
    current_location
    and current_weather
):

    st.divider()

    location_name = current_location.get(
        "name",
        "Current Location"
    )

    display_weather_card(
        "🌍 Current Weather",
        current_weather,
        location_name
    )

    current_advice = generate_daily_advice(
        current_weather
    )

    if current_advice["level"] == "danger":

        st.markdown(
            '<div class="danger-card">',
            unsafe_allow_html=True
        )

    elif current_advice["level"] == "warning":

        st.markdown(
            '<div class="warning-card">',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<div class="success-card">',
            unsafe_allow_html=True
        )

    st.subheader(
        current_advice["title"]
    )

    for item in current_advice["items"]:

        st.write(item)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

else:

    st.info(
        "📍 Select a location from the map or click "
        "**Get My Current Location**."
    )


# ============================================================
# DESTINATION
# ============================================================

st.divider()

st.header(
    "🎯 Plan Your Journey"
)

destination_input = st.text_input(
    "Enter your destination",
    placeholder="Example: Vijayawada"
)

search_destination = st.button(
    "🔎 Find Destination"
)


# ============================================================
# SEARCH DESTINATION
# ============================================================

if search_destination:

    if not destination_input.strip():

        st.warning(
            "Please enter a destination."
        )

    else:

        results = geocode_place(
            destination_input.strip()
        )

        if not results:

            st.error(
                "Destination not found. "
                "Try another city or place name."
            )

        else:

            st.session_state.destination_results = (
                results
            )


# ============================================================
# DESTINATION SELECTION
# ============================================================

destination_results = (
    st.session_state.destination_results
)


if destination_results:

    options = []

    for item in destination_results:

        label = (
            f"{item['name']}, "
            f"{item['state']}, "
            f"{item['country']}"
        )

        options.append(
            label
        )

    selected_destination_label = st.selectbox(
        "Select the correct destination",
        options
    )

    selected_index = options.index(
        selected_destination_label
    )

    selected_destination = (
        destination_results[
            selected_index
        ]
    )

    if st.button(
        "🎯 Set Destination",
        type="primary"
    ):

        st.session_state.destination = (
            selected_destination
        )

        st.session_state.routes = []

        st.session_state.selected_route = None

        st.session_state.route_weather = []

        st.session_state.last_route_key = None

        st.rerun()


# ============================================================
# DESTINATION WEATHER
# ============================================================

destination = (
    st.session_state.destination
)


if (
    destination
    and current_location
):

    st.divider()

    st.subheader(
        f"🎯 Destination: {destination['name']}"
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
            f"{destination.get('state', '')}, "
            f"{destination.get('country', '')}"
        )
    )

    destination_advice = generate_daily_advice(
        destination_weather
    )

    st.markdown(
        '<div class="advice-card">',
        unsafe_allow_html=True
    )

    st.subheader(
        "🧠 Destination Advice"
    )

    for item in destination_advice["items"]:

        st.write(item)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # ========================================================
    # ROUTES
    # ========================================================

    st.divider()

    st.header(
        "🗺️ Possible Routes"
    )

    if st.button(
        "🚗 Find Available Routes",
        type="primary"
    ):

        with st.spinner(
            "Finding possible routes..."
        ):

            routes = get_routes(
                current_location[
                    "latitude"
                ],
                current_location[
                    "longitude"
                ],
                destination[
                    "latitude"
                ],
                destination[
                    "longitude"
                ]
            )

        if not routes:

            st.error(
                "No route was found for this journey."
            )

        else:

            st.session_state.routes = (
                routes
            )

            st.session_state.selected_route = (
                None
            )

            st.session_state.route_weather = (
                []
            )

            st.session_state.last_route_key = (
                None
            )

            st.rerun()


# ============================================================
# ROUTE LIST
# ============================================================

routes = (
    st.session_state.routes
)


if routes:

    st.subheader(
        f"🛣️ {len(routes)} route option(s) found"
    )

    st.caption(
        "Routes are shown with the shorter-distance route first. "
        "Alternative routes depend on the routing service."
    )

    route_labels = []

    for route in routes:

        route_labels.append(
            f"Route {route['id']} — "
            f"{route['distance_km']:.1f} km — "
            f"{route['duration_min']:.0f} min"
        )

    selected_route_label = st.radio(
        "Which route do you want to analyse?",
        route_labels,
        index=0
    )

    selected_route_index = (
        route_labels.index(
            selected_route_label
        )
    )

    selected_route = routes[
        selected_route_index
    ]

    st.session_state.selected_route = (
        selected_route
    )

    # ========================================================
    # SELECTED ROUTE
    # ========================================================

    st.markdown(
        f"""
        <div class="route-card">

        <h2>🛣️ Route {selected_route['id']}</h2>

        <p>
        📏 Distance:
        <b>{selected_route['distance_km']:.1f} km</b>
        </p>

        <p>
        ⏱️ Estimated travel time:
        <b>{selected_route['duration_min']:.0f} minutes</b>
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    analyze_button = st.button(
        "🌦️ Analyze Weather Along This Route",
        type="primary"
    )

    route_key = (
        f"{selected_route['id']}_"
        f"{selected_route['distance_km']:.2f}"
    )

    if analyze_button:

        with st.spinner(
            "Checking weather at multiple points along the selected route..."
        ):

            route_weather = analyze_route_weather(
                selected_route,
                current_location,
                destination
            )

        st.session_state.route_weather = (
            route_weather
        )

        st.session_state.last_route_key = (
            route_key
        )

        st.rerun()


# ============================================================
# ROUTE WEATHER RESULT
# ============================================================

selected_route = (
    st.session_state.selected_route
)

route_weather = (
    st.session_state.route_weather
)


if (
    selected_route
    and route_weather
    and st.session_state.last_route_key
):

    st.divider()

    st.header(
        "🌦️ Weather Along Selected Route"
    )

    risk = route_risk_analysis(
        route_weather
    )

    # ========================================================
    # RISK SUMMARY
    # ========================================================

    if risk["level"] == "high":

        st.markdown(
            '<div class="danger-card">',
            unsafe_allow_html=True
        )

        st.subheader(
            "⚠️ Significant weather risk detected"
        )

    elif risk["level"] == "medium":

        st.markdown(
            '<div class="warning-card">',
            unsafe_allow_html=True
        )

        st.subheader(
            "⚠️ Weather changes detected along the route"
        )

    else:

        st.markdown(
            '<div class="success-card">',
            unsafe_allow_html=True
        )

        st.subheader(
            "✅ No major weather risk detected"
        )

    if risk["problems"]:

        for problem in risk["problems"]:

            st.write(
                f"• {problem}"
            )

    else:

        st.write(
            "Weather conditions look generally stable "
            "along the sampled route points."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # ========================================================
    # ROUTE POINT WEATHER
    # ========================================================

    st.subheader(
        "📍 Weather at Journey Points"
    )

    for point in route_weather:

        weather = point["weather"]

        with st.expander(
            f"{weather['icon']} "
            f"{point['name']} — "
            f"{weather['temperature']} °C — "
            f"{weather['description']}"
        ):

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Temperature",
                    f"{weather['temperature']} °C"
                )

            with c2:

                st.metric(
                    "Rain",
                    f"{weather['rain']} mm"
                )

            with c3:

                st.metric(
                    "Wind",
                    f"{weather['wind_speed']} km/h"
                )

            with c4:

                st.metric(
                    "Humidity",
                    f"{weather['humidity']} %"
                )

    # ========================================================
    # TRAVEL ADVICE
    # ========================================================

    st.divider()

    st.header(
        "🤖 Smart Travel Advice"
    )

    start_weather = (
        current_weather
    )

    destination_weather = get_point_weather(
        destination["latitude"],
        destination["longitude"]
    )

    travel_advice = generate_travel_advice(
        start_weather,
        destination_weather,
        route_weather,
        selected_route,
        risk
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

    # ========================================================
    # ROUTE MAP
    # ========================================================

    st.divider()

    st.header(
        "🗺️ Selected Route + Weather Points"
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
        key="route_analysis_map"
    )


# ============================================================
# ROUTE CHANGE MESSAGE
# ============================================================

if routes and selected_route:

    st.divider()

    st.info(
        "🔄 Select another route above and click "
        "**Analyze Weather Along This Route** again. "
        "The agent will analyse that route separately."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌦️ Weather Travel Agent | "
    "Current location, interactive map, destination weather, "
    "route analysis and practical travel assistance."
)