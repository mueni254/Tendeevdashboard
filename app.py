import streamlit as st
import requests
from geopy.geocoders import Nominatim
import math

# Load Mapbox API Key from secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "email" not in st.session_state:
    st.session_state.email = ""

if "registered_users" not in st.session_state:
    st.session_state.registered_users = {}

# Utility functions

def calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent):
    base_efficiency = 5  # km per kWh base
    if vehicle_type.lower() == "car":
        efficiency_factor = 1.0
    elif vehicle_type.lower() == "motorbike":
        efficiency_factor = 1.5
    else:
        efficiency_factor = 1.0

    if engine_cc < 100:
        efficiency_factor *= 1.3
    elif engine_cc > 1500:
        efficiency_factor *= 0.7

    est_range = battery_kwh * (charge_percent / 100) * base_efficiency * efficiency_factor
    return round(est_range, 1)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearby_charging_stations(lat, lon, max_results=3):
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/charging%20station.json"
    params = {
        "proximity": f"{lon},{lat}",
        "limit": 10,
        "access_token": MAPBOX_API_KEY,
        "types": "poi"
    }
    response = requests.get(url, params=params)
    data = response.json()

    stations = []
    if "features" in data:
        for feature in data["features"]:
            name = feature.get("text", "Unknown")
            coords = feature.get("geometry", {}).get("coordinates", [None, None])
            if coords[0] is not None and coords[1] is not None:
                distance = haversine(lat, lon, coords[1], coords[0])
                stations.append({
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0],
                    "distance_km": distance
                })
    stations_sorted = sorted(stations, key=lambda x: x["distance_km"])
    return stations_sorted[:max_results]

# Authentication pages

def login():
    st.header("Log In")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        if email in st.session_state.registered_users and st.session_state.registered_users[email] == password:
            st.session_state.authenticated = True
            st.session_state.email = email
            st.success(f"Welcome back, {email}!")
        else:
            st.error("Invalid email or password.")


def register():
    st.header("Register")
    new_email = st.text_input("New Email")
    new_password = st.text_input("New Password", type="password")

    if st.button("Register"):
        if new_email and new_password:
            if new_email in st.session_state.registered_users:
                st.error("This email is already registered.")
            else:
                st.session_state.registered_users[new_email] = new_password
                st.success("Registration successful! You can now log in.")
        else:
            st.error("Please enter both email and password.")

def logout():
    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.success("You have been logged out.")


# Main App

def main_app():
    st.title("Twende EV Charging & Range Assistant")
    st.write(f"Logged in as: **{st.session_state.email}**")
    logout()

    st.header("Calculate Your EV Range")
    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Motorbike", "Other"])
    engine_cc = st.number_input("Engine CC", min_value=50, max_value=5000, value=1500, step=10)
    battery_kwh = st.number_input("Battery Capacity (kWh)", min_value=1.0, max_value=200.0, value=40.0, step=0.5)
    charge_percent = st.slider("Current Battery Charge (%)", 0, 100, 75)
    if st.button("Calculate Range"):
        est_range = calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent)
        st.success(f"Estimated driving range: **{est_range} km**")

    st.markdown("---")
    st.header("Find Nearby Charging Stations")
    location_input = st.text_input("Enter your current location (e.g., Nairobi CBD):")

    if location_input:
        try:
            geolocator = Nominatim(user_agent="twende_ev_locator")
            location = geolocator.geocode(location_input)
            if location:
                lat, lon = location.latitude, location.longitude
                stations = find_nearby_charging_stations(lat, lon)

                if stations:
                    st.write(f"### Charging stations near {location_input}:")
                    for s in stations:
                        st.write(f"- **{s['name']}** ({s['distance_km']:.2f} km away)")
                else:
                    st.info("No charging stations found nearby.")
            else:
                st.warning("📍 Location not found. Please try a more specific address.")
        except Exception as e:
            st.error(f"Error during location search: {e}")


def run_app():
    if st.session_state.authenticated:
        main_app()
    else:
        choice = st.radio("Select an option", ("Log In", "Register"))
        if choice == "Log In":
            login()
        else:
            register()


if __name__ == "__main__":
    run_app()





