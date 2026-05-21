import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import time
st.set_page_config(
    page_title="India AQI Monitor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ─── City Data ────────────────────────────────────────────────────────────────────
CITIES = {
    "Nagpur":    {"lat": 21.1458, "lon": 79.0882},
    "Delhi":     {"lat": 28.6139, "lon": 77.2090},
    "Mumbai":    {"lat": 19.0760, "lon": 72.8777},
    "Pune":      {"lat": 18.5204, "lon": 73.8567},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Chennai":   {"lat": 13.0827, "lon": 80.2707},
    "Kolkata":   {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Jaipur":    {"lat": 26.9124, "lon": 75.7873},
}
# ─── AQI Categories ──────────────────────────────────────────────────────────────
def get_aqi_category(pm25):
    if pm25 is None:
        return "N/A", "#94a3b8", "#f1f5f9"
    if pm25 <= 12:
        return "Good", "#059669", "#ecfdf5"
    elif pm25 <= 35.4:
        return "Satisfactory", "#d97706", "#fffbeb"
    elif pm25 <= 55.4:
        return "Moderate", "#ea580c", "#fff7ed"
    elif pm25 <= 150.4:
        return "Poor", "#dc2626", "#fef2f2"
    elif pm25 <= 250.4:
        return "Very Poor", "#7c3aed", "#f5f3ff"
    else:
        return "Severe", "#be123c", "#fff1f2"
# ─── Database ─────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("aqi_history.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT, timestamp TEXT,
            pm25 REAL, pm10 REAL,
            ozone REAL, no2 REAL, category TEXT
        )
    """)
    conn.commit()
    return conn
def save_reading(conn, city, pm25, pm10, ozone, no2, category):
    conn.execute(
        "INSERT INTO readings (city, timestamp, pm25, pm10, ozone, no2, category) VALUES (?,?,?,?,?,?,?)",
        (city, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pm25, pm10, ozone, no2, category)
    )
    conn.commit()
def get_history(conn, city, hours=24):
    df = pd.read_sql_query(
        "SELECT * FROM readings WHERE city=? ORDER BY timestamp DESC LIMIT ?",
        conn, params=(city, hours)
    )
    return df
# ─── API Fetch ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_aqi(lat, lon):
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&current=pm2_5,pm10,ozone,nitrogen_dioxide"
        f"&hourly=pm2_5,pm10,ozone,nitrogen_dioxide"
        f"&timezone=Asia%2FKolkata&past_days=1"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
# ─── Global CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');
    /* ── Foundation ──────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    /* ── Scrollbar ──────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    /* ── Sidebar ────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f4f8 0%, #e8edf3 100%) !important;
        border-right: 1px solid #dde3ea !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stToggle label {
        color: #475569 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    /* ── Metric Cards ──────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 18px 20px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.07) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #0f172a !important;
        font-size: 26px !important;
        font-weight: 800 !important;
    }
    /* ── Expander ───────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }
    /* ── Alerts ─────────────────────────────────────────── */
    .stAlert > div {
        border-radius: 12px !important;
    }
    /* ── Divider ────────────────────────────────────────── */
    hr {
        border-color: #e2e8f0 !important;
    }
    /* ── Animations ─────────────────────────────────────── */
    @keyframes slide-up {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes breathe {
        0%, 100% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.15); }
    }
</style>
""", unsafe_allow_html=True)
# ─── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:6px 0 2px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;border-radius:10px;
                        background:linear-gradient(135deg,#0d9488,#14b8a6);
                        display:flex;align-items:center;justify-content:center;
                        font-size:16px;box-shadow:0 2px 8px rgba(13,148,136,0.25);">
                🌿
            </div>
            <div>
                <div style="font-size:15px;font-weight:800;color:#0f172a;letter-spacing:-0.3px;">
                    AQI Monitor
                </div>
                <div style="font-size:10px;color:#94a3b8;font-weight:500;">
                    India · Real-time
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    selected_city = st.selectbox("📍 Select City", list(CITIES.keys()), index=0)
    auto_refresh = st.toggle("🔄 Auto Refresh (60s)", value=False)
    st.divider()
    # AQI Scale Legend
    st.markdown('<div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Air Quality Index</div>', unsafe_allow_html=True)
    scale_items = [
        ("Good",         "0 – 12",   "#059669"),
        ("Satisfactory", "12 – 35",  "#d97706"),
        ("Moderate",     "35 – 55",  "#ea580c"),
        ("Poor",         "55 – 150", "#dc2626"),
        ("Very Poor",    "150 – 250","#7f1d1d"),
        ("Severe",       "250+",     "#be123c"),
    ]
    for label, rng, clr in scale_items:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:4px 0;">
            <div style="width:3px;height:18px;border-radius:2px;background:{clr};flex-shrink:0;"></div>
            <span style="font-size:12px;font-weight:600;color:#334155;flex:1;">{label}</span>
            <span style="font-size:11px;color:#94a3b8;font-weight:500;">{rng}</span>
        </div>
        """, unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="font-size:10px;color:#94a3b8;line-height:1.7;">
        📡 Open-Meteo API<br>🔓 Free · No key required
    </div>
    """, unsafe_allow_html=True)
# ─── Header ───────────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime('%d %b %Y, %I:%M %p')
st.markdown(f"""
<div style="margin-bottom:24px;animation:slide-up 0.5s ease-out;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <div style="font-size:32px;font-weight:900;color:#0f172a;letter-spacing:-0.8px;line-height:1.1;">
            India Real-Time
        </div>
    </div>
    <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:10px;">
        <div style="font-size:32px;font-weight:900;letter-spacing:-0.8px;line-height:1.1;">
            <span style="color:#0f172a;">AQI </span><span style="color:#0d9488;">Dashboard</span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:7px;height:7px;border-radius:50%;background:#10b981;
                    animation:breathe 2.5s ease-in-out infinite;
                    box-shadow:0 0 6px rgba(16,185,129,0.4);"></div>
        <span style="font-size:12px;color:#64748b;font-weight:500;">
            Last refreshed: {now_str} · Deep dive: <strong style="color:#0f172a;">{selected_city}</strong>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)
conn = init_db()
# ─── Section Title Helper ─────────────────────────────────────────────────────────
def section_title(emoji, text):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:6px;margin:10px 0 14px;">
        <span style="font-size:14px;">{emoji}</span>
        <span style="font-size:14px;font-weight:700;color:#0f172a;">{text}</span>
    </div>
    """, unsafe_allow_html=True)
# ─── Shared Chart Layout ──────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155", size=12),
    xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", tickfont=dict(color="#64748b", size=11)),
    yaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", tickfont=dict(color="#64748b", size=11)),
    margin=dict(l=0, r=20, t=56, b=20),
)
# ─── All Cities Overview ─────────────────────────────────────────────────────────
section_title("📊", "All Cities Overview")
    st.divider()
    # ── Plotly shared layout ───────────────────────────────────────────────────
    CHART_LAYOUT = dict(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155", size=12),
        xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", tickfont=dict(color="#64748b", size=11)),
        yaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#f1f5f9", tickfont=dict(color="#64748b", size=11)),
        margin=dict(l=0, r=20, t=56, b=20),
    )
    # ── Bar Chart ──────────────────────────────────────────────────────────────
    df_sorted = df_all.sort_values("PM2.5", ascending=True)
    fig_bar = px.bar(
    time.sleep(60)
    st.rerun()
