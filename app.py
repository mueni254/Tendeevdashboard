import streamlit as st
import requests
import joblib
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import sqlite3
import hashlib

# ---------------------------
# Load model
# ---------------------------
model = None
try:
    model = joblib.load("ev_range_model.pkl")
except Exception as e:
    st.warning(f"Failed to load range estimation model: {e}")

# ---------------------------
# Utility: Secrets loader
# ---------------------------
def get_secret(section, key, default=None):
    try:
        return st.secrets[section][key]
    except Exception:
        return default

# ---------------------------
# Predict Range
# ---------------------------
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
# Weather Fetcher
# ---------------------------
def fetch_weather(city="Nairobi"):
    api_key = get_secret("openweather", "api_key")
    if not api_key:
        return {"temperature_C": 25, "humidity_percent": 50, "wind_speed_mps": 2}
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        return {
            "temperature_C": data["main"]["temp"],
            "humidity_percent": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"],
        }
    except Exception:
        return {"temperature_C": 25, "humidity_percent": 50, "wind_speed_mps": 2}

# ---------------------------
# Geocoding
# ---------------------------
def geocode_location(place_name):
    mapbox_key = st.secrets["mapbox"]["api_key"]
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json".format(place_name)
    params = {
        "access_token": mapbox_key,
        "limit": 1,
        "country": "KE"  # restrict to Kenya for more accurate results
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data["features"]:
            coords = data["features"][0]["center"]
            lon, lat = coords[0], coords[1]
            return lat, lon
        else:
            st.warning("No results found for that location.")
            return None, None
    except Exception as e:
        st.error(f"Geocoding failed: {e}")
        return None, None


# ---------------------------
# Charging Station Lookup
# ---------------------------
def get_nearest_stations(lat, lon):
    api_key = get_secret("open_charge_map", "api_key")
    if not api_key:
        return []

    base_url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "countrycode": "KE",
        "latitude": lat,
        "longitude": lon,
        "maxresults": 10,
        "compact": "true"
    }
    headers = {"X-API-Key": api_key}

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=7)
        data = response.json()

        if not data:
            params.pop("countrycode", None)
            response = requests.get(base_url, params=params, headers=headers, timeout=7)
            data = response.json()

        if not data:
            return []

        stations = []
        for station in data:
            info = station.get("AddressInfo", {})
            title = info.get("Title", "Unnamed")
            slat = info.get("Latitude")
            slon = info.get("Longitude")
            if slat is None or slon is None:
                continue
            distance = geodesic((lat, lon), (slat, slon)).km
            num_points = station.get("NumberOfPoints")
            conns = station.get("Connections", [])
            if num_points is None:
                num_points = len(conns) if isinstance(conns, list) else None
            stations.append({
                "name": title,
                "lat": slat,
                "lon": slon,
                "distance": distance,
                "number_of_points": num_points
            })
        return sorted(stations, key=lambda x: x["distance"])[:5]
    except Exception:
        return []

# ---------------------------
# Authentication
# ---------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)''')
conn.commit()

def hash_password(password):
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
# Streamlit App
# ---------------------------
def main():
    st.set_page_config("EV Smart Dashboard", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #0f9d58;'>\U0001F30D TWENDE EV: Your Smart Electric Journey Starts Here!</h1>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            st.header("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
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
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Register"):
                if register_user(new_user, new_pass):
                    st.success("Registered! Please login.")
                else:
                    st.error("Registration failed (username may exist).")
        return

    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Welcome", "Range Estimator", "Charging Stations", "Logout"])

    if page == "Welcome":
        st.title("Welcome to EV Smart Dashboard 🚗🔋")
        st.write(f"Logged in as: **{st.session_state.username}**")

    elif page == "Range Estimator":
        st.title("🔋 Estimate Your EV Range")
        with st.form("range_form"):
            st.subheader("Vehicle & Environment")
            vehicle_type = st.selectbox("Vehicle Type", ["motorbike", "truck", "car", "bus"])
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
                    "wind_speed_mps": weather["wind_speed_mps"]
                }
                estimated_km = predict_range(input_data)
                if estimated_km:
                    st.success(f"🔋 Estimated Range: **{estimated_km} km**")

    elif page == "Charging Stations":
        st.title("📍 Locate Nearby Charging Stations")
        city = st.text_input("Enter location", "Nairobi")
        if st.button("Find Stations"):
            lat, lon = geocode_location(city)
            if lat is None:
                st.error("Could not locate that place.")
            else:
                stations = get_nearest_stations(lat, lon)
                if not stations:
                    st.warning("No stations found. Try a nearby city.")
                else:
                    st.subheader("Nearest Stations")
                    for i, s in enumerate(stations, start=1):
                        count_str = f"{s['number_of_points']} point(s)" if s['number_of_points'] else "Unknown points"
                        st.markdown(f"{i}. **{s['name']}** — {s['distance']:.2f} km away — {count_str}")

    elif page == "Logout":
        st.session_state.logged_in = False
        st.success("Logged out.")
        st.experimental_rerun()

if __name__ == "__main__":
    main()




