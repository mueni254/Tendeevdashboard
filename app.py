import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim
import requests

st.set_page_config(page_title="Nairobi EV Charging Station Finder", layout="wide")

# Load your Mapbox API key from secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]
pdk.settings.mapbox_api_key = MAPBOX_API_KEY

# Hardcoded Nairobi EV stations (replace/update as needed)
hardcoded_stations = pd.DataFrame([
    {"name": "The Hub EV Charging Station", "lat": -1.275, "lon": 36.819},
    {"name": "Garden City EV Charging", "lat": -1.258, "lon": 36.888},
    {"name": "Two Rivers Mall EV Station", "lat": -1.228, "lon": 36.841},
    {"name": "Kenya Power EV Charging", "lat": -1.286, "lon": 36.817},
    {"name": "Westgate Mall EV Charging", "lat": -1.273, "lon": 36.797},
])

def search_mapbox_ev_stations(lat, lon, limit=5):
    """Search Mapbox Places API for EV charging stations near lat/lon."""
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/charging station.json"
    params = {
        "proximity": f"{lon},{lat}",
        "types": "poi",
        "limit": limit,
        "access_token": MAPBOX_API_KEY,
        "country": "KE",  # Kenya country code to limit search
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Error fetching data from Mapbox Places API.")
        return pd.DataFrame()

    data = response.json()
    features = data.get("features", [])
    results = []
    for feat in features:
        coords = feat["geometry"]["coordinates"]
        name = feat["text"]
        results.append({"name": name, "lon": coords[0], "lat": coords[1]})
    return pd.DataFrame(results)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in km."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # Earth radius km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2*atan2(sqrt(a), sqrt(1 - a))
    return R * c

st.title("🔋 EV Charging Station Finder — Nairobi")

location_input = st.text_input("Enter your location in Nairobi (e.g., Kilimani, Westlands)")

if location_input:
    geolocator = Nominatim(user_agent="ev_locator")
    location = geolocator.geocode(f"{location_input}, Nairobi, Kenya")

    if location:
        user_lat, user_lon = location.latitude, location.longitude

        # Search Mapbox API for nearby EV stations
        mapbox_stations = search_mapbox_ev_stations(user_lat, user_lon, limit=5)

        # Combine hardcoded and Mapbox stations
        combined = pd.concat([hardcoded_stations, mapbox_stations], ignore_index=True)

        # Calculate distance to user location
        combined["distance_km"] = combined.apply(
            lambda row: haversine_distance(user_lat, user_lon, row["lat"], row["lon"]), axis=1
        )

        # Pick 3 nearest stations
        nearest = combined.nsmallest(3, "distance_km")

        st.success(f"Nearest 3 EV charging stations to {location_input}:")

        for i, row in nearest.iterrows():
            st.write(f"**{row['name']}** — approx {row['distance_km']:.2f} km away")

        # Prepare map data: user + stations
        map_data = pd.DataFrame([
            {"name": "You", "lat": user_lat, "lon": user_lon, "color": [255, 0, 0, 160], "radius": 500},
            *[
                {"name": row["name"], "lat": row["lat"], "lon": row["lon"], "color": [0, 150, 255, 160], "radius": 300}
                for _, row in nearest.iterrows()
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





