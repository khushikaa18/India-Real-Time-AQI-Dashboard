# 🌿 India Real-Time AQI Dashboard

A real-time air quality monitoring dashboard for 10 major Indian cities, built with Python, Streamlit, and the Open-Meteo Air Quality API. No API key required.

**Live Demo → [your-app-name.streamlit.app](#)**

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red) ![Plotly](https://img.shields.io/badge/Plotly-5.22-purple) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 Features

- **Live AQI data** for Delhi, Mumbai, Nagpur, Pune, Bengaluru, Chennai, Kolkata, Hyderabad, Ahmedabad, and Jaipur
- **Auto-refresh** every 60 seconds — toggle in sidebar
- **Pollutants tracked**: PM2.5, PM10, Ozone (O3), Nitrogen Dioxide (NO2)
- **24-hour trend charts** with AQI zone shading
- **Radar chart** showing pollutant profile per city
- **SQLite history** — stores readings locally, builds trend over time
- **Health alert banners** — context-aware warnings based on AQI level
- **Horizontal bar chart** comparing PM2.5 across all 10 cities

---

## 🗂️ Project Structure

```
aqi_dashboard/
│
├── app.py               # Main Streamlit app
├── requirements.txt     # Python dependencies
├── aqi_history.db       # SQLite DB (auto-created on first run)
└── README.md
```

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/khushikaa18/india-aqi-dashboard.git
cd india-aqi-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## 🔌 Data Source

| Source | Endpoint | Cost |
|--------|----------|------|
| [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) | `air-quality-api.open-meteo.com` | Free, no key |

Parameters used: `pm2_5`, `pm10`, `ozone`, `nitrogen_dioxide`  
Timezone: `Asia/Kolkata`  
Update frequency: hourly from API, app refreshes every 10 min (cached)

---

## 🧱 Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Streamlit | Web app framework + deployment |
| Plotly | Interactive charts (bar, line, radar) |
| Pandas | Data wrangling |
| SQLite | Local history storage |
| Requests | API calls |
| Open-Meteo | Free real-time AQI data |

---
