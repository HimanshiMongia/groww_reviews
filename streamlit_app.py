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
    /* Remove fixed background color to let user theme handle it */
    .stApp > header { background: transparent; }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        color: #00d09c !important;
        font-weight: 700;
        font-size: 2.2rem !important;
    }
    
    [data-testid="metric-container"] {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.5px;
    }
    h1 { color: #00d09c; font-weight: 800; }
    h2 { margin-top: 1.5rem !important; }
    
    /* Cards for Themes */
    .theme-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-left: 4px solid #00d09c;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .theme-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        background: rgba(128, 128, 128, 0.1);
    }
    .theme-header {
        color: #00d09c;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
    .review-text {
        font-style: italic;
        opacity: 0.8;
        font-size: 0.9rem;
    }
    
    /* Section Divider */
    .section-divider {
        height: 1px;
        background: rgba(128, 128, 128, 0.2);
        margin: 2rem 0;
    }
    
    .footer-text {
        text-align: center;
        opacity: 0.7;
        font-size: 12px;
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
    st.markdown("""
        *A weekly pulse of Groww app's user sentiment. Reviews are automatically scraped from the Google Play Store 
        and updated every week to provide actionable product insights.*
    """)

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
    
    st.write("")
    st.write("")
    
    # -- INTEGRATED ANALYTICS (Directly below metrics) --
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.subheader("📊 Theme Distribution")
        if classified:
            df_class = pd.DataFrame(classified)
            theme_counts = df_class['theme'].value_counts().reset_index()
            theme_counts.columns = ['Theme', 'Count']
            
            # Custom Sort: Decreasing order, but 'Other' at the end
            others_mask = theme_counts['Theme'].str.lower().isin(['other', 'others'])
            df_others = theme_counts[others_mask]
            df_main = theme_counts[~others_mask].sort_values('Count', ascending=True) # Asc for horizontal plot
            
            # Combine back (Main themes first, then Other)
            # Since Plotly horizontal bars plot bottom-to-top, we reverse the logical order
            # To show highest on TOP: [Other, ...Smallest, ...Largest]
            final_df = pd.concat([df_others, df_main])
            
            fig = px.bar(
                final_df, x='Count', y='Theme', orientation='h',
                color='Count', color_continuous_scale='Viridis'
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False, height=350, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("🎯 Rating Distribution")
        df_revs = pd.DataFrame(reviews)
        rating_counts = df_revs['rating(5star)'].value_counts().sort_index().reset_index()
        rating_counts.columns = ['Rating', 'Count']
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=rating_counts['Rating'].apply(lambda x: f"{x} ⭐"),
            values=rating_counts['Count'],
            hole=.6,
            marker=dict(colors=['#ef4444', '#f97316', '#eab308', '#3b82f6', '#00d09c']),
            textinfo='label+percent'
        )])
        fig_donut.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=350,
            annotations=[dict(text='Ratings', x=0.5, y=0.5, font_size=18, showarrow=False, font_color="#00d09c")]
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
else:
    st.info("No data available. Run the pipeline locally or in cloud.")

# -- TABS (Rest of the features) --
tab1, tab2, tab3 = st.tabs(["🎯 Weekly Pulse Report", "🔍 Theme Explorer", "📧 Email Preview"])

with tab1:
    if pulse_md:
        st.markdown(pulse_md)
        st.download_button("Download Report", pulse_md, file_name="groww_weekly_pulse.md")
    else:
        st.info("Weekly pulse report not generated.")

with tab2:
    st.subheader("Review Deep Dive")
    if classified:
        df_class = pd.DataFrame(classified)
        
        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            selected_theme = st.selectbox("Filter by Theme", ["All"] + sorted(list(df_class['theme'].unique())))
        with c_filter2:
            st.write("") # Spacer
            st.write(f"*Showing top reviews for **{selected_theme}***")

        filtered_df = df_class if selected_theme == "All" else df_class[df_class['theme'] == selected_theme]
        
        # Display cards
        for _, row in filtered_df.head(30).iterrows():
            stars = "⭐" * int(row['rating(5star)'])
            st.markdown(f"""
                <div class="theme-card">
                    <div class="theme-header">{row['theme']} | {stars}</div>
                    <div class="review-text">"{row['review']}"</div>
                    <div style="font-size:0.75rem; color:#606080; margin-top:5px;">Date: {row['date time']}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No classified reviews available.")

with tab3:
    if email_html:
        st.subheader("Stakeholder Email Preview")
        components.html(email_html, height=800, scrolling=True)
    else:
        st.info("Email template not ready.")

# -- FOOTER --
st.markdown("---")
st.markdown("<div class='footer-text'>Build with ❤️ for Groww Product Team</div>", unsafe_allow_html=True)
