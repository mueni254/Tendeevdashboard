import streamlit as st
import requests
import joblib
import folium
import pandas as pd
from streamlit_folium import st_folium
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from chatbot import chatbot_response
import sqlite3
import hashlib

# ---------------------------
# Load model (unchanged)
# ---------------------------
model = None
try:
    model = joblib.load("ev_range_model.pkl")
except Exception as e:
    st.warning(f"Failed to load range estimation model: {e}")

def predict_range(inputs: dict):
    if model is None:
        st.error("Range estimation model not available.")
        return None
    df = pd.DataFrame([inputs])
    try:
        prediction = model.predict(df)
        return round(prediction[0], 2)
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# ---------------------------
# API key resolver (flat or nested)
# ---------------------------
def resolve_api_key(name: str):
    """
    Handles both flat and nested secret formats:
      groq = "..."             (flat)
      [groq]
      api_key = "..."          (nested)
    """
    val = st.secrets.get(name)
    if isinstance(val, dict):
        return val.get("api_key")
    return val  # could be string or None

# ---------------------------
# External data fetchers
# ---------------------------
def fetch_weather(city="Nairobi"):
    # support both flat and nested key names
    api_key = resolve_api_key("openweather") or resolve_api_key("OPENWEATHER_API_KEY")
    if not api_key:
        st.warning("OpenWeather API key missing; using fallback values.")
        return {"temperature_C": 25, "humidity_percent": 50, "wind_speed_mps": 2}
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if response.status_code != 200:
            raise ValueError(data.get("message", "weather API error"))
        return {
            "temperature_C": data["main"]["temp"],
            "humidity_percent": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"],
        }
    except Exception:
        return {"temperature_C": 25, "humidity_percent": 50, "wind_speed_mps": 2}

def get_nearest_stations(lat, lon):
    openchargemap_key = resolve_api_key("open_charge_map") or resolve_api_key("OPENCHARGEMAP_API_KEY")
    if not openchargemap_key:
        st.warning("OpenChargeMap API key missing; cannot search stations.")
        return []
    api_url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "countrycode": "KE",
        "latitude": lat,
        "longitude": lon,
        "maxresults": 10,
        "compact": "true",
    }
    headers = {"X-API-Key": openchargemap_key}
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=7)
        data = response.json()
        stations = []
        for station in data:
            try:
                info = station.get("AddressInfo", {})
                title = info.get("Title", "Unnamed")
                slat = info.get("Latitude")
                slon = info.get("Longitude")
                if slat is None or slon is None:
                    continue
                distance = geodesic((lat, lon), (slat, slon)).km
                number_of_points = station.get("NumberOfPoints")
                connections = station.get("Connections", [])
                if number_of_points is None:
                    number_of_points = len(connections) if isinstance(connections, list) else None
                stations.append({
                    "name": title,
                    "lat": slat,
                    "lon": slon,
                    "distance": distance,
                    "number_of_points": number_of_points,
                    "connections": connections
                })
            except Exception:
                continue
        sorted_stations = sorted(stations, key=lambda x: x["distance"])
        return sorted_stations[:5]
    except Exception:
        return []

