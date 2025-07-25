import streamlit as st
import requests
from geopy.geocoders import Nominatim
import math

# Mapbox API Key from Streamlit secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Session state setup
if "registered_users" not in st.session_state:
    st.session_state.registered_users = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "email" not in st.session_state:
    st.session_state.email = ""

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
        "proximity": f"{lon},{lat}",  # Note: lon,lat order for Mapbox proximity
        "limit": 10,
        "access_token": MAPBOX_API_KEY,
        "types": "poi",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error querying Mapbox API: {e}")
        data = {}

    stations = []
    if "features" in data:
        for feature in data["features"]:
            name = feature.get("text", "").strip()
            coords = feature.get("geometry", {}).get("coordinates", [None, None])
            if coords[0] is not None and coords[1] is not None and name:
                distance = haversine(lat, lon, coords[1], coords[0])
                stations.append({
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0],
                    "distance_km": distance
                })

    # Hardcoded fallback stations in Nairobi area
    hardcoded_stations = [
        {"name": "Westlands Charging Station", "lat": -1.2667, "lon": 36.8123},
        {"name": "Karen Mall Charging Station", "lat": -1.3100, "lon": 36.7261},
        {"name": "Upper Hill Charging Station", "lat": -1.2900, "lon": 36.8172},
        {"name": "CBD Charging Station", "lat": -1.2833, "lon": 36.8167},
        {"name": "Langata Charging Station", "lat": -1.3500, "lon": 36.7500},
    ]

    # Calculate distances for hardcoded stations
    for s in hardcoded_stations:
        s["distance_km"] = haversine(lat, lon, s["lat"], s["lon"])

    # Combine API stations + hardcoded stations, avoiding duplicates by name
    combined = stations.copy()
    existing_names = {s["name"] for s in combined}

    for hc in hardcoded_stations:
        if hc["name"] not in existing_names:
            combined.append(hc)

    # Sort combined list by distance
    combined_sorted = sorted(combined, key=lambda x: x["distance_km"])

    # Return top max_results stations
    return combined_sorted[:max_results]

def calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent):
    # Simple heuristic for range estimation
    base_efficiency = 5  # km per kWh base efficiency
    if vehicle_type.lower() == "car":
        efficiency_factor = 1.0
    elif vehicle_type.lower() == "motorbike":
        efficiency_factor = 1.5  # Motorbikes more efficient
    else:
        efficiency_factor = 1.0

    if engine_cc < 100:
        efficiency_factor *= 1.3
    elif engine_cc > 1500:
        efficiency_factor *= 0.7

    estimated_km = battery_kwh * (charge_percent / 100) * base_efficiency * efficiency_factor
    return round(estimated_km, 1)

def show_welcome():
    st.markdown("# 🚗 Welcome to Twende EV")
    st.markdown("### Powering the Future of Mobility – One Charge at a Time")
    st.write("""
Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

**Key Benefits**  
- 🔋 Smart Charging: No more guesswork—get precise, data-driven charging recommendations.  
- 🗺️ Journey Confidence: Plan routes with real-time battery and station insights.  
- ⚙️ Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

---
**Drive Smarter. Charge Smarter.**  
Log in now to take full command of your electric journey.
""")

    option = st.radio("Select an option", ["Log In", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            if email and password:
                if email in st.session_state.registered_users:
                    st.error("Email already registered. Please log in.")
                else:
                    st.session_state.registered_users[email] = password
                    st.success("✅ Registration successful! You can now log in.")
            else:
                st.error("Please provide both email and password.")

    if option == "Log In":
        if st.button("Log In"):
            if st.session_state.registered_users.get(email) == password:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.success(f"✅ Welcome back, {email}!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

def main_app():
    st.markdown(f"### 👋 Hello, {st.session_state.email}")
    st.title("Twende EV Charging & Range Assistant")

    with st.form("range_form"):
        st.header("Calculate Your EV Range")
        vehicle_type = st.selectbox("Vehicle Type", ["Car", "Motorbike", "Other"])
        engine_cc = st.number_input("Engine CC", min_value=50, max_value=5000, value=1500, step=10)
        battery_kwh = st.number_input("Battery Capacity (kWh)", min_value=1.0, max_value=200.0, value=40.0, step=0.5)
        charge_percent = st.slider("Current Battery Charge (%)", 0, 100, 75)
        submitted = st.form_submit_button("Calculate Range")

        if submitted:
            est_range = calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent)
            st.success(f"Estimated driving range: **{est_range} km**")

    st.markdown("---")
    st.header("Find Nearby Charging Stations")

    location_input = st.text_input("Enter your current location (e.g., Nairobi CBD):")

    if location_input:
        geolocator = Nominatim(user_agent="ev_locator")
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

    if st.button("🔒 Log out"):
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.experimental_rerun()

def run_app():
    if st.session_state.authenticated:
        main_app()
    else:
        show_welcome()

if __name__ == "__main__":
    run_app()






