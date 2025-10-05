import streamlit as st

def show():
    # Custom CSS for the steps layout
    st.markdown("""
    <style>
        .steps-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
        }
        .step-card {
            
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            flex: 1 1 calc(50% - 20px);
            min-width: 250px;
            min-height: 160px;
            display: flex;
            flex-direction: column;
        }
        .step-number {
            font-size: 1.5rem;
            font-weight: bold;
            color: #FFFFFF;
            margin-bottom: 10px;
        }
        .step-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: #FFFFFF;
        }
        .step-content {
            flex-grow: 1;
            color: #FFFFFF;
        }
        .pointer-left {
            text-align: left;
            margin-top: 20px;
            font-size: 40px;
        }
        @media (max-width: 768px) {
            .step-card {
                flex: 1 1 100%;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    
        <h1 style='color:#FFFFFF;text-align:center;margin:0'>📊 Multiplatform Analytics Dashboard</h1>
        <p style='text-align:center;color:#FFFFFF;margin-top:10px'>
        Your one-stop solution for comprehensive data analysis across multiple platforms
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # How to Use section - now with 2 steps per row
    st.markdown("### 🚀 How to Use the App")
    
    steps = [
        {"number": "1.", "title": "Select Platform", "content": "Choose your analytics platform from the sidebar navigation menu"},
        {"number": "2.", "title": "Upload Data", "content": "Connect to APIs or upload your data files in supported formats"},
        {"number": "3.", "title": "View Insights", "content": "Explore interactive dashboards with charts and metrics"},
        {"number": "4.", "title": "Export Reports", "content": "Generate and download reports in PDF format"}
    ]
    
    # Create the steps container
    st.markdown('<div class="steps-container">', unsafe_allow_html=True)
    
    # Add step cards
    for step in steps:
        st.markdown(f"""
        <div class="step-card">
            <div class="step-number">{step['number']}</div>
            <div class="step-title">{step['title']}</div>
            <div class="step-content">{step['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Platforms section
    st.header("🌟 Available Platforms", divider='rainbow')
    
    platforms = [
        {"title": "📺 YouTube Analytics", "desc": "Analyze channel performance metrics", "color": "#660000", "bg_color": "#FF0000"},
        {"title": "📈 Business Analytics", "desc": "Analyze business data, including sales, revenue, and customer insights.", "color": "#808000", "bg_color": "#FFFF00"},
        {"title": "📄 PDF Analytics", "desc": "Analyze and compare PDF files, including word count, readability, and more.", "color": "#660066", "bg_color": "#FF00FF"},
        {"title": "💻 Python Code Analytics", "desc": "Analyze Python code structure, metrics, and dependencies.", "color": "#0000FF", "bg_color": "#00FFFF"},
        {"title": "🌦️ Weather Analytics", "desc": "Analyze weather data, including current conditions, forecasts.", "color": "#066306", "bg_color": "#00FF00"}
    ]
    
    # Display platforms 2 per row
    for i in range(0, len(platforms), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(platforms):
                with cols[j]:
                    p = platforms[i + j]
                    st.markdown(f"""
                    <div style='background-color:{p['bg_color']}; border-left: 4px solid {p['color']};
                                padding: 20px; border-radius: 10px; margin-bottom: 20px; height: 180px;'>
                        <h3 style='color:{p['color']}; margin-top:0'>{p['title']}</h3>
                        <p style='color:#000000'>{p['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Left-aligned finger pointer
    st.markdown("""
    
        <h2 style='color:#FFFFFF'>Ready to Get Started?</h2>
        <p style='margin-bottom:10px'>Select a platform from the sidebar to begin your analysis journey</p>
        <div class="pointer-left">👈</div>
    </div>
    """, unsafe_allow_html=True)