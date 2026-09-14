import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime

# ============================================================
# AI PERSONAL WEATHER ADVISOR
# ============================================================

st.set_page_config(
    page_title="AI Personal Weather Advisor",
    page_icon="🌦️",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 18px;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 18px;
    background: #f7f9fc;
    border: 1px solid #e2e8f0;
    margin-bottom: 15px;
}

.good {
    padding: 18px;
    border-radius: 15px;
    background: #eaf8ef;
    border: 1px solid #b7e4c7;
}

.warning {
    padding: 18px;
    border-radius: 15px;
    background: #fff7df;
    border: 1px solid #f0d98c;
}

.danger {
    padding: 18px;
    border-radius: 15px;
    background: #fff0f0;
    border: 1px solid #efb4b4;
}

.advice {
    padding: 20px;
    border-radius: 18px;
    background: #eef7ff;
    border: 1px solid #cfe8ff;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🌦️ AI Personal Weather Advisor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Weather intelligence + personal outdoor advice'
    '</div>',
    unsafe_allow_html=True
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

# ============================================================
# WEATHER FUNCTION
# ============================================================

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
            "uv_index"
        ]),

        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "uv_index"
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
            "sunset"
        ]),

        "timezone": "auto",
        "forecast_days": 7
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except Exception as error:

        st.error(f"Weather API error: {error}")

        return None


# ============================================================
# WEATHER CODE
# ============================================================

def weather_description(code):

    weather_codes = {

        0: "☀️ Clear sky",

        1: "🌤️ Mainly clear",
        2: "⛅ Partly cloudy",
        3: "☁️ Overcast",

        45: "🌫️ Fog",
        48: "🌫️ Depositing rime fog",

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
        99: "⛈️ Severe thunderstorm"

    }

    return weather_codes.get(
        code,
        "🌤️ Unknown weather"
    )


# ============================================================
# GEOCODING
# ============================================================

def reverse_geocode(latitude, longitude):

    url = "https://geocoding-api.open-meteo.com/v1/reverse"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if data.get("results"):

            result = data["results"][0]

            name = result.get("name", "")
            country = result.get("country", "")

            if name and country:
                return f"{name}, {country}"

            return name

    except Exception:

        pass

    return "Your Current Location"


def search_location(city):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if data.get("results"):

            result = data["results"][0]

            return (
                result["latitude"],
                result["longitude"],
                result.get("name", city),
                result.get("country", "")
            )

    except Exception:

        pass

    return None


# ============================================================
# LOCATION SECTION
# ============================================================

st.subheader("📍 Location")

location_col1, location_col2 = st.columns([1, 2])

with location_col1:

    if st.button(
        "📍 Use My Current Location",
        use_container_width=True
    ):

        location = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        resolve({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude
                        });
                    },
                    error => {
                        resolve({
                            error: error.message
                        });
                    }
                );
            })
            """,
            want_output=True,
            key="get_location"
        )

        if location:

            if "latitude" in location:

                st.session_state.latitude = location["latitude"]
                st.session_state.longitude = location["longitude"]

                location_name = reverse_geocode(
                    location["latitude"],
                    location["longitude"]
                )

                st.session_state.location_name = location_name

                st.success("📍 Current location detected!")

            else:

                st.error(
                    "Location permission was not allowed."
                )


with location_col2:

    search_city = st.text_input(
        "🌎 Search any city in the world",
        placeholder="Example: Tokyo, London, New York"
    )

    if st.button(
        "🔎 Search Location",
        use_container_width=True
    ):

        if search_city.strip():

            result = search_location(
                search_city.strip()
            )

            if result:

                lat, lon, name, country = result

                st.session_state.latitude = lat
                st.session_state.longitude = lon

                st.session_state.location_name = (
                    f"{name}, {country}"
                )

                st.success(
                    f"📍 Location changed to {name}, {country}"
                )

            else:

                st.error(
                    "Location not found. Try another city."
                )


# ============================================================
# GET WEATHER
# ============================================================

latitude = st.session_state.latitude
longitude = st.session_state.longitude

weather = get_weather(
    latitude,
    longitude
)

if weather is None:

    st.stop()

# ============================================================
# CURRENT WEATHER
# ============================================================

current = weather["current"]

temperature = current["temperature_2m"]
humidity = current["relative_humidity_2m"]
feels_like = current["apparent_temperature"]
precipitation = current["precipitation"]
rain = current["rain"]
wind = current["wind_speed_10m"]
wind_gust = current["wind_gusts_10m"]
uv_index = current["uv_index"]
weather_code = current["weather_code"]

condition = weather_description(
    weather_code
)

# ============================================================
# LOCATION DISPLAY
# ============================================================

st.markdown(
    f"## 📍 {st.session_state.location_name}"
)

st.caption(
    f"Coordinates: {latitude:.4f}, {longitude:.4f}"
)

# ============================================================
# WORLD MAP
# ============================================================

st.subheader("🌍 Live Location Map")

world_map = folium.Map(
    location=[
        latitude,
        longitude
    ],
    zoom_start=5,
    tiles="OpenStreetMap"
)

folium.Marker(
    [latitude, longitude],
    tooltip="📍 You are here",
    popup=(
        f"<b>📍 You are here</b><br>"
        f"{st.session_state.location_name}<br>"
        f"{temperature}°C"
    ),
    icon=folium.Icon(
        color="red",
        icon="user"
    )
).add_to(world_map)

st_folium(
    world_map,
    width=None,
    height=500
)

# ============================================================
# CURRENT WEATHER
# ============================================================

st.subheader("🌦️ Current Weather")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "🌡️ Temperature",
        f"{temperature} °C"
    )

with col2:

    st.metric(
        "🌡️ Feels Like",
        f"{feels_like} °C"
    )

with col3:

    st.metric(
        "💧 Humidity",
        f"{humidity}%"
    )

with col4:

    st.metric(
        "💨 Wind",
        f"{wind} km/h"
    )

st.markdown(
    f"""
    <div class="card">

    <h2>{condition}</h2>

    <b>🌧️ Rain:</b> {rain} mm<br>
    <b>💧 Precipitation:</b> {precipitation} mm<br>
    <b>💨 Wind Gust:</b> {wind_gust} km/h<br>
    <b>☀️ UV Index:</b> {uv_index}

    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# AI ADVICE ENGINE
