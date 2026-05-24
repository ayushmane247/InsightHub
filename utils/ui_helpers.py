import streamlit as st

def mobile_friendly_css():
    """Enhanced mobile CSS with better touch targets"""
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .stSelectbox > div > div {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        
        .stButton > button {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
        }
        
        .stDataFrame {
            font-size: 14px !important;
            overflow-x: auto !important;
        }
        
        /* Stack columns on mobile */
        .element-container {
            width: 100% !important;
        }
    }
    
    /* Progress indicators */
    .progress-container {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
    
    /* Status indicators */
    .status-critical { background-color: #ff4444; color: white; padding: 5px 10px; border-radius: 15px; }
    .status-warning { background-color: #ffaa00; color: white; padding: 5px 10px; border-radius: 15px; }
    .status-good { background-color: #00aa44; color: white; padding: 5px 10px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

def show_progress(step, total_steps, message):
    """Show progress with visual indicator"""
    progress = int((step / total_steps) * 100)
    st.markdown(f"""
    <div class="progress-container">
        <div>Step {step}/{total_steps}: {message}</div>
        <div style="background: rgba(255,255,255,0.3); border-radius: 5px; margin-top: 5px;">
            <div style="background: white; height: 8px; width: {progress}%; border-radius: 5px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)