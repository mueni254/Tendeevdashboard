import streamlit as st
import requests
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# -----------------------
# In-memory user storage
# -----------------------
users = {}

def register_user(email, password):
    if email in users:
        return False
    users[email] = {"password": password}
    return True

def login_user(email, password):
    return email in users and users[email]["password"] == password

def logout_user():
    st.session_state["authenticated"] = False

def is_authenticated():
    return st.session_state.get("authenticated", False)

# -----------------------
# EV Station Fetcher
# -----------------------
def get_nearest_charging_stations(user_location, max_results=3):
    api_key = st.secrets["open_charge_map"]["api_key"]
    latitude, longitude = user_location

    url = f"https://api.openchargemap.io/v3/poi/?output=json&latitude={latitude}&longitude={longitude}&distance=20&distanceunit=KM&maxresults=20&key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch charging stations.")
        return []

    data = response.json()
    stations = []

    for station in data:
        if "AddressInfo" in station:
            station_info = {
                "name": station["AddressInfo"].get("Title", "Unknown"),
                "latitude": station["AddressInfo"]["Latitude"],
                "longitude": station["AddressInfo"]["Longitude"],
                "distance": geodesic(user_location, (station["AddressInfo"]["Latitude"], station["AddressInfo"]["Longitude"])).km,
            }
            stations.append(station_info)

    stations.sort(key=lambda x: x["distance"])
    return stations[:max_results]

# -----------------------
# Map Rendering
# -----------------------
def show_map(user_location, stations):
    m = folium.Map(location=user_location, zoom_start=12)

    # Add user location
    folium.Marker(user_location, tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)

    # Add station markers
    for station in stations:
        folium.Marker(
            location=[station["latitude"], station["longitude"]],
            popup=f"{station['name']} ({station['distance']:.2f} km)",
            icon=folium.Icon(color='green')
        ).add_to(m)

    st_folium(m, width=700)

# -----------------------
# Login Page
# -----------------------
def login_page():
    st.title("🔐 Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if login_user(email, password):
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown("Don't have an account?")
    if st.button("Register"):
        st.session_state["show_register"] = True
        st.experimental_rerun()

# -----------------------
# Registration Page
# -----------------------
def register_page():
    st.title("📝 Register")

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Register")

    if submit:
        if register_user(email, password):
            st.success("Registration successful. You can now login.")
            st.session_state["show_register"] = False
            st.experimental_rerun()
        else:
            st.error("Email already registered.")

    st.markdown("Already have an account?")
    if st.button("Back to Login"):
        st.session_state["show_register"] = False
        st.experimental_rerun()

# -----------------------
# Dashboard Page
# -----------------------
def dashboard():
    st.title("🔋 EV Charging Station Finder")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

    st.markdown("### 📍 Enter your location")
    lat = st.number_input("Latitude", value=-1.2921, format="%.6f")
    lon = st.number_input("Longitude", value=36.8219, format="%.6f")

    if st.button("Find Nearest Stations"):
        user_location = (lat, lon)
        stations = get_nearest_charging_stations(user_location)

        if stations:
            st.success(f"Found {len(stations)} nearby stations:")
            for s in stations:
                st.write(f"- {s['name']} ({s['distance']:.2f} km)")

            show_map(user_location, stations)
        else:
            st.warning("No charging stations found nearby.")

# -----------------------
# App Entry Point
# -----------------------
def main():
    st.set_page_config(page_title="EV Dashboard", layout="centered")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "show_register" not in st.session_state:
        st.session_state["show_register"] = False

    if is_authenticated():
        dashboard()
    elif st.session_state["show_register"]:
        register_page()
    else:
        login_page()

if __name__ == "__main__":
    main()

