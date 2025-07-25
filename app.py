import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim

# Set page title
st.set_page_config(page_title="EV Charging Map", layout="wide")

# Load Mapbox key from secrets
pdk.settings.mapbox_api_key = st.secrets["mapbox"]["api_key"]

# Sample EV charging stations data
stations_data = pd.DataFrame([
    {"name": "EV Station Nairobi", "lat": -1.2921, "lon": 36.8219},
    {"name": "EV Station Mombasa", "lat": -4.0435, "lon": 39.6682},
    {"name": "EV Station Kisumu", "lat": -0.0917, "lon": 34.7679},
])

# Title
st.title("🔋 EV Charging Station Finder (Kenya)")

# User input
location_input = st.text_input("Enter your location (e.g., Nairobi, Mombasa)")

if location_input:
    with st.spinner("Searching location..."):
        geolocator = Nominatim(user_agent="ev_locator")
        location = geolocator.geocode(location_input)

        if location:
            user_lat = location.latitude
            user_lon = location.longitude

            # Find nearest station
            stations_data["distance"] = ((stations_data["lat"] - user_lat)**2 + (stations_data["lon"] - user_lon)**2)**0.5
            nearest_station = stations_data.loc[stations_data["distance"].idxmin()]

            st.success(f"Nearest station: {nearest_station['name']}")

            # Plot on map
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=pd.DataFrame([
                    {"name": "You", "lat": user_lat, "lon": user_lon},
                    {"name": nearest_station["name"], "lat": nearest_station["lat"], "lon": nearest_station["lon"]},
                ]),
                get_position='[lon, lat]',
                get_color='[0, 150, 255, 160]',
                get_radius=30000,
            )

            view_state = pdk.ViewState(
                latitude=user_lat,
                longitude=user_lon,
                zoom=6,
                pitch=0,
            )

            st.pydeck_chart(pdk.Deck(
                map_style='mapbox://styles/mapbox/streets-v11',
                initial_view_state=view_state,
                layers=[layer],
                tooltip={"text": "{name}"}
            ))

        else:
            st.error("Location not found. Please try a more specific name.")
else:
    st.info("Enter your location to find the nearest EV charging station.")


