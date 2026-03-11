import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# -- PAGE CONFIG --
st.set_page_config(
    page_title="Groww Weekly Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -- PREMIUM CSS --
st.markdown("""
    <style>
    /* Dark Premium Background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
        color: #e8e8f0;
    }
    
    /* Meta tags */
    .stApp > header { background: transparent; }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        color: #00d09c !important;
        font-weight: 700;
    }
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    h1 { color: #00d09c; font-weight: 800; }
    
    /* Cards for Themes */
    .theme-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 4px solid #00d09c;
    }
    .theme-header {
        color: #00d09c;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 10px;
    }
    .review-text {
        font-style: italic;
        color: #b0b0c0;
        font-size: 0.95rem;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: transparent;
        border-radius: 8px;
        color: #8080a0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 208, 156, 0.1) !important;
        color: #00d09c !important;
        border-bottom: 2px solid #00d09c !important;
    }
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

# Data
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

if pulse_md:
    mtime = os.path.getmtime(pulse_path)
    gen_time = datetime.fromtimestamp(mtime).strftime('%B %d, %Y at %I:%M %p')
    st.caption(f"Last Updated: {gen_time}")
else:
    st.caption("Status: Waiting for data pipeline run...")

st.markdown("---")

# -- KEY METRICS --
m1, m2, m3, m4 = st.columns(4)
if reviews:
    avg_rating = sum(r.get('rating(5star)', 0) for r in reviews) / len(reviews)
    m1.metric("Reviews Scanned", f"{len(reviews):,}")
    m2.metric("Avg. App Rating", f"{avg_rating:.2f} ⭐")
    m3.metric("Themes Identified", len(themes_data.get('themes', [])))
    m4.metric("Insights Generated", "3 Core")
else:
    st.info("Run the pipeline locally to populate metrics.")

# -- TABS --
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Weekly Pulse", "📊 Sentiment Analytics", "🔍 Theme Explorer", "📧 Email Preview"])

with tab1:
    if pulse_md:
        st.markdown(pulse_md)
        st.download_button("Download Report", pulse_md, file_name="groww_weekly_pulse.md")
    else:
        st.info("The Pulse Report will appear here once the pipeline runs.")

with tab2:
    if reviews:
        c1, c2 = st.columns([1.2, 1])
        
        with c1:
            st.subheader("Theme Volume")
            if classified:
                df_class = pd.DataFrame(classified)
                theme_counts = df_class['theme'].value_counts().reset_index()
                theme_counts.columns = ['Theme', 'Count']
                fig = px.bar(
                    theme_counts, x='Count', y='Theme', orientation='h',
                    color='Count', color_continuous_scale='Viridis',
                    template='plotly_dark'
                )
                fig.update_layout(showlegend=False, coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                
        with c2:
            st.subheader("Rating Breakdown")
            df_revs = pd.DataFrame(reviews)
            rating_counts = df_revs['rating(5star)'].value_counts().sort_index().reset_index()
            rating_counts.columns = ['Rating', 'Count']
            
            # Premium Doughnut Chart
            fig_donut = go.Figure(data=[go.Pie(
                labels=rating_counts['Rating'].apply(lambda x: f"{x} ⭐"),
                values=rating_counts['Count'],
                hole=.6,
                marker=dict(colors=['#ef4444', '#f97316', '#eab308', '#3b82f6', '#00d09c']),
                textinfo='label+percent'
            )])
            fig_donut.update_layout(
                template='plotly_dark',
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=450,
                annotations=[dict(text='Ratings', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No data available for charts.")

with tab3:
    st.subheader("Explore Reviews by Theme")
    if classified:
        df_class = pd.DataFrame(classified)
        selected_theme = st.selectbox("Select a Theme to Filter", ["All"] + sorted(list(df_class['theme'].unique())))
        
        filtered_df = df_class if selected_theme == "All" else df_class[df_class['theme'] == selected_theme]
        
        # Display as cards for premium look
        for _, row in filtered_df.head(20).iterrows():
            stars = "⭐" * int(row['rating(5star)'])
            st.markdown(f"""
                <div class="theme-card">
                    <div class="theme-header">{row['theme']} | {stars}</div>
                    <div class="review-text">"{row['review']}"</div>
                    <div style="font-size:0.8rem; color:#606080; margin-top:5px;">{row['date time']}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Classify reviews to see theme explorer.")

with tab4:
    if email_html:
        st.subheader("Automated Stakeholder Report")
        st.info("This is how the email pulse looks when delivered to the Groww leadership team.")
        components.html(email_html, height=800, scrolling=True)
    else:
        st.info("Email template not ready.")

# -- FOOTER --
st.markdown("---")
st.markdown("<div style='text-align: center; color: #a0a0b8; font-size: 12px;'>Build with ❤️ for Groww Product Team</div>", unsafe_allow_html=True)
