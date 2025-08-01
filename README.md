# Tendeevdashboard

## Live Demo

Try the live Streamlit app here:  
[https://tendeevdashboard-b26ripkc446hnrkmskwujk.streamlit.app/](https://tendeevdashboard-b26ripkc446hnrkmskwujk.streamlit.app/)

---

## TWENDEEV APP PITCH LINK

[https://www.canva.com/design/DAGli_GFO2Y/eUYfO74IZ8cbVXt0W-_E5A/edit?utm_content=DAGli_GFO2Y&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton](https://www.canva.com/design/DAGli_GFO2Y/eUYfO74IZ8cbVXt0W-_E5A/edit?utm_content=DAGli_GFO2Y&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

---

## TWENDE EV DASHBOARD

A smart, user-friendly dashboard for electric vehicle (EV) drivers with the following core functionalities:

### Key Features

- - **User Authentication**  
  Secure login and registration using hashed passwords and SQLite database.

- **EV Range Estimator (AI-Powered)**  
  Input vehicle specs and environmental data (live weather) to estimate your EV's remaining range.  
  The estimator is powered by a **machine learning model** trained on synthetic and sample EV operational datasets, including variables such as:
  - Vehicle type (car, bus, truck, motorbike)  
  - Engine size (cc)  
  - Battery voltage and age  
  - Battery charge percentage  
  - Environmental conditions (temperature, humidity, wind speed)  
  - file link https://colab.research.google.com/drive/18LYhcOM1dQrlnQQ7xVRVGu9IgXuvBIYZ?usp=sharing
  - 
- **Charging Station Finder**  
  Search nearest EV charging stations by location with distance and number of charging points displayed (powered by OpenChargeMap API).

- **Chatbot Assistant**  
  Ask EV-related questions to a helpful AI assistant integrated via Groq's language model API.

- **Robust Location Lookup**  
  Location search powered by OpenStreetMap/Nominatim with automatic Kenya suffix addition for accurate geocoding.

- **Clean, Responsive UI**  
  Built with Streamlit's interactive widgets and layouts.**User Authentication**  
  Secure login and registration using hashed passwords and SQLite database.

- **EV Range Estimator**  
  Input vehicle specs and environmental data (live weather) to estimate your EV's remaining range.

- **Charging Station Finder**  
  Search nearest EV charging stations by location with distance and number of charging points displayed (powered by OpenChargeMap API).

- **Chatbot Assistant**  
  Ask EV-related questions to a helpful AI assistant integrated via Groq's language model API.

- **Robust Location Lookup**  
  Location search powered by OpenStreetMap/Nominatim with automatic Kenya suffix addition for accurate geocoding.

- **Clean, Responsive UI**  
  Built with Streamlit's interactive widgets and layouts.

---

## Setup and Configuration

### API Keys & Secrets

The app requires the following API keys stored securely in Streamlit secrets (`.streamlit/secrets.toml`):

```toml
[mapbox]
api_key = "your_mapbox_api_key"

[open_charge_map]
api_key = "your_openchargemap_api_key"

[groq]
api_key = "your_groq_api_key"

[openweather]
api_key = "your_openweather_api_key"

## Dependencies
Python 3.8+
streamlit
requests
joblib
pandas
geopy
sqlite3 (built-in)
hashlib (built-in)



## Usage
Register or login before accessing app features.
Use the Range Estimator page to input your vehicle and environment info to estimate driving range.
Use the Charging Stations page to search for nearby EV charging stations by city or place name.
Chat with the AI-powered EV Assistant chatbot for answers to EV questions.
Logout securely via sidebar navigation.

## Resources
OpenChargeMap API Documentation
OpenWeather API Documentation
MapBox API
Groq AI Language Models


## AI Ethics Compliance Statement

The **TwendeEV Dashboard** incorporates a machine learning–based range estimator trained on simulated electric vehicle (EV) data.  
We are committed to ensuring that all AI components in this application adhere to responsible AI principles:

1. **Transparency**  
   We clearly disclose that range predictions are based on simulated data and may not reflect all real-world conditions.  
   Users are encouraged to use the predictions as guidance, not as an absolute measure.

2. **Fairness & Accessibility**  
   The platform offers free access for electric motorbike users to support equitable adoption of EV technology.  
   We aim to ensure future models are trained on diverse, representative datasets to serve all EV types and user groups fairly.

3. **Privacy**  
   The app uses secure authentication with hashed passwords and does not collect personal driving or location histories without consent.  
   Any future data collection will be anonymized and handled in accordance with data protection best practices.

4. **Accountability**  
   Users can report errors or inaccuracies in range predictions or charging station information to help improve the system.

5. **Sustainability**  
   This project supports the transition to clean transportation and aligns with the UN Sustainable Development Goals:  
   - **SDG 7:** Affordable and Clean Energy  
   - **SDG 13:** Climate Action

We are committed to continuous improvement to ensure that our AI solutions remain ethical, safe, and beneficial to all users.



Developed by Jacqueline Musyoka


