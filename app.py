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

def get_aqi_category(pm25):
    if pm25 is None:
        return "N/A", "#808080"
    if pm25 <= 12:
        return "Good", "#16a34a"
    elif pm25 <= 35.4:
        return "Satisfactory", "#ca8a04"
    elif pm25 <= 55.4:
        return "Moderate", "#ea580c"
    elif pm25 <= 150.4:
        return "Poor", "#dc2626"
    elif pm25 <= 250.4:
        return "Very Poor", "#7f1d1d"
    else:
        return "Severe", "#9f1239"

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

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:4px;">🌿 India AQI Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#64748b;margin-bottom:12px;">Real-time air quality · Open-Meteo API</div>', unsafe_allow_html=True)
    st.divider()
    selected_city = st.selectbox("📍 Select City", list(CITIES.keys()), index=0)
    auto_refresh = st.toggle("🔄 Auto Refresh (60s)", value=False)
    st.divider()
    st.markdown('<div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;">AQI SCALE (PM2.5)</div>', unsafe_allow_html=True)
    scale = [
        ("🟢", "Good",         "0-12 ug/m3",    "#16a34a"),
        ("🟡", "Satisfactory", "12-35 ug/m3",   "#ca8a04"),
        ("🟠", "Moderate",     "35-55 ug/m3",   "#ea580c"),
        ("🔴", "Poor",         "55-150 ug/m3",  "#dc2626"),
        ("🟤", "Very Poor",    "150-250 ug/m3", "#7f1d1d"),
        ("⚫", "Severe",       "250+ ug/m3",    "#9f1239"),
    ]
    for emoji, label, rng, clr in scale:
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px;"><span>{emoji}</span><span style="color:{clr};font-weight:600;">{label}</span><span style="color:#94a3b8;margin-left:auto;">{rng}</span></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div style="font-size:11px;color:#94a3b8;">Data: Open-Meteo · Free · No API key required</div>', unsafe_allow_html=True)

# ─── Global CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 3rem !important; }
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 12px !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #0f172a !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime('%d %b %Y, %I:%M %p')
st.markdown(f"""
<div style="padding-top:40px;margin-bottom:20px;">
    <div style="font-size:14px;color:#64748b;font-weight:500;letter-spacing:0.5px;margin-bottom:4px;">INDIA REAL-TIME</div>
    <div style="font-size:36px;font-weight:800;line-height:1.1;margin-bottom:8px;">
        <span style="color:#0f172a;">AQI </span>
        <span style="color:#16a34a;">Dashboard</span>
    </div>
    <div style="font-size:12px;color:#64748b;">
        Last refreshed: {now_str} · Deep dive: <strong>{selected_city}</strong>
    </div>
</div>
""", unsafe_allow_html=True)

conn = init_db()

# ─── All Cities Overview ─────────────────────────────────────────────────────────
st.markdown('<div style="font-size:15px;font-weight:700;color:#1e293b;margin:0 0 12px;">📊 All Cities Overview</div>', unsafe_allow_html=True)

city_data = []
with st.spinner("Fetching live data..."):
    for city, coords in CITIES.items():
        data = fetch_aqi(coords["lat"], coords["lon"])
        if data and "current" in data:
            curr = data["current"]
            pm25 = curr.get("pm2_5")
            pm10 = curr.get("pm10")
            ozone = curr.get("ozone")
            no2 = curr.get("nitrogen_dioxide")
            cat, color = get_aqi_category(pm25)
            city_data.append({
                "City": city,
                "PM2.5": round(pm25, 1) if pm25 else None,
                "PM10": round(pm10, 1) if pm10 else None,
                "Ozone": round(ozone, 1) if ozone else None,
                "NO2": round(no2, 1) if no2 else None,
                "Category": cat,
                "Color": color,
            })
            save_reading(conn, city, pm25, pm10, ozone, no2, cat)

