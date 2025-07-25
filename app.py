import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Nairobi EV Charging Station Finder", layout="wide")

pdk.settings.mapbox_api_key = st.secrets["mapbox"]["api_key"]

# Hardcoded EV charging stations in Nairobi with actual names & coords
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

        # Compute approximate Euclidean distance (not perfect but good for small area)
        stations_data["distance"] = ((stations_data["lat"] - user_lat)**2 + (stations_data["lon"] - user_lon)**2)**0.5

        # Get 3 nearest stations sorted by distance
        nearest_stations = stations_data.nsmallest(3, "distance")

        st.success(f"Nearest 3 EV charging stations to {location_input}:")

        for i, row in nearest_stations.iterrows():
            st.write(f"**{row['name']}** — approx {row['distance']*111:.2f} km away")  # ~111km per degree latitude approx

        # Prepare map data: user location + 3 stations
        map_data = pd.DataFrame([
            {"name": "You", "lat": user_lat, "lon": user_lon, "color": [255, 0, 0, 160], "radius": 500},
            *[
                {"name": row["name"], "lat": row["lat"], "lon": row["lon"], "color": [0, 150, 255, 160], "radius": 300}
                for _, row in nearest_stations.iterrows()
            ]
        ])

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position='[lon, lat]',
            get_fill_color='color',
            get_radius='radius',
            pickable=True,
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




