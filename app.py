import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Weather Agent",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# PROFESSIONAL LIGHT THEME
# BLACK TEXT
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

/* Main application background */
.stApp {
    background-color: #F5F7FB !important;
}

/* Normal text */
.stMarkdown p {
    color: #000000 !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #000000 !important;
}

/* Main title */
.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    color: #000000 !important;
    margin-bottom: 5px;
}

/* Subtitle */
.subtitle {
    text-align: center;
    font-size: 17px;
    color: #333333 !important;
    margin-bottom: 30px;
}

/* Cards */
.card {
    background-color: #FFFFFF !important;
    border-radius: 18px;
    padding: 22px;
    margin: 10px 0;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    color: #000000 !important;
}

.card * {
    color: #000000 !important;
}

/* AI advice */
.advice {
    background-color: #EAF4FF !important;
    border-left: 6px solid #2563EB;
    border-radius: 14px;
    padding: 20px;
    margin: 12px 0;
    color: #000000 !important;
}

.advice * {
    color: #000000 !important;
}

/* Good */
.good {
    background-color: #E9F8EF !important;
    border-left: 6px solid #16A34A;
    border-radius: 14px;
    padding: 18px;
    color: #000000 !important;
}

.good * {
    color: #000000 !important;
}

/* Warning */
.warning {
    background-color: #FFF8DD !important;
    border-left: 6px solid #EAB308;
    border-radius: 14px;
    padding: 18px;
    color: #000000 !important;
}

.warning * {
    color: #000000 !important;
}

/* Danger */
.danger {
    background-color: #FFECEC !important;
    border-left: 6px solid #DC2626;
    border-radius: 14px;
    padding: 18px;
    color: #000000 !important;
}

.danger * {
    color: #000000 !important;
}

/* Section titles */
.section-title {
    color: #000000 !important;
    font-size: 27px;
    font-weight: 750;
    margin-top: 25px;
    margin-bottom: 12px;
}

/* Small labels */
.small-label {
    color: #333333 !important;
    font-size: 14px;
}

/* Metric boxes */
.metric-box {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}

.metric-title {
    color: #333333 !important;
    font-size: 14px;
    font-weight: 600;
}

.metric-value {
    color: #000000 !important;
    font-size: 26px;
    font-weight: 800;
}

/* Weather description */
.weather-description {
    color: #000000 !important;
    font-size: 18px;
    font-weight: 600;
}

/* Location box */
.location-box {
    background: #FFFFFF !important;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}

.location-box * {
    color: #000000 !important;
}

/* Streamlit labels */
[data-testid="stWidgetLabel"] p {
    color: #000000 !important;
    font-weight: 600 !important;
}

/* Text inputs */
div[data-baseweb="input"] {
    background-color: #FFFFFF !important;
}

div[data-baseweb="input"] input {
    color: #000000 !important;
    background-color: #FFFFFF !important;
}

/* Selectbox */
div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
}

div[data-baseweb="select"] * {
    color: #000000 !important;
}

/* Buttons */
.stButton button {
    color: #000000 !important;
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

.stButton button:hover {
    border-color: #2563EB !important;
    color: #000000 !important;
}

/* Success / info messages */
[data-testid="stAlert"] {
    color: #000000 !important;
}

[data-testid="stAlert"] * {
    color: #000000 !important;
}

/* Dataframe text */
[data-testid="stDataFrame"] {
    color: #000000 !important;
}

/* Footer */
.footer {
    text-align: center;
    color: #333333 !important;
    font-size: 13px;
    margin-top: 40px;
    padding: 20px;
}

/* Divider */
hr {
    border-color: #D1D5DB !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🌤️ AI Weather Agent</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Smart weather analysis with personalized outdoor recommendations'
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

if "city" not in st.session_state:
    st.session_state.city = DEFAULT_CITY


# ============================================================
# WEATHER FUNCTION
# ============================================================

def get_weather(lat, lon):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "uv_index"
        ),
        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "precipitation,"
            "uv_index,"
            "wind_speed_10m"
        ),
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "uv_index_max"
        ),
        "timezone": "auto",
        "forecast_days": 7
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            return response.json()

    except Exception:
        return None

    return None


