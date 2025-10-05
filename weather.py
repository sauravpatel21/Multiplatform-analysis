import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import folium
from streamlit_folium import st_folium  
import plotly.express as px
import plotly.graph_objects as go


# Base URLs for OpenWeatherMap API
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
AIR_QUALITY_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# List of popular cities for dropdown
POPULAR_CITIES = [
    "London", "New York", "Tokyo", "Paris", "Berlin", 
    "Sydney", "Mumbai", "Dubai", "Singapore", "Toronto",
    "Beijing", "Rio de Janeiro", "Cape Town", "Moscow", "Rome"
]

# Color palette
COLOR_PALETTE = {
    'background': '#F0F2F6',
    'text': '#FFFFFF',
    'primary': '#FF4B4B',
    'secondary': '#1A73E8',
    'accent': '#32CD32'
}


def apply_custom_styles():
    """Apply custom CSS styles for better UI"""
    st.markdown(f"""
        <style>
            /* Main container padding */
            .stApp {{
                padding-top: 0;
            }}
            /* Title spacing */
            h1 {{
                margin-top: 0;
                padding-top: 0;
            }}
            /* Remove Streamlit header space */
            header {{
                display: none;
            }}
            /* Adjust sidebar spacing */
            .css-1vq4p4l {{
                padding-top: 1.5rem;
            }}
            /* Main content area padding */
            .block-container {{
                padding-top: 1rem;
                padding-bottom: 1rem;
            }}
        </style>
    """, unsafe_allow_html=True)


def get_weather_data(city, api_key):
    """Fetch current weather data for a given city."""
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_forecast_data(city, api_key):
    """Fetch 5-day weather forecast for a given city."""
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_air_quality_data(lat, lon, api_key):
    """Fetch air quality data for a given location."""
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
    }
    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def display_current_weather(data):
    """Display current weather with enhanced visualization."""
    if not data:
        return
    
    main = data['main']
    weather = data['weather'][0]
    wind = data['wind']
    sys = data['sys']
    clouds = data.get('clouds', {}).get('all', 0)
    visibility = data.get('visibility', 'N/A')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Temperature", f"{main['temp']}°C", 
                 f"{main['temp'] - main['feels_like']:.1f}°C from feels like")
        st.metric("Humidity", f"{main['humidity']}%")
        
    with col2:
        st.metric("Weather", weather['description'].capitalize())
        st.metric("Cloud Coverage", f"{clouds}%")
        
    with col3:
        st.metric("Wind", f"{wind['speed']} m/s", 
                 f"Direction: {wind.get('deg', 'N/A')}°")
        st.metric("Visibility", 
                 f"{visibility}m" if visibility != 'N/A' else visibility)
    
    # Weather alerts
    if main['temp'] > 35:
        st.warning("🔥 Extreme Heat Alert: Temperature is above 35°C! Stay hydrated and avoid prolonged sun exposure.")
    elif main['temp'] < 0:
        st.warning("❄️ Extreme Cold Alert: Temperature is below 0°C! Dress warmly and limit outdoor exposure.")
    
    if wind['speed'] > 10:
        st.warning("💨 High Wind Alert: Wind speed exceeds 10 m/s! Secure outdoor objects.")
    
    if main['humidity'] > 80:
        st.info("💧 High Humidity: May feel warmer than actual temperature.")
    elif main['humidity'] < 30:
        st.info("🏜️ Low Humidity: May cause dry skin and dehydration.")

