import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import-module

# --- Page Configuration ---
# Use a wide layout for a better dashboard feel
st.set_page_config(page_title="Interactive Weather Map", layout="wide")

# --- Weather Data Fetching Function ---
# Use @st.cache_data to cache the results. This means if the user clicks the
# same spot twice, it won't re-download the data.
@st.cache_data
def get_weather(lat, lon):
    """
    Fetches hourly and daily weather data from the Open-Meteo API.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,rain,snowfall,weather_code,wind_speed_10m,wind_direction_10m,uv_index",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,precipitation_probability_max,wind_speed_10m_max,uv_index_max",
            "timezone": "auto"
        }
        response = requests.get(url, params=params)
        response.raise_for_status() # Raise an exception for bad status codes (like 404 or 500)
        data = response.json()
        
        # --- Process Hourly Data ---
        hourly_data = data['hourly']
        hourly_df = pd.DataFrame(hourly_data)
        hourly_df['time'] = pd.to_datetime(hourly_df['time'])
        hourly_df = hourly_df.rename(columns={
            "temperature_2m": "Temp (°C)",
            "relative_humidity_2m": "Humidity (%)",
            "apparent_temperature": "Apparent Temp (°C)",
            "precipitation_probability": "Precip. Prob. (%)",
            "precipitation": "Precip. (mm)",
            "rain": "Rain (mm)",
            "snowfall": "Snow (cm)",
            "weather_code": "Weather Code",
            "wind_speed_10m": "Wind Speed (km/h)",
            "wind_direction_10m": "Wind Dir (°)",
            "uv_index": "UV Index"
        })
        hourly_df = hourly_df.set_index('time')
        
        # --- Process Daily Data ---
        daily_data = data['daily']
        daily_df = pd.DataFrame(daily_data)
        daily_df['time'] = pd.to_datetime(daily_df['time'])
        daily_df = daily_df.rename(columns={
             "temperature_2m_max": "Max Temp (°C)",
             "temperature_2m_min": "Min Temp (°C)",
             "weather_code": "Weather Code",
             "precipitation_sum": "Precip. Sum (mm)",
             "rain_sum": "Rain Sum (mm)",
             "snowfall_sum": "Snow Sum (cm)",
             "precipitation_probability_max": "Max Precip. Prob. (%)",
             "wind_speed_10m_max": "Max Wind (km/h)",
             "uv_index_max": "Max UV Index"
        })
        daily_df = daily_df.set_index('time')

        return hourly_df, daily_df
        
    except requests.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None, None
    except Exception as e:
        st.error(f"An error occurred while processing data: {e}")
        return None, None

# --- Main Application UI ---

# --- Title ---
# We replicate the title from your screenshot, using columns for the icon.
col1, col2 = st.columns([1, 10])
with col1:
    # Using a placeholder emoji as an icon
    st.image("https://placehold.co/100x100/white/white?text=🌦️&font=noto-sans", width=80) 
with col2:
    st.title("Open-Meteo Interactive Weather Dashboard")

st.markdown(
    "If you click a location on the map, it will load the hourly weather data for that region.  \n"
    "*(지에서 위치를 클릭하면 해당 지역의 시간별 기온 데이터를 불러옵니다.)*"
)

# --- 1. Map for Location Selection ---
st.header("1. Select Region (Click the map)")
st.markdown("*(지역 선택 (지도를 클릭하세요))*")

# Create a Folium map centered on Seoul (like the image)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=5)

# Render the map using streamlit-folium.
# This component returns a dictionary with information about the map state.
map_data = st_folium(m, center=[37.5665, 126.9780], width=700, height=500)

# --- 2. Weather Data Display ---
# We check if the map_data dictionary is not empty and has the 'last_clicked' key.
if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng'] # Note: folium returns 'lng' for longitude

    st.info(f"Loading data for selected location... (Lat: {lat:.4f}, Lon: {lon:.4f})")
    
    # Fetch the weather data
    hourly_df, daily_df = get_weather(lat, lon)
    
    # If data was fetched successfully, display it
    if hourly_df is not None and daily_df is not None:
        st.header(f"2. Weather Forecast for (Lat: {lat:.4f}, Lon: {lon:.4f})")
        
        st.subheader("Hourly Forecast")
        
        # Create columns for side-by-side charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**Temperature & Apparent Temperature (°C)**")
            st.line_chart(hourly_df[["Temp (°C)", "Apparent Temp (°C)"]])
            
        with chart_col2:
            st.markdown("**Humidity (%)**")
            st.line_chart(hourly_df[["Humidity (%)"]])
        
        # --- Add new charts for the extra data ---
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            st.markdown("**Precipitation Probability (%)**")
            st.line_chart(hourly_df[["Precip. Prob. (%)"]])
        
        with chart_col4:
            st.markdown("**Precipitation (mm) & Snowfall (cm)**")
            st.line_chart(hourly_df[["Precip. (mm)", "Snow (cm)"]])

        chart_col5, chart_col6 = st.columns(2)

        with chart_col5:
            st.markdown("**Wind Speed (km/h)**")
            st.line_chart(hourly_df[["Wind Speed (km/h)"]])
        
        with chart_col6:
            st.markdown("**UV Index**")
            st.line_chart(hourly_df[["UV Index"]])
            
        st.subheader("7-Day Daily Forecast")
        # Display the daily forecast as a table
        st.dataframe(daily_df, use_container_width=True)

        st.subheader("Hourly Data Table (Raw)")
        # Display the full hourly data as an expandable table
        with st.expander("Click to see all hourly data"):
            st.dataframe(hourly_df, use_container_width=True)
        
else:
    # This is the default message shown before the user clicks
    st.info(
        "Click the map to fetch and display weather data for that location.  \n"
        "*(지도를 클릭하면 해당 지역의 날씨 데이터를 가져옵니다.)*"
    )

