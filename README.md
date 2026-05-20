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

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub → select `app.py`
4. Click **Deploy** — live link generated in ~2 minutes

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

## 📈 What I Learned

- Fetching and parsing JSON from REST APIs in Python
- Caching API responses with `st.cache_data` to avoid rate limits
- Storing time-series data in SQLite for historical trend analysis
- Building multi-chart dashboards with Plotly (line, bar, radar, choropleth)
- Deploying a live Python app on Streamlit Cloud

---

## 🗺️ Roadmap (Databricks Migration)

- [ ] Migrate ingestion layer to Databricks notebook + Delta Lake
- [ ] PySpark transformations for Bronze → Silver → Gold architecture
- [ ] Databricks SQL Dashboard for team-level sharing
- [ ] Add ARIMA forecasting for next-24-hour AQI prediction

---

## 👩‍💻 Author

**Khushika Surana** — B.Tech CSE (Data Science), RBU Nagpur  
[GitHub](https://github.com/khushikaa18) · [LinkedIn](#)
