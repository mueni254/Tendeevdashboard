import streamlit as st
import math
import pandas as pd
import pydeck as pdk

# -----------------------------
# Replace with your Mapbox API token
MAPBOX_API_TOKEN = "YOUR_MAPBOX_ACCESS_TOKEN"
# -----------------------------

st.set_page_config(page_title="Nearest EV Charging Station", layout="centered")

st.title("🔌 Nearest EV Charging Station Finder")

# Hardcoded charging station data (Name, Latitude, Longitude)
charging_stations = [
    {"name": "Station A - City Center", "lat": -1.286389, "lon": 36.817223},
    {"name": "Station B - Westlands", "lat": -1.2683, "lon": 36.8000},
    {"name": "Station C - Karen", "lat": -1.3200, "lon": 36.7200},
    {"name": "Station D - Thika Road", "lat": -1.2400, "lon": 36.9000},
]

# Haversine formula to calculate distance between two coordinates
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # in kilometers

# User input for current location
st.subheader("📍 Enter Your Current Location")
lat = st.number_input("Latitude", format="%.6f", value=-1.286389)
lon = st.number_input("Longitude", format="%.6f", value=36.817223)

# Compute nearest station
def find_nearest_station(user_lat, user_lon):
    nearest = None
    min_distance = float("inf")

    for station in charging_stations:
        dist = haversine(user_lat, user_lon, station["lat"], station["lon"])
        if dist < min_distance:
            min_distance = dist
            nearest = station.copy()
            nearest["distance_km"] = round(dist, 2)

    return nearest

if st.button("Find Nearest Station"):
    nearest = find_nearest_station(lat, lon)

    st.success(f"✅ Nearest Station: **{nearest['name']}**")
    st.write(f"📏 Distance: {nearest['distance_km']} km")

    # Optional: Show map
    st.subheader("🗺️ Map View")

    # Map data
    map_df = pd.DataFrame([
        {"name": "Your Location", "lat": lat, "lon": lon},
        {"name": nearest["name"], "lat": nearest["lat"], "lon": nearest["lon"]}
    ])

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=11,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=map_df,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=400,
                pickable=True
            )
        ],
        tooltip={"text": "{name}"},
        mapbox_key=MAPBOX_API_TOKEN
    ))
