import streamlit as st
import requests
import math

# Get Mapbox API key from secrets.toml
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Initialize session state
if "users" not in st.session_state:
    st.session_state.users = {}  # {email: password}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "email" not in st.session_state:
    st.session_state.email = ""

def login_user(email, password):
    users = st.session_state.users
    return email in users and users[email] == password

def register_user(email, password):
    if email in st.session_state.users:
        return False
    st.session_state.users[email] = password
    return True

def logout_user():
    st.session_state.authenticated = False
    st.session_state.email = ""

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

    estimated_km = battery_kwh * (charge_percent / 100) * base_efficiency * efficiency_factor
    return round(estimated_km, 1)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearby_stations(lat, lon, max_results=3):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/charging%20station.json"
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
            if coords[1] is not None and coords[0] is not None:
                distance = haversine(lat, lon, coords[1], coords[0])
                stations.append({
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0],
                    "distance_km": distance
                })

    stations = sorted(stations, key=lambda x: x["distance_km"])
    return stations[:max_results]

def login_page():
    st.title("🔌 Twende EV - Login / Register")

    choice = st.radio("Select option", ["Login", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Register":
        if st.button("Register"):
            if email and password:
                if register_user(email, password):
                    st.success("Registration successful! Please log in.")
                else:
                    st.error("User already exists.")
            else:
                st.error("Please enter email and password.")

    elif choice == "Login":
        if st.button("Login"):
            if login_user(email, password):
                st.session_state.authenticated = True
                st.session_state.email = email
                st.success(f"Welcome, {email}!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

def main_app():
    st.title("🚗 Twende EV Charging & Range Assistant")

    st.sidebar.write(f"Logged in as: {st.session_state.email}")
    if st.sidebar.button("Logout"):
        logout_user()
        st.experimental_rerun()

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

    location_input = st.text_input("Enter your location (e.g., Nairobi CBD):")

    if location_input:
        try:
            # Use Mapbox Geocoding API to get coordinates for the location input
            geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_input}.json"
            geocode_params = {"access_token": MAPBOX_API_KEY, "limit": 1}
            resp = requests.get(geocode_url, params=geocode_params)
            geocode_data = resp.json()

            if "features" in geocode_data and len(geocode_data["features"]) > 0:
                coords = geocode_data["features"][0]["geometry"]["coordinates"]
                lon, lat = coords[0], coords[1]

                stations = find_nearby_stations(lat, lon)

                if stations:
                    st.write(f"Charging stations near **{location_input}**:")
                    for s in stations:
                        st.write(f"- **{s['name']}** ({s['distance_km']:.2f} km away) at (Lat: {s['lat']:.4f}, Lon: {s['lon']:.4f})")
                else:
                    st.info("No charging stations found nearby.")
            else:
                st.warning("Location not found. Please try a more specific query.")
        except Exception as e:
            st.error(f"Error fetching charging stations: {e}")

def main():
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()








