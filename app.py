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
import os

# Load model
model = joblib.load("ev_range_model.pkl")

# Auth DB setup
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
conn.commit()

# Utility: hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Utility: verify login
def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?',
              (username, hash_password(password)))
    return c.fetchone()

# Utility: register user
def register_user(username, password):
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
              (username, hash_password(password)))
    conn.commit()

# Fetch weather
def fetch_weather(city="Nairobi"):
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        return {
            "temperature_C": data["main"]["temp"],
            "humidity_percent": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"]
        }
    except:
        return {"temperature_C": 25, "humidity_percent": 50, "wind_speed_mps": 2}

# Predict EV range
def predict_range(inputs):
    df = pd.DataFrame([inputs])  # <-- FIXED: wrap input in DataFrame
    prediction = model.predict(df)
    return round(prediction[0], 2)

# Charging station lookup
def get_nearest_stations(lat, lon):
    api_url = f"https://api.openchargemap.io/v3/poi/?output=json&countrycode=KE&latitude={lat}&longitude={lon}&maxresults=10&compact=true"
    headers = {'X-API-Key': st.secrets["OPENCHARGEMAP_API_KEY"]}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        stations = []
        for station in data:
            try:
                title = station["AddressInfo"]["Title"]
                slat = station["AddressInfo"]["Latitude"]
                slon = station["AddressInfo"]["Longitude"]
                distance = geodesic((lat, lon), (slat, slon)).km
                stations.append({
                    "name": title,
                    "lat": slat,
                    "lon": slon,
                    "distance": distance
                })
            except:
                continue
        sorted_stations = sorted(stations, key=lambda x: x["distance"])
        return sorted_stations[:5]
    except:
        return []

# Geocode city to lat/lon
def geocode_location(city):
    geolocator = Nominatim(user_agent="ev_dashboard")
    location = geolocator.geocode(city)
    if location:
        return location.latitude, location.longitude
    return None, None

# App UI
def main():
    st.set_page_config("EV Smart Dashboard", layout="wide")
    st.markdown("<h1 style='text-align: center; color: green;'>🌍 TWENDE EV: Your Smart Electric Journey Starts Here!</h1>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Login/Register Page
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
                    st.error("Invalid login.")
        with tab2:
            st.header("Register")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.button("Register"):
                register_user(new_user, new_pass)
                st.success("Registered! Please login.")
        return

    # Logged-in view
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Welcome", "Range Estimator", "Charging Stations", "Chatbot", "Logout"])

    if page == "Welcome":
        st.title("Welcome to EV Smart Dashboard 🚗🔋")
        st.write(f"Logged in as: {st.session_state.username}")

    elif page == "Range Estimator":
        st.title("🔋 Estimate Your EV Range")
        with st.form("vehicle_form"):
            st.subheader("Enter Your Vehicle Details:")
            vehicle_cc = st.slider("Engine Size (cc)", 800, 3000, 1500)
            battery_years = st.slider("Battery Age (years)", 0, 10, 2)
            battery_volts = st.slider("Battery Voltage (V)", 200, 800, 400)
            battery_percent = st.slider("Battery Charge (%)", 0, 100, 80)
            city = st.text_input("City for Weather Data", "Nairobi")

            submitted = st.form_submit_button("Estimate Range")

            if submitted:
                weather = fetch_weather(city)
                input_data = {
                    'vehicle_cc': vehicle_cc,
                    'battery_years': battery_years,
                    'battery_volts': battery_volts,
                    'battery_percent': battery_percent,
                    'temperature_C': weather["temperature_C"],
                    'humidity_percent': weather["humidity_percent"],
                    'wind_speed_mps': weather["wind_speed_mps"]
                }
                estimated_km = predict_range(input_data)
                st.success(f"🔋 Estimated Range: {estimated_km} km")

    elif page == "Charging Stations":
        st.title("📍 Locate Nearby Charging Stations")
        city = st.text_input("Enter your location (e.g. Nairobi, Kisumu)", "Nairobi")
        if st.button("Find Stations"):
            lat, lon = geocode_location(city)
            if lat is None:
                st.error("Could not locate that place.")
            else:
                nearest = get_nearest_stations(lat, lon)
                if not nearest:
                    st.warning("No stations found.")
                else:
                    m = folium.Map(location=[lat, lon], zoom_start=12)
                    folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color='green')).add_to(m)
                    for s in nearest:
                        folium.Marker([s["lat"], s["lon"]],
                                      tooltip=f'{s["name"]} ({s["distance"]:.2f} km)',
                                      icon=folium.Icon(color='blue')).add_to(m)
                    st_folium(m, width=700)

    elif page == "Chatbot":
        st.title("💬 EV Assistant")
        st.write("Ask me anything about electric vehicles!")
        prompt = st.text_input("You:", key="chat_input")
        if st.button("Send"):
            if prompt:
                response = chatbot_response(prompt)
                st.markdown(f"**Bot:** {response}")

    elif page == "Logout":
        st.session_state.logged_in = False
        st.success("You have logged out.")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
