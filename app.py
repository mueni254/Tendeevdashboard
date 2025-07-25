import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import math
import matplotlib.pyplot as plt
import pydeck as pdk

# ------------- USER AUTHENTICATION FUNCTIONS ------------- #

USER_DB = "users.json"

if not os.path.exists(USER_DB):
    with open(USER_DB, "w") as f:
        json.dump({}, f)

def register_user(email, password):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    if email in users:
        return False
    users[email] = {"password": password}
    with open(USER_DB, "w") as f:
        json.dump(users, f)
    return True

def login_user(email, password):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    return email in users and users[email]["password"] == password

def is_authenticated():
    return st.session_state.get("logged_in", False)

def logout_user():
    st.session_state.logged_in = False
    st.session_state.email = None


# ------------- MOCK CHARGING STATION DATA ------------- #

stations_data = pd.DataFrame([
    {"name": "Karen Mall Station", "lat": -1.329, "lon": 36.715},
    {"name": "Lang’ata Road Station", "lat": -1.360, "lon": 36.759},
    {"name": "Wilson Airport Station", "lat": -1.319, "lon": 36.814},
    {"name": "Nairobi CBD Station", "lat": -1.286, "lon": 36.817},
    {"name": "Galleria Mall Station", "lat": -1.343, "lon": 36.713},
])

# ------------- HELPER FUNCTIONS ------------- #

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def get_coordinates_from_location(location):
    location_map = {
        "langata": (-1.360, 36.759),
        "karen": (-1.329, 36.715),
        "cbd": (-1.286, 36.817),
    }
    return location_map.get(location.lower())

def find_nearest_stations(location, k=3):
    coords = get_coordinates_from_location(location)
    if coords is None:
        return []
    lat, lon = coords
    stations_data["distance"] = stations_data.apply(
        lambda row: haversine(lat, lon, row["lat"], row["lon"]), axis=1
    )
    return stations_data.sort_values("distance").head(k)


# ------------- MAIN APP PAGES ------------- #

def login_page():
    st.title("🔐 EV Dashboard Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.success("Logged in!")
            st.session_state.logged_in = True
            st.session_state.email = email
        else:
            st.error("Invalid credentials")

    st.markdown("---")
    st.subheader("New here?")
    new_email = st.text_input("New Email", key="new_email")
    new_password = st.text_input("New Password", type="password", key="new_pass")
    if st.button("Register"):
        if register_user(new_email, new_password):
            st.success("Registration successful!")
        else:
            st.error("Email already exists")


def dashboard_page():
    st.title("⚡ EV Smart Dashboard")

    if st.button("🔓 Logout"):
        logout_user()

    st.subheader("🔋 Battery Analytics")
    battery_data = pd.DataFrame({
        "Time": pd.date_range(start="2024-01-01", periods=12, freq="M"),
        "Charge Level": np.random.randint(40, 100, size=12),
    })
    fig, ax = plt.subplots()
    ax.plot(battery_data["Time"], battery_data["Charge Level"], marker="o", color="green")
    ax.set_title("Battery Level Over Time")
    ax.set_ylabel("% Charge")
    ax.set_xlabel("Month")
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("🗺️ Find Nearest Charging Stations")
    user_location = st.text_input("Enter your location (e.g., langata, karen, cbd)")

    if st.button("🔍 Search"):
        results = find_nearest_stations(user_location)
        if not results.empty:
            st.write("Nearest Charging Stations:")
            for _, row in results.iterrows():
                st.write(f"- {row['name']} ({row['distance']:.2f} km)")
            # Map
            st.pydeck_chart(pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=results["lat"].mean(),
                    longitude=results["lon"].mean(),
                    zoom=12,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=results,
                        get_position="[lon, lat]",
                        get_radius=500,
                        get_fill_color=[0, 128, 255, 140],
                        pickable=True,
                    )
                ],
            ))
        else:
            st.warning("No charging stations found for that location.")


# ------------- APP ENTRY POINT ------------- #

def main():
    st.set_page_config(page_title="EV Dashboard", layout="centered")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = None

    if st.session_state.logged_in:
        dashboard_page()
    else:
        login_page()

if __name__ == "__main__":
    main()








