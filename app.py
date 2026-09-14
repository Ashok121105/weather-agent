
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime

# ============================================================
# AI PERSONAL WEATHER ADVISOR — FINAL LIGHT SKY THEME
# Complete replacement app.py
# ============================================================

st.set_page_config(
    page_title="AI Personal Weather Advisor",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# THEME / CSS
# The important fix here is that ALL light cards explicitly
# force readable dark text. This prevents Streamlit's dark theme
# from making card text white/invisible.
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #123B6D;
    --blue: #218BE6;
    --blue-dark: #1769D0;
    --sky: #EAF6FF;
    --page: #F5FAFE;
    --text: #14532D;
    --text2: #2F6B46;
    --muted: #6B7F73;
    --border: #D5E8F6;
    --white: #FFFFFF;
}

/* ---------- GLOBAL LIGHT THEME ---------- */

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], section.main {
    font-family: 'Inter', sans-serif !important;
}

html, body {
    background: #F5FAFE !important;
    color: #14532D !important;
    color-scheme: light !important;
}

.stApp {
    background:
        radial-gradient(circle at 5% 0%, rgba(72, 169, 238, .18), transparent 25%),
        radial-gradient(circle at 95% 5%, rgba(111, 196, 255, .14), transparent 25%),
        linear-gradient(180deg, #EAF6FF 0%, #F6FBFF 45%, #FFFFFF 100%) !important;
    color: #14532D !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

section.main {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1480px !important;
    padding: 1.25rem 2rem 2.5rem !important;
}

/* Force ordinary Streamlit text to dark on the light page */
.stApp p,
.stApp label,
.stApp span,
.stApp div,
.stApp li,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    font-family: 'Inter', sans-serif;
}

[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #245C3A !important;
}

/* ---------- HERO ---------- */

.hero {
    position: relative;
    overflow: hidden;
    padding: 28px 32px;
    border-radius: 28px;
    margin-bottom: 18px;
    background: linear-gradient(135deg, #FFFFFF 0%, #E7F5FF 100%);
    border: 1px solid #C9E3F4;
    box-shadow: 0 14px 38px rgba(33, 112, 169, .10);
}

.hero:after {
    content: "☁️   ☀️   ☁️";
    position: absolute;
    right: 28px;
    top: 12px;
    font-size: 42px;
    opacity: .23;
    letter-spacing: 10px;
}

.hero-title {
    color: #166534 !important;
    font-size: clamp(30px, 4vw, 48px);
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -1.5px;
    margin: 0 !important;
}

.hero-subtitle {
    color: #557B67 !important;
    font-size: 16px;
    font-weight: 500;
    margin-top: 9px;
}

.hero-pill {
    display: inline-block;
    margin-top: 14px;
    padding: 7px 13px;
    border-radius: 999px;
    background: #E6F4FF;
    color: #16834D !important;
    border: 1px solid #C7E4F8;
    font-size: 13px;
    font-weight: 700;
}

/* ---------- SEARCH ---------- */

.search-box {
    background: #FFFFFF !important;
    border: 1px solid #CFE4F5;
    border-radius: 18px;
    padding: 13px;
    box-shadow: 0 8px 25px rgba(35, 105, 158, .08);
    margin-bottom: 18px;
}

/* ---------- CARD ---------- */

.card {
    background: #FFFFFF !important;
    border: 1px solid #D5E8F6;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 23px rgba(31, 91, 145, .07);
    margin-bottom: 12px;

    /* Critical readability fix */
    color: #14532D !important;
}

.card * {
    color: #14532D !important;
}

.card-title {
    color: #166534 !important;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 12px;
}

.muted {
    color: #6B7F73 !important;
}

.small {
    font-size: 13px;
}

/* ---------- WEATHER HERO ---------- */

.weather-hero {
    min-height: 280px;
    padding: 25px;
    border-radius: 22px;
    color: #FFFFFF !important;
    background:
        radial-gradient(circle at 85% 22%, rgba(255,255,255,.30), transparent 23%),
        linear-gradient(135deg, #1478BD 0%, #218BE6 52%, #1769B9 100%);
    border: 1px solid rgba(255,255,255,.30);
    box-shadow: 0 14px 34px rgba(23, 105, 185, .20);
    position: relative;
    overflow: hidden;
}

.weather-hero * {
    color: #FFFFFF !important;
}

.weather-hero:after {
    content: "☁️";
    position: absolute;
    right: 16px;
    bottom: -32px;
    font-size: 145px;
    opacity: .12;
}

.location-line {
    font-size: 15px;
    font-weight: 700;
}

.weather-condition {
    font-size: 17px;
    font-weight: 600;
    margin-top: 7px;
}

.temperature {
    font-size: clamp(58px, 7vw, 88px);
    line-height: .95;
    font-weight: 800;
    letter-spacing: -4px;
    margin-top: 18px;
}

.feels {
    font-size: 17px;
    opacity: .92;
    margin-top: 8px;
}

.weather-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 28px;
}

.weather-stat {
    border-top: 1px solid rgba(255,255,255,.25);
    padding-top: 11px;
}

.weather-stat-label {
    font-size: 11px;
    opacity: .78;
}

.weather-stat-value {
    font-size: 14px;
    font-weight: 700;
    margin-top: 3px;
}

/* ---------- STATUS ---------- */

.status {
    border-radius: 17px;
    padding: 15px 17px;
    margin-bottom: 11px;
    border: 1px solid;
}

.status * {
    font-family: 'Inter', sans-serif !important;
}

.status-good {
    background: linear-gradient(135deg, #F0FFF7, #E5F9EF) !important;
    border-color: #B9E8D0 !important;
}

.status-good * {
    color: #176B45 !important;
}

.status-warning {
    background: linear-gradient(135deg, #FFFBEF, #FFF3D4) !important;
    border-color: #F1D48B !important;
}

.status-warning * {
    color: #805B00 !important;
}

.status-danger {
    background: linear-gradient(135deg, #FFF2F3, #FFE7E9) !important;
    border-color: #F0BBC0 !important;
}

.status-danger * {
    color: #A32934 !important;
}

.status-kicker {
    font-size: 12px;
    font-weight: 700;
    opacity: .82;
}

.status-main {
    font-size: 17px;
    font-weight: 800;
    margin-top: 3px;
}

.status-detail {
    font-size: 12px;
    margin-top: 4px;
    opacity: .82;
}

/* ---------- METRICS ---------- */

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.metric-box {
    padding: 15px;
    border-radius: 16px;
    background: #F7FBFF !important;
    border: 1px solid #E0EEF8;
}

.metric-box * {
    color: #14532D !important;
}

.metric-icon {
    font-size: 20px;
}

.metric-label {
    font-size: 11px;
    color: #71847A !important;
    margin-top: 6px;
}

.metric-value {
    color: #166534 !important;
    font-size: 19px;
    font-weight: 800;
    margin-top: 2px;
}

/* ---------- AI CARD ---------- */

.ai-card {
    background: linear-gradient(135deg, #EFF8FF, #E8F3FF) !important;
    border: 1px solid #BFDFF6;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 9px 24px rgba(33, 139, 230, .08);
    color: #2F6B46 !important;
}

.ai-card * {
    color: #2F6B46 !important;
}

.ai-title {
    color: #205B3A !important;
    font-weight: 800;
    font-size: 18px;
}

.ai-text {
    color: #2F6B46 !important;
    font-size: 14px;
    line-height: 1.7;
    margin-top: 12px;
}

/* ---------- CHECKLIST ---------- */

.check-item {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 11px 4px;
    border-bottom: 1px solid #E8F0F6;
    color: #245C3A !important;
    font-size: 13px;
}

.check-item * {
    color: #245C3A !important;
}

.check-item:last-child {
    border-bottom: 0;
}

.check-icon {
    width: 27px;
    height: 27px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #E9F6FF;
    color: #21834A !important;
}

/* ---------- PLAN ---------- */

.plan-item {
    display: flex;
    gap: 11px;
    padding: 11px 0;
    border-bottom: 1px solid #E7EFF6;
}

.plan-item:last-child {
    border-bottom: 0;
}

.plan-time {
    color: #16834D !important;
    font-size: 12px;
    font-weight: 800;
}

.plan-text {
    color: #496B59 !important;
    font-size: 12px;
    margin-top: 2px;
}

/* ---------- SECTION TITLES ---------- */

.section-title {
    color: #166534 !important;
    font-size: 22px;
    font-weight: 800;
    margin: 15px 0 10px;
}

/* ---------- FORECAST ---------- */

.forecast-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 9px;
}

.forecast-card {
    min-height: 145px;
    text-align: center;
    padding: 14px 8px;
    border-radius: 16px;
    background: #FFFFFF !important;
    border: 1px solid #DCEBF7;
    box-shadow: 0 6px 16px rgba(31, 91, 145, .06);
}

.forecast-card * {
    color: #14532D !important;
}

.forecast-card.today {
    background: linear-gradient(180deg, #EDF8FF, #FFFFFF) !important;
    border-color: #A9D7F5;
}

.forecast-day {
    color: #496B59 !important;
    font-size: 12px;
    font-weight: 800;
}

.forecast-icon {
    font-size: 27px;
    margin: 10px 0;
}

.forecast-temp {
    color: #166534 !important;
    font-size: 14px;
    font-weight: 800;
}

.forecast-rain {
    color: #54806A !important;
    font-size: 11px;
    margin-top: 7px;
}

/* ---------- STREAMLIT INPUTS ---------- */

div[data-baseweb="input"] {
    background: #FFFFFF !important;
    border: 1px solid #CFE3F3 !important;
    border-radius: 12px !important;
}

div[data-baseweb="input"] input {
    color: #14532D !important;
    background: #FFFFFF !important;
    -webkit-text-fill-color: #14532D !important;
}

div[data-baseweb="input"] input::placeholder {
    color: #789083 !important;
    -webkit-text-fill-color: #789083 !important;
}

div[data-baseweb="select"] {
    background: #FFFFFF !important;
    border: 1px solid #CFE3F3 !important;
    border-radius: 12px !important;
}

div[data-baseweb="select"] * {
    color: #14532D !important;
}

div[role="listbox"],
div[role="option"] {
    background: #FFFFFF !important;
    color: #14532D !important;
}

div[role="option"]:hover {
    background: #EAF5FF !important;
}

/* ---------- BUTTONS ---------- */

.stButton button {
    min-height: 43px;
    border-radius: 12px !important;
    font-weight: 750 !important;
    border: 1px solid #2185DE !important;
    background: linear-gradient(135deg, #2196F3, #1769D0) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(33, 150, 243, .18);
}

.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 9px 20px rgba(33, 150, 243, .25);
}

.stButton button p,
.stButton button span,
.stButton button div {
    color: #FFFFFF !important;
}

/* ---------- ALERTS / CAPTIONS ---------- */

[data-testid="stAlert"] {
    border-radius: 12px !important;
}

[data-testid="stAlert"] p,
[data-testid="stCaptionContainer"] p {
    color: #2F6B46 !important;
}

hr {
    border-color: #D8EAF8 !important;
}

/* ---------- MAP ---------- */

.map-wrap {
    border: 1px solid #D7E9F7;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 9px 25px rgba(31, 91, 145, .08);
}

/* ---------- FOOTER ---------- */

.footer {
    text-align: center;
    color: #789083 !important;
    font-size: 12px;
    padding: 18px 0 5px;
}

/* ---------- RESPONSIVE ---------- */

@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .weather-stats {
        grid-template-columns: repeat(2, 1fr);
    }

    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .forecast-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (max-width: 600px) {
    .hero {
        padding: 20px;
    }

    .forecast-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* ---------- GREEN TEXT VISIBILITY OVERRIDE ---------- */
.card,
.card p,
.card span,
.card div,
.card li,
.card strong,
.card b,
.card em,
.card small,
.card-title,
.section-title,
.info-card,
.advice-card,
.forecast-card,
.metric-card,
.weather-detail {
    color: #14532D !important;
    -webkit-text-fill-color: #14532D !important;
}

.card-title,
.section-title {
    color: #166534 !important;
}

.muted,
.card .muted {
    color: #557B67 !important;
    -webkit-text-fill-color: #557B67 !important;
}

/* Keep white text where it belongs: the blue weather hero */
.weather-hero,
.weather-hero p,
.weather-hero span,
.weather-hero div,
.weather-hero strong,
.weather-hero b,
.weather-hero h1,
.weather-hero h2,
.weather-hero h3 {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# DEFAULT LOCATION
# ============================================================

DEFAULT_LAT = 16.3067
DEFAULT_LON = 80.4365
DEFAULT_CITY = "Guntur, India"

if "latitude" not in st.session_state:
    st.session_state.latitude = DEFAULT_LAT

if "longitude" not in st.session_state:
    st.session_state.longitude = DEFAULT_LON

if "location_name" not in st.session_state:
    st.session_state.location_name = DEFAULT_CITY


# ============================================================
# HELPERS
# ============================================================

def weather_description(code):
    codes = {
        0: "☀️ Clear sky",
        1: "🌤️ Mainly clear",
        2: "⛅ Partly cloudy",
        3: "☁️ Overcast",
        45: "🌫️ Fog",
        48: "🌫️ Rime fog",
        51: "🌦️ Light drizzle",
        53: "🌦️ Moderate drizzle",
        55: "🌧️ Heavy drizzle",
        56: "🌧️ Freezing drizzle",
        57: "🌧️ Heavy freezing drizzle",
        61: "🌦️ Light rain",
        63: "🌧️ Moderate rain",
        65: "🌧️ Heavy rain",
        66: "🌧️ Freezing rain",
        67: "🌧️ Heavy freezing rain",
        71: "❄️ Light snow",
        73: "❄️ Moderate snow",
        75: "❄️ Heavy snow",
        77: "❄️ Snow grains",
        80: "🌦️ Light rain showers",
        81: "🌧️ Moderate rain showers",
        82: "⛈️ Heavy rain showers",
        85: "🌨️ Snow showers",
        86: "❄️ Heavy snow showers",
        95: "⛈️ Thunderstorm",
        96: "⛈️ Thunderstorm with hail",
        99: "⛈️ Severe thunderstorm",
    }
    return codes.get(code, "🌤️ Unknown weather")


def weather_icon(code):
    return weather_description(code).split(" ")[0]


def format_time(value):
    try:
        return datetime.fromisoformat(value).strftime("%I:%M %p")
    except Exception:
        return str(value)


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
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        st.error(f"Weather API error: {error}")
        return None


def search_location(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            result = data["results"][0]
            return (
                result["latitude"],
                result["longitude"],
                result.get("name", city),
                result.get("country", ""),
            )
    except Exception:
        pass

    return None


def reverse_geocode(latitude, longitude):
    # Open-Meteo does not provide a reverse-geocoding endpoint.
    # Return a useful coordinate label when current location is used.
    return f"Current Location ({latitude:.2f}, {longitude:.2f})"


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">
    <div class="hero-title">🌦️ AI Personal Weather Advisor</div>
    <div class="hero-subtitle">
        Smarter Weather &nbsp;•&nbsp; Safer You &nbsp;•&nbsp; Better Decisions
    </div>
    <div class="hero-pill">🤖 Personalized outdoor weather intelligence</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LOCATION SEARCH
# ============================================================

st.markdown('<div class="search-box">', unsafe_allow_html=True)

c1, c2, c3 = st.columns([4.5, 1.35, 1.35])

with c1:
    search_city = st.text_input(
        "🌎 Search any city",
        placeholder="Example: Hyderabad, Tokyo, London, New York",
        label_visibility="collapsed",
    )

with c2:
    search_clicked = st.button("🔎 Get Weather", use_container_width=True)

with c3:
    current_clicked = st.button("📍 My Location", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)


if search_clicked:
    if not search_city.strip():
        st.warning("Please enter a city name.")
    else:
        result = search_location(search_city.strip())

        if result:
            lat, lon, name, country = result
            st.session_state.latitude = lat
            st.session_state.longitude = lon
            st.session_state.location_name = (
                f"{name}, {country}" if country else name
            )
            st.rerun()
        else:
            st.error("Location not found. Please try another city.")


if current_clicked:
    location = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({error: "Geolocation is not supported by this browser."});
                return;
            }

            navigator.geolocation.getCurrentPosition(
                position => resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                }),
                error => resolve({error: error.message})
            );
        })
        """,
        want_output=True,
        key="current_location",
    )

    if location and isinstance(location, dict):
        if "latitude" in location and "longitude" in location:
            st.session_state.latitude = location["latitude"]
            st.session_state.longitude = location["longitude"]
            st.session_state.location_name = reverse_geocode(
                location["latitude"],
                location["longitude"]
            )
            st.rerun()
        elif "error" in location:
            st.warning(f"Location permission: {location['error']}")


# ============================================================
# WEATHER DATA
# ============================================================

latitude = st.session_state.latitude
longitude = st.session_state.longitude

weather = get_weather(latitude, longitude)

if weather is None:
    st.stop()

current = weather["current"]
hourly = weather["hourly"]
daily = weather["daily"]

temperature = current["temperature_2m"]
humidity = current["relative_humidity_2m"]
feels_like = current["apparent_temperature"]
precipitation = current["precipitation"]
rain = current["rain"]
wind = current["wind_speed_10m"]
wind_gust = current["wind_gusts_10m"]
uv_index = current["uv_index"]
weather_code = current["weather_code"]

condition = weather_description(weather_code)

rain_probabilities = hourly.get("precipitation_probability", [])
next_hours = rain_probabilities[:6]
max_rain_probability = max(next_hours) if next_hours else 0


# ============================================================
# LOCATION LABEL
# ============================================================

st.markdown(
    f"""
    <div style="margin:5px 2px 14px;">
        <div style="color:#123B6D !important;font-size:14px;font-weight:800;">
            📍 {st.session_state.location_name}
        </div>
        <div style="color:#7893AD !important;font-size:11px;margin-top:3px;">
            Coordinates: {latitude:.4f}, {longitude:.4f}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# THREE-COLUMN MAIN DASHBOARD
# ============================================================

left, middle, right = st.columns([1.25, 1.05, .95], gap="medium")


# ============================================================
# LEFT
# ============================================================

with left:

    st.markdown(
        f"""
        <div class="weather-hero">
            <div class="location-line">📍 {st.session_state.location_name}</div>
            <div class="weather-condition">{condition}</div>
            <div class="temperature">{temperature:.0f}°C</div>
            <div class="feels">Feels like {feels_like:.0f}°C</div>

            <div class="weather-stats">
                <div class="weather-stat">
                    <div class="weather-stat-label">💧 HUMIDITY</div>
                    <div class="weather-stat-value">{humidity}%</div>
                </div>

                <div class="weather-stat">
                    <div class="weather-stat-label">💨 WIND</div>
                    <div class="weather-stat-value">{wind:.0f} km/h</div>
                </div>

                <div class="weather-stat">
                    <div class="weather-stat-label">☀️ UV INDEX</div>
                    <div class="weather-stat-value">{uv_index:.1f}</div>
                </div>

                <div class="weather-stat">
                    <div class="weather-stat-label">🌧️ RAIN</div>
                    <div class="weather-stat-value">{rain:.1f} mm</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Determine overall risk.
    risk = "good"

    if temperature >= 40 or feels_like >= 42 or wind >= 50 or uv_index >= 9:
        risk = "danger"
    elif (
        temperature >= 35
        or feels_like >= 38
        or wind >= 30
        or uv_index >= 6
        or max_rain_probability >= 70
        or rain > 0
    ):
        risk = "warning"

    if risk == "good":
        st.markdown("""
        <div class="status status-good">
            <div class="status-kicker">✓ WEATHER CONDITION</div>
            <div class="status-main">Good Conditions</div>
            <div class="status-detail">
                You can generally go outside. Normal precautions are enough.
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif risk == "warning":
        st.markdown("""
        <div class="status status-warning">
            <div class="status-kicker">⚠ WEATHER CONDITION</div>
            <div class="status-main">Caution Recommended</div>
            <div class="status-detail">
                Outdoor activity is possible, but follow the recommendations below.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="status status-danger">
            <div class="status-kicker">! WEATHER CONDITION</div>
            <div class="status-main">Conditions Need Attention</div>
            <div class="status-detail">
                Consider delaying unnecessary outdoor activity and take precautions.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Activity
    st.markdown(
        '<div class="section-title">🏃 Activity Recommendation</div>',
        unsafe_allow_html=True,
    )

    activity = st.selectbox(
        "Choose an activity",
        [
            "Just going outside",
            "🚶 Walking",
            "🏃 Running",
            "🏏 Playing sports",
            "🚗 Travelling",
            "🏫 Going to college",
            "💼 Going to work",
            "🛍️ Shopping",
            "🌳 Outdoor event",
        ],
        label_visibility="collapsed",
    )

    if activity == "🏃 Running":
        if temperature >= 35 or feels_like >= 38:
            activity_advice = (
                "🔴 Running is not recommended right now. "
                "Try early morning or evening."
            )
        elif rain > 0 or max_rain_probability >= 70:
            activity_advice = (
                "🌧️ Rain is likely. Consider postponing your run."
            )
        elif uv_index >= 8:
            activity_advice = (
                "☀️ UV is very high. Run during a cooler time "
                "and use sun protection."
            )
        else:
            activity_advice = "🟢 Good conditions for running."

    elif activity == "🚶 Walking":
        if temperature >= 38:
            activity_advice = (
                "🟡 Walking is possible, but choose a cooler time and carry water."
            )
        else:
            activity_advice = "🟢 Good conditions for walking."

    elif activity == "🏏 Playing sports":
        if temperature >= 35:
            activity_advice = (
                "🟡 Heat may make outdoor sports uncomfortable. "
                "Prefer morning or evening."
            )
        elif max_rain_probability >= 70:
            activity_advice = (
                "🌧️ Rain may interrupt outdoor sports. Consider postponing."
            )
        else:
            activity_advice = "🟢 Conditions are generally suitable for outdoor sports."

    elif activity == "🚗 Travelling":
        if max_rain_probability >= 70 or wind >= 50:
            activity_advice = (
                "🟡 Travel with extra caution because weather may affect the journey."
            )
        else:
            activity_advice = "🟢 No major weather-related concern detected."

    elif activity in ["🏫 Going to college", "💼 Going to work", "🛍️ Shopping"]:
        if max_rain_probability >= 70:
            activity_advice = "☂️ Carry an umbrella before leaving."
        elif temperature >= 38:
            activity_advice = (
                "☀️ It is hot. Use sunscreen, carry water and avoid long exposure."
            )
        else:
            activity_advice = "🟢 Conditions are generally comfortable."

    elif activity == "🌳 Outdoor event":
        if temperature >= 38:
            activity_advice = "🟡 Consider moving the event to a cooler time."
        elif max_rain_probability >= 70:
            activity_advice = (
                "🌧️ Rain may affect the event. Have an indoor backup plan."
            )
        else:
            activity_advice = "🟢 Conditions look suitable for an outdoor event."

    else:
        activity_advice = "🟢 Normal outdoor precautions should be enough."

    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-title">{activity}</div>
            <div class="ai-text">{activity_advice}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MIDDLE
# ============================================================

with middle:

    st.markdown(
        '<div class="section-title">🌡️ Today\'s Weather Details</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="metric-grid">

                <div class="metric-box">
                    <div class="metric-icon">🌡️</div>
                    <div class="metric-label">MAX TEMP</div>
                    <div class="metric-value">
                        {daily["temperature_2m_max"][0]:.0f}°C
                    </div>
                </div>

                <div class="metric-box">
                    <div class="metric-icon">❄️</div>
                    <div class="metric-label">MIN TEMP</div>
                    <div class="metric-value">
                        {daily["temperature_2m_min"][0]:.0f}°C
                    </div>
                </div>

                <div class="metric-box">
                    <div class="metric-icon">🌧️</div>
                    <div class="metric-label">RAIN CHANCE</div>
                    <div class="metric-value">
                        {daily["precipitation_probability_max"][0]}%
                    </div>
                </div>

                <div class="metric-box">
                    <div class="metric-icon">☀️</div>
                    <div class="metric-label">UV INDEX</div>
                    <div class="metric-value">{uv_index:.1f}</div>
                </div>

                <div class="metric-box">
                    <div class="metric-icon">💨</div>
                    <div class="metric-label">WIND</div>
                    <div class="metric-value">{wind:.0f}</div>
                </div>

                <div class="metric-box">
                    <div class="metric-icon">🌡️</div>
                    <div class="metric-label">FEELS LIKE</div>
                    <div class="metric-value">{feels_like:.0f}°C</div>
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Checklist
    st.markdown(
        '<div class="section-title">🎒 Personal Checklist</div>',
        unsafe_allow_html=True,
    )

    checklist = []

    if temperature >= 35 or uv_index >= 6:
        checklist.append(("🧴", "Carry sunscreen"))

    if temperature >= 32:
        checklist.append(("💧", "Carry a water bottle"))

    if temperature >= 32 or uv_index >= 6:
        checklist.append(("🧢", "Wear a cap / hat"))

    if uv_index >= 6:
        checklist.append(("🕶️", "Keep sunglasses"))

    if max_rain_probability >= 50 or rain > 0:
        checklist.append(("☂️", "Carry an umbrella"))

    if temperature <= 18:
        checklist.append(("🧥", "Take a jacket"))

    if not checklist:
        checklist.append(("🎒", "No special weather equipment needed"))

    checklist_html = '<div class="card">'

    for icon, item in checklist:
        checklist_html += f"""
        <div class="check-item">
            <div class="check-icon">{icon}</div>
            <div>{item}</div>
        </div>
        """

    checklist_html += "</div>"

    st.markdown(checklist_html, unsafe_allow_html=True)

    # Best time
    st.markdown(
        '<div class="section-title">⏰ Best Time to Go Outside</div>',
        unsafe_allow_html=True,
    )

    hourly_temp = hourly.get("temperature_2m", [])
    hourly_uv = hourly.get("uv_index", [])
    hourly_rain = hourly.get("precipitation_probability", [])

    scores = []

    for i in range(min(24, len(hourly_temp))):
        score = 0
        temp = hourly_temp[i]
        uv = hourly_uv[i] if i < len(hourly_uv) else 0
        rain_probability = (
            hourly_rain[i] if i < len(hourly_rain) else 0
        )

        if 20 <= temp <= 32:
            score += 3
        elif 18 <= temp <= 35:
            score += 1

        if uv <= 5:
            score += 2

        if rain_probability < 30:
            score += 2
        elif rain_probability < 60:
            score += 1

        scores.append(score)

    if scores and hourly.get("time"):
        best_index = scores.index(max(scores))
        best_time = format_time(hourly["time"][best_index])
    else:
        best_time = "Not available"

    st.markdown(
        f"""
        <div class="card"
             style="background:linear-gradient(135deg,#FFF9EC,#FFFFFF) !important;">
            <div style="color:#8A6200 !important;font-size:12px;font-weight:700;">
                RECOMMENDED TIME
            </div>
            <div style="color:#173B68 !important;font-size:22px;font-weight:800;margin-top:4px;">
                {best_time}
            </div>
            <div class="muted small">
                Based on temperature, UV and rain probability.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# RIGHT
# ============================================================

with right:

    advice_parts = []

    if temperature >= 40 or feels_like >= 42:
        advice_parts.append(
            "Extreme heat is present. Avoid unnecessary outdoor activity "
            "and stay hydrated."
        )
    elif temperature >= 35 or feels_like >= 38:
        advice_parts.append(
            "It is hot outside. Limit prolonged exposure and carry water."
        )
    else:
        advice_parts.append(
            "The temperature is generally comfortable for outdoor activities."
        )

    if uv_index >= 8:
        advice_parts.append(
            "UV is very high, so use sunscreen, sunglasses and shade."
        )
    elif uv_index >= 6:
        advice_parts.append(
            "UV is high, so sun protection is recommended."
        )

    if max_rain_probability >= 70:
        advice_parts.append(
            "Rain is likely in the next few hours, so carry an umbrella."
        )

    if wind >= 40:
        advice_parts.append(
            "Wind is strong, so take extra care outdoors."
        )

    ai_message = " ".join(advice_parts)

    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-title">🤖 AI Personal Advice</div>
            <div class="ai-text">“{ai_message}”</div>
            <div style="margin-top:15px;color:#2D78B5 !important;font-size:12px;font-weight:700;">
                💙 Stay Safe &nbsp;•&nbsp; Stay Healthy &nbsp;•&nbsp; Stay Happy
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">📅 Daily Plan</div>',
        unsafe_allow_html=True,
    )

    daily_plan = [
        ("🌅", "6:00 AM – 9:00 AM", "Best window for walking / exercise"),
        ("💼", "9:00 AM – 12:00 PM", "Work, college or study"),
        ("☀️", "12:00 PM – 4:00 PM", "Avoid long exposure if heat/UV is high"),
        ("🚶", "4:00 PM – 7:00 PM", "Outdoor activities if conditions permit"),
        ("🌙", "7:00 PM – 10:00 PM", "Relax / family time"),
    ]

    plan_html = '<div class="card">'

    for icon, time_text, detail in daily_plan:
        plan_html += f"""
        <div class="plan-item">
            <div style="font-size:20px;">{icon}</div>
            <div>
                <div class="plan-time">{time_text}</div>
                <div class="plan-text">{detail}</div>
            </div>
        </div>
        """

    plan_html += "</div>"

    st.markdown(plan_html, unsafe_allow_html=True)

    sunrise = format_time(daily["sunrise"][0])
    sunset = format_time(daily["sunset"][0])

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🌅 Sun Schedule</div>

            <div style="display:flex;justify-content:space-between;">
                <div>
                    <div class="muted small">Sunrise</div>
                    <div style="color:#123B6D !important;font-weight:800;">
                        {sunrise}
                    </div>
                </div>

                <div style="text-align:right;">
                    <div class="muted small">Sunset</div>
                    <div style="color:#123B6D !important;font-weight:800;">
                        {sunset}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LIVE MAP
# ============================================================

st.markdown(
    '<div class="section-title">🌍 Live Location Map</div>',
    unsafe_allow_html=True,
)

world_map = folium.Map(
    location=[latitude, longitude],
    zoom_start=7,
    tiles="OpenStreetMap",
)

folium.Marker(
    [latitude, longitude],
    tooltip="📍 Your location",
    popup=(
        f"<b>📍 {st.session_state.location_name}</b><br>"
        f"{temperature:.0f}°C<br>{condition}"
    ),
    icon=folium.Icon(color="blue", icon="cloud"),
).add_to(world_map)

st.markdown('<div class="map-wrap">', unsafe_allow_html=True)

st_folium(
    world_map,
    width=None,
    height=430,
    returned_objects=[],
)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 7-DAY FORECAST
# ============================================================

st.markdown(
    '<div class="section-title">📅 7-Day Forecast</div>',
    unsafe_allow_html=True,
)

forecast_html = '<div class="forecast-grid">'

for i in range(7):
    day = daily["time"][i]

    try:
        date_obj = datetime.fromisoformat(day)
        day_name = date_obj.strftime("%a")
        date_name = date_obj.strftime("%d %b")
    except Exception:
        day_name = str(day)
        date_name = ""

    code = daily["weather_code"][i]
    max_temp = daily["temperature_2m_max"][i]
    min_temp = daily["temperature_2m_min"][i]
    rain_chance = daily["precipitation_probability_max"][i]

    today_class = " today" if i == 0 else ""

    forecast_html += f"""
    <div class="forecast-card{today_class}">
        <div class="forecast-day">{day_name}</div>
        <div style="color:#7893AD !important;font-size:10px;margin-top:2px;">
            {date_name}
        </div>
        <div class="forecast-icon">{weather_icon(code)}</div>
        <div class="forecast-temp">
            {min_temp:.0f}° / {max_temp:.0f}°C
        </div>
        <div class="forecast-rain">🌧️ {rain_chance}%</div>
    </div>
    """

forecast_html += "</div>"

st.markdown(forecast_html, unsafe_allow_html=True)


# ============================================================
# AI SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">🤖 AI Summary</div>',
    unsafe_allow_html=True,
)

summary_items = []

if temperature >= 38:
    summary_items.append("☀️ It is hot, so protect yourself from heat.")
elif temperature <= 18:
    summary_items.append("🧥 Temperatures are cool, so consider an extra layer.")

if uv_index >= 6:
    summary_items.append(
        "🧴 UV is high, so sunscreen and sun protection are recommended."
    )

if max_rain_probability >= 70:
    summary_items.append("☂️ Rain is likely, so carry an umbrella.")

if wind >= 40:
    summary_items.append("💨 Wind is strong, so take care outdoors.")

if not summary_items:
    summary_items.append("🟢 Weather conditions look generally comfortable.")

summary_text = " ".join(summary_items)

st.markdown(
    f"""
    <div class="ai-card">
        <div class="ai-title">🧠 Your Personal Weather Summary</div>
        <div class="ai-text">{summary_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🌦️ AI Personal Weather Advisor
        &nbsp;•&nbsp;
        Weather data powered by Open-Meteo
    </div>
    """,
    unsafe_allow_html=True,
)
