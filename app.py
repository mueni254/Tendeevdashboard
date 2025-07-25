import streamlit as st
import requests
import math

# Load Mapbox API key
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Helper: Get coordinates for a place name
def get_coordinates(place_name):
    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{place_name}.json"
        params = {
            "access_token": MAPBOX_API_KEY,
            "limit": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        coords = data["features"][0]["center"]
        lon, lat = coords[0], coords[1]
        return lat, lon
    except Exception as e:
        st.warning(f"Could not resolve location '{place_name}'. Error: {e}")
        return None, None

# Helper: Get nearby charging stations
def get_nearest_charging_stations(lat, lon):
    try:
        url = "https://api.mapbox.com/geocoding/v5/mapbox.places/charging station.json"
        params = {
            "proximity": f"{lon},{lat}",
            "access_token": MAPBOX_API_KEY,
            "types": "poi",
            "limit": 10
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("features"):
            return []

        stations = []
        for feature in data["features"]:
            name = feature.get("text", "Unknown")
            address = feature.get("place_name", "No address")
            coords = feature.get("center", [])
            if coords:
                stations.append({
                    "name": name,
                    "address": address,
                    "latitude": coords[1],
                    "longitude": coords[0]
                })

        return stations
    except Exception as e:
        st.error(f"Error retrieving stations: {e}")
        return []

# Feature: Battery range estimation
def estimate_range(vehicle_type, vehicle_cc, battery_cc, percent_charge):
    try:
        battery_efficiency = int(battery_cc) / int(vehicle_cc)
        usable_capacity = (int(percent_charge) / 100.0) * int(battery_cc)
        range_km = usable_capacity * battery_efficiency * 0.5  # Example formula
        return round(range_km, 2)
    except:
        return None

# UI Section: Welcome and Login
def show_welcome():
    st.title("Welcome to Twende EV")
    st.subheader("Powering the Future of Mobility – One Charge at a Time")

    st.markdown("""
    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.  
    **Twende EV** is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best — so you can focus on the road ahead.

    #### Key Benefits:
    - 🚗 **Smart Charging:** No more guesswork—get precise, data-driven charging recommendations.  
    - 🗺️ **Journey Confidence:** Plan routes with real-time battery and station insights.  
    - 🛠️ **Proactive Maintenance:** Stay ahead with alerts and diagnostics tailored to your EV.  

    **Drive Smarter. Charge Smarter.**  
    **Log in now** to take full command of your electric journey.  
    """)

    st.info("🚀 Ready to redefine your EV experience?")
    if st.button("Get Started"):
        st.session_state.logged_in = False  # Allow user to go to login

# UI Section: Login page
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.warning("Please enter both email and password.")

# UI Section: Main dashboard
def main_dashboard():
    st.title("🔋 Twende EV Dashboard")

    st.subheader("🔍 Search Nearby Charging Stations")
    place_input = st.text_input("Enter your location (e.g., Langata)")

    if st.button("Search"):
        if place_input:
            lat, lon = get_coordinates(place_input)
            st.write(f"📍 Coordinates for {place_input}: {lat}, {lon}")
            if lat and lon:
                stations = get_nearest_charging_stations(lat, lon)
                if stations:
                    st.success(f"Found {len(stations)} nearby station(s):")
                    for s in stations:
                        st.markdown(f"**{s['name']}** - {s['address']}")
                else:
                    st.warning("⚠️ No charging stations found nearby.")
            else:
                st.warning("Could not resolve the location.")
        else:
            st.warning("Please enter a location.")

    st.divider()
    st.subheader("⚡ Estimate Battery Range")
    vehicle_type = st.selectbox("Select Vehicle Type", ["Car", "Motorbike", "Tuk-tuk"])
    vehicle_cc = st.number_input("Enter Vehicle CC", min_value=50)
    battery_cc = st.number_input("Enter Battery CC", min_value=50)
    percent_charge = st.slider("Current Battery %", 1, 100, 50)

    if st.button("Estimate Range"):
        result = estimate_range(vehicle_type, vehicle_cc, battery_cc, percent_charge)
        if result:
            st.success(f"🔋 Estimated Range: {result} km")
        else:
            st.error("Could not calculate range. Check input values.")

# App runner
def run_app():
    if "logged_in" not in st.session_state:
        show_welcome()
    elif st.session_state.logged_in:
        main_dashboard()
    else:
        login_page()

if __name__ == "__main__":
    run_app()