# ============================================================
# WEATHER DESCRIPTION
# ============================================================

def weather_description(code):

    weather_codes = {

        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",

        45: "Fog 🌫️",
        48: "Depositing rime fog 🌫️",

        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌦️",
        55: "Dense drizzle 🌧️",

        56: "Light freezing drizzle 🧊",
        57: "Dense freezing drizzle 🧊",

        61: "Slight rain 🌦️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain 🌧️",

        66: "Light freezing rain 🧊",
        67: "Heavy freezing rain 🧊",

        71: "Slight snow ❄️",
        73: "Moderate snow ❄️",
        75: "Heavy snow ❄️",

        77: "Snow grains ❄️",

        80: "Slight rain showers 🌦️",
        81: "Moderate rain showers 🌧️",
        82: "Violent rain showers ⛈️",

        85: "Slight snow showers ❄️",
        86: "Heavy snow showers ❄️",

        95: "Thunderstorm ⛈️",
        96: "Thunderstorm with hail ⛈️",
        99: "Severe thunderstorm with hail ⛈️"
    }

    return weather_codes.get(code, "Unknown weather")


# ============================================================
# REVERSE GEOCODING
# ============================================================

def reverse_geocode(lat, lon):

    url = "https://geocoding-api.open-meteo.com/v1/reverse"

    params = {
        "latitude": lat,
        "longitude": lon,
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

        if response.status_code == 200:

            data = response.json()

            if data.get("results"):

                result = data["results"][0]

                city = result.get("name", "Your Location")
                country = result.get("country", "")

                return f"{city}, {country}"

    except Exception:
        pass

    return "Your Location"


# ============================================================
# SEARCH LOCATION
# ============================================================

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

        if response.status_code == 200:

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

st.markdown(
    '<div class="section-title">📍 Your Location</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="location-box">',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])

with col1:

    if st.button(
        "📍 Use My Live Location",
        use_container_width=True
    ):

        location = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    p => resolve({
                        latitude: p.coords.latitude,
                        longitude: p.coords.longitude
                    }),
                    e => resolve(null)
                );
            })
            """,
            key="get_location"
        )

        if location:

            try:

                lat = float(location["latitude"])
                lon = float(location["longitude"])

                st.session_state.latitude = lat
                st.session_state.longitude = lon

                st.session_state.city = reverse_geocode(
                    lat,
                    lon
                )

                st.success(
                    f"Live location detected: {st.session_state.city}"
                )

                st.rerun()

            except Exception:
                st.error("Unable to read your location.")

        else:

            st.warning(
                "Please allow location permission in your browser."
            )


with col2:

    search_city = st.text_input(
        "Search any city",
        placeholder="Example: Hyderabad, Mumbai, Chennai"
    )

    if st.button(
        "🔎 Search City",
        use_container_width=True
    ):

        if search_city.strip():

            result = search_location(
                search_city.strip()
            )

            if result:

                lat, lon, city, country = result

                st.session_state.latitude = lat
                st.session_state.longitude = lon

                st.session_state.city = (
                    f"{city}, {country}"
                )

                st.success(
                    f"Location changed to {city}, {country}"
                )

                st.rerun()

            else:

                st.error(
                    "City not found. Please try another city."
                )

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# GET WEATHER
# ============================================================

weather = get_weather(
    st.session_state.latitude,
    st.session_state.longitude
)

if weather is None:

    st.error(
        "Unable to get weather data. Please try again."
    )

    st.stop()


current = weather["current"]


# ============================================================
# CURRENT WEATHER
# ============================================================

st.markdown(
    '<div class="section-title">🌡️ Current Weather</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="card">

        <h2 style="color:#000000;">
            {st.session_state.city}
        </h2>

        <p class="weather-description">
            {weather_description(current["weather_code"])}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# WEATHER METRICS
# ============================================================

cols = st.columns(4)

metrics = [

    (
        "🌡️ Temperature",
        f'{current["temperature_2m"]} °C'
    ),

    (
        "🤗 Feels Like",
        f'{current["apparent_temperature"]} °C'
    ),

    (
        "💧 Humidity",
        f'{current["relative_humidity_2m"]}%'
    ),

    (
        "💨 Wind",
        f'{current["wind_speed_10m"]} km/h'
    ),

    (
        "🌧️ Rain",
        f'{current["rain"]} mm'
    ),

    (
        "☔ Precipitation",
        f'{current["precipitation"]} mm'
    ),

    (
        "💨 Gusts",
        f'{current["wind_gusts_10m"]} km/h'
    ),

    (
        "☀️ UV Index",
        f'{current["uv_index"]}'
    )
]


for i, (title, value) in enumerate(metrics):

    with cols[i % 4]:

        st.markdown(
            f"""
            <div class="metric-box">

                <div class="metric-title">
                    {title}
                </div>

                <div class="metric-value">
                    {value}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# WORLD MAP
