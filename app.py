import streamlit as st
import requests
from geopy.geocoders import Nominatim
import math

# Secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]
OCM_API_KEY = st.secrets["open_charge_map"]["api_key"]

# Hardcoded fallback charging stations
HARDCODED_STATIONS = [
    {"name": "Karen EV Charging Station", "lat": -1.3247, "lon": 36.7069},
    {"name": "Westlands EV Station", "lat": -1.2667, "lon": 36.8070},
    {"name": "CBD EV Charging Hub", "lat": -1.2864, "lon": 36.8172}
]

# Session state for login
if "users" not in st.session_state:
    st.session_state.users = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "email" not in st.session_state:
    st.session_state.email = ""

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearby_stations(lat, lon, max_results=3):
    stations = []

    # Primary: Open Charge Map
    try:
        ocm_url = "https://api.openchargemap.io/v3/poi/"
        ocm_params = {
            "output": "json",
            "latitude": lat,
            "longitude": lon,
            "distance": 10,
            "distanceunit": "KM",
            "maxresults": 10,
            "key": OCM_API_KEY
        }
        response = requests.get(ocm_url, params=ocm_params, timeout=5)
        data = response.json()
        if data:
            for item in data:
                info = item.get("AddressInfo", {})
                name = info.get("Title", "Unknown")
                lat_, lon_ = info.get("Latitude"), info.get("Longitude")
                if lat_ and lon_:
                    distance = haversine(lat, lon, lat_, lon_)
                    stations.append({
                        "name": name,
                        "lat": lat_,
                        "lon": lon_,
                        "distance_km": distance
                    })
    except Exception:
        st.warning("Could not load stations from Open Charge Map. Trying fallback options...")

    # Fallback: Mapbox
    if len(stations) < max_results:
        try:
            mapbox_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/charging%20station.json"
            mapbox_params = {
                "access_token": MAPBOX_API_KEY,
                "limit": 5,
                "types": "poi",
                "proximity": f"{lon},{lat}"
            }
            res = requests.get(mapbox_url, params=mapbox_params, timeout=5)
            data = res.json()
            if "features" in data:
                for feature in data["features"]:
                    name = feature.get("text", "Unknown")
                    coords = feature.get("geometry", {}).get("coordinates", [None, None])
                    if coords[0] and coords[1]:
                        distance = haversine(lat, lon, coords[1], coords[0])
                        stations.append({
                            "name": name,
                            "lat": coords[1],
                            "lon": coords[0],
                            "distance_km": distance
                        })
        except Exception:
            st.warning("Mapbox fallback also failed. Using hardcoded stations...")

    # Fallback: Hardcoded
    if len(stations) < max_results:
        for s in HARDCODED_STATIONS:
            distance = haversine(lat, lon, s["lat"], s["lon"])
            stations.append({
                "name": s["name"],
                "lat": s["lat"],
                "lon": s["lon"],
                "distance_km": distance
            })

    # Remove duplicates
    unique = {}
    for s in stations:
        unique[(s["lat"], s["lon"])] = s
    return sorted(unique.values(), key=lambda x: x["distance_km"])[:max_results]

# Range Calculator & UI functions (unchanged)...

# Add rest of your code here: calculate_range(), login_page(), main_app(), main()

# END