def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="ev_dashboard")
        location = geolocator.geocode(place_name, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

# ---------------------------
# Auth setup
# ---------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)''')
conn.commit()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    return c.fetchone()

def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except Exception:
        return False

# ---------------------------
# App UI
# ---------------------------
def main():
    st.set_page_config("EV Smart Dashboard", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #0f9d58;'>🌍 TWENDE EV: Your Smart Electric Journey Starts Here!</h1>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # Debugging secrets (remove once stable)
    st.sidebar.markdown("**Secrets diagnostics**")
    st.sidebar.write("Loaded secret sections:", list(st.secrets.keys()))
    st.sidebar.write("OpenChargeMap resolved:", bool(resolve_api_key("open_charge_map") or resolve_api_key("OPENCHARGEMAP_API_KEY")))
    st.sidebar.write("OpenWeather resolved:", bool(resolve_api_key("openweather") or resolve_api_key("OPENWEATHER_API_KEY")))
    st.sidebar.write("Groq resolved:", bool(resolve_api_key("groq") or resolve_api_key("groq")))  # fallback same

    # Authentication
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Logged in!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials.")
        with tab2:
            st.header("Register")
            new_user = st.text_input("New Username", key="reg_user")
            new_pass = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Register"):
                success = register_user(new_user, new_pass)
                if success:
                    st.success("Registered! Please log in.")
                else:
                    st.error("Registration failed (username may already exist).")
        return

    # Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Welcome", "Range Estimator", "Charging Stations", "Chatbot", "Logout"])

    if page == "Welcome":
        st.title("Welcome to EV Smart Dashboard 🚗🔋")
        st.write(f"Logged in as: **{st.session_state.username}**")
        st.markdown(
            """
            This dashboard helps you:
            - Estimate your EV range using real-time weather and vehicle parameters.
            - Locate nearby charging stations by place name.
            - Ask questions via the EV assistant chatbot.
            """
        )

    elif page == "Range Estimator":
        st.title("🔋 Estimate Your EV Range")
        with st.form("vehicle_form"):
            st.subheader("Enter Vehicle & Environmental Details")
            vehicle_type = st.selectbox(
                "Vehicle Type",
                ["motorbike", "truck", "car", "bus"]  # exactly as in training
            )
            vehicle_cc = st.slider("Engine Size (cc)", 800, 3000, 1500)
            battery_years = st.slider("Battery Age (years)", 0, 10, 2)
            battery_volts = st.slider("Battery Voltage (V)", 200, 800, 400)
            battery_percent = st.slider("Battery Charge (%)", 0, 100, 80)
            city = st.text_input("City for Weather Data", "Nairobi")
            submitted = st.form_submit_button("Estimate Range")

            if submitted:
                weather = fetch_weather(city)
                input_data = {
                    "vehicle_type": vehicle_type,
                    "vehicle_cc": vehicle_cc,
                    "battery_years": battery_years,
                    "battery_volts": battery_volts,
                    "battery_percent": battery_percent,
                    "temperature_C": weather["temperature_C"],
                    "humidity_percent": weather["humidity_percent"],
                    "wind_speed_mps": weather["wind_speed_mps"],
                }
                estimated_km = predict_range(input_data)
                if estimated_km is not None:
                    st.success(f"🔋 Estimated Range: **{estimated_km} km**")
                else:
                    st.error("Could not compute range.")

    elif page == "Charging Stations":
        st.title("📍 Locate Nearby Charging Stations")
        st.write("Search by place name (e.g., Nairobi, Kisumu).")
        with st.form("station_form"):
            city = st.text_input("Enter your location", "Nairobi")
            submitted = st.form_submit_button("Find Stations")

        if submitted:
            lat, lon = geocode_location(city)
            if lat is None or lon is None:
                st.error("Could not geocode that location.")
            else:
                nearest = get_nearest_stations(lat, lon)
                if not nearest:
                    st.warning("No stations found.")
                else:
                    st.subheader("Nearest charging stations")
                    for idx, s in enumerate(nearest, start=1):
                        num_points = s.get("number_of_points", "N/A")
                        if isinstance(num_points, int):
                            point_label = f"{num_points} charging point{'s' if num_points != 1 else ''}"
                        else:
                            point_label = "Charging points: N/A"
                        map_link = (
                            f"https://www.openstreetmap.org/?mlat={s['lat']}&mlon={s['lon']}#map=14/"
                            f"{s['lat']}/{s['lon']}"
                        )
                        st.markdown(
                            f"{idx}. **{s['name']}** — {s['distance']:.2f} km away — {point_label}  "
                            f"[View on map]({map_link})"
                        )

                    with st.expander("Show map"):
                        m = folium.Map(location=[lat, lon], zoom_start=12)
                        folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color="green")).add_to(m)
                        for s in nearest:
                            folium.Marker(
                                [s["lat"], s["lon"]],
                                tooltip=f'{s["name"]} ({s["distance"]:.2f} km)',
                                icon=folium.Icon(color="blue"),
                            ).add_to(m)
                        st_folium(m, width=700)

    elif page == "Chatbot":
        st.title("💬 EV Assistant")
        st.write("Ask me anything about electric vehicles.")
        prompt = st.text_input("You:", key="chat_input")
        groq_key = resolve_api_key("groq")  # safely get groq key (nested or flat)
        if not groq_key:
            st.warning("Groq API key not configured; responses may be limited.")

        if st.button("Send"):
            if prompt:
                # Try passing key if signature allows, else fallback
                try:
                    response = chatbot_response(prompt, groq_key=groq_key)
                except TypeError:
                    response = chatbot_response(prompt)
                st.markdown(f"**Bot:** {response}")

    elif page == "Logout":
        st.session_state.logged_in = False
        st.success("You have logged out.")
        st.experimental_rerun()

def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="ev_dashboard")
        location = geolocator.geocode(place_name, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

if __name__ == "__main__":
    main()