# ============================================================

st.markdown(
    '<div class="section-title">🌍 Your Location on World Map</div>',
    unsafe_allow_html=True
)

map_obj = folium.Map(
    location=[
        st.session_state.latitude,
        st.session_state.longitude
    ],
    zoom_start=5,
    control_scale=True
)

folium.Marker(
    [
        st.session_state.latitude,
        st.session_state.longitude
    ],
    popup=st.session_state.city,
    tooltip="You are here 📍",
    icon=folium.Icon(
        color="red",
        icon="info-sign"
    )
).add_to(map_obj)

st_folium(
    map_obj,
    width=None,
    height=450,
    returned_objects=[]
)


# ============================================================
# AI WEATHER ADVICE
# ============================================================

temperature = current["temperature_2m"]
feels_like = current["apparent_temperature"]
humidity = current["relative_humidity_2m"]
wind = current["wind_speed_10m"]
rain = current["rain"]
uv = current["uv_index"]


hourly = weather["hourly"]

rain_probabilities = hourly.get(
    "precipitation_probability",
    []
)

max_rain_probability = max(
    rain_probabilities[:24]
) if rain_probabilities else 0


# ============================================================
# RISK ENGINE
# ============================================================

if temperature >= 40 or uv >= 9:

    risk = "danger"

    risk_title = "High Outdoor Risk ⚠️"

    risk_message = (
        "The weather is very hot or UV exposure is high. "
        "Avoid long outdoor activities during peak afternoon hours."
    )

elif (
    temperature >= 34
    or uv >= 7
    or max_rain_probability >= 60
    or wind >= 35
):

    risk = "warning"

    risk_title = "Moderate Outdoor Risk ⚠️"

    risk_message = (
        "Outdoor activity is possible, but some precautions "
        "are recommended."
    )

else:

    risk = "good"

    risk_title = "Good Outdoor Conditions ✅"

    risk_message = (
        "Current weather conditions are generally suitable "
        "for outdoor activities."
    )


# ============================================================
# AI PERSONAL ADVICE
# ============================================================

