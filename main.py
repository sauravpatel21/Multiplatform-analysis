import streamlit as st

# Streamlit App Configuration
st.set_page_config(
    page_title="Multiplatform Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from home import show as home_show
from youtube import main as youtube_main
from business import main as business_main
from PDF_Analytics_and_Comparison_Tool import main as pdf_main
from python_CODE import main as code_main
from weather import main as weather_main


# Custom CSS for green home button
st.markdown("""
<style>
    div[data-testid="stButton"] button:contains('🏠 Home') {
        background-color: #28a745 !important;
        color: white !important;
        border: 1px solid #28a745 !important;
    }
    div[data-testid="stButton"] button:contains('🏠 Home'):hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    .empty-selectbox .stSelectbox > div > div {
        color: #999 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
    st.session_state.last_nav = None
    st.session_state.platform_selected = False  # Track if platform has been selected

# Handle page transition
if st.session_state.current_page == "Code Analytics":
    st.session_state.current_page = "Python Code Analytics"

# Sidebar navigation
with st.sidebar:
    # Sidebar header with logo
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <h1 style="margin: 0;">🔍 Explore Analytics</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Platform options with icons for selectbox
    platform_options = {
        "": "Select a platform...",  # Empty default option
        "YouTube Analytics": "📺",
        "Business Analytics": "💼", 
        "PDF Analytics": "📄",
        "Python Code Analytics": "🐍",
        "Weather Analytics": "⛅"
    }
    
    # Add empty-selectbox class if no platform selected
    selectbox_class = "empty-selectbox" if not st.session_state.platform_selected else ""
    
    # Platform selection as selectbox with help text
    selected_platform = st.selectbox(
        "Select Platform",
        options=list(platform_options.keys()),
        index=0,  # Always default to empty option
        format_func=lambda x: f"{platform_options[x]} {x}" if x else platform_options[x],
        key="platform_select",
        help="Choose the platform you want to analyze."
    )
    
    # Navigation logic
    if selected_platform and (selected_platform != st.session_state.current_page and 
        st.session_state.get("last_nav") != "home_button"):
        st.session_state.current_page = selected_platform
        st.session_state.last_nav = "selectbox"
        st.session_state.platform_selected = True
        st.rerun()
    
    # Spacer to push home button down
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    # Green Home button at the bottom with help text
    if st.button("🏠 Home", 
                key="home_button", 
                use_container_width=True,
                help="Return to the main dashboard homepage"):
        st.session_state.current_page = "Home"
        st.session_state.last_nav = "home_button"
        st.session_state.platform_selected = False
        st.rerun()
    
    # Reset navigation source
    st.session_state.last_nav = None

# Page routing
page_functions = {
    "Home": home_show,
    "YouTube Analytics": youtube_main,
    "Business Analytics": business_main,
    "PDF Analytics": pdf_main,
    "Python Code Analytics": code_main,
    "Weather Analytics": weather_main
}

# Display current page
current_page = st.session_state.get("current_page", "Home")
if current_page in page_functions:
    page_functions[current_page]()
else:
    st.session_state.current_page = "Home"
    st.rerun()

# Main content footer
st.markdown("---")
st.write("© 2025 Multiplatform Analytics Dashboard. All rights reserved.")  