# ============================================================

st.subheader("🤖 AI Personal Advice")

advice = []

risk_level = "good"

# ------------------------------------------------------------
# HEAT
# ------------------------------------------------------------

if temperature >= 40 or feels_like >= 42:

    risk_level = "danger"

    advice.append(
        "🔥 **Extreme heat:** Avoid unnecessary outdoor activity."
    )

    advice.append(
        "🧴 **Sunscreen:** Strongly recommended."
    )

    advice.append(
        "💧 **Hydration:** Carry water and drink regularly."
    )

    advice.append(
        "🧢 **Protection:** Wear a cap/hat and light clothing."
    )

elif temperature >= 35 or feels_like >= 38:

    if risk_level != "danger":
        risk_level = "warning"

    advice.append(
        "☀️ **Hot weather:** Limit long outdoor exposure."
    )

    advice.append(
        "🧴 **Sunscreen:** Recommended."
    )

    advice.append(
        "💧 **Water:** Carry water when going outside."
    )

    advice.append(
        "🧢 **Cap:** Recommended during strong sunlight."
    )

else:

    advice.append(
        "🌡️ **Temperature:** Comfortable for most outdoor activities."
    )

# ------------------------------------------------------------
# UV
# ------------------------------------------------------------

if uv_index >= 8:

    risk_level = "danger"

    advice.append(
        "☀️ **UV:** Very high. Use sunscreen, sunglasses and sun protection."
    )

elif uv_index >= 6:

    if risk_level == "good":
        risk_level = "warning"

    advice.append(
        "🧴 **UV:** High. Sunscreen and sun protection are recommended."
    )

elif uv_index >= 3:

    advice.append(
        "🧴 **UV:** Moderate. Sunscreen is useful for extended outdoor exposure."
    )

# ------------------------------------------------------------
# RAIN
# ------------------------------------------------------------

if rain > 0:

    if risk_level == "good":
        risk_level = "warning"

    advice.append(
        "🌧️ **Rain:** Rain is currently occurring."
    )

    advice.append(
        "☂️ **Umbrella:** Take an umbrella."
    )

# ------------------------------------------------------------
# HOURLY RAIN
# ------------------------------------------------------------

hourly = weather["hourly"]

rain_probabilities = hourly[
    "precipitation_probability"
]

next_hours = rain_probabilities[:6]

if next_hours:

    max_rain_probability = max(
        next_hours
    )

else:

    max_rain_probability = 0


if max_rain_probability >= 70:

    if risk_level == "good":
        risk_level = "warning"

    advice.append(
        f"🌧️ **Rain alert:** "
        f"Rain probability may reach "
        f"{max_rain_probability}% in the next few hours."
    )

    advice.append(
        "☂️ **Umbrella:** Carry one before leaving."
    )

