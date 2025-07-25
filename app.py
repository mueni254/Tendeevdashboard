import streamlit as st
import requests
from geopy.geocoders import Nominatim
import math

# Mapbox API Key from secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Initialize session state variables if not present
if "registered_users" not in st.session_state:
    st.session_state.registered_users = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "email" not in st.session_state:
    st.session_state.email = ""

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

    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if option == "Register":
                if email and password:
                    if email in st.session_state.registered_users:
                        st.warning("This email is already registered. Please log in.")
                    else:
                        st.session_state.registered_users[email] = password
                        st.success("✅ Registration successful! You can now log in.")
                else:
                    st.error("Please provide both email and password.")

            elif option == "Log In":
                if st.session_state.registered_users.get(email) == password:
                    st.session_state.authenticated = True
                    st.session_state.email = email
                    st.success(f"✅ Welcome back, {email}!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password.")

def calculate_range(vehicle_type, engine_cc, battery_kwh, charge_percent):
    # Basic example logic for range estimation:
    base_efficiency = 5  # km per kWh base, adjust per vehicle_type
    if vehicle_type.lower() == "car":
        efficiency_factor = 1.0
    elif vehicle_type.lower() == "motorbike":
        efficiency_factor = 1.5  # more efficient
    else:
        efficiency_factor = 1.0  # default

    # Adjust by engine_cc roughly (less cc = better efficiency)
    if engine_cc < 100:
        efficiency_factor *= 1.3
    elif engine_cc > 1500:
        efficiency_factor *= 0.7

    estimated_km = battery_kwh * (charge_percent / 100) * base_efficiency * efficiency_factor
    return round(estimated_km, 1)

def haversine(lat1, lon1, lat2, lon2):
    # Calculate distance in km between two points
    R = 6371  # Earth radius km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearby_charging_stations(lat, lon, max_results=3):
    # Mapbox POI search API endpoint
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/charging%20station.json"
    params = {
        "proximity": f"{lon},{lat}",
        "limit": 10,
        "access_token": MAPBOX_API_KEY,
        "types": "poi"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error fetching charging stations: {e}")
        return []

    stations = []
    if "features" in data:
        for feature in data["features"]:
            name = feature.get("text", "Unknown")
            coords = feature.get("geometry", {}).get("coordinates", [None, None])
            if coords[1] is not None and coords[0] is not None:
                distance = haversine(lat, lon, coords[1], coords[0])
                stations.append({
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0],
                    "distance_km": distance
                })

    # Sort by distance and return top N
    stations_sorted = sorted(stations, key=lambda x: x["distance_km"])
    return stations_sorted[:max_results]

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
        try:
            geolocator = Nominatim(user_agent="ev_locator")
            location = geolocator.geocode(location_input)
            if location:
                lat, lon = location.latitude, location.longitude

                stations = find_nearby_charging_stations(lat, lon)

                if stations:
                    st.write(f"### Charging stations near {location_input}:")
                    for s in stations:
                        st.write(f"- **{s['name']}** ({s['distance_km']:.2f} km away) at (Lat: {s['lat']:.4f}, Lon: {s['lon']:.4f})")
                else:
                    st.info("No charging stations found nearby.")
            else:
                st.warning("📍 Location not found. Please try a more specific address.")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🔒 Log out"):
        st.session_state.authenticated = False
        st.experimental_rerun()

def run_app():
    if st.session_state.authenticated:
        main_app()
    else:
        show_welcome()

if __name__ == "__main__":
    run_app()