def display_forecast(forecast_data):
    """Display 5-day weather forecast with enhanced visualization."""
    if not forecast_data:
        st.warning("No forecast data available.")
        return
    
    st.subheader("🌤️ 5-Day Weather Forecast")
    
    # Process forecast data
    forecast_list = forecast_data['list']
    daily_data = []
    
    for forecast in forecast_list:
        date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
        time = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
        temp = forecast['main']['temp']
        feels_like = forecast['main']['feels_like']
        weather = forecast['weather'][0]['description'].capitalize()
        wind_speed = forecast['wind']['speed']
        humidity = forecast['main']['humidity']
        
        daily_data.append({
            'Date': date,
            'Time': time,
            'Temperature': temp,
            'Feels Like': feels_like,
            'Weather': weather,
            'Wind Speed': wind_speed,
            'Humidity': humidity
        })
    
    df = pd.DataFrame(daily_data)
    
    # Group by date and aggregate data
    df_grouped = df.groupby('Date').agg({
        'Temperature': ['min', 'max', 'mean'],
        'Weather': lambda x: x.mode()[0],
        'Wind Speed': 'mean',
        'Humidity': 'mean'
    }).reset_index()
    
    # Flatten multi-index columns and rename
    df_grouped.columns = ['Date', 'Min Temp', 'Max Temp', 'Avg Temp', 
                         'Weather', 'Avg Wind Speed', 'Avg Humidity']
    
    # Display forecast cards
    cols = st.columns(len(df_grouped))
    
    for idx, (col, row) in enumerate(zip(cols, df_grouped.to_dict('records'))):
        with col:
            st.markdown(f"""
                <div style="
                    background:#33FF33;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    text-align: center;
                    margin-bottom: 10px;
                ">
                    <h4 style="margin: 0; color: {COLOR_PALETTE['primary']}">
                        {datetime.strptime(row['Date'], '%Y-%m-%d').strftime('%a, %b %d')}
                    </h4>
                    <p style="margin: 5px 0; font-size: 14px;">{row['Weather']}</p>
                    <p style="margin: 5px 0; font-size: 16px;">
                        <span style="color: {COLOR_PALETTE['secondary']}">↑{row['Max Temp']:.1f}°</span> / 
                        <span style="color: {COLOR_PALETTE['primary']}">↓{row['Min Temp']:.1f}°</span>
                    </p>
                    <p style="margin: 5px 0; font-size: 12px;">
                        🌬️ {row['Avg Wind Speed']:.1f} m/s | 💧 {row['Avg Humidity']:.0f}%
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    # Detailed forecast chart
    fig = px.line(df, x='Time', y='Temperature', color='Date',
                  title='Detailed Temperature Forecast',
                  labels={'Temperature': 'Temperature (°C)', 'Time': 'Time of Day'},
                  template='plotly_white')
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLOR_PALETTE['text']),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_air_quality(air_quality_data):
    """Display air quality index (AQI) with enhanced visualization."""
    if not air_quality_data:
        st.warning("No air quality data available.")
        return
    
    aqi = air_quality_data['list'][0]['main']['aqi']
    components = air_quality_data['list'][0]['components']
    
    # AQI scale information
    aqi_scale = {
        1: {"label": "Good", "color": "#00E400", "message": "Air quality is satisfactory."},
        2: {"label": "Fair", "color": "#FFFF00", "message": "Air quality is acceptable."},
        3: {"label": "Moderate", "color": "#FF7E00", "message": "Sensitive groups may experience health effects."},
        4: {"label": "Poor", "color": "#FF0000", "message": "Everyone may begin to experience health effects."},
        5: {"label": "Very Poor", "color": "#8F3F97", "message": "Health warnings of emergency conditions."}
    }
    
    current_level = aqi_scale.get(aqi, {"label": "Unknown", "color": "#666666", "message": "No data available."})
    
    # Create AQI gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = aqi,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Air Quality Index (AQI)"},
        gauge = {
            'axis': {'range': [None, 5], 'tickvals': [1, 2, 3, 4, 5]},
            'bar': {'color': current_level['color']},
            'steps': [
                {'range': [0, 1], 'color': "#00E400"},
                {'range': [1, 2], 'color': "#FFFF00"},
                {'range': [2, 3], 'color': "#FF7E00"},
                {'range': [3, 4], 'color': "#FF0000"},
                {'range': [4, 5], 'color': "#8F3F97"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': aqi
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color=COLOR_PALETTE['text'])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display AQI level and message
    st.markdown(f"""
        <div style="
            background: {current_level['color']}20;
            border-left: 4px solid {current_level['color']};
            padding: 10px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        ">
            <h4 style="margin: 0; color: {current_level['color']}">
                {current_level['label']} (AQI: {aqi})
            </h4>
            <p style="margin: 5px 0 0 0;">{current_level['message']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display pollutant components
    st.subheader("Pollutant Components (μg/m³)")
    
    pollutants = {
        'CO': components.get('co', 0),
        'NO₂': components.get('no2', 0),
        'O₃': components.get('o3', 0),
        'SO₂': components.get('so2', 0),
        'PM2.5': components.get('pm2_5', 0),
        'PM10': components.get('pm10', 0),
        'NH₃': components.get('nh3', 0)
    }
    
    cols = st.columns(len(pollutants))
    
    for col, (name, value) in zip(cols, pollutants.items()):
        with col:
            st.metric(name, f"{value:.1f}")

def display_map(lat, lon, city_name):
    """Display an interactive map with the city's location."""
    m = folium.Map(location=[lat, lon], zoom_start=10, tiles='cartodbpositron')
    
    # Add marker with custom icon
    folium.Marker(
        [lat, lon],
        popup=city_name,
        tooltip="Click for more info",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add circle for area
    folium.Circle(
        radius=5000,
        location=[lat, lon],
        color=COLOR_PALETTE['primary'],
        fill=True,
        fill_color=COLOR_PALETTE['primary']
    ).add_to(m)
    
    st_folium(m, width=800, height=500, returned_objects=[])


def main():
    """Main function to run the Streamlit app."""
    apply_custom_styles()

    # Set main page title
    st.title("🌦️ Weather Dashboard")
    
    # Initialize session state
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    
    # Sidebar for inputs
    with st.sidebar:
        st.title("📍 Location & Settings")
        st.markdown("""
            <div style="margin-bottom: 20px;">
                Configure your location and API settings to view weather information.
            </div>
        """, unsafe_allow_html=True)
  
        # Input for API key
        api_key = st.text_input("Enter your OpenWeatherMap API key:", type="password", 
                               help="Get a free API key from https://openweathermap.org/api")
        
        if not api_key:
            st.warning("Please enter your API key to proceed.")
            st.info("Don't have an API key? Get one for free at [OpenWeatherMap](https://openweathermap.org/api)")
            return
        
        # City input options
        st.subheader("📍 Select Location")
        input_method = st.radio("City input method:", 
                              ["Select from popular cities", "Enter custom city name"],
                              horizontal=True)
        
        if input_method == "Select from popular cities":
            city = st.selectbox("Choose a city:", POPULAR_CITIES)
        else:
            city = st.text_input("Enter city name:", placeholder="e.g., Chicago, Berlin, Tokyo")
        
        if not city:
            st.warning("Please select or enter a city name.")
            return
        
        if st.button("🚀 Get Weather Data", type="primary", use_container_width=True):
            st.session_state.analyze_clicked = True
    
    # Main content area
    if st.session_state.get('analyze_clicked', False):
        with st.spinner("Fetching weather data..."):
            # Fetch current weather data
            current_data = get_weather_data(city, api_key)
            
            if current_data:
                st.success(f"Successfully retrieved data for {current_data['name']}, {current_data['sys']['country']}")
                
                # Create tabs for different sections
                tab1, tab2, tab3 = st.tabs(["🌡️ Current", "🌤️ Forecast", "🌫️ Air Quality"])
                
                with tab1:
                    # Display current weather analysis
                    st.subheader(f"Current Weather in {current_data['name']}")
                    display_current_weather(current_data)
                    
                    # Weather summary
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"""
                            <div style="margin-top: 20px;">
                                <h2 style="margin-bottom: 5px;">{current_data['main']['temp']}°C</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                            <div style="margin-top: 20px;">
                                <p style="font-size: 18px; margin: 0;">
                                    {current_data['weather'][0]['description'].capitalize()}
                                </p>
                                <p style="font-size: 14px; margin: 5px 0 0 0;">
                                    Feels like {current_data['main']['feels_like']}°C
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                
                # Get coordinates for other APIs
                lat, lon = current_data['coord']['lat'], current_data['coord']['lon']
                
                with tab2:
                    # Fetch and display forecast
                    forecast_data = get_forecast_data(city, api_key)
                    display_forecast(forecast_data)
                
                with tab3:
                    # Fetch and display air quality
                    air_quality_data = get_air_quality_data(lat, lon, api_key)
                    display_air_quality(air_quality_data)
                
                # Display map below all tabs
                st.subheader(f"🗺️ Location of {current_data['name']}")
                display_map(lat, lon, current_data['name'])
                
            else:
                st.error(f"Failed to retrieve weather data for {city}. Please check:")
                st.error("- Your API key is valid")
                st.error("- The city name is spelled correctly")
                st.error("- You haven't exceeded your API quota")

if __name__ == "__main__":
    main()