st.markdown(
    '<div class="section-title">🤖 AI Personal Advice</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="advice">

        <h3 style="color:#000000;">
            🤖 AI Weather Agent
        </h3>

        <p>
            Based on the current weather in
            <b>{st.session_state.city}</b>:
        </p>

        <p>
            <b>{risk_title}</b>
        </p>

        <p>
            {risk_message}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# EXTRA WEATHER ADVICE
# ============================================================

advice = []

if temperature >= 35:

    advice.append(
        "🔥 It is hot outside. Drink enough water and avoid unnecessary exposure."
    )

elif temperature <= 15:

    advice.append(
        "🧥 The temperature is relatively cool. Consider carrying a jacket."
    )

else:

    advice.append(
        "🌤️ Temperature is reasonably comfortable for outdoor activity."
    )


if uv >= 7:

    advice.append(
        "☀️ UV is high. Use sunscreen, sunglasses and a cap."
    )

elif uv >= 4:

    advice.append(
        "☀️ UV is moderate. Sunscreen is recommended for longer outdoor exposure."
    )


if rain > 0:

    advice.append(
        "🌧️ Rain is currently occurring. Carry an umbrella or rain protection."
    )

elif max_rain_probability >= 60:

    advice.append(
        "☔ There is a significant chance of rain today. Carry an umbrella."
    )


if wind >= 35:

    advice.append(
        "💨 Strong winds are possible. Be careful around trees and open areas."
    )


for item in advice:

    st.markdown(
        f"""
        <div class="card">
            <p>{item}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ACTIVITY SELECTOR
# ============================================================

st.markdown(
    '<div class="section-title">🏃 What are you planning to do?</div>',
    unsafe_allow_html=True
)

activity = st.selectbox(
    "Select your activity",
    [
        "Just going outside",
        "Walking",
        "Running",
        "Sports",
        "Travelling",
        "College",
        "Work",
        "Shopping",
        "Outdoor Event"
    ]
)


# ============================================================
# ACTIVITY RECOMMENDATION
# ============================================================

def activity_recommendation(activity):

    if activity == "Running":

        if temperature >= 35 or uv >= 7:

            return (
                "🏃 Avoid running during peak afternoon heat. "
                "Early morning or evening is better."
            )

        return (
            "🏃 Running is generally suitable. "
            "Carry water and stay hydrated."
        )


    if activity == "Walking":

        return (
            "🚶 Walking is possible. "
            "Choose a cooler time if the temperature is high."
        )


    if activity == "Sports":

        if temperature >= 35:

            return (
                "🏅 Outdoor sports may be uncomfortable in the heat. "
                "Prefer morning or evening."
            )

        return (
            "🏅 Sports are possible. Stay hydrated and monitor UV exposure."
        )


    if activity == "Travelling":

        if max_rain_probability >= 60:

            return (
                "🚗 Rain is possible. Keep an umbrella and allow extra travel time."
            )

        return (
            "🚗 Travel conditions look generally manageable."
        )


    if activity == "College":

        return (
            "🎓 College travel looks manageable. "
            "Carry water and weather protection if needed."
        )


    if activity == "Work":

        return (
            "💼 Work-related outdoor travel looks manageable. "
            "Check rain conditions before leaving."
        )


    if activity == "Shopping":

        return (
            "🛍️ Shopping is possible. "
            "Carry an umbrella if rain probability is high."
        )


    if activity == "Outdoor Event":

        if rain > 0 or max_rain_probability >= 60:

            return (
                "🎉 Outdoor event conditions may be affected by rain. "
                "Have a backup indoor option."
            )

        return (
            "🎉 Outdoor event conditions look reasonable."
        )


    return (
        "🌤️ Going outside is generally okay with normal precautions."
    )


st.markdown(
    f"""
    <div class="advice">

        <h3>🎯 Activity Recommendation</h3>

        <p>
            <b>{activity}</b>
        </p>

        <p>
            {activity_recommendation(activity)}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PERSONAL CHECKLIST
# ============================================================

st.markdown(
    '<div class="section-title">🎒 Personal Checklist</div>',
    unsafe_allow_html=True
)

checklist = []

if temperature >= 30:
    checklist.append("💧 Carry water")

if uv >= 4:
    checklist.append("🧴 Use sunscreen")

if uv >= 6:
    checklist.append("🧢 Carry a cap / hat")

if uv >= 6:
    checklist.append("🕶️ Wear sunglasses")

if rain > 0 or max_rain_probability >= 50:
    checklist.append("☔ Carry an umbrella")

if temperature <= 18:
    checklist.append("🧥 Carry a jacket")

if wind >= 35:
    checklist.append("💨 Be careful in strong winds")


if checklist:

    for item in checklist:

        st.markdown(
            f"""
            <div class="card">
                <p>☑️ {item}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:

    st.markdown(
        """
        <div class="good">
            <b>✅ No special weather precautions are currently required.</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# BEST TIME TO GO OUT
# ============================================================

st.markdown(
    '<div class="section-title">⏰ Best Time to Go Outside</div>',
    unsafe_allow_html=True
)

times = weather["hourly"]["time"]
temps = weather["hourly"]["temperature_2m"]
uv_values = weather["hourly"]["uv_index"]
rain_probs = weather["hourly"]["precipitation_probability"]

best_time = None
best_score = float("inf")

current_date = datetime.now().strftime("%Y-%m-%d")


for i in range(min(24, len(times))):

    if not times[i].startswith(current_date):
        continue

    temp = temps[i]
    uv_value = uv_values[i]
    rain_prob = rain_probs[i]

    score = (
        abs(temp - 25)
        + uv_value * 2
        + rain_prob * 0.08
    )

    if score < best_score:

        best_score = score
        best_time = times[i]


if best_time:

    formatted_time = best_time.replace(
        "T",
        " "
    )

    st.markdown(
        f"""
        <div class="good">

            <h3>🌤️ Recommended Time</h3>

            <p>
                Around <b>{formatted_time}</b>
            </p>

            <p>
                This period has a relatively better balance
                of temperature, UV and rain probability.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DAILY PLAN
# ============================================================

st.markdown(
    '<div class="section-title">📅 Today's AI Plan</div>',
    unsafe_allow_html=True
)

if temperature >= 35:

    plan = """
    🌅 Morning: Best time for outdoor activity.<br>
    ☀️ Afternoon: Avoid unnecessary outdoor exposure.<br>
    🌆 Evening: Better for walking and outdoor activities.
    """

elif rain > 0 or max_rain_probability >= 60:

    plan = """
    🌅 Morning: Check rain conditions before leaving.<br>
    ☔ Afternoon: Keep an umbrella ready.<br>
    🌆 Evening: Recheck weather before outdoor plans.
    """

else:

    plan = """
    🌅 Morning: Good for outdoor activity.<br>
    ☀️ Afternoon: Normal precautions are enough.<br>
    🌆 Evening: Good for walking and outdoor activities.
    """


st.markdown(
    f"""
    <div class="card">

        <h3>🧠 AI Daily Schedule</h3>

        <p>
            {plan}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 7-DAY FORECAST
# ============================================================

st.markdown(
    '<div class="section-title">📊 7-Day Forecast</div>',
    unsafe_allow_html=True
)

daily = weather["daily"]

forecast_cols = st.columns(7)

for i in range(7):

    date = daily["time"][i]

    max_temp = daily["temperature_2m_max"][i]

    min_temp = daily["temperature_2m_min"][i]

    rain_chance = daily[
        "precipitation_probability_max"
    ][i]

    uv_max = daily["uv_index_max"][i]

    code = daily["weather_code"][i]

    short_date = date[5:]

    with forecast_cols[i]:

        st.markdown(
            f"""
            <div class="card"
                 style="text-align:center;">

                <b>{short_date}</b>

                <p style="font-size:26px;">
                    {weather_description(code).split()[0]}
                </p>

                <p>
                    🌡️ <b>{max_temp}°</b>
                    / {min_temp}°
                </p>

                <p>
                    ☔ {rain_chance}%
                </p>

                <p>
                    ☀️ UV {uv_max}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# FINAL AI SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">🧠 AI Summary</div>',
    unsafe_allow_html=True
)


summary_parts = []

if temperature >= 35:

    summary_parts.append(
        "The main concern is high temperature."
    )

elif temperature <= 15:

    summary_parts.append(
        "The main concern is cooler conditions."
    )

else:

    summary_parts.append(
        "Temperature conditions are generally comfortable."
    )


if uv >= 7:

    summary_parts.append(
        "UV exposure is high."
    )


if rain > 0:

    summary_parts.append(
        "Rain is currently present."
    )

elif max_rain_probability >= 60:

    summary_parts.append(
        "There is a high chance of rain."
    )


if wind >= 35:

    summary_parts.append(
        "Strong winds may affect outdoor activities."
    )


final_summary = " ".join(summary_parts)


st.markdown(
    f"""
    <div class="advice">

        <h3>🤖 Final Recommendation</h3>

        <p>
            {final_summary}
        </p>

        <p>
            <b>
            For your selected activity:
            {activity}
            </b>
        </p>

        <p>
            {activity_recommendation(activity)}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        🌤️ AI Weather Agent<br><br>

        Weather data powered by Open-Meteo

    </div>
    """,
    unsafe_allow_html=True
)
