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
        return "Good", "#00e400"
    elif pm25 <= 35.4:
        return "Satisfactory", "#ffff00"
    elif pm25 <= 55.4:
        return "Moderate", "#ff7e00"
    elif pm25 <= 150.4:
        return "Poor", "#ff0000"
    elif pm25 <= 250.4:
        return "Very Poor", "#8f3f97"
    else:
        return "Severe", "#7e0023"

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
    st.markdown("## 🌿 India AQI Monitor")
    st.markdown("Real-time air quality from Open-Meteo — updated every 10 min.")
    st.divider()
    selected_city = st.selectbox("📍 Select City", list(CITIES.keys()), index=0)
    auto_refresh = st.toggle("🔄 Auto Refresh (60s)", value=False)
    st.divider()
    st.markdown("**AQI Scale (PM2.5)**")
    scale = {
        "🟢 Good": "0–12 µg/m³",
        "🟡 Satisfactory": "12–35 µg/m³",
        "🟠 Moderate": "35–55 µg/m³",
        "🔴 Poor": "55–150 µg/m³",
        "🟣 Very Poor": "150–250 µg/m³",
        "🔵 Severe": "250+ µg/m³",
    }
    for k, v in scale.items():
        st.markdown(f"<div style='font-size:12px'>{k} — {v}</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<div style='font-size:11px;color:gray;'>Data: Open-Meteo · Free · No API key</div>", unsafe_allow_html=True)

# ─── Global CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem !important; }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────────
st.markdown('<div style="font-size:28px;font-weight:800;color:#ffffff;margin-bottom:6px;padding-top:6px;letter-spacing:-0.5px;">🌍 India Real-Time AQI Dashboard</div>', unsafe_allow_html=True)
st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}  ·  Deep dive: **{selected_city}**")

conn = init_db()

# ─── All Cities ──────────────────────────────────────────────────────────────────
st.subheader("📊 All Cities Overview")

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

    # ── Cards — 100% inline styles, no external CSS classes ──────────────────
    card_html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:1rem;">'

    for _, row in df_all.iterrows():
        c = row['Color']
        card_html += f"""<div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-top:3px solid {c};border-radius:12px;padding:14px 16px;">
<div style="font-size:13px;font-weight:600;color:rgba(255,255,255,0.6);margin-bottom:8px;">{row['City']}</div>
<div style="font-size:30px;font-weight:700;color:{c};line-height:1;margin-bottom:4px;">{row['PM2.5'] or 'N/A'}</div>
<div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:8px;">PM2.5 µg/m³</div>
<div style="display:inline-block;font-size:11px;font-weight:600;padding:2px 10px;border-radius:20px;color:{c};border:1px solid {c};background:rgba(255,255,255,0.05);">{row['Category']}</div>
</div>"""

    card_html += '</div>'
    st.markdown(card_html, unsafe_allow_html=True)

    st.divider()

    # ── Bar Chart ─────────────────────────────────────────────────────────────
    fig_bar = px.bar(
        df_all.sort_values("PM2.5", ascending=True),
        x="PM2.5", y="City", orientation="h",
        color="PM2.5",
        color_continuous_scale=["#00e400", "#ffff00", "#ff7e00", "#ff0000", "#8f3f97"],
        title="PM2.5 Levels Across Indian Cities (µg/m³)",
        height=380,
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#cdd6f4", coloraxis_showscale=False,
    )
    fig_bar.add_vline(x=35.4, line_dash="dash", line_color="#ffff00", annotation_text="Moderate threshold")
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── Deep Dive ───────────────────────────────────────────────────────────────────
st.subheader(f"🔍 Deep Dive — {selected_city}")

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
    m1.metric("PM2.5 (µg/m³)", f"{round(pm25,1) if pm25 else 'N/A'}")
    m2.metric("PM10 (µg/m³)", f"{round(pm10,1) if pm10 else 'N/A'}")
    m3.metric("Ozone (µg/m³)", f"{round(ozone,1) if ozone else 'N/A'}")
    m4.metric("NO2 (µg/m³)", f"{round(no2,1) if no2 else 'N/A'}")

    hourly = data.get("hourly", {})
    if hourly and "time" in hourly:
        df_hourly = pd.DataFrame({
            "Time": pd.to_datetime(hourly["time"]),
            "PM2.5": hourly.get("pm2_5", []),
            "PM10": hourly.get("pm10", []),
            "Ozone": hourly.get("ozone", []),
            "NO2": hourly.get("nitrogen_dioxide", []),
        }).dropna()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["PM2.5"], name="PM2.5", line=dict(color="#ff7e00", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["PM10"], name="PM10", line=dict(color="#ff0000", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["Ozone"], name="Ozone", line=dict(color="#00e400", width=2)))
        fig_trend.add_trace(go.Scatter(x=df_hourly["Time"], y=df_hourly["NO2"], name="NO2", line=dict(color="#8f3f97", width=2)))
        fig_trend.add_hrect(y0=0, y1=35.4, fillcolor="#00e400", opacity=0.05, line_width=0)
        fig_trend.add_hrect(y0=35.4, y1=55.4, fillcolor="#ffff00", opacity=0.05, line_width=0)
        fig_trend.add_hrect(y0=55.4, y1=150.4, fillcolor="#ff7e00", opacity=0.05, line_width=0)
        fig_trend.update_layout(
            title=f"24-Hour Pollutant Trend — {selected_city}",
            xaxis_title="Time", yaxis_title="Concentration (µg/m³)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cdd6f4",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=380,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    if all([pm25, pm10, ozone, no2]):
        fig_radar = go.Figure(go.Scatterpolar(
            r=[pm25, pm10, ozone, no2, pm25],
            theta=["PM2.5", "PM10", "Ozone", "NO2", "PM2.5"],
            fill="toself", fillcolor="rgba(255,126,0,0.2)",
            line=dict(color="#ff7e00"), name=selected_city
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title=f"Pollutant Profile — {selected_city}",
            paper_bgcolor="rgba(0,0,0,0)", font_color="#cdd6f4", height=350,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_radar, use_container_width=True)
        with col2:
            hist = get_history(conn, selected_city, 48)
            if not hist.empty:
                hist["timestamp"] = pd.to_datetime(hist["timestamp"])
                fig_hist = px.line(hist, x="timestamp", y="pm25",
                    title="Stored History — PM2.5",
                    labels={"pm25": "PM2.5 (µg/m³)", "timestamp": "Time"},
                    color_discrete_sequence=["#cba6f7"], height=350,
                )
                fig_hist.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#cdd6f4",
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

