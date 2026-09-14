import streamlit as st
import requests
import folium
import math
from datetime import datetime, timedelta
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval


# ============================================================
# AI PERSONAL WEATHER ADVISOR
# Weather + GPS + Worldwide Search + Route Weather
# ============================================================

st.set_page_config(
    page_title="AI Personal Weather Advisor",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CONFIGURATION
# ============================================================

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

DEFAULT_LAT = 16.3067
DEFAULT_LON = 80.4365
DEFAULT_CITY = "Guntur, India"

REQUEST_TIMEOUT = 20
ROUTE_POINTS = 8


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #ffffff;
    }

    .main {
        padding-top: 1rem;
    }

    h1, h2, h3 {
        color: #183b56;
    }

    .top-title {
        text-align: center;
        font-size: 18px;
        margin-bottom: 25px;
        color: #557083;
    }

    .section-title {
        font-size: 30px;
        font-weight: 700;
        color: #183b56;
        margin-top: 28px;
        margin-bottom: 15px;
    }

    .weather-card {
        padding: 28px;
        border-radius: 22px;
        background: linear-gradient(
            135deg,
            #2374ab,
            #4c9ed0
        );
        color: white;
        margin: 20px 0;
        box-shadow: 0 6px 24px rgba(0,0,0,0.10);
    }

    .weather-card h1,
    .weather-card h2,
    .weather-card h3,
    .weather-card p,
    .weather-card div {
        color: white !important;
    }

    .weather-icon {
        font-size: 55px;
    }

    .big-temp {
        font-size: 62px;
        font-weight: 700;
        line-height: 1;
        margin-top: 8px;
    }

    .condition {
        font-size: 25px;
        font-weight: 600;
        margin-top: 10px;
    }

    .metric-box {
        padding: 18px 12px;
        border-radius: 16px;
        border: 1px solid #dce7ee;
        background: #f8fbfd;
        text-align: center;
        min-height: 115px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }

    .metric-value {
        font-size: 25px;
        font-weight: 700;
        color: #183b56;
    }

    .metric-label {
        font-size: 14px;
        color: #66808f;
        margin-top: 5px;
    }

    .good-box {
        padding: 18px;
        border-radius: 15px;
        background: #eaf8ef;
        border-left: 6px solid #28a745;
        margin: 10px 0;
    }

    .warning-box {
        padding: 18px;
        border-radius: 15px;
        background: #fff8e6;
        border-left: 6px solid #f0ad00;
        margin: 10px 0;
    }

    .danger-box {
        padding: 18px;
        border-radius: 15px;
        background: #fff0f0;
        border-left: 6px solid #dc3545;
        margin: 10px 0;
    }

    .route-header {
        padding: 24px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #173f5f,
            #287da8
        );
        color: white;
        margin: 20px 0;
    }

    .route-header h2,
    .route-header p,
    .route-header div {
        color: white !important;
    }

    .route-stat {
        text-align: center;
        padding: 10px;
    }

    .route-stat-value {
        font-size: 28px;
        font-weight: 700;
    }

    .route-stat-label {
        font-size: 14px;
    }

    .info-box {
        padding: 18px;
        border-radius: 15px;
        background: #f4f9fc;
        border: 1px solid #dbeaf2;
        margin: 10px 0;
    }

    .notification-box {
        padding: 20px;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            #f4f9fc,
            #eef7fb
        );
        border: 1px solid #d6e7ef;
        margin: 15px 0;
    }

    .notification-title {
        font-size: 22px;
        font-weight: 700;
        color: #183b56;
    }

    .small-text {
        color: #718692;
        font-size: 13px;
    }

    .stat-highlight {
        font-size: 32px;
        font-weight: 700;
        color: #183b56;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "latitude": DEFAULT_LAT,
    "longitude": DEFAULT_LON,
    "location_name": DEFAULT_CITY,
    "location_source": "default",

    "route_data": None,
    "route_weather": None,

    "destination_name": "",
    "destination_lat": None,
    "destination_lon": None,

    "notifications_enabled": False,
    "notification_permission": "default",
    "last_notification_key": "",

    "gps_request_id": 0,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# WEATHER DESCRIPTIONS
# ============================================================

def weather_description(code):

    descriptions = {

        0: "Clear sky",

        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing rime fog",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",

        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",

        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",

        66: "Light freezing rain",
        67: "Heavy freezing rain",

        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",

        77: "Snow grains",

        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",

        85: "Slight snow showers",
        86: "Heavy snow showers",

        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return descriptions.get(
        int(code) if code is not None else 0,
        "Unknown weather"
    )


# ============================================================
# WEATHER ICON
# ============================================================

def weather_icon(code):

    try:
        code = int(code)
    except Exception:
        code = 0

    if code == 0:
        return "☀️"

    if code in [1, 2]:
        return "🌤️"

    if code == 3:
        return "☁️"

    if code in [45, 48]:
        return "🌫️"

    if code in [51, 53, 55, 56, 57]:
        return "🌦️"

    if code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "🌧️"

    if code in [71, 73, 75, 77, 85, 86]:
        return "❄️"

    if code in [95, 96, 99]:
        return "⛈️"

    return "🌦️"


# ============================================================
# TIME HELPERS
# ============================================================

def parse_datetime(value):

    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def format_time(value):

    dt = parse_datetime(value)

    if dt is None:
        return str(value)

    return dt.strftime("%I:%M %p")


def format_duration(seconds):

    try:
        seconds = int(seconds)
    except Exception:
        return "Unknown"

    minutes = max(0, round(seconds / 60))

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours:

        if remaining_minutes:
            return f"{hours} hr {remaining_minutes} min"

        return f"{hours} hr"

    return f"{remaining_minutes} min"


# ============================================================
# WEATHER RISK
# ============================================================

def calculate_risk(
    temperature,
    feels_like,
    rain_probability,
    wind,
    uv,
    weather_code
):

    try:
        weather_code = int(weather_code)
    except Exception:
        weather_code = 0

    if weather_code in [95, 96, 99]:

        return "🔴 High Risk"

    if temperature >= 40 or feels_like >= 42:

        return "🔴 High Risk"

    if rain_probability >= 85:

        return "🔴 High Risk"

    if wind >= 50:

        return "🔴 High Risk"

    if temperature >= 35:

        return "🟡 Caution"

    if feels_like >= 38:

        return "🟡 Caution"

    if rain_probability >= 60:

        return "🟡 Caution"

    if wind >= 30:

        return "🟡 Caution"

    if uv >= 8:

        return "🟡 Caution"

    if rain_probability >= 30:

        return "🟡 Caution"

    return "🟢 Good"


# ============================================================
# WEATHER ALERT
# ============================================================

def get_weather_alert(
    temperature,
    feels_like,
    rain_probability,
    wind,
    uv,
    weather_code
):

    if weather_code in [95, 96, 99]:

        return {
            "level": "danger",
            "title": "⛈️ Thunderstorm Warning",
            "message":
                "Thunderstorm conditions are possible. "
                "Avoid unnecessary outdoor activity.",
        }

    if temperature >= 40 or feels_like >= 42:

        return {
            "level": "danger",
            "title": "🔥 Extreme Heat Warning",
            "message":
                "Very hot conditions detected. "
                "Drink plenty of water and avoid "
                "long outdoor exposure.",
        }

    if rain_probability >= 85:

        return {
            "level": "danger",
            "title": "🌧️ Heavy Rain Warning",
            "message":
                "There is a very high chance of rain. "
                "Carry rain protection and take care outdoors.",
        }

    if wind >= 50:

        return {
            "level": "danger",
            "title": "💨 Strong Wind Warning",
            "message":
                "Strong winds are expected. "
                "Take care during outdoor activities and travel.",
        }

    if uv >= 9:

        return {
            "level": "warning",
            "title": "☀️ Very High UV Warning",
            "message":
                "UV levels are very high. "
                "Use sunscreen and avoid prolonged direct sunlight.",
        }

    if temperature >= 35 or feels_like >= 38:

        return {
            "level": "warning",
            "title": "🌡️ Heat Warning",
            "message":
                "It is hot outside. Carry water and "
                "avoid peak afternoon heat.",
        }

    if rain_probability >= 70:

        return {
            "level": "warning",
            "title": "🌧️ Rain Warning",
            "message":
                "Rain is likely soon. "
                "Carry an umbrella or raincoat.",
        }

    if wind >= 30:

        return {
            "level": "warning",
            "title": "💨 Wind Warning",
            "message":
                "Strong winds are possible. Take care outdoors.",
        }

    if uv >= 8:

        return {
            "level": "warning",
            "title": "☀️ High UV Warning",
            "message":
                "UV levels are high. Use sunscreen and "
                "protect your skin.",
        }

    return {
        "level": "normal",
        "title": "🌤️ Weather Update",
        "message":
            "Current weather conditions are generally comfortable.",
    }


# ============================================================
# BROWSER NOTIFICATION
# ============================================================

def send_browser_notification(
    title,
    message,
    notification_context=""
):

    key = (
        f"{notification_context}|"
        f"{title}|"
        f"{message}"
    )

    if st.session_state.last_notification_key == key:
        return

    st.session_state.last_notification_key = key

    js_code = f"""
    (async function() {{

        try {{

            if (!("Notification" in window)) {{
                return {{
                    status: "unsupported"
                }};
            }}

            let permission = Notification.permission;

            if (permission === "default") {{

                permission =
                    await Notification.requestPermission();

            }}

            if (permission === "granted") {{

                new Notification(
                    {title!r},
                    {{
                        body: {message!r},
                        tag: "weather-agent-alert"
                    }}
                );

                return {{
                    status: "sent"
                }};

            }}

            return {{
                status: permission
            }};

        }} catch (error) {{

            return {{
                status: "error",
                message: String(error)
            }};

        }}

    }})()
    """

    try:

        result = streamlit_js_eval(
            js_expressions=js_code,
            want_output=True,
            key=f"notification_{abs(hash(key))}"
        )

        if isinstance(result, dict):

            st.session_state.notification_permission = (
                result.get("status", "unknown")
            )

    except Exception:
        pass


# ============================================================
# OPEN-METEO WEATHER
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_weather(latitude, longitude):

    params = {

        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
            "uv_index",
        ]),

        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
            "relative_humidity_2m",
            "uv_index",
        ]),

        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "precipitation_probability_max",
            "precipitation_sum",
            "uv_index_max",
            "wind_speed_10m_max",
            "sunrise",
            "sunset",
        ]),

        "timezone": "auto",
        "forecast_days": 7,
    }

    try:

        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        if "current" not in data:
            return None

        return data

    except requests.RequestException:
        return None

    except Exception:
        return None