elif max_rain_probability >= 40:

    advice.append(
        f"🌦️ **Possible rain:** "
        f"Rain probability may reach "
        f"{max_rain_probability}%."
    )

# ------------------------------------------------------------
# WIND
# ------------------------------------------------------------

if wind >= 50:

    risk_level = "danger"

    advice.append(
        "💨 **Strong wind:** Avoid unnecessary outdoor activity."
    )

    advice.append(
        "🏍️ **Travel:** Two-wheeler users should use extra caution."
    )

elif wind >= 30:

    if risk_level == "good":
        risk_level = "warning"

    advice.append(
        "💨 **Wind:** Moderate to strong wind. Be careful outdoors."
    )

# ------------------------------------------------------------
# GENERAL ADVICE
# ------------------------------------------------------------

if risk_level == "good":

    status_text = "🟢 GOOD TO GO"

    st.markdown(
        '<div class="good">'
        '<h3>🟢 Good Conditions</h3>'
        'You can generally go outside. '
        'Normal precautions are enough.'
        '</div>',
        unsafe_allow_html=True
    )

elif risk_level == "warning":

    status_text = "🟡 GO WITH CAUTION"

    st.markdown(
        '<div class="warning">'
        '<h3>🟡 Caution Recommended</h3>'
        'You can go outside, but take the precautions below.'
        '</div>',
        unsafe_allow_html=True
    )

else:

    status_text = "🔴 AVOID / TAKE EXTRA CARE"

    st.markdown(
        '<div class="danger">'
        '<h3>🔴 Conditions Need Attention</h3>'
        'Consider delaying unnecessary outdoor activities '
        'and follow local safety guidance.'
        '</div>',
        unsafe_allow_html=True
    )

st.write("")

