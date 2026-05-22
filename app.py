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
        return "Satisfactory", "#f59e0b", "#fffbeb"
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
    # Auto-delete readings older than 24 hours
    conn.execute("""
        DELETE FROM readings 
        WHERE timestamp < datetime('now', '-24 hours')
    """)
    conn.commit()
    return conn

def save_reading(conn, city, pm25, pm10, ozone, no2, category):
    # Only save if last reading for this city was more than 10 minutes ago
    cursor = conn.execute(
        "SELECT timestamp FROM readings WHERE city=? ORDER BY timestamp DESC LIMIT 1",
        (city,)
    )
    last = cursor.fetchone()
    if last:
        last_time = datetime.strptime(last[0], "%Y-%m-%d %H:%M:%S")
        diff = (datetime.now() - last_time).total_seconds()
        if diff < 600:  # less than 10 minutes
            return  # skip saving
    conn.execute(
        "INSERT INTO readings (city, timestamp, pm25, pm10, ozone, no2, category) VALUES (?,?,?,?,?,?,?)",
        (city, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pm25, pm10, ozone, no2, category)
    )
    conn.commit()

def get_history(conn, city, hours=24):
    df = pd.read_sql_query(
        """SELECT * FROM readings 
           WHERE city=? 
           AND timestamp >= datetime('now', ?)
           ORDER BY timestamp ASC""",
        conn, params=(city, f'-{hours} hours')
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
        ("Satisfactory", "12 – 35",  "#f59e0b"),
        ("Moderate",     "35 – 55",  "#ea580c"),
        ("Poor",         "55 – 150", "#dc2626"),
        ("Very Poor",    "150 – 250","#7c3aed"),
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

city_data = []
with st.spinner("Fetching live data…"):
    for city, coords in CITIES.items():
        data = fetch_aqi(coords["lat"], coords["lon"])
        if data and "current" in data:
            curr = data["current"]
            pm25 = curr.get("pm2_5")
            pm10 = curr.get("pm10")
            ozone = curr.get("ozone")
            no2 = curr.get("nitrogen_dioxide")
            cat, color, bg_tint = get_aqi_category(pm25)
            city_data.append({
                "City": city,
                "PM2.5": round(pm25, 1) if pm25 else None,
                "PM10": round(pm10, 1) if pm10 else None,
                "Ozone": round(ozone, 1) if ozone else None,
                "NO2": round(no2, 1) if no2 else None,
                "Category": cat,
                "Color": color,
                "BgTint": bg_tint,
            })
            save_reading(conn, city, pm25, pm10, ozone, no2, cat)

if city_data:
    df_all = pd.DataFrame(city_data)

    # ── City Cards ─────────────────────────────────────────────────────────────
    rows = [city_data[:5], city_data[5:]]
    for row_idx, row_data in enumerate(rows):
        card_row = f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:14px;">'
        for i, item in enumerate(row_data):
            c = item['Color']
            delay = (row_idx * 5 + i) * 0.04
            bg = item['BgTint']
            card_row += f"""
            <div style="
                background: {bg};
                border: 1px solid #e2e8f0;
                border-left: 5px solid {c};
                border-radius: 14px;
                padding: 22px 20px 20px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.03);
                transition: all 0.3s ease;
                animation: slide-up 0.4s ease-out {delay}s both;
                position: relative;
            " onmouseover="this.style.boxShadow='0 6px 24px rgba(0,0,0,0.08)';this.style.transform='translateY(-3px)'"
               onmouseout="this.style.boxShadow='0 1px 4px rgba(0,0,0,0.03)';this.style.transform='translateY(0)'">
                <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;
                            letter-spacing:0.8px;margin-bottom:12px;">{item['City']}</div>
                <div style="font-size:36px;font-weight:900;color:{c};line-height:1;
                            margin-bottom:6px;letter-spacing:-1px;">{item['PM2.5'] if item['PM2.5'] else 'N/A'}</div>
                <div style="font-size:11px;color:#94a3b8;margin-bottom:16px;font-weight:500;">PM2.5 ug/m3</div>
                <div style="display:inline-block;font-size:11px;font-weight:700;
                            padding:4px 14px;border-radius:20px;
                            color:{c};background:transparent;
                            border:2px solid {c};">{item['Category']}</div>
            </div>"""
        card_row += '</div>'
        st.markdown(card_row, unsafe_allow_html=True)

    st.divider()

    # ── Bar Chart ──────────────────────────────────────────────────────────────
    df_sorted = df_all.sort_values("PM2.5", ascending=True)
    fig_bar = px.bar(
        df_sorted,
        x="PM2.5", y="City", orientation="h",
        color="PM2.5",
        color_continuous_scale=["#059669","#f59e0b","#ea580c","#dc2626","#7c3aed"],
        height=400,
    )
    fig_bar.update_traces(marker_line_width=0, marker_cornerradius=5)
    fig_bar.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text="<b>PM2.5 Levels Across Indian Cities</b><br><span style='font-size:12px;color:#94a3b8;'>Concentration in µg/m³</span>",
            font=dict(size=14, color="#0f172a"),
        ),
        coloraxis_showscale=False,
    )
    fig_bar.add_vline(
        x=35.4, line_dash="dot", line_color="#f59e0b", line_width=2,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("""
    <div style="display:flex;justify-content:center;margin-top:-12px;margin-bottom:16px;">
        <div style="display:inline-flex;align-items:center;gap:6px;
                    padding:6px 18px;border-radius:50px;
                    background:#fffbeb;border:2px solid #f59e0b;
                    font-size:12px;font-weight:700;color:#f59e0b;
                    box-shadow:0 2px 8px rgba(245,158,11,0.15);">
            <div style="width:6px;height:6px;border-radius:50%;background:#f59e0b;"></div>
            Moderate Threshold — 35.4 µg/m³
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Deep Dive ────────────────────────────────────────────────────────────────────
section_title("🔍", f"Deep Dive — {selected_city}")

coords = CITIES[selected_city]
data = fetch_aqi(coords["lat"], coords["lon"])

if data:
    curr = data.get("current", {})
    pm25 = curr.get("pm2_5")
    pm10 = curr.get("pm10")
    ozone = curr.get("ozone")
    no2 = curr.get("nitrogen_dioxide")
    cat, color, bg_tint = get_aqi_category(pm25)

    # Status Banner
    if pm25 and pm25 > 150:
        st.error(f"🚨 **Health Alert** — {selected_city} AQI is **{cat}**. Avoid outdoor activities.")
    elif pm25 and pm25 > 55:
        st.warning(f"⚠️ **Caution** — {selected_city} AQI is **{cat}**. Sensitive groups should limit exposure.")
    else:
        st.success(f"✅ **{selected_city} air quality is {cat}** — Safe for outdoor activities.")

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PM2.5 (µg/m³)", f"{round(pm25,1) if pm25 else 'N/A'}")
    m2.metric("PM10 (µg/m³)", f"{round(pm10,1) if pm10 else 'N/A'}")
    m3.metric("Ozone (µg/m³)", f"{round(ozone,1) if ozone else 'N/A'}")
    m4.metric("NO₂ (µg/m³)", f"{round(no2,1) if no2 else 'N/A'}")

    # ── 24h Trend ──────────────────────────────────────────────────────────────
    hourly = data.get("hourly", {})
    if hourly and "time" in hourly:
        df_hourly = pd.DataFrame({
            "Time": pd.to_datetime(hourly["time"]),
            "PM2.5": hourly.get("pm2_5", []),
            "PM10": hourly.get("pm10", []),
            "Ozone": hourly.get("ozone", []),
            "NO2": hourly.get("nitrogen_dioxide", []),
        }).dropna()

        pollutant_colors = {
            "PM2.5": "#ea580c",
            "PM10":  "#dc2626",
            "Ozone": "#059669",
            "NO2":   "#7c3aed",
        }

        fig_trend = go.Figure()
        for pol, clr in pollutant_colors.items():
            fig_trend.add_trace(go.Scatter(
                x=df_hourly["Time"], y=df_hourly[pol],
                name=pol,
                line=dict(color=clr, width=2.5, shape="spline"),
                mode="lines",
                hovertemplate=f"<b>{pol}</b>: %{{y:.1f}} µg/m³<br>%{{x|%H:%M}}<extra></extra>",
            ))
        # AQI zone bands
        fig_trend.add_hrect(y0=0, y1=35.4, fillcolor="#059669", opacity=0.03, line_width=0)
        fig_trend.add_hrect(y0=35.4, y1=55.4, fillcolor="#d97706", opacity=0.03, line_width=0)
        fig_trend.add_hrect(y0=55.4, y1=150.4, fillcolor="#ea580c", opacity=0.03, line_width=0)

        fig_trend.update_layout(
            **CHART_LAYOUT,
            title=dict(
                text=f"<b>24-Hour Pollutant Trend</b><br><span style='font-size:12px;color:#94a3b8;'>{selected_city} — All pollutants</span>",
                font=dict(size=14, color="#0f172a"),
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                font=dict(size=11, color="#64748b"),
                bgcolor="rgba(255,255,255,0)",
            ),
            height=400,
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # ── Radar + History ────────────────────────────────────────────────────────
    if all([pm25, pm10, ozone, no2]):
        col1, col2 = st.columns(2)

        with col1:
            fig_radar = go.Figure(go.Scatterpolar(
                r=[pm25, pm10, ozone, no2, pm25],
                theta=["PM2.5", "PM10", "Ozone", "NO₂", "PM2.5"],
                fill="toself",
                fillcolor="rgba(13,148,136,0.08)",
                line=dict(color="#0d9488", width=2),
                marker=dict(size=6, color="#0d9488"),
                name=selected_city,
                hovertemplate="%{theta}: %{r:.1f} µg/m³<extra></extra>",
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, gridcolor="#f1f5f9",
                                    tickfont=dict(size=10, color="#94a3b8"),
                                    linecolor="#e2e8f0"),
                    angularaxis=dict(gridcolor="#f1f5f9",
                                     tickfont=dict(size=12, color="#334155"),
                                     linecolor="#e2e8f0"),
                    bgcolor="#ffffff",
                ),
                title=dict(
                    text=f"<b>Pollutant Profile</b><br><span style='font-size:12px;color:#94a3b8;'>{selected_city}</span>",
                    font=dict(size=14, color="#0f172a"),
                ),
                paper_bgcolor="#ffffff",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155"),
                height=380,
                margin=dict(l=40, r=40, t=60, b=40),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with col2:
            hist = get_history(conn, selected_city, 12)
            if not hist.empty:
                hist["timestamp"] = pd.to_datetime(hist["timestamp"])
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(
                    x=hist["timestamp"], y=hist["pm25"],
                    mode="lines",
                    line=dict(color="#7c3aed", width=2.5, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(124, 58, 237, 0.05)",
                    hovertemplate="<b>PM2.5</b>: %{y:.1f} µg/m³<br>%{x|%d %b %H:%M}<extra></extra>",
                ))
                fig_hist.update_layout(
                    **CHART_LAYOUT,
                    title=dict(
                        text="<b>Stored History</b><br><span style='font-size:12px;color:#94a3b8;'>PM2.5 readings over time</span>",
                        font=dict(size=14, color="#0f172a"),
                    ),
                    height=380,
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.markdown("""
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                            height:300px;border:1.5px dashed #e2e8f0;border-radius:14px;background:#fafafa;">
                    <div style="font-size:28px;margin-bottom:8px;opacity:0.3;">📈</div>
                    <div style="font-size:13px;color:#94a3b8;text-align:center;line-height:1.6;">
                        History builds as you refresh.<br>Check back in a few minutes!
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("Could not fetch data. Check your internet connection.")

# ─── Raw Table ────────────────────────────────────────────────────────────────────
if city_data:
    with st.expander("📋 View Raw Data Table"):
        st.dataframe(df_all.drop(columns=["Color", "BgTint"]), use_container_width=True, hide_index=True)

# ─── Footer ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:40px;padding:18px 0;border-top:1px solid #e2e8f0;text-align:center;">
    <span style="font-size:11px;color:#94a3b8;">
        Built with Streamlit & Open-Meteo · No API key required ·
        <span style="color:#cbd5e1;">v1.0</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ─── Auto Refresh ─────────────────────────────────────────────────────────────────
if auto_refresh:
    st.caption("⏱ Auto-refreshing every 60 seconds…")
    time.sleep(60)
    st.rerun()