# ============================================================
# WORLDWIDE LOCATION SEARCH
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def search_location(city):

    city = str(city).strip()

    if not city:
        return None

    queries = list(dict.fromkeys([
        city,
        city.title(),
        city.replace(",", " ").strip(),
    ]))

    for query in queries:

        params = {
            "name": query,
            "count": 10,
            "language": "en",
            "format": "json",
        }

        try:

            response = requests.get(
                GEOCODING_URL,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            results = response.json().get(
                "results",
                []
            )

            if not results:
                continue

            query_lower = query.lower()

            # Exact city name
            for result in results:

                result_name = str(
                    result.get("name", "")
                ).lower()

                if result_name == query_lower:

                    return (
                        result.get("latitude"),
                        result.get("longitude"),
                        result.get("name", query),
                        result.get("country", ""),
                    )

            # Partial match
            for result in results:

                result_name = str(
                    result.get("name", "")
                ).lower()

                if (
                    query_lower in result_name
                    or result_name in query_lower
                ):

                    return (
                        result.get("latitude"),
                        result.get("longitude"),
                        result.get("name", query),
                        result.get("country", ""),
                    )

            # First valid result
            for result in results:

                if (
                    result.get("latitude") is not None
                    and result.get("longitude") is not None
                ):

                    return (
                        result.get("latitude"),
                        result.get("longitude"),
                        result.get("name", query),
                        result.get("country", ""),
                    )

        except Exception:
            continue

    return None


# ============================================================
# OSRM ROAD ROUTE
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    url = (
        f"{OSRM_URL}/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        routes = data.get(
            "routes",
            []
        )

        if not routes:
            return None

        route = routes[0]

        return {
            "distance_m":
                float(route.get("distance", 0)),

            "duration_s":
                float(route.get("duration", 0)),

            "geometry":
                route.get("geometry", {}),

            "legs":
                route.get("legs", []),

            "weight_name":
                route.get("weight_name", ""),
        }

    except Exception:
        return None


# ============================================================
# HAVERSINE
# ============================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    radius = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        +
        math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# ============================================================
# ROUTE POINT SAMPLING
# ============================================================

def sample_route_points(
    coordinates,
    number_of_points=ROUTE_POINTS
):

    if not coordinates:
        return []

    total = len(coordinates)

    if total <= number_of_points:

        return [
            {
                "index": i,
                "latitude": coordinate[1],
                "longitude": coordinate[0],
            }
            for i, coordinate in enumerate(coordinates)
        ]

    points = []

    step = (total - 1) / (
        number_of_points - 1
    )

    used_indices = set()

    for i in range(number_of_points):

        position = round(i * step)

        if position in used_indices:
            continue

        used_indices.add(position)

        coordinate = coordinates[position]

        points.append({
            "index": i,
            "latitude": coordinate[1],
            "longitude": coordinate[0],
        })

    return points


# ============================================================
# REVERSE GEOCODING
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def reverse_geocode_route(
    latitude,
    longitude
):

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent":
            "AI-Personal-Weather-Advisor/1.0"
    }

    try:

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        address = data.get(
            "address",
            {}
        )

        place = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("suburb")
            or address.get("county")
        )

        if place:
            return place

        display_name = data.get(
            "display_name",
            ""
        )

        if display_name:
            return display_name.split(",")[0]

    except Exception:
        pass

    return "Route Point"


