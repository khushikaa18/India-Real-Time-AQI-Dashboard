# India Real-Time AQI Dashboard

A real-time Air Quality Index (AQI) monitoring dashboard built using **Python, Streamlit, Plotly, and Pandas** that tracks live pollution data across major Indian cities without requiring any API key.

## Features

- Real-time AQI monitoring for 10 Indian cities
- Tracks PM2.5, PM10, Ozone, and NO₂ levels
- Interactive 24-hour pollutant trend charts
- Radar charts for city-wise pollutant comparison
- AQI-based health alert system
- Mobile-friendly and responsive dashboard design
- Auto-refresh every 60 seconds
- IST timestamp conversion for accurate local monitoring
- Fully deployed on Streamlit Cloud
- 100% free architecture with no paid APIs

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Streamlit | Web app framework + deployment |
| Plotly | Interactive charts (bar, line, radar) |
| Pandas | Data wrangling |
| Streamlit Session State | In-session history storage |
| Requests | API calls |
| Open-Meteo | Free real-time AQI data |

---

## Dashboard Insights

The dashboard helps users:

- Monitor air quality in real time
- Compare pollution levels across cities
- Analyze short-term pollutant trends
- Understand AQI severity using color-coded categories
- Receive health alerts based on AQI conditions
- Access the dashboard seamlessly on desktop and mobile devices

---

## Project Structure

```bash
India-Real-Time-AQI-Dashboard/
│── app.py
│── requirements.txt
│── README.md
│── assets/
│── data/
```
## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/khushikaa18/India-Real-Time-AQI-Dashboard.git
```

### 2️. Navigate to Project Directory

```bash
cd India-Real-Time-AQI-Dashboard
```

### 3️. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️. Run the Streamlit App

```bash
streamlit run app.py
```

---

## Live Demo

🔗 https://india-real-time-aqi.streamlit.app/

---

## Learning Outcomes

This project helped in gaining practical experience with:

- API Integration
- Real-Time Data Pipelines
- Time-Series Analysis
- Interactive Data Visualization
- Dashboard Development
- Responsive UI Design
- Streamlit Cloud Deployment

---

## If you found this project useful, consider giving it a star!
