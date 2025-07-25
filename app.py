import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Nairobi EV Charging Station Finder", layout="wide")

pdk.settings.mapbox_api_key = st.secrets["mapbox"]["api_key"]

# Hardcoded stations in Nairobi area (latitude and longitude approx)
stations_data = pd.DataFrame([
    {"name": "Westlands EV Station", "lat": -1.265, "lon": 36.807},
    {"name": "Kilimani EV Station", "lat": -1.292, "lon": 36.794},
    {"name": "CBD EV Station", "lat": -1.283, "lon": 36.821},
    {"name": "Karen EV Station", "lat": -1.324, "lon": 36.726},
    {"name": "Langata EV Station", "lat": -1.365, "lon": 36.747},
])

st.title("🔋 EV Charging Station Finder — Nairobi")

location_input = st.text_input("Enter your location in Nairobi (e.g., Kilimani, Westlands)")

if location_input:
    geolocator = Nominatim(user_agent="ev_locator")
    location = geolocator.geocode(f"{location_input}, Nairobi, Kenya")
    if location:
        user_lat, user_lon = location.latitude, location.longitude

        # Calculate distance (approximate) using Euclidean distance for simplicity
        stations_data["distance"] = ((stations_data["lat"] - user_lat)**2 + (stations_data["lon"] - user_lon)**2)**0.5

        # Filter stations within a radius (~0.05 degrees ~ 5km approx)
        nearby_stations = stations_data[stations_data["distance"] < 0.05]

        if nearby_stations.empty:
            st.warning("No EV charging stations found near your location in Nairobi.")
        else:
            nearest_station = nearby_stations.loc[nearby_stations["distance"].idxmin()]
            st.success(f"Nearest station: {nearest_station['name']}")

            # Plot user and stations on the map
            map_data = pd.DataFrame([
                {"name": "You", "lat": user_lat, "lon": user_lon},
                *nearby_stations[["name", "lat", "lon"]].to_dict(orient="records")
            ])

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position='[lon, lat]',
                get_color='[0, 150, 255, 160]',
                get_radius=300,
            )

            view_state = pdk.ViewState(
                latitude=user_lat,
                longitude=user_lon,
                zoom=13,
                pitch=0,
            )

            st.pydeck_chart(pdk.Deck(
                map_style='mapbox://styles/mapbox/streets-v11',
                initial_view_state=view_state,
                layers=[layer],
                tooltip={"text": "{name}"}
            ))
    else:
        st.error("Could not find that location in Nairobi. Please try a more specific place.")
else:
    st.info("Enter a location within Nairobi to find nearby EV charging stations.")