# ============================================================
# BUILD ROUTE LOCATIONS
# ============================================================

def build_route_locations(
    route,
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    geometry = route.get(
        "geometry",
        {}
    )

    coordinates = geometry.get(
        "coordinates",
        []
    )

    if not coordinates:
        return []

    points = sample_route_points(
        coordinates,
        ROUTE_POINTS
    )

    total_distance = (
        route["distance_m"] / 1000
    )

    route_locations = []

    for i, point in enumerate(points):

        lat = point["latitude"]
        lon = point["longitude"]

        if i == 0:

            place = "Starting Location"
            distance = 0.0

        elif i == len(points) - 1:

            place = "Destination"
            distance = total_distance

        else:

            place = reverse_geocode_route(
                lat,
                lon
            )

            # Approximate distance from origin.
            distance = haversine_distance(
                start_lat,
                start_lon,
                lat,
                lon
            )

            # Prevent an occasional geocoding/routing
            # coordinate from producing a value larger
            # than the route itself.
            distance = min(
                distance,
                total_distance
            )

        route_locations.append({
            "place": place,
            "latitude": lat,
            "longitude": lon,
            "distance_km": distance,
        })

    # Remove consecutive duplicate names
    cleaned = []

    for item in route_locations:

        if cleaned:

            if (
                cleaned[-1]["place"].lower()
                ==
                item["place"].lower()
            ):
                continue

        cleaned.append(item)

    return cleaned


# ============================================================
# NEAREST HOURLY FORECAST
# ============================================================

def find_nearest_hour(
    hourly_times,
    target_datetime
):

    if not hourly_times:
        return 0

    best_index = 0
    best_difference = None

    for i, value in enumerate(hourly_times):

        current_time = parse_datetime(value)

        if current_time is None:
            continue

        difference = abs(
            (
                current_time -
                target_datetime
            ).total_seconds()
        )

        if (
            best_difference is None
            or
            difference < best_difference
        ):

            best_difference = difference
            best_index = i

    return best_index


# ============================================================
# ROUTE WEATHER
# ============================================================

def get_route_weather(
    route_locations,
    route_duration_seconds
):

    if not route_locations:
        return []

    # We use the weather API's timezone-aware
    # current timestamp where possible.
    first_weather = get_weather(
        route_locations[0]["latitude"],
        route_locations[0]["longitude"]
    )

    if first_weather:

        current_time_string = (
            first_weather
            .get("current", {})
            .get("time")
        )

        start_time = parse_datetime(
            current_time_string
        )

    else:

        start_time = None

    if start_time is None:
        start_time = datetime.now()

    total_distance = route_locations[-1][
        "distance_km"
    ]

    if total_distance <= 0:
        total_distance = 1

    results = []

    for location in route_locations:

        progress = (
            location["distance_km"]
            / total_distance
        )

        progress = max(
            0,
            min(1, progress)
        )

        estimated_seconds = (
            route_duration_seconds
            * progress
        )

        estimated_time = (
            start_time
            + timedelta(
                seconds=estimated_seconds
            )
        )

        weather = get_weather(
            location["latitude"],
            location["longitude"]
        )

        if weather is None:
            continue

        hourly = weather.get(
            "hourly",
            {}
        )

        current = weather.get(
            "current",
            {}
        )

        hourly_times = hourly.get(
            "time",
            []
        )

        hour_index = find_nearest_hour(
            hourly_times,
            estimated_time
        )

        def hourly_value(
            key,
            fallback=0
        ):

            values = hourly.get(
                key,
                []
            )

            if (
                values
                and
                hour_index < len(values)
            ):

                return values[hour_index]

            return fallback

        temperature = hourly_value(
            "temperature_2m",
            current.get(
                "temperature_2m",
                0
            )
        )

        feels_like = hourly_value(
            "apparent_temperature",
            current.get(
                "apparent_temperature",
                0
            )
        )

        rain_probability = hourly_value(
            "precipitation_probability",
            0
        )

        precipitation = hourly_value(
            "precipitation",
            0
        )

        rain = hourly_value(
            "rain",
            0
        )

        wind = hourly_value(
            "wind_speed_10m",
            current.get(
                "wind_speed_10m",
                0
            )
        )

        humidity = hourly_value(
            "relative_humidity_2m",
            current.get(
                "relative_humidity_2m",
                0
            )
        )

        uv = hourly_value(
            "uv_index",
            current.get(
                "uv_index",
                0
            )
        )

        code = hourly_value(
            "weather_code",
            current.get(
                "weather_code",
                0
            )
        )

        risk = calculate_risk(
            temperature,
            feels_like,
            rain_probability,
            wind,
            uv,
            code
        )

        results.append({

            **location,

            "estimated_time":
                estimated_time,

            "temperature":
                float(temperature or 0),

            "feels_like":
                float(feels_like or 0),

            "rain_probability":
                float(rain_probability or 0),

            "precipitation":
                float(precipitation or 0),

            "rain":
                float(rain or 0),

            "wind":
                float(wind or 0),

            "humidity":
                float(humidity or 0),

            "uv":
                float(uv or 0),

            "weather_code":
                int(code or 0),

            "condition":
                weather_description(code),

            "icon":
                weather_icon(code),

            "risk":
                risk,
        })

    return results


# ============================================================
# ROUTE ANALYSIS
# ============================================================

def analyze_route_weather(
    route_weather
):

    if not route_weather:

        return {
            "risk": "⚪ Unknown",
            "message":
                "Route weather data is unavailable.",
            "advice": [
                "Check the route again before travelling."
            ],
        }

    high_risk = [
        p for p in route_weather
        if "🔴" in p["risk"]
    ]

    caution = [
        p for p in route_weather
        if "🟡" in p["risk"]
    ]

    if high_risk:

        worst = max(
            high_risk,
            key=lambda p: (
                p["rain_probability"],
                p["wind"],
                p["temperature"]
            )
        )

        advice = [
            f"Be especially careful near {worst['place']}.",
            (
                f"Forecast there: "
                f"{worst['condition']}, "
                f"rain {worst['rain_probability']:.0f}%, "
                f"wind {worst['wind']:.0f} km/h."
            ),
            "Check the forecast immediately before departure.",
            "Consider delaying the journey if severe conditions develop.",
        ]

        return {
            "risk": "🔴 High Risk",
            "message":
                "Weather conditions may become unsafe "
                "during part of your journey.",
            "advice": advice,
        }

    if caution:

        worst = max(
            caution,
            key=lambda p: (
                p["rain_probability"],
                p["wind"],
                p["uv"]
            )
        )

        return {
            "risk": "🟡 Moderate Risk",
            "message":
                "Most of the route looks manageable, "
                "but some sections need extra caution.",
            "advice": [
                f"Take extra care around {worst['place']}.",
                "Carry water.",
                "Keep rain protection available.",
                "Allow some extra travel time.",
            ],
        }

    return {
        "risk": "🟢 Good",
        "message":
            "Weather conditions look generally "
            "favorable across the route.",
        "advice": [
            "Carry drinking water.",
            "Use sunscreen during daytime.",
            "Wear comfortable clothing.",
            "Check the weather again before departure.",
        ],
    }


# ============================================================
# ACTIVITY ADVISOR
# ============================================================

def activity_advice(
    activity,
    temp,
    rain_chance,
    wind_speed,
    uv
):

    if temp >= 40:

        return (
            "🔥 Extreme heat. Avoid prolonged outdoor "
            "exposure and stay hydrated."
        )

    if rain_chance >= 70:

        return (
            "🌧️ Rain is likely. Carry an umbrella "
            "or raincoat."
        )

    if temp >= 35:

        return (
            "☀️ Hot conditions. Carry water and "
            "avoid peak afternoon heat."
        )

    if wind_speed >= 35:

        return (
            "💨 Strong wind. Take extra care outdoors."
        )

    if uv >= 8:

        return (
            "☀️ High UV. Use sunscreen and protect "
            "your skin."
        )

    if activity == "Running":

        return (
            "🏃 Conditions look reasonably suitable "
            "for running. Stay hydrated."
        )

    if activity == "Walking":

        return (
            "🚶 Conditions look good for walking."
        )

    if activity == "Playing sports":

        return (
            "🏏 Outdoor sports look manageable. "
            "Keep water with you."
        )

    if activity == "Travelling":

        return (
            "🚗 Travel conditions look generally good."
        )

    if activity == "Outdoor event":

        return (
            "🎪 Outdoor conditions look manageable. "
            "Check rain chances again before the event."
        )

    return (
        "🟢 Conditions are generally comfortable "
        "for outdoor activity."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <h1 style="text-align:center;">
        🌦️ AI Personal Weather Advisor
    </h1>

    <div class="top-title">
        Weather intelligence + personal outdoor advice
        + route weather analysis
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NOTIFICATIONS
# ============================================================

st.markdown(
    '<div class="section-title">🔔 Weather Notifications</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="notification-box">

        <div class="notification-title">
            📱 Device Weather Alerts
        </div>

        <p>
            Receive browser alerts when important weather
            conditions are detected.
        </p>

        <p class="small-text">
            Notifications depend on browser and operating-system
            permission settings.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

notification_col1, notification_col2 = st.columns(2)

with notification_col1:

    enable_notifications = st.checkbox(
        "🔔 Enable weather notifications",
        value=st.session_state.notifications_enabled,
        key="notification_checkbox"
    )

with notification_col2:

    test_notification = st.button(
        "🧪 Test Notification",
        use_container_width=True
    )

st.session_state.notifications_enabled = (
    enable_notifications
)

if test_notification:

    if enable_notifications:

        send_browser_notification(
            "🌦️ Weather Agent Test",
            (
                "Notifications are working. "
                "You can now receive weather alerts."
            ),
            "test"
        )

        st.success(
            "🔔 Notification request sent."
        )

    else:

        st.warning(
            "Enable notifications first."
        )

if enable_notifications:

    st.success(
        "🔔 Weather notifications are enabled."
    )

else:

    st.info(
        "🔕 Weather notifications are disabled."
    )


# ============================================================
# LOCATION
# ============================================================

st.markdown(
    '<div class="section-title">📍 Location</div>',
    unsafe_allow_html=True
)

location_col1, location_col2, location_col3 = st.columns(
    [4.5, 1.5, 1.5]
)

with location_col1:

    search_city = st.text_input(
        "🌎 Search city",
        placeholder=(
            "Vijayawada, Hyderabad, Tokyo, London..."
        ),
        label_visibility="collapsed",
        key="city_search"
    )

with location_col2:

    search_clicked = st.button(
        "🔎 Search",
        use_container_width=True
    )

with location_col3:

    current_clicked = st.button(
        "📍 My Location",
        use_container_width=True
    )


# ============================================================
# CITY SEARCH
# ============================================================

if search_clicked:

    if not search_city.strip():

        st.warning(
            "Please enter a city or location."
        )

    else:

        with st.spinner(
            "🌍 Searching worldwide..."
        ):

            result = search_location(
                search_city
            )

        if result:

            lat, lon, name, country = result

            st.session_state.latitude = float(lat)
            st.session_state.longitude = float(lon)

            if country:

                st.session_state.location_name = (
                    f"{name}, {country}"
                )

            else:

                st.session_state.location_name = name

            st.session_state.location_source = "search"

            st.session_state.route_data = None
            st.session_state.route_weather = None

            st.session_state.last_notification_key = ""

            st.rerun()

        else:

            st.error(
                f"❌ Could not find '{search_city}'. "
                "Try adding the country."
            )


# ============================================================
# GPS
# ============================================================

if current_clicked:

    st.session_state.gps_request_id += 1

    gps_key = (
        f"gps_{st.session_state.gps_request_id}"
    )

    location = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve) => {

            if (!navigator.geolocation) {

                resolve({
                    error: "Geolocation is not supported."
                });

                return;
            }

            navigator.geolocation.getCurrentPosition(

                (position) => {

                    resolve({
                        latitude:
                            position.coords.latitude,

                        longitude:
                            position.coords.longitude
                    });

                },

                (error) => {

                    resolve({
                        error: error.message
                    });

                },

                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                }
            );

        })
        """,
        want_output=True,
        key=gps_key
    )

    if isinstance(location, dict):

        if (
            location.get("latitude") is not None
            and
            location.get("longitude") is not None
        ):

            st.session_state.latitude = float(
                location["latitude"]
            )

            st.session_state.longitude = float(
                location["longitude"]
            )

            st.session_state.location_name = (
                "Current Location"
            )

            st.session_state.location_source = "gps"

            st.session_state.route_data = None
            st.session_state.route_weather = None

            st.session_state.last_notification_key = ""

            st.success(
                "📍 Current location detected."
            )

            st.rerun()

        elif location.get("error"):

            st.warning(
                "📍 Location permission/error: "
                + str(location["error"])
            )


# ============================================================
# LOAD CURRENT WEATHER
# ============================================================

latitude = float(
    st.session_state.latitude
)

longitude = float(
    st.session_state.longitude
)

weather = get_weather(
    latitude,
    longitude
)

if weather is None:

    st.error(
        "❌ Unable to load weather data. "
        "Please check your internet connection and try again."
    )

    st.stop()


current = weather.get(
    "current",
    {}
)

hourly = weather.get(
    "hourly",
    {}
)

daily = weather.get(
    "daily",
    {}
)


# ============================================================
# CURRENT WEATHER VALUES
# ============================================================

temperature = float(
    current.get(
        "temperature_2m",
        0
    ) or 0
)

humidity = float(
    current.get(
        "relative_humidity_2m",
        0
    ) or 0
)

feels_like = float(
    current.get(
        "apparent_temperature",
        0
    ) or 0
)

precipitation = float(
    current.get(
        "precipitation",
        0
    ) or 0
)

rain = float(
    current.get(
        "rain",
        0
    ) or 0
)

wind = float(
    current.get(
        "wind_speed_10m",
        0
    ) or 0
)

wind_gust = float(
    current.get(
        "wind_gusts_10m",
        0
    ) or 0
)

uv_index = float(
    current.get(
        "uv_index",
        0
    ) or 0
)

weather_code = int(
    current.get(
        "weather_code",
        0
    ) or 0
)

condition = weather_description(
    weather_code
)

icon = weather_icon(
    weather_code
)


# ============================================================
# NEXT HOURS RAIN
# ============================================================

rain_probabilities = hourly.get(
    "precipitation_probability",
    []
)

current_hour_index = 0

current_time = parse_datetime(
    current.get("time")
)

hourly_times = hourly.get(
    "time",
    []
)

if current_time and hourly_times:

    current_hour_index = find_nearest_hour(
        hourly_times,
        current_time
    )

next_hours = rain_probabilities[
    current_hour_index:
    current_hour_index + 6
]

max_rain_probability = (
    max(next_hours)
    if next_hours
    else 0
)


# ============================================================
# AUTOMATIC ALERT
# ============================================================

if st.session_state.notifications_enabled:

    alert = get_weather_alert(
        temperature,
        feels_like,
        max_rain_probability,
        wind,
        uv_index,
        weather_code
    )

    if alert["level"] != "normal":

        send_browser_notification(
            alert["title"],
            alert["message"],
            st.session_state.location_name
        )


# ============================================================
# LOCATION HEADER
# ============================================================

st.markdown(
    f"""
    <h2>📍 {st.session_state.location_name}</h2>

    <p class="small-text">
        Coordinates:
        {latitude:.4f}, {longitude:.4f}
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# WEATHER HERO
# ============================================================

