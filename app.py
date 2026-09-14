import streamlit as st
import requests
import folium
import math
import time
from datetime import datetime, timedelta

from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval


# ============================================================
# WEATHER AGENT
# Personal Weather + Route Weather Intelligence
# ============================================================

st.set_page_config(
    page_title="AI Personal Weather Advisor",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# THEME / CSS
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

    p, label, span, div {
        color: #24506b;
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
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .weather-card {
        padding: 25px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #2374ab,
            #4c9ed0
        );
        color: white;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.10);
    }

    .weather-card h1,
    .weather-card h2,
    .weather-card h3,
    .weather-card p,
    .weather-card div {
        color: white !important;
    }

    .big-temp {
        font-size: 58px;
        font-weight: 700;
    }

    .condition {
        font-size: 25px;
        font-weight: 600;
    }

    .metric-box {
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #dce7ee;
        background: #f8fbfd;
        text-align: center;
        min-height: 105px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #183b56;
    }

    .metric-label {
        font-size: 14px;
        color: #66808f;
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
        padding: 20px;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            #173f5f,
            #287da8
        );
        color: white;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .route-header h2,
    .route-header p,
    .route-header div {
        color: white !important;
    }

    .route-stat {
        text-align: center;
        padding: 12px;
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

    .search-box {
        padding: 15px;
        border-radius: 15px;
        background: #f7fafc;
        border: 1px solid #dce6ed;
        margin-bottom: 20px;
    }

    .small-text {
        color: #718692;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DEFAULT LOCATION
# ============================================================

DEFAULT_LAT = 16.3067
DEFAULT_LON = 80.4365
DEFAULT_CITY = "Guntur, India"


# ============================================================
# SESSION STATE
# ============================================================

if "latitude" not in st.session_state:
    st.session_state.latitude = DEFAULT_LAT

if "longitude" not in st.session_state:
    st.session_state.longitude = DEFAULT_LON

if "location_name" not in st.session_state:
    st.session_state.location_name = DEFAULT_CITY

if "location_source" not in st.session_state:
    st.session_state.location_source = "default"

if "route_data" not in st.session_state:
    st.session_state.route_data = None

if "route_weather" not in st.session_state:
    st.session_state.route_weather = None

if "destination_name" not in st.session_state:
    st.session_state.destination_name = ""

if "destination_lat" not in st.session_state:
    st.session_state.destination_lat = None

if "destination_lon" not in st.session_state:
    st.session_state.destination_lon = None


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

    return descriptions.get(code, "Unknown weather")


def weather_icon(code):

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

    if code in [61, 63, 65, 80, 81, 82]:
        return "🌧️"

    if code in [66, 67]:
        return "🌧️"

    if code in [71, 73, 75, 77, 85, 86]:
        return "❄️"

    if code in [95, 96, 99]:
        return "⛈️"

    return "🌦️"


def format_time(value):

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%I:%M %p")
    except Exception:
        return value


# ============================================================
# OPEN-METEO WEATHER
# ============================================================

@st.cache_data(ttl=300)
def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

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
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None


# ============================================================
# WORLDWIDE SEARCH
# ============================================================

@st.cache_data(ttl=3600)
def search_location(city):

    city = city.strip()

    if not city:
        return None

    url = "https://geocoding-api.open-meteo.com/v1/search"

    queries = [
        city,
        city.title(),
        city.replace(",", " ").strip()
    ]

    for query in queries:

        params = {
            "name": query,
            "count": 10,
            "language": "en",
            "format": "json",
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

            results = data.get("results", [])

            if not results:
                continue

            query_lower = city.lower()

            # Exact match
            for result in results:

                result_name = str(
                    result.get("name", "")
                ).lower()

                if result_name == query_lower:

                    return (
                        result.get("latitude"),
                        result.get("longitude"),
                        result.get("name", city),
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
                        result.get("name", city),
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
                        result.get("name", city),
                        result.get("country", ""),
                    )

        except Exception:
            continue

    return None


# ============================================================
# OSRM ROUTING
# ============================================================

@st.cache_data(ttl=600)
def get_route(start_lat, start_lon, end_lat, end_lon):

    url = (
        "https://router.project-osrm.org/"
        f"route/v1/driving/"
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

        routes = data.get("routes", [])

        if not routes:
            return None

        route = routes[0]

        return {
            "distance_m": route.get("distance", 0),
            "duration_s": route.get("duration", 0),
            "geometry": route.get(
                "geometry",
                {}
            ),
            "legs": route.get("legs", []),
        }

    except Exception:
        return None


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):

    R = 6371.0

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

    return R * c


# ============================================================
# SAMPLE ROUTE POINTS
# ============================================================

def sample_route_points(
    coordinates,
    number_of_points=8
):

    if not coordinates:
        return []

    # OSRM GeoJSON is:
    # [longitude, latitude]

    points = []

    if len(coordinates) <= number_of_points:

        for index, coordinate in enumerate(coordinates):

            points.append({
                "index": index,
                "latitude": coordinate[1],
                "longitude": coordinate[0],
            })

        return points

    step = (len(coordinates) - 1) / (
        number_of_points - 1
    )

    for i in range(number_of_points):

        position = round(i * step)

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

@st.cache_data(ttl=86400)
def reverse_geocode_route(
    latitude,
    longitude
):

    url = "https://nominatim.openstreetmap.org/reverse"

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
            url,
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
            address.get("village")
            or address.get("town")
            or address.get("city")
            or address.get("municipality")
            or address.get("suburb")
            or address.get("hamlet")
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

    sample_points = sample_route_points(
        coordinates,
        number_of_points=8
    )

    route_locations = []

    total_distance = route["distance_m"] / 1000

    for i, point in enumerate(sample_points):

        lat = point["latitude"]
        lon = point["longitude"]

        if i == 0:

            place_name = "Starting Location"
            distance_km = 0

        elif i == len(sample_points) - 1:

            place_name = "Destination"
            distance_km = total_distance

        else:

            place_name = reverse_geocode_route(
                lat,
                lon
            )

            distance_km = haversine_distance(
                start_lat,
                start_lon,
                lat,
                lon
            )

        route_locations.append({
            "place": place_name,
            "latitude": lat,
            "longitude": lon,
            "distance_km": distance_km,
        })

        # Small delay for public reverse-geocoding service
        if 0 < i < len(sample_points) - 1:
            time.sleep(0.8)

    # Remove consecutive duplicate names

    cleaned = []

    for item in route_locations:

        if (
            cleaned
            and
            cleaned[-1]["place"].lower()
            == item["place"].lower()
        ):

            continue

        cleaned.append(item)

    return cleaned


# ============================================================
# ROUTE WEATHER
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

        try:

            current_time = datetime.fromisoformat(
                value
            )

            difference = abs(
                (
                    current_time
                    - target_datetime
                ).total_seconds()
            )

            if (
                best_difference is None
                or
                difference < best_difference
            ):

                best_difference = difference
                best_index = i

        except Exception:
            continue

    return best_index


def get_route_weather(
    route_locations,
    route_duration_seconds
):

    if not route_locations:
        return []

    start_time = datetime.now()

    total_distance = route_locations[-1][
        "distance_km"
    ]

    results = []

    for location in route_locations:

        if total_distance > 0:

            progress = (
                location["distance_km"]
                / total_distance
            )

        else:

            progress = 0

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

        def get_hourly(
            key,
            default=0
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

            return default

        temperature = get_hourly(
            "temperature_2m",
            current.get(
                "temperature_2m",
                0
            )
        )

        feels_like = get_hourly(
            "apparent_temperature",
            current.get(
                "apparent_temperature",
                0
            )
        )

        rain_probability = get_hourly(
            "precipitation_probability",
            0
        )

        precipitation = get_hourly(
            "precipitation",
            0
        )

        rain = get_hourly(
            "rain",
            0
        )

        wind = get_hourly(
            "wind_speed_10m",
            current.get(
                "wind_speed_10m",
                0
            )
        )

        humidity = get_hourly(
            "relative_humidity_2m",
            current.get(
                "relative_humidity_2m",
                0
            )
        )

        uv = get_hourly(
            "uv_index",
            current.get(
                "uv_index",
                0
            )
        )

        code = get_hourly(
            "weather_code",
            current.get(
                "weather_code",
                0
            )
        )

        # Risk

        risk = "🟢 Good"

        if (
            code in [95, 96, 99]
            or rain_probability >= 85
            or wind >= 50
            or temperature >= 40
            or feels_like >= 42
        ):

            risk = "🔴 High Risk"

        elif (
            rain_probability >= 60
            or wind >= 30
            or temperature >= 35
            or feels_like >= 38
            or uv >= 8
            or rain > 0
        ):

            risk = "🟡 Caution"

        results.append({
            **location,
            "estimated_time": estimated_time,
            "temperature": temperature,
            "feels_like": feels_like,
            "rain_probability": rain_probability,
            "precipitation": precipitation,
            "rain": rain,
            "wind": wind,
            "humidity": humidity,
            "uv": uv,
            "weather_code": code,
            "condition": weather_description(code),
            "icon": weather_icon(code),
            "risk": risk,
        })

    return results


# ============================================================
# ROUTE AI ANALYSIS
# ============================================================

def analyze_route_weather(route_weather):

    if not route_weather:

        return {
            "risk": "🟢 Unknown",
            "message":
                "Route weather data is unavailable.",
            "advice": [
                "Check your route again.",
            ],
        }

    high_risk = []
    caution = []

    for point in route_weather:

        if "🔴" in point["risk"]:
            high_risk.append(point)

        elif "🟡" in point["risk"]:
            caution.append(point)

    if high_risk:

        worst = high_risk[0]

        return {
            "risk": "🔴 High Risk",
            "message": (
                "Weather conditions may become "
                "unsafe during part of your journey."
            ),
            "advice": [
                (
                    f"Be careful around "
                    f"{worst['place']}."
                ),
                (
                    "Check rain and wind conditions "
                    "before starting."
                ),
                (
                    "Consider delaying the journey "
                    "if severe weather is expected."
                ),
            ],
        }

    if caution:

        first = caution[0]

        return {
            "risk": "🟡 Moderate Risk",
            "message": (
                "Most of the route looks manageable, "
                "but some sections need caution."
            ),
            "advice": [
                (
                    f"Take extra care around "
                    f"{first['place']}."
                ),
                "Carry water.",
                "Keep an umbrella or rain protection.",
                "Allow some extra travel time.",
            ],
        }

    return {
        "risk": "🟢 Good",
        "message": (
            "Weather conditions look generally "
            "favorable across the route."
        ),
        "advice": [
            "Carry drinking water.",
            "Use sunscreen during daytime.",
            "Wear comfortable/light clothing.",
            "Check the weather again before departure.",
        ],
    }


# ============================================================
# LOCATION SECTION
# ============================================================

st.markdown(
    '<div class="top-title">'
    'Weather intelligence + personal outdoor advice'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">📍 Location</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="search-box">',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(
    [4.5, 1.4, 1.4]
)

with col1:

    search_city = st.text_input(
        "🌎 Search any city in the world",
        placeholder=(
            "Example: Vijayawada, Hyderabad, "
            "Tokyo, London, New York"
        ),
        label_visibility="collapsed",
    )

with col2:

    search_clicked = st.button(
        "🔎 Search Location",
        use_container_width=True
    )

with col3:

    current_clicked = st.button(
        "📍 My Location",
        use_container_width=True
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# SEARCH LOCATION
# ============================================================

if search_clicked:

    search_text = search_city.strip()

    if not search_text:

        st.warning(
            "⚠️ Please enter a location."
        )

    else:

        with st.spinner(
            "🌍 Searching worldwide..."
        ):

            result = search_location(
                search_text
            )

        if result:

            lat, lon, name, country = result

            st.session_state.latitude = float(
                lat
            )

            st.session_state.longitude = float(
                lon
            )

            if country:

                st.session_state.location_name = (
                    f"{name}, {country}"
                )

            else:

                st.session_state.location_name = name

            st.session_state.location_source = (
                "search"
            )

            # Reset previous route
            st.session_state.route_data = None
            st.session_state.route_weather = None

            st.rerun()

        else:

            st.error(
                f"❌ Could not find "
                f"'{search_text}'. "
                "Try adding the state or country."
            )


# ============================================================
# CURRENT LOCATION
# ============================================================

if current_clicked:

    location = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve) => {

            if (!navigator.geolocation) {

                resolve({
                    error:
                    "Geolocation is not supported."
                });

                return;
            }

            navigator.geolocation.getCurrentPosition(

                position => {

                    resolve({

                        latitude:
                            position.coords.latitude,

                        longitude:
                            position.coords.longitude
                    });

                },

                error => {

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
        key="current_location"
    )

    if (
        location
        and isinstance(location, dict)
    ):

        if (
            "latitude" in location
            and
            "longitude" in location
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

            st.session_state.location_source = (
                "gps"
            )

            st.session_state.route_data = None
            st.session_state.route_weather = None

            st.rerun()

        elif "error" in location:

            st.warning(
                "📍 Location permission: "
                + str(location["error"])
            )


# ============================================================
# CURRENT WEATHER
# ============================================================

latitude = st.session_state.latitude
longitude = st.session_state.longitude

weather = get_weather(
    latitude,
    longitude
)

if weather is None:

    st.error(
        "Unable to load weather data."
    )

    st.stop()

current = weather["current"]
hourly = weather["hourly"]
daily = weather["daily"]

temperature = current.get(
    "temperature_2m",
    0
)

humidity = current.get(
    "relative_humidity_2m",
    0
)

feels_like = current.get(
    "apparent_temperature",
    0
)

precipitation = current.get(
    "precipitation",
    0
)

rain = current.get(
    "rain",
    0
)

wind = current.get(
    "wind_speed_10m",
    0
)

wind_gust = current.get(
    "wind_gusts_10m",
    0
)

uv_index = current.get(
    "uv_index",
    0
)

weather_code = current.get(
    "weather_code",
    0
)

condition = weather_description(
    weather_code
)

icon = weather_icon(
    weather_code
)

rain_probabilities = hourly.get(
    "precipitation_probability",
    []
)

next_hours = rain_probabilities[:6]

max_rain_probability = (
    max(next_hours)
    if next_hours
    else 0
)


# ============================================================
# LOCATION DISPLAY
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

        <div style="font-size:45px;">
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
# RISK
# ============================================================

if (
    temperature >= 40
    or feels_like >= 42
    or wind >= 50
    or uv_index >= 9
):

    risk = "🔴 Dangerous"

elif (
    temperature >= 35
    or feels_like >= 38
    or wind >= 30
    or uv_index >= 6
    or max_rain_probability >= 70
    or rain > 0
):

    risk = "🟡 Caution"

else:

    risk = "🟢 Good"


st.markdown(
    f"""
    <div class="info-box">
        <b>Overall Weather:</b> {risk}
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# WEATHER METRICS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🌦️ Current Conditions'
    '</div>',
    unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)

with m1:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">
                {temperature:.0f}°C
            </div>
            <div class="metric-label">
                Temperature
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m2:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">
                {humidity:.0f}%
            </div>
            <div class="metric-label">
                Humidity
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m3:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">
                {wind:.0f} km/h
            </div>
            <div class="metric-label">
                Wind
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with m4:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-value">
                {uv_index:.0f}
            </div>
            <div class="metric-label">
                UV Index
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ROUTE & TRAVEL SECTION
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🚗 Route & Travel Weather'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="info-box">

    Enter any destination. The app will calculate the
    actual road route from your current location,
    estimate distance and travel time, and analyze
    weather conditions at multiple places along the route.

    </div>
    """,
    unsafe_allow_html=True
)


destination_text = st.text_input(
    "🎯 Where do you want to go?",
    placeholder=(
        "Example: Vijayawada, Hyderabad, Chennai, "
        "Bangalore, Mumbai, London..."
    ),
    key="destination_input"
)

route_col1, route_col2 = st.columns(
    [2, 1]
)

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
                f"❌ Destination "
                f"'{destination}' was not found."
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
                    f"{dest_name}, "
                    f"{dest_country}"
                )

            else:

                final_destination_name = dest_name

            with st.spinner(
                "🛣️ Finding the actual road route..."
            ):

                route = get_route(
                    latitude,
                    longitude,
                    float(dest_lat),
                    float(dest_lon)
                )

            if route is None:

                st.error(
                    "❌ Could not calculate "
                    "the road route."
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

                # ------------------------------------------------
                # Route locations
                # ------------------------------------------------

                with st.spinner(
                    "📍 Finding places along your route..."
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

                # ------------------------------------------------
                # Route weather
                # ------------------------------------------------

                with st.spinner(
                    "🌦️ Analyzing weather along your route..."
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

    duration_minutes = (
        route["duration_s"] / 60
    )

    hours = int(
        duration_minutes // 60
    )

    minutes = int(
        duration_minutes % 60
    )

    if hours > 0:

        duration_text = (
            f"{hours} hr {minutes} min"
        )

    else:

        duration_text = (
            f"{minutes} min"
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
                    📏 Distance
                </div>

            </div>

            <div class="route-stat">

                <div class="route-stat-value">
                    {duration_text}
                </div>

                <div class="route-stat-label">
                    ⏱️ Estimated travel time
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

    # Route geometry

    geometry = route.get(
        "geometry",
        {}
    )

    coordinates = geometry.get(
        "coordinates",
        []
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
            tooltip=(
                "🚗 Your calculated route"
            )
        ).add_to(route_map)


    # Start marker

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


    # Destination marker

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


    # Weather route points

    if route_weather:

        for point in route_weather:

            risk_text = point["risk"]

            marker_color = "green"

            if "🟡" in risk_text:
                marker_color = "orange"

            if "🔴" in risk_text:
                marker_color = "red"

            popup = f"""
            <b>📍 {point['place']}</b><br>
            🌡️ {point['temperature']:.0f}°C<br>
            🌧️ Rain: {point['rain_probability']:.0f}%<br>
            💨 Wind: {point['wind']:.0f} km/h<br>
            💧 Humidity: {point['humidity']:.0f}%<br>
            ☀️ UV: {point['uv']:.0f}<br>
            {point['icon']} {point['condition']}<br>
            {risk_text}
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
                popup=popup
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
            "Route weather data could not be loaded."
        )


    # ========================================================
    # ROUTE AI ADVICE
    # ========================================================

    analysis = analyze_route_weather(
        route_weather
    )

    st.markdown(
        "### 🤖 Journey Weather Advisor"
    )

    if "🔴" in analysis["risk"]:

        st.markdown(
            f"""
            <div class="danger-box">

            <h3>{analysis['risk']}</h3>

            <p>
            {analysis['message']}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    elif "🟡" in analysis["risk"]:

        st.markdown(
            f"""
            <div class="warning-box">

            <h3>{analysis['risk']}</h3>

            <p>
            {analysis['message']}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="good-box">

            <h3>{analysis['risk']}</h3>

            <p>
            {analysis['message']}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # ADVICE
    # ========================================================

    st.markdown(
        "### 🎒 AI Travel Advice"
    )

    for advice in analysis["advice"]:

        st.write(
            f"• {advice}"
        )


    # ========================================================
    # EXTRA ROUTE WARNINGS
    # ========================================================

    if route_weather:

        max_rain_point = max(
            route_weather,
            key=lambda x:
            x["rain_probability"]
        )

        max_wind_point = max(
            route_weather,
            key=lambda x:
            x["wind"]
        )

        max_temp_point = max(
            route_weather,
            key=lambda x:
            x["temperature"]
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
# ACTIVITY ADVISOR
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🏃 Personal Outdoor Advisor'
    '</div>',
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
    ]
)


def activity_advice(
    activity,
    temp,
    rain_chance,
    wind_speed,
    uv
):

    if rain_chance >= 70:

        return (
            "🌧️ Rain is likely. "
            "Carry an umbrella or raincoat."
        )

    if temp >= 40:

        return (
            "🔥 Very hot conditions. "
            "Avoid long outdoor exposure."
        )

    if temp >= 35:

        return (
            "☀️ Hot conditions. "
            "Carry water and avoid peak afternoon heat."
        )

    if wind_speed >= 35:

        return (
            "💨 Strong wind. "
            "Be careful during outdoor activities."
        )

    if uv >= 8:

        return (
            "☀️ High UV. "
            "Use sunscreen and protect your skin."
        )

    if activity == "Running":

        return (
            "🏃 Conditions are reasonably suitable "
            "for running. Stay hydrated."
        )

    if activity == "Walking":

        return (
            "🚶 Good conditions for walking."
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

    return (
        "🟢 Conditions are generally comfortable "
        "for outdoor activity."
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
# PERSONAL CHECKLIST
# ============================================================

st.markdown(
    "### 🎒 Before You Go"
)

checklist = []

if temperature >= 35:
    checklist.append("💧 Carry enough water")

if uv_index >= 6:
    checklist.append("🧴 Sunscreen recommended")

if max_rain_probability >= 50:
    checklist.append("☔ Carry an umbrella/raincoat")

if wind >= 30:
    checklist.append("💨 Be careful with strong wind")

if temperature <= 15:
    checklist.append("🧥 Carry a light jacket")

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

hourly_times = hourly.get(
    "time",
    []
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

for i in range(
    min(
        24,
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

    if temp_value < 18:
        score -= 15

    if uv_value >= 8:
        score -= 25

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
        "🌤️ Suggested time: "
        + format_time(best_time)
    )


# ============================================================
# 7 DAY FORECAST
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

    forecast_rows.append({
        "Date":
            daily_times[i],

        "Condition":
            (
                weather_icon(
                    daily_codes[i]
                )
                + " "
                + weather_description(
                    daily_codes[i]
                )
            ),

        "Min":
            f"{daily_min[i]:.0f}°C",

        "Max":
            f"{daily_max[i]:.0f}°C",

        "Rain":
            f"{daily_rain[i]:.0f}%",

        "UV":
            f"{daily_uv[i]:.0f}",
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

sun_col1, sun_col2 = st.columns(2)

sunrise = daily.get(
    "sunrise",
    []
)

sunset = daily.get(
    "sunset",
    []
)

with sun_col1:

    if sunrise:

        st.info(
            "🌅 Sunrise: "
            + format_time(
                sunrise[0]
            )
        )

with sun_col2:

    if sunset:

        st.info(
            "🌇 Sunset: "
            + format_time(
                sunset[0]
            )
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
        f"</b><br>"
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
# AI PERSONAL SUMMARY
# ============================================================

st.markdown(
    "### 🤖 AI Personal Weather Summary"
)

summary_parts = []

if temperature >= 35:

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
# FOOTER
# ============================================================

st.markdown(
    """
    <hr>

    <div style="
        text-align:center;
        color:#78909c;
        font-size:13px;
        padding:15px;
    ">

    🌦️ AI Personal Weather Advisor<br>

    Weather data powered by Open-Meteo<br>

    Route data powered by OpenStreetMap / OSRM

    </div>
    """,
    unsafe_allow_html=True
)
