import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -- PAGE CONFIG --
st.set_page_config(
    page_title="Groww Weekly Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -- THEME & STYLING --
st.markdown("""
    <style>
    /* Main Background */
    .main {
        background-color: #0f0f23;
        color: #e8e8f0;
    }
    /* Card Styling */
    .stMetric {
        background-color: #1a1a2e;
        border: 1px solid #2a2a45;
        border-radius: 12px;
        padding: 15px;
    }
    .stMarkdown h1 {
        color: #00d09c;
    }
    .stMarkdown h2 {
        color: #e8e8f0;
        border-bottom: 1px solid #2a2a45;
        padding-bottom: 10px;
    }
    /* Hide Streamlit Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Theme Bar */
    .theme-bar-container {
        background-color: #2a2a45;
        border-radius: 10px;
        height: 10px;
        width: 100%;
        margin-bottom: 15px;
    }
    .theme-bar-fill {
        height: 100%;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# -- DATA LOADING --
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_json(path):
    print(f"Attempting to load JSON: {path}")
    if not os.path.exists(path): 
        print(f"File NOT found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON {path}: {e}")
        return None

def load_text(path):
    print(f"Attempting to load TEXT: {path}")
    if not os.path.exists(path): 
        print(f"File NOT found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading TEXT {path}: {e}")
        return None

# Load data paths
reviews_path = os.path.join(PROJECT_ROOT, 'phase1_ingestion', 'groww_reviews_cleaned.json')
themes_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'discovered_themes.json')
classified_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'classified_reviews.json')
pulse_path = os.path.join(PROJECT_ROOT, 'phase3_note_generation', 'weekly_pulse.md')

reviews = load_json(reviews_path) or []
themes_data = load_json(themes_path) or {"themes": []}
classified = load_json(classified_path) or []
pulse_md = load_text(pulse_path) or "## No Pulse Data Available\nRun the pipeline to generate insights."

# -- HEADER --
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown('<div style="background-color:#00d09c; color:#0f0f23; font-weight:bold; width:50px; height:50px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:24px;">G</div>', unsafe_allow_html=True)
with col_title:
    st.title("Groww Weekly Pulse")

# Metadata / Timestamp
if os.path.exists(pulse_path):
    mtime = os.path.getmtime(pulse_path)
    gen_time = datetime.fromtimestamp(mtime).strftime('%B %d, %Y at %I:%M %p')
    st.caption(f"Last Updated: {gen_time}")
else:
    st.caption(f"Status: Waiting for first pipeline run...")

st.markdown("---")

# -- STATS SECTION --
col1, col2, col3, col4 = st.columns(4)

if reviews:
    total_revs = len(reviews)
    avg_rating = sum(r.get('rating(5star)', 0) for r in reviews) / total_revs
    classified_count = len(classified)
    theme_count = len(themes_data.get('themes', []))
    
    col1.metric("Total Reviews", f"{total_revs:,}")
    col2.metric("Avg Rating", f"{avg_rating:.2f} / 5")
    col3.metric("Classified", f"{classified_count:,}")
    col4.metric("Themes Found", theme_count)
else:
    st.warning("No data found. Please run the pipeline first.")

st.write("")

# -- DASHBOARD LAYOUT --
tab1, tab2, tab3 = st.tabs(["🎯 Weekly Pulse", "📊 Analytics", "📝 Sample Reviews"])

with tab1:
    st.markdown(pulse_md)

with tab2:
    if classified:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Theme Distribution")
            df_class = pd.DataFrame(classified)
            if not df_class.empty and 'theme' in df_class.columns:
                theme_counts = df_class['theme'].value_counts().reset_index()
                theme_counts.columns = ['Theme', 'Count']
                
                fig_bar = px.bar(
                    theme_counts, 
                    x='Count', 
                    y='Theme', 
                    orientation='h',
                    color_discrete_sequence=['#00d09c'],
                    template="plotly_dark"
                )
                fig_bar.update_layout(xaxis_title="Number of Reviews", yaxis_title="")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No theme data available to chart.")
            
        with col_c2:
            st.subheader("Rating distribution")
            df_revs = pd.DataFrame(reviews)
            if not df_revs.empty and 'rating(5star)' in df_revs.columns:
                rating_counts = df_revs['rating(5star)'].value_counts().sort_index().reset_index()
                rating_counts.columns = ['Rating', 'Count']
                
                fig_pie = px.pie(
                    rating_counts, 
                    values='Count', 
                    names='Rating', 
                    hole=0.4,
                    color_discrete_sequence=['#ef4444', '#ff6b35', '#eab308', '#5b86e5', '#00d09c'],
                    template="plotly_dark"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No rating data available to chart.")
    else:
        st.info("Run classification to see analytics.")

with tab3:
    if classified:
        st.subheader("Recent Classified Reviews")
        df_display = pd.DataFrame(classified)[['date time', 'rating(5star)', 'theme', 'review']]
        st.dataframe(
            df_display.head(50), 
            hide_index=True,
            use_container_width=True,
            column_config={
                "date time": "Date",
                "rating(5star)": st.column_config.NumberColumn("Rating", format="%d ⭐"),
                "theme": "Theme",
                "review": "Content"
            }
        )
    else:
        st.info("Reviews will appear here after classification.")

# -- FOOTER --
st.markdown("---")
st.markdown("<div style='text-align: center; color: #a0a0b8; font-size: 12px;'>Build with ❤️ for Groww Product Team</div>", unsafe_allow_html=True)