for item in advice:

    st.markdown(
        f"""
        <div class="advice">
        {item}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

# ============================================================
# ACTIVITY SELECTOR
# ============================================================

st.subheader("🏃 What are you planning to do?")

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
        "🌳 Outdoor event"
    ]
)

# ============================================================
# ACTIVITY ADVICE
# ============================================================

st.subheader("🤖 Activity Recommendation")

activity_advice = ""

if activity == "🏃 Running":

    if temperature >= 35 or feels_like >= 38:

        activity_advice = (
            "🔴 Running is not recommended right now. "
            "Try early morning or evening when temperatures are lower."
        )

    elif rain > 0 or max_rain_probability >= 70:

        activity_advice = (
            "🌧️ Consider postponing your run because rain is likely."
        )

    elif uv_index >= 8:

        activity_advice = (
            "☀️ UV is very high. Run during a cooler time "
            "and use proper sun protection."
        )

    else:

        activity_advice = (
            "🟢 Good conditions for running."
        )

elif activity == "🚶 Walking":

    if temperature >= 38:

        activity_advice = (
            "🟡 Walking is possible, but choose a cooler time "
            "and carry water."
        )

    else:

        activity_advice = (
            "🟢 Good conditions for walking."
        )

elif activity == "🏏 Playing sports":

    if temperature >= 35:

        activity_advice = (
            "🟡 Heat may make outdoor sports uncomfortable. "
            "Prefer morning/evening and stay hydrated."
        )

    elif max_rain_probability >= 70:

        activity_advice = (
            "🌧️ Rain may interrupt outdoor sports. "
            "Consider postponing."
        )

    else:

        activity_advice = (
            "🟢 Conditions are generally suitable for outdoor sports."
        )

elif activity == "🚗 Travelling":

    if max_rain_probability >= 70 or wind >= 50:

        activity_advice = (
            "🟡 Travel with extra caution because weather conditions "
            "may affect the journey."
        )

    else:

        activity_advice = (
            "🟢 No major weather-related concern detected."
        )

elif activity in [
    "🏫 Going to college",
    "💼 Going to work",
    "🛍️ Shopping"
]:

    if max_rain_probability >= 70:

        activity_advice = (
            "☂️ Carry an umbrella before leaving."
        )

    elif temperature >= 38:

        activity_advice = (
            "☀️ It's hot. Use sunscreen, carry water "
            "and avoid unnecessary exposure."
        )

    else:

        activity_advice = (
            "🟢 Conditions are generally comfortable."
        )

elif activity == "🌳 Outdoor event":

    if temperature >= 38:

        activity_advice = (
            "🟡 Consider moving the event to a cooler time."
        )

    elif max_rain_probability >= 70:

        activity_advice = (
            "🌧️ Rain may affect the event. "
            "Have an indoor backup plan."
        )

    else:

        activity_advice = (
            "🟢 Conditions look suitable for an outdoor event."
        )

else:

    activity_advice = (
        "🟢 You can generally go outside with normal precautions."
    )


st.markdown(
    f"""
    <div class="advice">
    <h3>{activity}</h3>
    {activity_advice}
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# PERSONAL CHECKLIST
# ============================================================

st.subheader("🎒 What should you take?")

checklist = []

if temperature >= 35 or uv_index >= 6:

    checklist.append("🧴 Sunscreen")

if temperature >= 35:

    checklist.append("💧 Water bottle")

if temperature >= 32 or uv_index >= 6:

    checklist.append("🧢 Cap / Hat")

if uv_index >= 6:

    checklist.append("🕶️ Sunglasses")

if max_rain_probability >= 50 or rain > 0:

    checklist.append("☂️ Umbrella")

if temperature <= 18:

    checklist.append("🧥 Jacket")

if not checklist:

    checklist.append("🎒 No special weather equipment needed.")

for item in checklist:

    st.write(f"• {item}")

# ============================================================
# BEST TIME TO GO OUT
# ============================================================

st.subheader("⏰ Best Time to Go Outside")

hourly_temp = hourly["temperature_2m"]
hourly_uv = hourly["uv_index"]
hourly_rain = hourly["precipitation_probability"]

scores = []

for i in range(min(
    24,
    len(hourly_temp)
)):

    score = 0

    temp = hourly_temp[i]
    uv = hourly_uv[i]
    rain_probability = hourly_rain[i]

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


if scores:

    best_index = scores.index(
        max(scores)
    )

    hourly_time = hourly["time"][best_index]

    try:

        best_time = datetime.fromisoformat(
            hourly_time
        ).strftime("%I:%M %p")

    except Exception:

        best_time = hourly_time

    st.success(
        f"🟢 Recommended time: **{best_time}**"
    )

# ============================================================
# DAILY PLAN
# ============================================================

st.subheader("📅 Your Weather Plan")

daily = weather["daily"]

today_max = daily["temperature_2m_max"][0]
today_min = daily["temperature_2m_min"][0]
today_rain = daily["precipitation_probability_max"][0]
today_uv = daily["uv_index_max"][0]

st.markdown(
    f"""
    <div class="card">

    <h3>Today's Plan</h3>

    🌡️ Temperature:
    {today_min}°C – {today_max}°C

    <br><br>

    🌧️ Maximum rain probability:
    {today_rain}%

    <br><br>

    ☀️ Maximum UV:
    {today_uv}

    <br><br>

    🤖 Recommendation:

    """

    +

    (
        "🧴 Use sunscreen and avoid long afternoon exposure."
        if today_uv >= 8
        else
        "☀️ Normal sun protection is recommended."
    )

    +

    """

    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 7 DAY FORECAST
# ============================================================

st.subheader("📅 7-Day Forecast")

forecast_cols = st.columns(7)

for i in range(7):

    with forecast_cols[i]:

        day = daily["time"][i]

        try:

            day_name = datetime.fromisoformat(
                day
            ).strftime("%a")

        except Exception:

            day_name = day

        code = daily["weather_code"][i]

        max_temp = daily["temperature_2m_max"][i]
        min_temp = daily["temperature_2m_min"][i]

        rain_chance = daily[
            "precipitation_probability_max"
        ][i]

        st.markdown(
            f"""
            <div class="card">

            <b>{day_name}</b>

            <br><br>

            {weather_description(code)}

            <br><br>

            🌡️ {min_temp}°C – {max_temp}°C

            <br>

            🌧️ {rain_chance}%

            </div>
            """,
            unsafe_allow_html=True
        )

# ============================================================
# FINAL SUMMARY
# ============================================================

st.subheader("🤖 AI Summary")

summary = []

if temperature >= 38:

    summary.append(
        "☀️ It is hot, so protect yourself from heat."
    )

if uv_index >= 6:

    summary.append(
        "🧴 UV is high, so sunscreen and sun protection are recommended."
    )

if max_rain_probability >= 70:

    summary.append(
        "☂️ Rain is likely, so carry an umbrella."
    )

if wind >= 40:

    summary.append(
        "💨 Wind is strong, so take care outdoors."
    )

if not summary:

    summary.append(
        "🟢 Weather conditions look generally comfortable."
    )

for item in summary:

    st.info(item)

st.divider()

st.caption(
    "🌦️ AI Personal Weather Advisor | "
    "Weather data powered by Open-Meteo"
)