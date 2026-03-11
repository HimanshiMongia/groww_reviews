import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components

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
    .main {
        background-color: #0f0f23;
        color: #e8e8f0;
    }
    .stMetric {
        background-color: #1a1a2e;
        border: 1px solid #2a2a45;
        border-radius: 12px;
        padding: 15px;
    }
    .stMarkdown h1 { color: #00d09c; }
    .stMarkdown h2 { color: #e8e8f0; border-bottom: 1px solid #2a2a45; padding-bottom: 10px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# -- DATA LOADING --
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_json(path):
    if not os.path.exists(path): return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return None

def load_text(path):
    if not os.path.exists(path): return ""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except: return ""

# Paths
reviews_path = os.path.join(PROJECT_ROOT, 'phase1_ingestion', 'groww_reviews_cleaned.json')
themes_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'discovered_themes.json')
classified_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'classified_reviews.json')
pulse_path = os.path.join(PROJECT_ROOT, 'phase3_note_generation', 'weekly_pulse.md')
email_path = os.path.join(PROJECT_ROOT, 'phase4_email_delivery', 'weekly_pulse_email.html')

# Load data
reviews = load_json(reviews_path) or []
themes_data = load_json(themes_path) or {"themes": []}
classified = load_json(classified_path) or []
pulse_md = load_text(pulse_path)
email_html = load_text(email_path)

# -- HEADER --
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown('<div style="background-color:#00d09c; color:#0f0f23; font-weight:bold; width:50px; height:50px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:24px;">G</div>', unsafe_allow_html=True)
with col_title:
    st.title("Groww Weekly Pulse")

if os.path.exists(pulse_path):
    mtime = os.path.getmtime(pulse_path)
    gen_time = datetime.fromtimestamp(mtime).strftime('%B %d, %Y at %I:%M %p')
    st.caption(f"Last Updated: {gen_time}")
else:
    st.caption("Status: Waiting for first pipeline run...")

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
    st.warning("No data found. Please run the pipeline first or push JSON files to GitHub.")

st.write("")

# -- DASHBOARD LAYOUT --
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Weekly Pulse", "📊 Analytics", "📝 Sample Reviews", "📧 Email Preview"])

with tab1:
    if pulse_md:
        st.markdown(pulse_md)
        st.download_button("Download Pulse Report", pulse_md, file_name="weekly_pulse.md")
    else:
        st.info("Weekly pulse report has not been generated yet.")

with tab2:
    st.subheader("Sentiment & Theme Insights")
    if classified:
        df_class = pd.DataFrame(classified)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Theme Distribution")
            if 'theme' in df_class.columns:
                theme_counts = df_class['theme'].value_counts().reset_index()
                theme_counts.columns = ['Theme', 'Count']
                fig_bar = px.bar(
                    theme_counts, x='Count', y='Theme', orientation='h',
                    color_discrete_sequence=['#00d09c'], template="plotly_dark"
                )
                fig_bar.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.error("Column 'theme' missing in classified data.")

        with c2:
            st.markdown("#### Rating Distribution")
            if 'rating(5star)' in df_class.columns:
                rating_counts = df_class['rating(5star)'].value_counts().sort_index().reset_index()
                rating_counts.columns = ['Rating', 'Count']
                fig_pie = px.pie(
                    rating_counts, values='Count', names='Rating', hole=0.4,
                    color_discrete_sequence=['#ef4444', '#ff6b35', '#eab308', '#5b86e5', '#00d09c'],
                    template="plotly_dark"
                )
                fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.error("Column 'rating(5star)' missing in reviews data.")
    else:
        st.info("No classified reviews found. Run the pipeline to see charts.")

with tab3:
    if classified:
        st.subheader("Categorized Reviews")
        df_disp = pd.DataFrame(classified)[['date time', 'rating(5star)', 'theme', 'review']]
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Waiting for data...")

with tab4:
    st.subheader("Email Report Preview")
    if email_html:
        st.info("This is how the automated email looks in the inbox:")
        components.html(email_html, height=800, scrolling=True)
    else:
        st.info("Email template not generated yet.")

# -- FOOTER --
st.markdown("---")
st.markdown("<div style='text-align: center; color: #a0a0b8; font-size: 12px;'>Build with ❤️ for Groww Product Team</div>", unsafe_allow_html=True)
