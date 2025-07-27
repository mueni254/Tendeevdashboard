import streamlit as st
import requests
from geopy.geocoders import Nominatim
import math

# Load API keys from Streamlit secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]
OCM_API_KEY = st.secrets["openchargemap"]["api_key"]

# Hardcoded fallback charging stations (Nairobi)
HARDCODED_STATIONS = [
    {"name": "Karen EV Charging Station", "lat": -1.3247, "lon": 36.7069},
    {"name": "Westlands EV Station", "lat": -1.2667, "lon": 36.8070},
    {"name": "CBD EV Charging Hub", "lat": -1.2864, "lon": 36.8172}
]

# Auth state
if "users" not in st.session_state:
    st.session_state.users = {}  # email: password
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "email" not in st.session_state:
    st.session_state.email = ""

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearby_stations(lat, lon, max_results=3):
    stations = []

    # Try Open Charge Map first
    try:
        ocm_url = "https://api.openchargemap.io/v3/poi/"
        ocm_params = {
            "output": "json",
            "latitude": lat,
            "longitude": lon,
            "distance": 10,
            "maxresults": 10,
            "compact": "true",
            "verbose": "false",
            "key": OCM_API_KEY
        }
        ocm_response = requests.get(ocm_url, params=ocm_params, timeout=5)
        data = ocm_response.json()
        for item in data:
            info = item.get("AddressInfo", {})
            distance = haversine(lat, lon, info.get("Latitude"), info.get("Longitude"))
            stations.append({
                "name": info.get("Title", "Unnamed OCM Station"),
                "lat": info.get("Latitude"),
                "lon": info.get("Longitude"),
                "distance_km": distance
            })
    except Exception as e:
        st.warning("Open Charge Map API failed, using fallback data.")

    # Fallback to hardcoded stations if none found
    if len(stations) < max_results:
        for s in HARDCODED_STATIONS:
            distance = haversine(lat, lon, s["lat"], s["lon"])
            stations.append({
                "name": s["name"],
                "lat": s["lat"],
                "lon": s["lon"],
                "distance_km": distance
            })

    # Remove duplicates
    unique = {}
    for s in stations:
        unique[(s["lat"], s["lon"])] = s

    sorted_stations = sorted(unique.values(), key=lambda x: x["distance_km"])
    return sorted_stations[:max_results]

def calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent):
    base_efficiency = 5
    efficiency_factor = 1.0
    if vehicle_type.lower() == "motorbike":
        efficiency_factor = 1.5
    if engine_cc < 100:
        efficiency_factor *= 1.3
    elif engine_cc > 1500:
        efficiency_factor *= 0.7
    est_km = battery_kwh * (charge_percent / 100) * base_efficiency * efficiency_factor
    return round(est_km, 1)

def login_page():
    st.title("Welcome to Twende EV - Login/Register")
    option = st.radio("Select option", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if option == "Register":
        if st.button("Register"):
            if not email or not password:
                st.error("Please enter both email and password.")
            elif email in st.session_state.users:
                st.warning("User already registered. Please login.")
            else:
                st.session_state.users[email] = password
                st.success("Registration successful! Please login.")
    else:
        if st.button("Login"):
            if email in st.session_state.users and st.session_state.users[email] == password:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.success(f"Welcome back, {email}!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

def main_app():
    st.title(f"Twende EV Dashboard - Hello, {st.session_state.email}")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.experimental_rerun()

    st.header("🔋 EV Range Calculator")
    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Motorbike", "Other"])
    engine_cc = st.number_input("Engine CC", min_value=50, max_value=5000, value=1500, step=10)
    battery_kwh = st.number_input("Battery Capacity (kWh)", min_value=1.0, max_value=200.0, value=40.0, step=0.5)
    charge_percent = st.slider("Current Battery Charge (%)", 0, 100, 75)
    if st.button("Calculate Range"):
        est_range = calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent)
        st.success(f"Estimated driving range: **{est_range} km**")

    st.markdown("---")
    st.header("🔌 Nearby EV Charging Stations")
    location_input = st.text_input("Enter your current location (e.g., Nairobi CBD)")
    if location_input:
        geolocator = Nominatim(user_agent="twende_ev_app")
        location = geolocator.geocode(location_input)
        if location:
            stations = find_nearby_stations(location.latitude, location.longitude)
            if stations:
                st.write(f"### Charging stations near **{location_input}**:")
                for s in stations:
                    st.write(f"- **{s['name']}** ({s['distance_km']:.2f} km away) at (Lat: {s['lat']:.4f}, Lon: {s['lon']:.4f})")
            else:
                st.info("No charging stations found nearby.")
        else:
            st.warning("Location not found. Please try a more specific address.")

def main():
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()