st.markdown(
    f"""
    <div class="weather-card">

        <div class="weather-icon">
            {icon}
        </div>

        <div class="big-temp">
            {temperature:.0f}°C
        </div>

        <div class="condition">
            {condition}
        </div>

        <p>
            Feels like {feels_like:.0f}°C
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# OVERALL RISK
# ============================================================

overall_risk = calculate_risk(
    temperature,
    feels_like,
    max_rain_probability,
    wind,
    uv_index,
    weather_code
)

risk_html = "info-box"

if "🔴" in overall_risk:
    risk_html = "danger-box"

elif "🟡" in overall_risk:
    risk_html = "warning-box"

elif "🟢" in overall_risk:
    risk_html = "good-box"

st.markdown(
    f"""
    <div class="{risk_html}">
        <b>Overall Weather:</b> {overall_risk}
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CURRENT CONDITIONS
# ============================================================

st.markdown(
    '<div class="section-title">🌦️ Current Conditions</div>',
    unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)

metric_values = [
    (f"{temperature:.0f}°C", "Temperature"),
    (f"{humidity:.0f}%", "Humidity"),
    (f"{wind:.0f} km/h", "Wind"),
    (f"{uv_index:.0f}", "UV Index"),
]

for column, (value, label) in zip(
    [m1, m2, m3, m4],
    metric_values
):

    with column:

        st.markdown(
            f"""
            <div class="metric-box">

                <div class="metric-value">
                    {value}
                </div>

                <div class="metric-label">
                    {label}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# EXTRA CURRENT CONDITIONS
# ============================================================

extra1, extra2, extra3 = st.columns(3)

with extra1:

    st.metric(
        "🌧️ Precipitation",
        f"{precipitation:.1f} mm"
    )

with extra2:

    st.metric(
        "💨 Wind Gust",
        f"{wind_gust:.0f} km/h"
    )

with extra3:

    st.metric(
        "☔ Next 6h Rain Chance",
        f"{max_rain_probability:.0f}%"
    )


# ============================================================
# ROUTE SECTION
# ============================================================

st.markdown(
    '<div class="section-title">🚗 Route & Travel Weather</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="info-box">

    Enter a destination to calculate a road route and
    estimate weather conditions at several points along
    your journey.

    </div>
    """,
    unsafe_allow_html=True
)

destination_text = st.text_input(
    "🎯 Destination",
    placeholder=(
        "Vijayawada, Hyderabad, Chennai, Bangalore..."
    ),
    key="destination_input"
)

route_col1, route_col2 = st.columns(2)

with route_col1:

    calculate_route_clicked = st.button(
        "🚗 Calculate Route & Weather",
        use_container_width=True
    )

with route_col2:

    clear_route_clicked = st.button(
        "🗑️ Clear Route",
        use_container_width=True
    )


# ============================================================
# CLEAR ROUTE
# ============================================================

if clear_route_clicked:

    st.session_state.route_data = None
    st.session_state.route_weather = None

    st.session_state.destination_name = ""
    st.session_state.destination_lat = None
    st.session_state.destination_lon = None

    st.rerun()


# ============================================================
# CALCULATE ROUTE
# ============================================================

if calculate_route_clicked:

    destination = destination_text.strip()

    if not destination:

        st.warning(
            "🎯 Please enter a destination."
        )

    else:

        with st.spinner(
            "🌍 Finding destination..."
        ):

            destination_result = search_location(
                destination
            )

        if not destination_result:

            st.error(
                f"❌ Destination '{destination}' "
                "was not found."
            )

        else:

            (
                dest_lat,
                dest_lon,
                dest_name,
                dest_country
            ) = destination_result

            if dest_country:

                final_destination_name = (
                    f"{dest_name}, {dest_country}"
                )

            else:

                final_destination_name = dest_name

            # Avoid calculating a route to the same
            # coordinates.
            straight_distance = haversine_distance(
                latitude,
                longitude,
                float(dest_lat),
                float(dest_lon)
            )

            if straight_distance < 0.1:

                st.warning(
                    "📍 The destination is extremely close "
                    "to your current location."
                )

            with st.spinner(
                "🛣️ Calculating road route..."
            ):

                route = get_route(
                    latitude,
                    longitude,
                    float(dest_lat),
                    float(dest_lon)
                )

            if route is None:

                st.error(
                    "❌ Could not calculate a road route "
                    "between these locations."
                )

            else:

                st.session_state.destination_name = (
                    final_destination_name
                )

                st.session_state.destination_lat = (
                    float(dest_lat)
                )

                st.session_state.destination_lon = (
                    float(dest_lon)
                )

                st.session_state.route_data = route

                with st.spinner(
                    "📍 Finding places along the route..."
                ):

                    route_locations = (
                        build_route_locations(
                            route,
                            latitude,
                            longitude,
                            float(dest_lat),
                            float(dest_lon)
                        )
                    )

                with st.spinner(
                    "🌦️ Analyzing route weather..."
                ):

                    route_weather = (
                        get_route_weather(
                            route_locations,
                            route["duration_s"]
                        )
                    )

                st.session_state.route_weather = (
                    route_weather
                )

                st.rerun()


# ============================================================
# DISPLAY ROUTE
# ============================================================

route = st.session_state.route_data
route_weather = st.session_state.route_weather


if route is not None:

    distance_km = (
        route["distance_m"] / 1000
    )

    duration_text = format_duration(
        route["duration_s"]
    )

    # ========================================================
    # ROUTE HEADER
    # ========================================================

    st.markdown(
        f"""
        <div class="route-header">

            <h2>
                🚗 {st.session_state.location_name}
                → {st.session_state.destination_name}
            </h2>

            <div class="route-stat">

                <div class="route-stat-value">
                    {distance_km:.1f} km
                </div>

                <div class="route-stat-label">
                    📏 Road Distance
                </div>

            </div>

            <div class="route-stat">

                <div class="route-stat-value">
                    {duration_text}
                </div>

                <div class="route-stat-label">
                    ⏱️ Estimated Driving Time
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # ROUTE MAP
    # ========================================================

    st.markdown(
        "### 🗺️ Actual Road Route"
    )

    route_map = folium.Map(
        location=[
            latitude,
            longitude
        ],
        zoom_start=9,
        tiles="OpenStreetMap"
    )

    coordinates = (
        route
        .get("geometry", {})
        .get("coordinates", [])
    )

    if coordinates:

        route_line = [
            [
                coordinate[1],
                coordinate[0]
            ]
            for coordinate in coordinates
        ]

        folium.PolyLine(
            route_line,
            weight=6,
            opacity=0.85,
            tooltip="🚗 Calculated road route"
        ).add_to(route_map)


    # START

    folium.Marker(
        [
            latitude,
            longitude
        ],
        tooltip="📍 Start",
        popup=(
            f"<b>📍 Start</b><br>"
            f"{st.session_state.location_name}"
        ),
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(route_map)


    # DESTINATION

    folium.Marker(
        [
            st.session_state.destination_lat,
            st.session_state.destination_lon
        ],
        tooltip="🎯 Destination",
        popup=(
            f"<b>🎯 Destination</b><br>"
            f"{st.session_state.destination_name}"
        ),
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(route_map)


    # WEATHER POINTS

    if route_weather:

        for point in route_weather:

            risk_text = point["risk"]

            marker_color = "green"

            if "🟡" in risk_text:
                marker_color = "orange"

            if "🔴" in risk_text:
                marker_color = "red"

            popup = f"""
            <b>📍 {point['place']}</b><br><br>

            🕐 ETA:
            {point['estimated_time'].strftime("%I:%M %p")}
            <br>

            🌡️ Temperature:
            {point['temperature']:.0f}°C
            <br>

            🌧️ Rain:
            {point['rain_probability']:.0f}%
            <br>

            💨 Wind:
            {point['wind']:.0f} km/h
            <br>

            💧 Humidity:
            {point['humidity']:.0f}%
            <br>

            ☀️ UV:
            {point['uv']:.0f}
            <br>

            {point['icon']}
            {point['condition']}
            <br><br>

            <b>{risk_text}</b>
            """

            folium.CircleMarker(
                [
                    point["latitude"],
                    point["longitude"]
                ],
                radius=8,
                color=marker_color,
                fill=True,
                fill_opacity=0.85,
                popup=folium.Popup(
                    popup,
                    max_width=320
                )
            ).add_to(route_map)


    st_folium(
        route_map,
        width=None,
        height=520,
        returned_objects=[]
    )


    # ========================================================
    # ROUTE WEATHER TABLE
    # ========================================================

    st.markdown(
        "### 🌦️ Weather Along Your Journey"
    )

    if route_weather:

        table_data = []

        for point in route_weather:

            table_data.append({

                "📍 Location":
                    point["place"],

                "📏 Distance":
                    f"{point['distance_km']:.1f} km",

                "🕐 ETA":
                    point["estimated_time"].strftime(
                        "%I:%M %p"
                    ),

                "🌡️ Temp":
                    f"{point['temperature']:.0f}°C",

                "🌧️ Rain":
                    f"{point['rain_probability']:.0f}%",

                "💨 Wind":
                    f"{point['wind']:.0f} km/h",

                "💧 Humidity":
                    f"{point['humidity']:.0f}%",

                "☀️ UV":
                    f"{point['uv']:.0f}",

                "🌦️ Condition":
                    (
                        f"{point['icon']} "
                        f"{point['condition']}"
                    ),

                "Risk":
                    point["risk"],
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "⚠️ Route weather data could not be loaded."
        )


    # ========================================================
    # ROUTE SUMMARY
    # ========================================================

    if route_weather:

        high_risk_count = sum(
            "🔴" in p["risk"]
            for p in route_weather
        )

        caution_count = sum(
            "🟡" in p["risk"]
            for p in route_weather
        )

        good_count = sum(
            "🟢" in p["risk"]
            for p in route_weather
        )

        r1, r2, r3 = st.columns(3)

        with r1:

            st.metric(
                "🔴 High Risk Points",
                high_risk_count
            )

        with r2:

            st.metric(
                "🟡 Caution Points",
                caution_count
            )

        with r3:

            st.metric(
                "🟢 Good Points",
                good_count
            )


    # ========================================================
    # ROUTE NOTIFICATION
    # ========================================================

    if (
        st.session_state.notifications_enabled
        and route_weather
    ):

        route_high_risk = [
            point
            for point in route_weather
            if "🔴" in point["risk"]
        ]

        route_caution = [
            point
            for point in route_weather
            if "🟡" in point["risk"]
        ]

        route_context = (
            st.session_state.location_name
            + " → "
            + st.session_state.destination_name
        )

        if route_high_risk:

            worst = max(
                route_high_risk,
                key=lambda p: (
                    p["rain_probability"],
                    p["wind"],
                    p["temperature"]
                )
            )

            send_browser_notification(
                "🛣️ Route Weather Warning",
                (
                    f"High-risk weather near "
                    f"{worst['place']}. "
                    f"{worst['condition']}, "
                    f"rain {worst['rain_probability']:.0f}%, "
                    f"wind {worst['wind']:.0f} km/h."
                ),
                route_context
            )

        elif route_caution:

            first = route_caution[0]

            send_browser_notification(
                "🛣️ Route Weather Caution",
                (
                    f"Weather needs caution near "
                    f"{first['place']}. "
                    "Check conditions before travelling."
                ),
                route_context
            )


    # ========================================================
    # JOURNEY ADVISOR
    # ========================================================

    analysis = analyze_route_weather(
        route_weather
    )

    st.markdown(
        "### 🤖 Journey Weather Advisor"
    )

    if "🔴" in analysis["risk"]:

        box_class = "danger-box"

    elif "🟡" in analysis["risk"]:

        box_class = "warning-box"

    else:

        box_class = "good-box"

    st.markdown(
        f"""
        <div class="{box_class}">

            <h3>
                {analysis['risk']}
            </h3>

            <p>
                {analysis['message']}
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # TRAVEL ADVICE
    # ========================================================

    st.markdown(
        "### 🎒 AI Travel Advice"
    )

    for advice in analysis["advice"]:

        st.write(
            f"• {advice}"
        )


    # ========================================================
    # EXTREME ROUTE VALUES
    # ========================================================

    if route_weather:

        max_rain_point = max(
            route_weather,
            key=lambda x: x["rain_probability"]
        )

        max_wind_point = max(
            route_weather,
            key=lambda x: x["wind"]
        )

        max_temp_point = max(
            route_weather,
            key=lambda x: x["temperature"]
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.markdown(
                f"""
                <div class="metric-box">

                    <div class="metric-value">
                        🌧️
                        {max_rain_point['rain_probability']:.0f}%
                    </div>

                    <div class="metric-label">
                        Highest rain chance<br>
                        {max_rain_point['place']}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
                <div class="metric-box">

                    <div class="metric-value">
                        💨
                        {max_wind_point['wind']:.0f}
                        km/h
                    </div>

                    <div class="metric-label">
                        Strongest wind<br>
                        {max_wind_point['place']}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                f"""
                <div class="metric-box">

                    <div class="metric-value">
                        🌡️
                        {max_temp_point['temperature']:.0f}°C
                    </div>

                    <div class="metric-label">
                        Highest temperature<br>
                        {max_temp_point['place']}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# PERSONAL OUTDOOR ADVISOR
# ============================================================

st.markdown(
    '<div class="section-title">🏃 Personal Outdoor Advisor</div>',
    unsafe_allow_html=True
)

activity = st.selectbox(
    "What are you planning to do?",
    [
        "Just going outside",
        "Walking",
        "Running",
        "Playing sports",
        "Travelling",
        "Going to college",
        "Going to work",
        "Shopping",
        "Outdoor event",
    ],
    key="activity_select"
)

st.info(
    activity_advice(
        activity,
        temperature,
        max_rain_probability,
        wind,
        uv_index
    )
)


# ============================================================
# BEFORE YOU GO
# ============================================================

st.markdown(
    "### 🎒 Before You Go"
)

checklist = []

if temperature >= 35:

    checklist.append(
        "💧 Carry enough water"
    )

if uv_index >= 6:

    checklist.append(
        "🧴 Sunscreen recommended"
    )

if max_rain_probability >= 50:

    checklist.append(
        "☔ Carry an umbrella/raincoat"
    )

if wind >= 30:

    checklist.append(
        "💨 Be careful in strong wind"
    )

if temperature <= 15:

    checklist.append(
        "🧥 Carry a jacket"
    )

if weather_code in [95, 96, 99]:

    checklist.append(
        "⛈️ Avoid unnecessary outdoor activity"
    )

if not checklist:

    checklist = [
        "💧 Carry water",
        "👕 Wear comfortable clothing",
        "📱 Keep your phone charged",
    ]

for item in checklist:

    st.write(
        f"• {item}"
    )


# ============================================================
# BEST TIME TO GO OUT
# ============================================================

st.markdown(
    "### ⏰ Best Time to Go Outside"
)

hourly_temp = hourly.get(
    "temperature_2m",
    []
)

hourly_uv = hourly.get(
    "uv_index",
    []
)

hourly_rain = hourly.get(
    "precipitation_probability",
    []
)

scores = []

start_index = current_hour_index

for i in range(
    start_index,
    min(
        start_index + 24,
        len(hourly_times)
    )
):

    score = 100

    temp_value = (
        hourly_temp[i]
        if i < len(hourly_temp)
        else temperature
    )

    uv_value = (
        hourly_uv[i]
        if i < len(hourly_uv)
        else uv_index
    )

    rain_value = (
        hourly_rain[i]
        if i < len(hourly_rain)
        else 0
    )

    if temp_value > 35:
        score -= 30

    elif temp_value > 32:
        score -= 10

    if temp_value < 18:
        score -= 15

    if uv_value >= 8:
        score -= 25

    elif uv_value >= 6:
        score -= 10

    if rain_value >= 70:
        score -= 40

    elif rain_value >= 40:
        score -= 20

    scores.append(
        (
            score,
            hourly_times[i]
        )
    )


if scores:

    best_score, best_time = max(
        scores,
        key=lambda x: x[0]
    )

    st.success(
        f"🌤️ Suggested time: "
        f"{format_time(best_time)} "
        f"(comfort score {best_score}/100)"
    )

else:

    st.info(
        "Best-time recommendation is unavailable."
    )


# ============================================================
# 7-DAY FORECAST
# ============================================================

st.markdown(
    "### 📅 7-Day Forecast"
)

forecast_rows = []

daily_times = daily.get(
    "time",
    []
)

daily_max = daily.get(
    "temperature_2m_max",
    []
)

daily_min = daily.get(
    "temperature_2m_min",
    []
)

daily_codes = daily.get(
    "weather_code",
    []
)

daily_rain = daily.get(
    "precipitation_probability_max",
    []
)

daily_uv = daily.get(
    "uv_index_max",
    []
)

for i in range(
    min(7, len(daily_times))
):

    code = (
        daily_codes[i]
        if i < len(daily_codes)
        else 0
    )

    minimum = (
        daily_min[i]
        if i < len(daily_min)
        else 0
    )

    maximum = (
        daily_max[i]
        if i < len(daily_max)
        else 0
    )

    rain_probability = (
        daily_rain[i]
        if i < len(daily_rain)
        else 0
    )

    uv = (
        daily_uv[i]
        if i < len(daily_uv)
        else 0
    )

    forecast_rows.append({

        "Date":
            daily_times[i],

        "Condition":
            (
                weather_icon(code)
                + " "
                + weather_description(code)
            ),

        "Min":
            f"{minimum:.0f}°C",

        "Max":
            f"{maximum:.0f}°C",

        "Rain":
            f"{rain_probability:.0f}%",

        "UV":
            f"{uv:.0f}",
    })


st.dataframe(
    forecast_rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SUN SCHEDULE
# ============================================================

st.markdown(
    "### 🌅 Sun Schedule"
)

sunrise = daily.get(
    "sunrise",
    []
)

sunset = daily.get(
    "sunset",
    []
)

sun_col1, sun_col2 = st.columns(2)

with sun_col1:

    if sunrise:

        st.info(
            "🌅 Sunrise: "
            + format_time(sunrise[0])
        )

with sun_col2:

    if sunset:

        st.info(
            "🌇 Sunset: "
            + format_time(sunset[0])
        )


# ============================================================
# LIVE LOCATION MAP
# ============================================================

st.markdown(
    "### 🌍 Live Location Map"
)

world_map = folium.Map(
    location=[
        latitude,
        longitude
    ],
    zoom_start=7,
    tiles="OpenStreetMap"
)

folium.Marker(
    [
        latitude,
        longitude
    ],
    tooltip="📍 Current location",
    popup=(
        f"<b>📍 "
        f"{st.session_state.location_name}"
        f"</b><br><br>"
        f"{temperature:.0f}°C<br>"
        f"{condition}"
    ),
    icon=folium.Icon(
        color="blue",
        icon="cloud"
    )
).add_to(world_map)

st_folium(
    world_map,
    width=None,
    height=430,
    returned_objects=[]
)


# ============================================================
# PERSONAL SUMMARY
# ============================================================

st.markdown(
    "### 🤖 AI Personal Weather Summary"
)

summary_parts = []

if temperature >= 40:

    summary_parts.append(
        "Extreme heat is present, so avoid prolonged outdoor exposure."
    )

elif temperature >= 35:

    summary_parts.append(
        "It is quite hot, so stay hydrated."
    )

elif temperature <= 18:

    summary_parts.append(
        "The weather is relatively cool."
    )

else:

    summary_parts.append(
        "The temperature is generally comfortable."
    )


if max_rain_probability >= 70:

    summary_parts.append(
        "Rain is likely in the coming hours."
    )

elif max_rain_probability >= 40:

    summary_parts.append(
        "There is some possibility of rain."
    )

else:

    summary_parts.append(
        "Rain probability is currently low."
    )


if uv_index >= 8:

    summary_parts.append(
        "UV levels are high, so sunscreen is recommended."
    )

elif uv_index >= 6:

    summary_parts.append(
        "UV protection is recommended."
    )


if wind >= 35:

    summary_parts.append(
        "Winds are strong, so take care outdoors."
    )


st.info(
    " ".join(summary_parts)
)


# ============================================================
# ACTIVE WEATHER ALERT
# ============================================================

if st.session_state.notifications_enabled:

    alert = get_weather_alert(
        temperature,
        feels_like,
        max_rain_probability,
        wind,
        uv_index,
        weather_code
    )

    if alert["level"] == "danger":

        st.markdown(
            f"""
            <div class="danger-box">

                <h3>
                    🔔 Active Weather Alert
                </h3>

                <p>
                    <b>{alert['title']}</b>
                </p>

                <p>
                    {alert['message']}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    elif alert["level"] == "warning":

        st.markdown(
            f"""
            <div class="warning-box">

                <h3>
                    🔔 Weather Advisory
                </h3>

                <p>
                    <b>{alert['title']}</b>
                </p>

                <p>
                    {alert['message']}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# DATA SOURCES / FOOTER
# ============================================================

st.markdown(
    """
    <hr>

    <div style="
        text-align:center;
        color:#78909c;
        font-size:13px;
        padding:18px;
    ">

        🌦️ <b>AI Personal Weather Advisor</b>
        <br><br>

        Weather data:
        Open-Meteo
        <br>

        Geocoding:
        Open-Meteo
        <br>

        Road routing:
        OSRM
        <br>

        Map data:
        OpenStreetMap

    </div>
    """,
    unsafe_allow_html=True
)