if city_data:
    df_all = pd.DataFrame(city_data)

    # ── Cards ─────────────────────────────────────────────────────────────────
    card_html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:1.5rem;">'
    for _, row in df_all.iterrows():
        c = row['Color']
        card_html += (
            f'<div style="background:#ffffff;border:1px solid #e2e8f0;border-top:4px solid {c};'
            f'border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
            f'<div style="font-size:12px;font-weight:600;color:#64748b;margin-bottom:8px;'
            f'text-transform:uppercase;letter-spacing:0.5px;">{row["City"]}</div>'
            f'<div style="font-size:32px;font-weight:800;color:{c};line-height:1;margin-bottom:4px;">'
            f'{row["PM2.5"] or "N/A"}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-bottom:10px;">PM2.5 ug/m3</div>'
            f'<div style="display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;'
            f'border-radius:20px;color:{c};background:rgba(0,0,0,0.04);border:1px solid {c};">'
            f'{row["Category"]}</div></div>'
        )
    card_html += '</div>'
    st.markdown(card_html, unsafe_allow_html=True)

    st.divider()

    # ── Bar Chart ─────────────────────────────────────────────────────────────
    df_sorted = df_all.sort_values("PM2.5", ascending=True).reset_index(drop=True)
    bar_colors = [row["Color"] for _, row in df_sorted.iterrows()]

    fig_bar = px.bar(
        df_sorted,
        x="PM2.5", y="City",
        orientation="h",
        title="PM2.5 Levels Across Indian Cities (ug/m3)",
        height=380,
        text="PM2.5",
    )
    fig_bar.update_traces(marker_color=bar_colors, textposition="outside")
    fig_bar.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1e293b",
        title_font_size=14,
        xaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#f1f5f9", showgrid=False),
        margin=dict(l=0, r=60, t=40, b=0),
        bargap=0.3,
        coloraxis_showscale=False,
    )
    fig_bar.add_vline(
        x=35.4,
        line_dash="dash",
        line_color="#ca8a04",
        annotation_text="Moderate",
        annotation_font_color="#ca8a04",
        annotation_position="top",
        annotation_font_size=11,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── Deep Dive ───────────────────────────────────────────────────────────────────
st.markdown(f'<div style="font-size:15px;font-weight:700;color:#1e293b;margin:8px 0 10px;">🔍 Deep Dive — {selected_city}</div>', unsafe_allow_html=True)

coords = CITIES[selected_city]
data = fetch_aqi(coords["lat"], coords["lon"])

if data:
    curr = data.get("current", {})
    pm25 = curr.get("pm2_5")
    pm10 = curr.get("pm10")
    ozone = curr.get("ozone")
    no2 = curr.get("nitrogen_dioxide")
    cat, color = get_aqi_category(pm25)

    if pm25 and pm25 > 150:
        st.error(f"🚨 **Health Alert** — {selected_city} AQI is {cat}. Avoid outdoor activities.")
    elif pm25 and pm25 > 55:
        st.warning(f"⚠️ **Caution** — {selected_city} AQI is {cat}. Sensitive groups should limit exposure.")
    else:
        st.success(f"✅ **{selected_city} AQI is {cat}** — Air quality is acceptable.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PM2.5 (ug/m3)", f"{round(pm25,1) if pm25 else 'N/A'}")
    m2.metric("PM10 (ug/m3)",  f"{round(pm10,1) if pm10 else 'N/A'}")
    m3.metric("Ozone (ug/m3)", f"{round(ozone,1) if ozone else 'N/A'}")
    m4.metric("NO2 (ug/m3)",   f"{round(no2,1) if no2 else 'N/A'}")

    hourly = data.get("hourly", {})
    if hourly and "time" in hourly:
        df_hourly = pd.DataFrame({
            "Time":  pd.to_datetime(hourly["time"]),
            "PM2.5": hourly.get("pm2_5", []),
            "PM10":  hourly.get("pm10", []),
            "Ozone": hourly.get("ozone", []),
            "NO2":   hourly.get("nitrogen_dioxide", []),
        }).dropna()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["PM2.5"], name="PM2.5", line=dict(color="#ea580c", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["PM10"],  name="PM10",  line=dict(color="#dc2626", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["Ozone"], name="Ozone", line=dict(color="#16a34a", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["NO2"],   name="NO2",   line=dict(color="#7c3aed", width=2)))
        fig_trend.add_hrect(y0=0,    y1=35.4,  fillcolor="#16a34a", opacity=0.06, line_width=0)
        fig_trend.add_hrect(y0=35.4, y1=55.4,  fillcolor="#ca8a04", opacity=0.06, line_width=0)
        fig_trend.add_hrect(y0=55.4, y1=150.4, fillcolor="#ea580c", opacity=0.06, line_width=0)
        fig_trend.update_layout(
            title=f"24-Hour Pollutant Trend — {selected_city}",
            xaxis_title="Time",
            yaxis_title="Concentration (ug/m3)",
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            font_color="#1e293b",
            xaxis=dict(gridcolor="#e2e8f0"),
            yaxis=dict(gridcolor="#e2e8f0"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=380,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    if all([pm25, pm10, ozone, no2]):
        fig_radar = go.Figure(go.Scatterpolar(
            r=[pm25, pm10, ozone, no2, pm25],
            theta=["PM2.5", "PM10", "Ozone", "NO2", "PM2.5"],
            fill="toself",
            fillcolor="rgba(234,88,12,0.15)",
            line=dict(color="#ea580c"),
            name=selected_city
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor="#e2e8f0"),
                bgcolor="#f8fafc",
            ),
            title=f"Pollutant Profile — {selected_city}",
            paper_bgcolor="#ffffff",
            font_color="#1e293b",
            height=350,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_radar, use_container_width=True)
        with col2:
            hist = get_history(conn, selected_city, 48)
            if not hist.empty:
                hist["timestamp"] = pd.to_datetime(hist["timestamp"])
                fig_hist = px.line(
                    hist, x="timestamp", y="pm25",
                    title="Stored History — PM2.5",
                    labels={"pm25": "PM2.5 (ug/m3)", "timestamp": "Time"},
                    color_discrete_sequence=["#7c3aed"],
                    height=350,
                )
                fig_hist.update_layout(
                    plot_bgcolor="#f8fafc",
                    paper_bgcolor="#ffffff",
                    font_color="#1e293b",
                    xaxis=dict(gridcolor="#e2e8f0"),
                    yaxis=dict(gridcolor="#e2e8f0"),
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("History builds as you refresh. Check back in a few minutes!")
else:
    st.error("Could not fetch data. Check your internet connection.")

# ─── Raw Table ───────────────────────────────────────────────────────────────────
if city_data:
    with st.expander("📋 View Raw Data Table"):
        st.dataframe(df_all.drop(columns=["Color"]), use_container_width=True, hide_index=True)

# ─── Auto Refresh ────────────────────────────────────────────────────────────────
if auto_refresh:
    st.caption("⏱ Auto-refreshing every 60 seconds...")
    time.sleep(60)
    st.rerun()
