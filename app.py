"""
PV Digital Twin – Smart Solar Monitoring
app.py — fichier principal Streamlit
Site : Mohammedia, Maroc | 3.96 kWp DC | 4.0 kW AC
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import yaml
import os
import time
from datetime import datetime, timedelta
import math

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PV Digital Twin – Smart Solar Monitoring",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# DARK THEME CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

  :root {
    --bg-main:    #0d1117;
    --bg-card:    #161b22;
    --bg-card2:   #1c2230;
    --border:     #30363d;
    --green:      #50c878;
    --orange:     #f0a500;
    --red:        #e74c3c;
    --blue:       #3498db;
    --cyan:       #00bcd4;
    --text-main:  #e6edf3;
    --text-muted: #8b949e;
    --font-main:  'Inter', sans-serif;
    --font-head:  'Rajdhani', sans-serif;
  }

  /* Base */
  .stApp { background-color: var(--bg-main) !important; color: var(--text-main) !important; font-family: var(--font-main); }
  .main .block-container { padding: 1rem 1.5rem 2rem 1.5rem; max-width: 100%; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] > div { padding: 0 !important; }

  /* Cards */
  .pv-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid var(--border);
    margin-bottom: 10px;
    transition: border-color .2s;
  }
  .pv-card:hover { border-color: #50c87840; }
  .pv-card-title {
    font-family: var(--font-head);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--blue);
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }

  /* KPI metrics */
  [data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
  }
  [data-testid="stMetricLabel"] { font-size: 11px !important; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: .8px; }
  [data-testid="stMetricValue"] { font-family: var(--font-head); font-size: 26px !important; color: var(--text-main) !important; }
  [data-testid="stMetricDelta"] { font-size: 11px !important; }

  /* Tabs */
  [data-testid="stTabs"] button {
    font-size: 12px !important;
    font-weight: 600;
    color: var(--text-muted) !important;
    border-bottom: 2px solid transparent;
    padding: 6px 14px;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--blue) !important;
    border-bottom-color: var(--blue) !important;
  }

  /* Radio sidebar nav */
  [data-testid="stRadio"] label {
    font-size: 13px !important;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
  }
  [data-testid="stRadio"] label:hover { background: var(--bg-card2); }

  /* Buttons */
  .stButton > button {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    color: var(--text-main);
    border-radius: 8px;
    font-size: 12px;
    padding: 6px 14px;
    font-weight: 500;
  }
  .stButton > button:hover { border-color: var(--blue); background: #1c2230; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg-main); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

  /* dataframe */
  [data-testid="stDataFrame"] { background: var(--bg-card); border-radius: 8px; }

  /* alerts */
  .stAlert { border-radius: 8px; }

  /* sidebar logo area */
  .sidebar-logo {
    padding: 20px 16px 14px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
  }
  .sidebar-logo h2 {
    font-family: var(--font-head);
    font-size: 18px;
    font-weight: 700;
    color: var(--text-main);
    margin: 4px 0 2px;
  }
  .sidebar-logo p { font-size: 11px; color: var(--orange); margin: 0; letter-spacing: .5px; }
  .sidebar-info {
    background: var(--bg-card);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 8px 10px;
    border: 1px solid var(--border);
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.7;
  }
  .sidebar-info strong { color: var(--text-main); font-size: 12px; }
  .badge-alarm {
    display: inline-block;
    background: var(--red);
    color: white;
    border-radius: 50%;
    width: 16px; height: 16px;
    font-size: 9px;
    font-weight: 700;
    line-height: 16px;
    text-align: center;
    margin-left: 6px;
    vertical-align: middle;
  }
  .energy-flow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    flex-wrap: wrap;
    padding: 8px 0;
  }
  .flow-box {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    text-align: center;
    min-width: 80px;
    flex: 1;
  }
  .flow-box .fb-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; }
  .flow-box .fb-value { font-family: var(--font-head); font-size: 16px; font-weight: 700; }
  .flow-arrow { font-size: 18px; color: var(--green); flex-shrink: 0; }
  .alarm-row { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid #21262d; }
  .alarm-icon { font-size: 16px; flex-shrink: 0; margin-top: 2px; }
  .alarm-title { font-size: 12px; font-weight: 600; color: var(--text-main); }
  .alarm-sub { font-size: 10px; color: var(--text-muted); }
  .alarm-meta { margin-left: auto; text-align: right; font-size: 10px; color: var(--text-muted); }
  .alarm-meta span { display: block; color: var(--red); font-weight: 600; }
  .weather-card { text-align: center; padding: 10px; background: var(--bg-card2); border-radius: 10px; border: 1px solid var(--border); }
  .weather-icon { font-size: 40px; }
  .weather-temp { font-family: var(--font-head); font-size: 28px; color: var(--text-main); margin: 4px 0; }
  .weather-sub { font-size: 11px; color: var(--text-muted); }
  .fc-card { background: var(--bg-card2); border-radius: 8px; padding: 8px 10px; text-align: center; border: 1px solid var(--border); flex: 1; min-width: 70px; }
  .fc-time { font-size: 11px; color: var(--text-muted); }
  .fc-temp { font-family: var(--font-head); font-size: 18px; color: var(--text-main); }
  .fc-rad { font-size: 10px; color: var(--orange); }
  .kpi-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  .kpi-mini { background: var(--bg-card2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; flex: 1; min-width: 80px; }
  .kpi-mini .kl { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; }
  .kpi-mini .kv { font-family: var(--font-head); font-size: 20px; font-weight: 700; }
  .kpi-mini .ku { font-size: 10px; color: var(--text-muted); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "site": {"lat": 33.6, "lon": -7.6, "alt": 56, "tilt": 31, "azimuth": 180, "tz": "Africa/Casablanca", "name": "Mohammedia"},
    "panel": {"Pmp": 330, "eta_stc": 0.17, "area": 1.939, "Voc": 40.0, "Isc": 9.0, "Vmp": 33.0, "Imp": 8.5, "gamma": -0.004, "NOCT": 45},
    "array": {"n_panels": 12, "n_series": 6, "n_parallel": 2, "n_mppt": 1},
    "losses": {"dc_total": 0.10, "ac_efficiency": 0.96, "inverter_threshold": 0.05, "p_rated": 4.0},
    "blynk": {"token": "", "server": "blynk.cloud", "pin_temp": "V0", "pin_irr": "V1"},
    "thresholds": {"pr_warning": 0.75, "pr_critical": 0.65, "temp_cell_warning": 55, "temp_cell_critical": 70},
    "economics": {"co2_factor": 0.233, "tarif": 1.32, "tree_co2": 21.77},
}

def load_config():
    if os.path.exists("config.yaml"):
        try:
            with open("config.yaml") as f:
                cfg = yaml.safe_load(f)
                # merge with defaults
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                    elif isinstance(v, dict):
                        for kk, vv in v.items():
                            if kk not in cfg[k]:
                                cfg[k][kk] = vv
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

# ─────────────────────────────────────────────────────────────────────────────
# PV MODEL
# ─────────────────────────────────────────────────────────────────────────────
class PVModel:
    def __init__(self, config):
        self.cfg = config
        p = config["panel"]
        a = config["array"]
        ls = config["losses"]
        self.eta_stc   = p["eta_stc"]
        self.area      = p["area"]
        self.Pmp       = p["Pmp"]
        self.Voc       = p["Voc"]
        self.Isc       = p["Isc"]
        self.Vmp       = p["Vmp"]
        self.Imp       = p["Imp"]
        self.gamma     = p["gamma"]
        self.NOCT      = p["NOCT"]
        self.n_panels  = a["n_panels"]
        self.n_series  = a["n_series"]
        self.n_parallel= a["n_parallel"]
        self.dc_losses = ls["dc_total"]
        self.ac_eff    = ls["ac_efficiency"]
        self.inv_thr   = ls["inverter_threshold"]
        self.p_rated   = ls["p_rated"]

    def compute(self, G, T_amb):
        """Single point computation."""
        if G <= 0:
            return {"G": 0, "T_amb": T_amb, "T_cell": T_amb, "eta": 0,
                    "P_dc_kW": 0, "P_ac_kW": 0, "eta_inv": 0, "PR": 0}
        # Cell temperature
        T_cell = T_amb + (self.NOCT - 20) / 800 * G
        # Panel efficiency
        eta = self.eta_stc * (1 + self.gamma * (T_cell - 25))
        if G < 200:
            eta *= max(0, G / 200 * 0.97 + 0.03)
        # DC power
        P_dc_kW = eta * self.area * G * self.n_panels * (1 - self.dc_losses) / 1000
        # Inverter efficiency
        load_ratio = P_dc_kW / self.p_rated if self.p_rated > 0 else 0
        eta_inv = self.ac_eff * (1 - 0.03 * (1 - load_ratio) ** 2)
        if P_dc_kW < self.inv_thr:
            eta_inv = 0
        # AC power
        P_ac_kW = P_dc_kW * eta_inv
        # Performance Ratio
        P_ref_kW = self.Pmp * self.n_panels * G / 1_000_000
        PR = P_dc_kW / P_ref_kW if P_ref_kW > 0 else 0
        return {
            "G": G, "T_amb": T_amb, "T_cell": T_cell,
            "eta": eta, "P_dc_kW": P_dc_kW, "P_ac_kW": P_ac_kW,
            "eta_inv": eta_inv, "PR": PR,
        }

    def compute_series(self, hours=None, G_series=None, T_series=None, seed=None):
        """Generate time series DataFrame."""
        rng = np.random.default_rng(seed if seed is not None else 42)
        if hours is None:
            hours = np.arange(0, 24, 0.25)
        if G_series is None:
            G_peak = rng.uniform(800, 950)
            G_series = np.array([
                max(0, G_peak * np.sin(np.pi * (h - 6) / 12) + rng.normal(0, 20))
                if 6 <= h <= 18 else 0
                for h in hours
            ])
        if T_series is None:
            T_series = np.array([
                25 + 5 * np.sin(np.pi * (h - 10) / 14) + rng.normal(0, 1)
                for h in hours
            ])
        rows = []
        for h, G, T in zip(hours, G_series, T_series):
            r = self.compute(G, T)
            r["hour"] = h
            rows.append(r)
        return pd.DataFrame(rows)

    def compute_iv_curve(self, G=None, T_amb=None):
        """Generate I-V and P-V curves."""
        G = G or 1000
        T_amb = T_amb or 25
        T_cell = T_amb + (self.NOCT - 20) / 800 * G
        scale_G = G / 1000
        scale_T = 1 + self.gamma * (T_cell - 25)
        Isc_t = self.Isc * self.n_parallel * scale_G
        Voc_t = self.Voc * self.n_series * scale_T
        Imp_t = self.Imp * self.n_parallel * scale_G
        Vmp_t = self.Vmp * self.n_series * scale_T
        try:
            a = np.log(self.Isc / max(self.Isc - self.Imp, 1e-6))
        except Exception:
            a = 10
        Rs = (self.Voc - self.Vmp) / max(self.Imp, 1e-6)
        v_range = np.linspace(0, Voc_t * 0.99, 200)
        denom = Voc_t / a + Rs * Isc_t
        I_curve = np.array([
            max(0, Isc_t * (1 - np.exp((v - Voc_t + Rs * Isc_t) / max(denom, 1e-6) * a)))
            for v in v_range
        ])
        P_curve = v_range * I_curve
        idx_mpp = np.argmax(P_curve)
        return {
            "V": v_range, "I": I_curve, "P": P_curve,
            "V_mpp": v_range[idx_mpp], "I_mpp": I_curve[idx_mpp],
            "P_mpp": P_curve[idx_mpp],
            "Voc": Voc_t, "Isc": Isc_t,
        }

    def recalibrate(self, P_ac_measured, G, T_amb):
        """Adaptive EMA recalibration."""
        r = self.compute(G, T_amb)
        P_ac_sim = r["P_ac_kW"]
        if P_ac_sim > 0:
            correction = P_ac_measured / P_ac_sim
            target = 1 - (1 - self.dc_losses) * correction
            target = max(0, min(0.30, target))
            self.dc_losses += 0.1 * (target - self.dc_losses)
        return self.dc_losses


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHER
# ─────────────────────────────────────────────────────────────────────────────
class DataFetcher:
    def __init__(self, config):
        self.cfg = config
        self.source = "Simulation"

    def fetch_blynk(self):
        token = self.cfg["blynk"].get("token", "")
        if not token:
            return None, None, "no_token"
        try:
            server = self.cfg["blynk"].get("server", "blynk.cloud")
            p0 = self.cfg["blynk"].get("pin_temp", "V0")
            p1 = self.cfg["blynk"].get("pin_irr", "V1")
            r0 = requests.get(f"https://{server}/external/api/get?token={token}&{p0}", timeout=3)
            r1 = requests.get(f"https://{server}/external/api/get?token={token}&{p1}", timeout=3)
            T = float(r0.text)
            G = float(r1.text)
            return T, G, "Blynk ESP32"
        except Exception:
            return None, None, "blynk_error"

    def fetch_open_meteo(self):
        try:
            lat = self.cfg["site"]["lat"]
            lon = self.cfg["site"]["lon"]
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,shortwave_radiation,windspeed_10m,weathercode"
                f"&hourly=shortwave_radiation,temperature_2m,windspeed_10m"
                f"&timezone=Africa%2FCasablanca&forecast_days=7"
            )
            resp = requests.get(url, timeout=5)
            data = resp.json()
            cur = data.get("current", {})
            T = cur.get("temperature_2m", None)
            G = cur.get("shortwave_radiation", None)
            wind = cur.get("windspeed_10m", 0)
            code = cur.get("weathercode", 0)
            hourly = data.get("hourly", {})
            return T, G, wind, code, hourly, "Open-Meteo"
        except Exception:
            return None, None, 0, 0, {}, "meteo_error"

    def get_live(self):
        """Try Blynk → Open-Meteo → Simulation fallback."""
        T_b, G_b, status_b = self.fetch_blynk()
        if T_b is not None and G_b is not None:
            self.source = "Blynk ESP32"
            return G_b, T_b, self.source

        T_m, G_m, wind, code, hourly, status_m = self.fetch_open_meteo()
        if T_m is not None and G_m is not None:
            self.source = "Open-Meteo"
            return G_m, T_m, self.source

        # Simulation
        h = datetime.now().hour + datetime.now().minute / 60
        G_sim = max(0, 900 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0
        T_sim = 25 + 5 * np.sin(np.pi * (h - 10) / 14)
        self.source = "Simulation"
        return G_sim, T_sim, "Simulation"

    def get_weather_full(self):
        T_m, G_m, wind, code, hourly, status = self.fetch_open_meteo()
        if T_m is None:
            h = datetime.now().hour + datetime.now().minute / 60
            G_m = max(0, 900 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0
            T_m = 25.0; wind = 8.0; code = 1
            hourly = {}
        return {"T": T_m, "G": G_m, "wind": wind, "code": code, "hourly": hourly, "source": status}


# ─────────────────────────────────────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────────────────────────────────────
WEATHER_ICONS = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
                 51: "🌦️", 53: "🌦️", 55: "🌧️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
                 80: "🌦️", 81: "🌧️", 95: "⛈️"}

def weather_icon(code):
    code = int(code) if code else 0
    for k in sorted(WEATHER_ICONS.keys(), reverse=True):
        if code >= k:
            return WEATHER_ICONS[k]
    return "🌤️"

def weather_label(code):
    labels = {0: "Ensoleillé", 1: "Principalement ensoleillé", 2: "Partiellement nuageux",
              3: "Couvert", 45: "Brumeux", 51: "Bruine légère", 61: "Pluie légère",
              80: "Averses", 95: "Orageux"}
    code = int(code) if code else 0
    for k in sorted(labels.keys(), reverse=True):
        if code >= k:
            return labels[k]
    return "Ensoleillé"

def format_power(kW):
    if kW >= 1000:
        return f"{kW/1000:.2f} MW"
    return f"{kW:.2f} kW"

def format_energy(kWh):
    if kWh >= 1e6:
        return f"{kWh/1e6:.2f} GWh"
    if kWh >= 1000:
        return f"{kWh/1000:.2f} MWh"
    return f"{kWh:.1f} kWh"

def format_co2(kg):
    if kg >= 1000:
        return f"{kg/1000:.2f} t CO₂"
    return f"{kg:.1f} kg CO₂"

def format_currency(mad):
    return f"{mad:,.0f} MAD"

def get_performance_color(pr):
    if pr >= 0.80: return "#50c878"
    if pr >= 0.75: return "#f0a500"
    if pr >= 0.65: return "#e67e22"
    return "#e74c3c"

def get_temp_color(t):
    if t < 45: return "#50c878"
    if t < 55: return "#f0a500"
    if t < 70: return "#e67e22"
    return "#e74c3c"

def compute_savings(energy_kWh, config):
    eco = config["economics"]
    co2 = energy_kWh * eco["co2_factor"]
    mad = energy_kWh * eco["tarif"]
    trees = co2 / eco["tree_co2"]
    return {"co2_kg": co2, "mad": mad, "trees": trees}

def diagnose(pr, temp_cell, thresholds):
    alerts = []
    if pr < thresholds["pr_critical"]:
        alerts.append(("error", f"🔴 PR critique : {pr*100:.1f}% < {thresholds['pr_critical']*100:.0f}%"))
    elif pr < thresholds["pr_warning"]:
        alerts.append(("warning", f"🟡 PR dégradé : {pr*100:.1f}% < {thresholds['pr_warning']*100:.0f}%"))
    if temp_cell > thresholds["temp_cell_critical"]:
        alerts.append(("error", f"🔴 Température cellule critique : {temp_cell:.1f}°C"))
    elif temp_cell > thresholds["temp_cell_warning"]:
        alerts.append(("warning", f"🟡 Température cellule élevée : {temp_cell:.1f}°C"))
    return alerts

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#e6edf3', size=11, family='Inter'),
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(gridcolor='#21262d', showgrid=True, zeroline=False),
    yaxis=dict(gridcolor='#21262d', showgrid=True, zeroline=False),
    legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0),
)

def apply_layout(fig, **kwargs):
    layout = {**PLOTLY_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "config" not in st.session_state:
    st.session_state.config = load_config()

if "model" not in st.session_state:
    st.session_state.model = PVModel(st.session_state.config)

if "fetcher" not in st.session_state:
    st.session_state.fetcher = DataFetcher(st.session_state.config)

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

cfg   = st.session_state.config
model = st.session_state.model
fetcher = st.session_state.fetcher

# ─────────────────────────────────────────────────────────────────────────────
# CACHED DATA FETCHERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_live_data(_fetcher):
    return _fetcher.get_live()

@st.cache_data(ttl=900)
def fetch_weather(_fetcher):
    return _fetcher.get_weather_full()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div style="font-size:32px">☀️</div>
      <h2>PV Digital Twin</h2>
      <p>Smart Solar Monitoring</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-info">
      <strong>📍 Mohammedia, Maroc</strong><br>
      3.96 kWp DC &nbsp;|&nbsp; 4.0 kW AC<br>
      Mise en service : Janvier 2023<br>
      12 panneaux PV &nbsp;|&nbsp; 1 MPPT<br>
      6s × 2p &nbsp;|&nbsp; Tilt 31° Az 180°
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='padding: 0 10px 4px;'>", unsafe_allow_html=True)
    nav_options = [
        "🏠 Vue d'ensemble",
        "🧊 Jumeau numérique",
        "📈 Performance",
        "⚙️ Équipements",
        "🔔 Alarmes",
        "🔍 Analyses",
        "📄 Rapports",
        "🌤️ Météo",
        "⚙️ Paramètres",
    ]
    page = st.radio("Navigation", nav_options, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Rafraîchir données", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    ts = st.session_state.last_refresh.strftime("%H:%M:%S")
    st.caption(f"Dernière MàJ : {ts}")

# ─────────────────────────────────────────────────────────────────────────────
# FETCH LIVE DATA
# ─────────────────────────────────────────────────────────────────────────────
G_live, T_live, source_live = fetch_live_data(fetcher)
result_live = model.compute(G_live, T_live)
weather_data = fetch_weather(fetcher)

# Precompute some values
P_ac = result_live["P_ac_kW"]
P_dc = result_live["P_dc_kW"]
T_cell = result_live["T_cell"]
PR = result_live["PR"]
eta = result_live["eta"]
eta_inv = result_live["eta_inv"]

# Daily energy (integrate 24h simulation)
df_day = model.compute_series(seed=int(datetime.now().strftime("%Y%m%d")))
energy_day_kWh = df_day["P_ac_kW"].mean() * 24
energy_total_kWh = energy_day_kWh * 365 * 3  # 3 years estimate
savings = compute_savings(energy_total_kWh, cfg)

thresholds = cfg["thresholds"]
alerts = diagnose(PR, T_cell, thresholds)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Vue d'ensemble":

    # ── HEADER ──────────────────────────────────────────────────────────────
    hc1, hc2, hc3 = st.columns([2, 5, 3])

    with hc1:
        wicon = weather_icon(weather_data["code"])
        wlabel = weather_label(weather_data["code"])
        st.markdown(f"""
        <div class="weather-card">
          <div class="weather-icon">{wicon}</div>
          <div class="weather-temp">{weather_data['T']:.1f}°C</div>
          <div style="font-size:12px; color:#e6edf3; margin-bottom:2px">{wlabel}</div>
          <div class="weather-sub">Irradiance &nbsp;<strong style="color:#f0a500">{weather_data['G']:.0f} W/m²</strong></div>
          <div class="weather-sub" style="margin-top:4px; font-size:10px; color:#50c878">● {source_live}</div>
        </div>
        """, unsafe_allow_html=True)

    with hc2:
        kc1, kc2, kc3, kc4 = st.columns(4)
        with kc1:
            st.metric("Puissance AC", format_power(P_ac),
                      f"{P_ac/cfg['losses']['p_rated']*100:.0f}% capacité")
        with kc2:
            st.metric("Production jour", format_energy(energy_day_kWh), "↑ aujourd'hui")
        with kc3:
            st.metric("Production totale", format_energy(energy_total_kWh), "3 ans estimé")
        with kc4:
            st.metric("CO₂ évité", format_co2(savings["co2_kg"]), f"🌳 {savings['trees']:.0f} arbres")

    with hc3:
        today = st.date_input("Date", datetime.now().date(), label_visibility="collapsed")
        periode = st.selectbox("Période", ["Aujourd'hui", "Semaine", "Mois", "Année"], label_visibility="collapsed")
        st.caption(f"⏱️ {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── MAIN GRID ────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([6, 4])

    # ════ LEFT COLUMN ═════════════════════════════════════════════════
    with col_left:

        # Panel 1 – 3D View / Digital Twin
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">☀ Jumeau numérique – Vue 3D</div>', unsafe_allow_html=True)

        scene_col, controls_col = st.columns([3, 1])
        with scene_col:
            if os.path.exists("assets/Scene_enset.png"):
                st.image("assets/Scene_enset.png", use_container_width=True)
            else:
                # Placeholder SVG solar farm
                st.markdown("""
                <div style="background:linear-gradient(135deg,#0d2137,#1a3a5c);border-radius:10px;
                            height:250px;display:flex;align-items:center;justify-content:center;
                            border:1px solid #30363d;position:relative;overflow:hidden">
                  <div style="text-align:center">
                    <div style="font-size:60px">🔆</div>
                    <div style="font-size:13px;color:#8b949e;margin-top:8px">Vue 3D – assets/Scene_enset.png</div>
                    <div style="font-size:11px;color:#50c878;margin-top:4px">● 12 panneaux actifs</div>
                  </div>
                  <div style="position:absolute;bottom:10px;right:10px;font-size:20px;opacity:.4">🧭</div>
                </div>
                """, unsafe_allow_html=True)

        with controls_col:
            st.radio("Vue", ["Vue libre","Irradiance","Température","Production","Pertes"],
                     label_visibility="collapsed", key="scene_view")
            st.markdown("""
            <div style="font-size:10px;line-height:2;margin-top:8px">
              <span style="color:#50c878">⬤</span> Normal<br>
              <span style="color:#f0a500">⬤</span> Attention<br>
              <span style="color:#e74c3c">⬤</span> Alarme<br>
              <span style="color:#3498db">⬤</span> Maintenance
            </div>
            """, unsafe_allow_html=True)

        tc = get_temp_color(T_cell)
        pc = get_performance_color(PR)
        st.markdown(f"""
        <div class="kpi-bar" style="margin-top:10px">
          <div class="kpi-mini">
            <div class="kl">T° Cellule</div>
            <div class="kv" style="color:{tc}">{T_cell:.1f}°</div>
            <div class="ku">°C</div>
          </div>
          <div class="kpi-mini">
            <div class="kl">Rendement</div>
            <div class="kv" style="color:#3498db">{eta*100:.1f}%</div>
            <div class="ku">η panneau</div>
          </div>
          <div class="kpi-mini">
            <div class="kl">Perf. Ratio</div>
            <div class="kv" style="color:{pc}">{PR*100:.1f}%</div>
            <div class="ku">PR actuel</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 2 – Production & Performance
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">📊 Production & Performance</div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["Jour", "Semaine", "Mois", "Année"])
        with t1:
            mc1, mc2, mc3 = st.columns(3)
            e_kWh = df_day["P_ac_kW"].mean() * 24
            rs = e_kWh / (cfg["panel"]["Pmp"] * cfg["array"]["n_panels"] / 1000)
            pr_mean = df_day["PR"].mean()
            with mc1:
                st.metric("Production", format_energy(e_kWh))
            with mc2:
                st.metric("Rend. spécifique", f"{rs:.2f} kWh/kWp")
            with mc3:
                st.metric("PR moyen", f"{pr_mean*100:.1f}%")

            fig_prod = make_subplots(specs=[[{"secondary_y": True}]])
            hours_plot = df_day["hour"]
            fig_prod.add_trace(go.Scatter(
                x=hours_plot, y=df_day["P_ac_kW"],
                name="P_ac (kW)", fill='tozeroy',
                line=dict(color='#50c878', width=2),
                fillcolor='rgba(80,200,120,0.15)'
            ), secondary_y=False)
            fig_prod.add_trace(go.Scatter(
                x=hours_plot, y=df_day["G"],
                name="G (W/m²)", line=dict(color='#f0a500', width=1.5, dash='dot')
            ), secondary_y=True)
            fig_prod.update_yaxes(title_text="P_ac (kW)", secondary_y=False,
                                   gridcolor='#21262d', color='#e6edf3')
            fig_prod.update_yaxes(title_text="G (W/m²)", secondary_y=True,
                                   gridcolor='#21262d', color='#f0a500')
            apply_layout(fig_prod, height=200, title_text="")
            st.plotly_chart(fig_prod, use_container_width=True, config={"displayModeBar": False})

        with t2:
            seeds = [int(f"{datetime.now().strftime('%Y%m%d')}{i}") for i in range(7)]
            e_week = [model.compute_series(seed=s)["P_ac_kW"].mean()*24 for s in seeds]
            days = [(datetime.now() - timedelta(days=6-i)).strftime("%d/%m") for i in range(7)]
            fig_w = go.Figure(go.Bar(x=days, y=e_week, marker_color='#50c878', opacity=0.8))
            apply_layout(fig_w, height=200)
            st.plotly_chart(fig_w, use_container_width=True, config={"displayModeBar": False})

        with t3:
            e_month = [model.compute_series(seed=i*100)["P_ac_kW"].mean()*24
                       for i in range(1, 31)]
            fig_m = go.Figure(go.Bar(x=list(range(1, 31)), y=e_month,
                                     marker_color='#3498db', opacity=0.7))
            apply_layout(fig_m, height=200)
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})

        with t4:
            months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
            e_yr = [model.compute_series(seed=i*1000)["P_ac_kW"].mean()*24*30 for i in range(12)]
            fig_y = go.Figure(go.Bar(x=months, y=e_yr, marker_color='#f0a500', opacity=0.8))
            apply_layout(fig_y, height=200)
            st.plotly_chart(fig_y, use_container_width=True, config={"displayModeBar": False})

        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 3 – I-V Curve
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">⚡ Courbe I-V instantanée</div>', unsafe_allow_html=True)

        iv = model.compute_iv_curve(G=G_live if G_live > 10 else 800, T_amb=T_live)
        fig_iv = make_subplots(specs=[[{"secondary_y": True}]])
        fig_iv.add_trace(go.Scatter(
            x=iv["V"], y=iv["I"], name="I(V)",
            line=dict(color='#3498db', width=2)
        ), secondary_y=False)
        fig_iv.add_trace(go.Scatter(
            x=iv["V"], y=iv["P"]/1000, name="P(V) kW",
            line=dict(color='#50c878', width=1.5, dash='dash')
        ), secondary_y=True)
        fig_iv.add_trace(go.Scatter(
            x=[iv["V_mpp"]], y=[iv["I_mpp"]], mode='markers+text',
            name="MPP", marker=dict(color='#e74c3c', size=10, symbol='star'),
            text=[f"  MPP\n{iv['P_mpp']/1000:.2f}kW"], textposition='top right',
            textfont=dict(size=9, color='#e74c3c')
        ), secondary_y=False)
        fig_iv.update_yaxes(title_text="Courant (A)", secondary_y=False, gridcolor='#21262d')
        fig_iv.update_yaxes(title_text="Puissance (kW)", secondary_y=True, gridcolor='#21262d')
        apply_layout(fig_iv, height=200)
        st.plotly_chart(fig_iv, use_container_width=True, config={"displayModeBar": False})

        col_iv1, col_iv2, col_iv3 = st.columns(3)
        col_iv1.metric("P_mpp", f"{iv['P_mpp']/1000:.2f} kW")
        col_iv2.metric("V_mpp", f"{iv['V_mpp']:.1f} V")
        col_iv3.metric("I_mpp", f"{iv['I_mpp']:.2f} A")
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 4 – 7-day Performance Comparison
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">📉 Comparaison Performance 7 jours</div>', unsafe_allow_html=True)

        s1, s2, s3 = st.tabs(["PR", "Production spécifique", "Irradiance"])
        rng7 = np.random.default_rng(42)
        days7 = [(datetime.now() - timedelta(days=6-i)).strftime("%d/%m") for i in range(7)]
        pr7 = [model.compute_series(seed=i*77)["PR"].mean() for i in range(7)]
        pr7_exp = [p * 1.05 for p in pr7]

        with s1:
            fig7 = go.Figure()
            fig7.add_trace(go.Scatter(x=days7, y=[p*100 for p in pr7],
                                       name="PR Réel", line=dict(color='#50c878', width=2)))
            fig7.add_trace(go.Scatter(x=days7, y=[p*100 for p in pr7_exp],
                                       name="PR Attendu", line=dict(color='#f0a500', width=2, dash='dash')))
            apply_layout(fig7, height=180)
            st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})

        with s2:
            pspec = [model.compute_series(seed=i*77)["P_ac_kW"].mean()*24 /
                     (cfg["panel"]["Pmp"]*cfg["array"]["n_panels"]/1000) for i in range(7)]
            fig7b = go.Figure()
            fig7b.add_trace(go.Scatter(x=days7, y=pspec, name="kWh/kWp",
                                        line=dict(color='#3498db', width=2)))
            apply_layout(fig7b, height=180)
            st.plotly_chart(fig7b, use_container_width=True, config={"displayModeBar": False})

        with s3:
            g7 = [model.compute_series(seed=i*77)["G"].max() for i in range(7)]
            fig7c = go.Figure(go.Bar(x=days7, y=g7, marker_color='#f0a500', opacity=0.8))
            apply_layout(fig7c, height=180)
            st.plotly_chart(fig7c, use_container_width=True, config={"displayModeBar": False})

        st.markdown('</div>', unsafe_allow_html=True)

    # ════ RIGHT COLUMN ═════════════════════════════════════════════════
    with col_right:

        # Panel 5 – Energy Flow
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">⚡ Flux d\'énergie</div>', unsafe_allow_html=True)

        dc_loss_kW = P_dc * model.dc_losses
        aux_kW = max(0, P_dc - P_ac)
        load_pct = P_ac / cfg["losses"]["p_rated"] * 100 if cfg["losses"]["p_rated"] > 0 else 0
        arrow_color = "#50c878" if load_pct > 80 else ("#f0a500" if load_pct > 50 else "#e74c3c")

        def img_or_emoji(path, emoji, size=32):
            if os.path.exists(path):
                return f'<img src="{path}" width="{size}" style="border-radius:4px">'
            return f'<span style="font-size:{size}px">{emoji}</span>'

        st.markdown(f"""
        <div class="energy-flow">
          <div class="flow-box">
            <div style="font-size:24px">☀️</div>
            <div class="fb-label">Générateur</div>
            <div class="fb-value" style="color:#f0a500">{G_live:.0f}<br><span style="font-size:11px">W/m²</span></div>
          </div>
          <div class="flow-arrow" style="color:{arrow_color}">▶</div>
          <div class="flow-box">
            <div style="font-size:24px">🔋</div>
            <div class="fb-label">DC</div>
            <div class="fb-value" style="color:#3498db">{P_dc:.2f}<br><span style="font-size:11px">kW</span></div>
          </div>
          <div class="flow-arrow" style="color:{arrow_color}">▶</div>
          <div class="flow-box">
            <div style="font-size:24px">⚡</div>
            <div class="fb-label">AC</div>
            <div class="fb-value" style="color:#50c878">{P_ac:.2f}<br><span style="font-size:11px">kW</span></div>
          </div>
          <div class="flow-arrow" style="color:{arrow_color}">▶</div>
          <div class="flow-box">
            <div style="font-size:24px">🏭</div>
            <div class="fb-label">Réseau</div>
            <div class="fb-value" style="color:#e6edf3">{P_ac:.2f}<br><span style="font-size:11px">kW</span></div>
          </div>
        </div>
        <div style="font-size:11px; color:#e74c3c; margin-top:4px">
          ⬇️ Pertes DC : {dc_loss_kW:.3f} kW &nbsp;|&nbsp;
          ⬇️ Pertes onduleur : {aux_kW:.3f} kW
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 6 – Equipment Status
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">🔧 État des équipements</div>', unsafe_allow_html=True)

        eq_data = {"Normal": 8, "Attention": 2, "Alarme": 1, "Maintenance": 1}
        eq_colors = ["#50c878", "#f0a500", "#e74c3c", "#3498db"]
        eq_total = sum(eq_data.values())

        ec1, ec2 = st.columns([4, 5])
        with ec1:
            fig_eq = go.Figure(go.Pie(
                labels=list(eq_data.keys()), values=list(eq_data.values()),
                marker_colors=eq_colors, hole=0.55,
                textinfo='none',
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"
            ))
            fig_eq.add_annotation(text=f"<b>{eq_total}</b>", x=0.5, y=0.5,
                                   font=dict(size=18, color='#e6edf3'), showarrow=False)
            apply_layout(fig_eq, height=160, showlegend=False, margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_eq, use_container_width=True, config={"displayModeBar": False})

        with ec2:
            for (label, count), color in zip(eq_data.items(), eq_colors):
                pct = count / eq_total * 100
                st.markdown(f"""
                <div style="font-size:12px; margin-bottom:4px">
                  <span style="color:{color}">⬤</span> {label}
                  <span style="float:right; color:#8b949e">{count} ({pct:.1f}%)</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<a href="#" style="font-size:11px;color:#3498db">→ Voir tous les équipements</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 7 – Loss Breakdown
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">📉 Répartition des pertes</div>', unsafe_allow_html=True)

        if G_live > 0:
            p_irr = max(0, (1 - eta / model.eta_stc) * P_dc * 0.6) * 100 / max(P_dc, 0.001)
            p_temp = abs(model.gamma * (T_cell - 25)) * 100
            p_dc = model.dc_losses * 100
            p_inv = (1 - eta_inv) * 100 if eta_inv > 0 else 5
            p_cable = 0.5
            p_other = max(0, 100 - p_irr - p_temp - p_dc - p_inv - p_cable)
            loss_labels = ["Irradiance","Température","DC","Onduleur","Câbles","Autres"]
            loss_vals = [p_irr, p_temp, p_dc, p_inv, p_cable, p_other]
            loss_colors = ["#3498db","#50c878","#e74c3c","#f0a500","#f39c12","#7f8c8d"]
        else:
            loss_labels = ["Irradiance","Température","DC","Onduleur","Câbles","Autres"]
            loss_vals = [6.2, 4.1, 10.0, 4.0, 0.5, 2.0]
            loss_colors = ["#3498db","#50c878","#e74c3c","#f0a500","#f39c12","#7f8c8d"]

        lc1, lc2 = st.columns([4, 5])
        with lc1:
            fig_loss = go.Figure(go.Pie(
                labels=loss_labels, values=loss_vals,
                marker_colors=loss_colors, hole=0.5,
                textinfo='none',
                hovertemplate="%{label}: %{value:.1f}%<extra></extra>"
            ))
            total_loss = sum(loss_vals)
            fig_loss.add_annotation(text=f"<b>{total_loss:.1f}%</b>", x=0.5, y=0.5,
                                     font=dict(size=14, color='#e74c3c'), showarrow=False)
            apply_layout(fig_loss, height=160, showlegend=False, margin=dict(l=0,r=0,t=10,b=10))
            st.plotly_chart(fig_loss, use_container_width=True, config={"displayModeBar": False})

        with lc2:
            for label, val, color in zip(loss_labels, loss_vals, loss_colors):
                st.markdown(f"""
                <div style="font-size:11px;margin-bottom:3px">
                  <span style="color:{color}">⬤</span> {label}
                  <span style="float:right;color:#8b949e">{val:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<a href="#" style="font-size:11px;color:#3498db">→ Détails</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 8 – Diagnostic
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">🩺 Diagnostic automatique</div>', unsafe_allow_html=True)

        if not alerts:
            st.success("✅ Système nominal – tous les paramètres dans les limites")
        else:
            for level, msg in alerts:
                if level == "error":
                    st.error(msg)
                else:
                    st.warning(msg)

        day_sav = compute_savings(energy_day_kWh, cfg)
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Économies", format_currency(day_sav["mad"]))
        sc2.metric("CO₂ évité", format_co2(day_sav["co2_kg"]))
        sc3.metric("🌳 Arbres", f"{day_sav['trees']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 9 – Recent Alarms
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">🔔 Alarmes récentes</div>', unsafe_allow_html=True)

        alarm_list = [
            {"icon": "🔴", "title": "Défaut communication INV-01", "sub": "Onduleur #01",
             "time": "10:15", "status": "Non acquittée", "color": "#e74c3c"},
        ]
        for a in alerts:
            if "T°" in a[1] or "température" in a[1].lower():
                alarm_list.append({"icon": "🟡", "title": a[1], "sub": "Auto-détecté",
                                   "time": datetime.now().strftime("%H:%M"),
                                   "status": "Auto", "color": "#f0a500"})
            elif "PR" in a[1]:
                alarm_list.append({"icon": "🟡", "title": a[1], "sub": "Auto-détecté",
                                   "time": datetime.now().strftime("%H:%M"),
                                   "status": "Auto", "color": "#f0a500"})

        for al in alarm_list[:3]:
            st.markdown(f"""
            <div class="alarm-row">
              <div class="alarm-icon">{al['icon']}</div>
              <div>
                <div class="alarm-title">{al['title']}</div>
                <div class="alarm-sub">{al['sub']}</div>
              </div>
              <div class="alarm-meta">
                {al['time']}
                <span style="color:{al['color']}">{al['status']}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<a href="#" style="font-size:11px;color:#3498db">→ Voir toutes les alarmes</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel 10 – Weather & Forecast
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">🌤️ Météo & Prévisions</div>', unsafe_allow_html=True)

        now_h = datetime.now().hour
        forecasts = [
            {"time": f"{(now_h+3)%24:02d}:00", "icon": "🌤️", "temp": weather_data['T']+1, "G": 900},
            {"time": f"{(now_h+6)%24:02d}:00", "icon": "☀️", "temp": weather_data['T']+3, "G": 950},
            {"time": f"{(now_h+9)%24:02d}:00", "icon": "⛅", "temp": weather_data['T']+1, "G": 800},
        ]
        # Try to use hourly data from Open-Meteo
        hourly = weather_data.get("hourly", {})
        if hourly and "temperature_2m" in hourly:
            times_h = hourly.get("time", [])
            temps_h = hourly.get("temperature_2m", [])
            rads_h  = hourly.get("shortwave_radiation", [])
            fc_new = []
            for i, t_str in enumerate(times_h[:24]):
                h = int(t_str[11:13]) if len(t_str) > 10 else 0
                if h in [(now_h+3)%24, (now_h+6)%24, (now_h+9)%24]:
                    fc_new.append({
                        "time": f"{h:02d}:00",
                        "icon": weather_icon(weather_data["code"]),
                        "temp": temps_h[i] if i < len(temps_h) else 25,
                        "G": rads_h[i] if i < len(rads_h) else 800,
                    })
            if fc_new:
                forecasts = fc_new[:3]

        fc_cols = st.columns(len(forecasts))
        for i, fc in enumerate(forecasts):
            with fc_cols[i]:
                st.markdown(f"""
                <div class="fc-card">
                  <div class="fc-time">{fc['time']}</div>
                  <div style="font-size:22px">{fc['icon']}</div>
                  <div class="fc-temp">{fc['temp']:.0f}°C</div>
                  <div class="fc-rad">{fc['G']:.0f} W/m²</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<a href="#" style="font-size:11px;color:#3498db;margin-top:6px;display:block">→ Voir la météo détaillée</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — JUMEAU NUMÉRIQUE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧊 Jumeau numérique":
    st.markdown("## 🧊 Jumeau Numérique")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">Vue 3D interactive</div>', unsafe_allow_html=True)
        if os.path.exists("assets/Scene_enset.png"):
            st.image("assets/Scene_enset.png", use_container_width=True)
        else:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#0d2137,#1a3a5c);border-radius:10px;
                        height:400px;display:flex;align-items:center;justify-content:center">
              <div style="text-align:center">
                <div style="font-size:80px">🔆</div>
                <div style="color:#8b949e;margin-top:12px">assets/Scene_enset.png requis</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">Paramètres temps réel</div>', unsafe_allow_html=True)
        metrics_2 = [
            ("☀️ Irradiance", f"{G_live:.0f} W/m²"),
            ("🌡️ T° ambiante", f"{T_live:.1f}°C"),
            ("🔥 T° cellule", f"{T_cell:.1f}°C"),
            ("⚡ P_dc", f"{P_dc:.3f} kW"),
            ("🔌 P_ac", f"{P_ac:.3f} kW"),
            ("📊 PR", f"{PR*100:.1f}%"),
            ("η panneau", f"{eta*100:.2f}%"),
            ("η onduleur", f"{eta_inv*100:.1f}%"),
        ]
        for label, val in metrics_2:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:6px 0;
                        border-bottom:1px solid #21262d;font-size:13px">
              <span style="color:#8b949e">{label}</span>
              <strong style="color:#e6edf3">{val}</strong>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Panel map
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">📍 Localisation</div>', unsafe_allow_html=True)
        loc_df = pd.DataFrame({"lat": [cfg["site"]["lat"]], "lon": [cfg["site"]["lon"]]})
        st.map(loc_df, zoom=10)
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Performance":
    st.markdown("## 📈 Performance")
    tab_d, tab_w, tab_m, tab_y = st.tabs(["Jour", "Semaine", "Mois", "Année"])

    def perf_tab(df, label):
        c1, c2, c3, c4 = st.columns(4)
        e = df["P_ac_kW"].mean() * (24 if label=="Jour" else 24*7 if label=="Semaine" else 24*30)
        c1.metric("Énergie", format_energy(e))
        c2.metric("PR moyen", f"{df['PR'].mean()*100:.1f}%")
        c3.metric("η moyen", f"{df['eta'].mean()*100:.2f}%")
        c4.metric("Heures soleil", f"{(df['G']>50).sum()*0.25:.1f}h")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df["hour"], y=df["P_ac_kW"], name="P_ac",
                                  fill='tozeroy', line=dict(color='#50c878', width=2),
                                  fillcolor='rgba(80,200,120,0.1)'), secondary_y=False)
        fig.add_trace(go.Scatter(x=df["hour"], y=df["G"], name="G (W/m²)",
                                  line=dict(color='#f0a500', width=1.5, dash='dot')), secondary_y=True)
        apply_layout(fig, height=260, title_text=f"Production & Irradiance – {label}")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        fig2 = go.Figure(go.Bar(
            x=df["hour"], y=df["PR"]*100,
            marker_color=[get_performance_color(p) for p in df["PR"]],
        ))
        apply_layout(fig2, height=180, title_text="Performance Ratio (PR)")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        st.dataframe(
            df[["hour","G","T_amb","T_cell","P_dc_kW","P_ac_kW","PR","eta_inv"]].round(3),
            use_container_width=True, height=200
        )

    with tab_d:
        perf_tab(df_day, "Jour")
    with tab_w:
        df_w = pd.concat([model.compute_series(seed=i*77) for i in range(7)], ignore_index=True)
        perf_tab(df_w, "Semaine")
    with tab_m:
        df_m = model.compute_series(
            hours=np.arange(0, 24*30, 0.5),
            seed=999
        )
        perf_tab(df_m, "Mois")
    with tab_y:
        df_y = pd.concat([model.compute_series(seed=i*1000) for i in range(12)], ignore_index=True)
        perf_tab(df_y, "Année")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ÉQUIPEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Équipements":
    st.markdown("## ⚙️ État des Équipements")
    equip_data = [
        {"id": "INV-01", "type": "Onduleur", "état": "🔴 Alarme",  "P": "0.0 kW",  "T": "—",     "note": "Défaut comm."},
        {"id": "INV-02", "type": "Onduleur", "état": "🟢 Normal",  "P": f"{P_ac:.2f} kW", "T": f"{T_cell:.1f}°C", "note": "OK"},
        {"id": "PNL-01", "type": "Panneau",  "état": "🟢 Normal",  "P": f"{P_dc/12*1:.3f} kW", "T": f"{T_cell:.1f}°C", "note": "OK"},
        {"id": "PNL-02", "type": "Panneau",  "état": "🟡 Attention","P": f"{P_dc/12*0.9:.3f} kW","T": f"{T_cell+5:.1f}°C","note": "T° élevée"},
        {"id": "PNL-03", "type": "Panneau",  "état": "🟢 Normal",  "P": f"{P_dc/12:.3f} kW", "T": f"{T_cell:.1f}°C", "note": "OK"},
        {"id": "MPPT-01","type": "MPPT",     "état": "🟢 Normal",  "P": f"{P_dc:.2f} kW",   "T": "—",     "note": "OK"},
        {"id": "MET-01", "type": "Station",  "état": "🔵 Maintenance","P":"—",            "T": f"{T_live:.1f}°C","note": "Calibration"},
    ]
    df_eq = pd.DataFrame(equip_data)
    st.dataframe(df_eq, use_container_width=True, height=300)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">Distribution des états</div>', unsafe_allow_html=True)
        eq_counts = {"Normal": 5, "Attention": 1, "Alarme": 1, "Maintenance": 1}
        fig_e = go.Figure(go.Pie(
            labels=list(eq_counts.keys()), values=list(eq_counts.values()),
            marker_colors=["#50c878","#f0a500","#e74c3c","#3498db"], hole=0.5
        ))
        apply_layout(fig_e, height=220, showlegend=True)
        st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_e2:
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">Production par panneau (simulée)</div>', unsafe_allow_html=True)
        panels = [f"PNL-{i+1:02d}" for i in range(12)]
        prods = [P_dc/12 * (1 + np.random.default_rng(i).normal(0, 0.05)) for i in range(12)]
        colors = ["#50c878" if p > P_dc/12*0.9 else "#f0a500" for p in prods]
        fig_pan = go.Figure(go.Bar(x=panels, y=prods, marker_color=colors))
        apply_layout(fig_pan, height=220)
        st.plotly_chart(fig_pan, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ALARMES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Alarmes":
    st.markdown("## 🔔 Gestion des Alarmes")

    alarm_full = [
        {"Priorité": "🔴 CRITIQUE", "Description": "Défaut communication INV-01",
         "Équipement": "Onduleur #01", "Heure": "10:15", "État": "Non acquittée"},
        {"Priorité": "🟡 ATTENTION", "Description": "Température cellule élevée",
         "Équipement": "PNL-02", "Heure": datetime.now().strftime("%H:%M"), "État": "Auto"},
        {"Priorité": "🟡 ATTENTION", "Description": "PR dégradé < seuil",
         "Équipement": "Système", "Heure": datetime.now().strftime("%H:%M"), "État": "Auto"},
        {"Priorité": "ℹ️ INFO", "Description": "Irradiance capteur météo anormale",
         "Équipement": "MET-01", "Heure": "09:20", "État": "Acquittée"},
    ]

    df_alarms = pd.DataFrame(alarm_full)
    st.dataframe(df_alarms, use_container_width=True)

    st.markdown("### Statistiques")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Total", len(alarm_full))
    a2.metric("Critiques", sum(1 for a in alarm_full if "CRITIQUE" in a["Priorité"]))
    a3.metric("Attention", sum(1 for a in alarm_full if "ATTENTION" in a["Priorité"]))
    a4.metric("Non acquittées", sum(1 for a in alarm_full if "Non" in a["État"]))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — ANALYSES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Analyses":
    st.markdown("## 🔍 Analyses Avancées")

    st.markdown("### 📐 Courbe I-V Interactive")
    a1, a2 = st.columns(2)
    with a1:
        g_slider = st.slider("Irradiance (W/m²)", 100, 1000, int(G_live or 800), 50)
    with a2:
        t_slider = st.slider("T° ambiante (°C)", 0, 45, int(T_live or 25), 1)

    iv2 = model.compute_iv_curve(G=g_slider, T_amb=t_slider)
    fig_iv2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig_iv2.add_trace(go.Scatter(x=iv2["V"], y=iv2["I"], name="I(V)",
                                  line=dict(color='#3498db', width=2)), secondary_y=False)
    fig_iv2.add_trace(go.Scatter(x=iv2["V"], y=iv2["P"]/1000, name="P(V) kW",
                                  line=dict(color='#50c878', width=2, dash='dash')), secondary_y=True)
    fig_iv2.add_trace(go.Scatter(x=[iv2["V_mpp"]], y=[iv2["I_mpp"]], mode='markers',
                                  name="MPP", marker=dict(color='#e74c3c', size=12, symbol='star')),
                       secondary_y=False)
    fig_iv2.update_yaxes(title_text="Courant (A)", secondary_y=False, gridcolor='#21262d')
    fig_iv2.update_yaxes(title_text="Puissance (kW)", secondary_y=True, gridcolor='#21262d')
    apply_layout(fig_iv2, height=300, title_text=f"G={g_slider}W/m² | T={t_slider}°C | MPP={iv2['P_mpp']/1000:.2f}kW")
    st.plotly_chart(fig_iv2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    st.markdown("### 📊 Analyse de Sensibilité")
    sa1, sa2 = st.columns(2)
    with sa1:
        dc_l_s = st.slider("Pertes DC (%)", 0, 20, int(model.dc_losses*100), 1)
    with sa2:
        ac_eff_s = st.slider("Rendement AC (%)", 90, 99, int(model.ac_eff*100), 1)

    model_tmp = PVModel({**cfg,
        "losses": {**cfg["losses"], "dc_total": dc_l_s/100, "ac_efficiency": ac_eff_s/100}})
    r_sens = model_tmp.compute(G_live or 800, T_live or 25)
    r_nom  = model.compute(G_live or 800, T_live or 25)
    delta_ac = r_sens["P_ac_kW"] - r_nom["P_ac_kW"]
    delta_pr = r_sens["PR"] - r_nom["PR"]

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("P_ac (sensibilité)", f"{r_sens['P_ac_kW']:.3f} kW", f"{delta_ac:+.3f} kW")
    sc2.metric("PR (sensibilité)", f"{r_sens['PR']*100:.1f}%", f"{delta_pr*100:+.1f}%")
    sc3.metric("Pertes DC", f"{dc_l_s}%")
    sc4.metric("η AC", f"{ac_eff_s}%")

    st.markdown("---")
    st.markdown("### 🔧 Recalage Adaptatif")
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        p_meas = st.number_input("P_ac mesurée (kW)", 0.0, 5.0, float(P_ac), 0.01)
    with rc2:
        st.markdown("<br>", unsafe_allow_html=True)
        do_recal = st.button("⚙️ Recalibrer")

    if do_recal and G_live > 0:
        old_losses = model.dc_losses
        new_losses = model.recalibrate(p_meas, G_live, T_live)
        st.success(f"Recalibration : dc_losses {old_losses*100:.2f}% → {new_losses*100:.2f}%")
    elif do_recal:
        st.warning("Irradiance nulle, recalibration impossible.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — RAPPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Rapports":
    st.markdown("## 📄 Rapports")
    rtype = st.selectbox("Type de rapport", ["Rapport journalier", "Hebdomadaire", "Mensuel"])

    with st.expander(f"📋 {rtype} – {datetime.now().strftime('%d/%m/%Y')}", expanded=True):
        st.markdown(f"**Site :** Mohammedia, Maroc | **Période :** {rtype}")

        e_rep = energy_day_kWh if "journalier" in rtype.lower() else (
            energy_day_kWh * 7 if "hebdo" in rtype.lower() else energy_day_kWh * 30)
        sav_rep = compute_savings(e_rep, cfg)

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Énergie produite", format_energy(e_rep))
        r2.metric("PR moyen", f"{df_day['PR'].mean()*100:.1f}%")
        r3.metric("Économies", format_currency(sav_rep["mad"]))
        r4.metric("CO₂ évité", format_co2(sav_rep["co2_kg"]))

        kpi_df = pd.DataFrame({
            "Indicateur": ["Énergie (kWh)", "PR moyen (%)", "η moyen (%)", "Heures soleil"],
            "Valeur": [f"{e_rep:.1f}", f"{df_day['PR'].mean()*100:.1f}",
                       f"{df_day['eta'].mean()*100:.2f}", f"{(df_day['G']>50).sum()*0.25:.1f}"]
        })
        st.table(kpi_df)

        st.markdown("**Économies & Impact environnemental**")
        eco_df = pd.DataFrame({
            "Métrique": ["MAD économisés", "CO₂ évité (kg)", "Équivalent arbres"],
            "Valeur": [f"{sav_rep['mad']:.2f}", f"{sav_rep['co2_kg']:.2f}", f"{sav_rep['trees']:.2f}"]
        })
        st.table(eco_df)

        # Production vs forecast chart
        periods = ["J-6","J-5","J-4","J-3","J-2","J-1","Auj"]
        prod_vals = [model.compute_series(seed=i*77)["P_ac_kW"].mean()*24 for i in range(7)]
        fc_vals = [p * 1.08 for p in prod_vals]
        fig_rep = go.Figure()
        fig_rep.add_trace(go.Bar(name="Production réelle", x=periods, y=prod_vals,
                                  marker_color='#50c878', opacity=0.85))
        fig_rep.add_trace(go.Bar(name="Prévision", x=periods, y=fc_vals,
                                  marker_color='#3498db', opacity=0.5))
        fig_rep.update_layout(barmode='group')
        apply_layout(fig_rep, height=220, title_text="Production vs Prévision (kWh)")
        st.plotly_chart(fig_rep, use_container_width=True, config={"displayModeBar": False})

    # Download CSV
    csv_df = df_day.copy()
    csv_df["date"] = datetime.now().strftime("%Y-%m-%d")
    csv_bytes = csv_df.to_csv(index=False).encode()
    st.download_button("📥 Télécharger CSV", data=csv_bytes,
                        file_name=f"rapport_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — MÉTÉO
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌤️ Météo":
    st.markdown("## 🌤️ Météo & Prévisions")

    wc1, wc2, wc3 = st.columns([2, 3, 2])
    with wc1:
        st.markdown(f"""
        <div class="pv-card" style="text-align:center">
          <div style="font-size:60px">{weather_icon(weather_data['code'])}</div>
          <div style="font-family:'Rajdhani';font-size:36px;font-weight:700;color:#e6edf3">
            {weather_data['T']:.1f}°C</div>
          <div style="color:#8b949e;font-size:13px">{weather_label(weather_data['code'])}</div>
          <hr style="border-color:#30363d;margin:10px 0">
          <div style="font-size:12px;color:#f0a500">☀️ {weather_data['G']:.0f} W/m²</div>
          <div style="font-size:12px;color:#3498db">💨 {weather_data['wind']:.1f} km/h</div>
          <div style="font-size:10px;color:#50c878;margin-top:6px">Source: {weather_data['source']}</div>
        </div>
        """, unsafe_allow_html=True)

    with wc2:
        hourly = weather_data.get("hourly", {})
        if hourly and "shortwave_radiation" in hourly:
            times_h = hourly.get("time", [])[:24]
            rads = hourly.get("shortwave_radiation", [])[:24]
            temps = hourly.get("temperature_2m", [])[:24]
            h_labels = [t[11:16] if len(t) > 10 else str(t) for t in times_h]
        else:
            h_labels = [f"{h:02d}:00" for h in range(24)]
            rads = [max(0, 900 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0 for h in range(24)]
            temps = [25 + 5 * np.sin(np.pi * (h - 10) / 14) for h in range(24)]

        fig_wx = make_subplots(specs=[[{"secondary_y": True}]])
        fig_wx.add_trace(go.Scatter(x=h_labels, y=rads, name="Irradiance (W/m²)",
                                     fill='tozeroy', line=dict(color='#f0a500', width=2),
                                     fillcolor='rgba(240,165,0,0.12)'), secondary_y=False)
        fig_wx.add_trace(go.Scatter(x=h_labels, y=temps, name="Température (°C)",
                                     line=dict(color='#e74c3c', width=2)), secondary_y=True)
        fig_wx.update_yaxes(title_text="Irradiance W/m²", secondary_y=False, gridcolor='#21262d')
        fig_wx.update_yaxes(title_text="T° (°C)", secondary_y=True, gridcolor='#21262d')
        apply_layout(fig_wx, height=280, title_text="Prévisions horaires 24h")
        st.plotly_chart(fig_wx, use_container_width=True, config={"displayModeBar": False})

    with wc3:
        st.markdown('<div class="pv-card">', unsafe_allow_html=True)
        st.markdown('<div class="pv-card-title">📍 Localisation</div>', unsafe_allow_html=True)
        loc_df = pd.DataFrame({"lat": [cfg["site"]["lat"]], "lon": [cfg["site"]["lon"]]})
        st.map(loc_df, zoom=9)
        st.markdown(f"""
        <div style="font-size:11px;color:#8b949e;margin-top:6px">
          Mohammedia, Maroc<br>
          Lat {cfg['site']['lat']} | Lon {cfg['site']['lon']}<br>
          Alt {cfg['site']['alt']}m | Tilt {cfg['site']['tilt']}° | Az {cfg['site']['azimuth']}°
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 7-day forecast table
    st.markdown("### Prévisions 7 jours")
    days_fc = [(datetime.now() + timedelta(days=i)).strftime("%a %d/%m") for i in range(7)]
    max_temps = [weather_data['T'] + np.random.default_rng(i*3).normal(0, 3) for i in range(7)]
    min_temps = [t - np.random.default_rng(i*5+1).uniform(5, 10) for i, t in enumerate(max_temps)]
    g_fc = [np.random.default_rng(i*7).uniform(600, 950) for i in range(7)]
    icons_fc = ["☀️","🌤️","⛅","☀️","🌦️","☀️","🌤️"]
    df_fc = pd.DataFrame({
        "Jour": days_fc, "Icône": icons_fc,
        "T max (°C)": [f"{t:.1f}" for t in max_temps],
        "T min (°C)": [f"{t:.1f}" for t in min_temps],
        "Irradiance (W/m²)": [f"{g:.0f}" for g in g_fc],
    })
    st.dataframe(df_fc, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 9 — PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Paramètres":
    st.markdown("## ⚙️ Paramètres du système")

    with st.form("config_form"):
        tabs_cfg = st.tabs(["📍 Site", "🔆 Panneau", "🔌 Array", "📉 Pertes", "📡 Blynk", "🚨 Seuils"])

        with tabs_cfg[0]:
            c1, c2 = st.columns(2)
            with c1:
                lat  = st.number_input("Latitude", value=cfg["site"]["lat"])
                lon  = st.number_input("Longitude", value=cfg["site"]["lon"])
                alt  = st.number_input("Altitude (m)", value=cfg["site"]["alt"])
            with c2:
                tilt = st.number_input("Tilt (°)", value=cfg["site"]["tilt"])
                azim = st.number_input("Azimuth (°)", value=cfg["site"]["azimuth"])
                tz   = st.text_input("Timezone", value=cfg["site"]["tz"])

        with tabs_cfg[1]:
            c1, c2, c3 = st.columns(3)
            with c1:
                Pmp  = st.number_input("Pmp (W)", value=cfg["panel"]["Pmp"])
                eta  = st.number_input("η STC", value=cfg["panel"]["eta_stc"], format="%.3f")
                area = st.number_input("Aire (m²)", value=cfg["panel"]["area"], format="%.3f")
            with c2:
                Voc  = st.number_input("Voc (V)", value=cfg["panel"]["Voc"])
                Isc  = st.number_input("Isc (A)", value=cfg["panel"]["Isc"])
                Vmp  = st.number_input("Vmp (V)", value=cfg["panel"]["Vmp"])
            with c3:
                Imp  = st.number_input("Imp (A)", value=cfg["panel"]["Imp"])
                gamma_v = st.number_input("γ_pmp (/°C)", value=cfg["panel"]["gamma"], format="%.4f")
                NOCT = st.number_input("NOCT (°C)", value=cfg["panel"]["NOCT"])

        with tabs_cfg[2]:
            n_panels = st.number_input("Nombre panneaux", value=cfg["array"]["n_panels"])
            n_series = st.number_input("Panneaux en série", value=cfg["array"]["n_series"])
            n_par    = st.number_input("Strings parallèle", value=cfg["array"]["n_parallel"])
            n_mppt   = st.number_input("MPPT", value=cfg["array"]["n_mppt"])

        with tabs_cfg[3]:
            dc_t = st.slider("Pertes DC totales (%)", 0, 30, int(cfg["losses"]["dc_total"]*100))
            ac_e = st.slider("Rendement AC (%)", 85, 100, int(cfg["losses"]["ac_efficiency"]*100))
            inv_thr_v = st.number_input("Seuil onduleur (kW)", value=cfg["losses"]["inverter_threshold"])
            p_rat = st.number_input("P_rated (kW)", value=cfg["losses"]["p_rated"])

        with tabs_cfg[4]:
            token = st.text_input("Blynk Token", value=cfg["blynk"].get("token",""), type="password")
            server_b = st.text_input("Serveur Blynk", value=cfg["blynk"].get("server","blynk.cloud"))
            pin_t = st.text_input("Pin Température", value=cfg["blynk"].get("pin_temp","V0"))
            pin_i = st.text_input("Pin Irradiance", value=cfg["blynk"].get("pin_irr","V1"))

        with tabs_cfg[5]:
            pr_w = st.slider("PR warning", 0.5, 0.95, cfg["thresholds"]["pr_warning"])
            pr_c = st.slider("PR critique", 0.4, 0.85, cfg["thresholds"]["pr_critical"])
            tc_w = st.slider("T° cellule warning (°C)", 40, 80, cfg["thresholds"]["temp_cell_warning"])
            tc_c = st.slider("T° cellule critique (°C)", 50, 90, cfg["thresholds"]["temp_cell_critical"])

        sb1, sb2 = st.columns(2)
        with sb1:
            save = st.form_submit_button("💾 Sauvegarder", use_container_width=True)
        with sb2:
            reset = st.form_submit_button("🔄 Réinitialiser", use_container_width=True)

        if save:
            new_cfg = {
                "site": {"lat": lat, "lon": lon, "alt": alt, "tilt": tilt,
                         "azimuth": azim, "tz": tz, "name": cfg["site"].get("name","Mohammedia")},
                "panel": {"Pmp": Pmp, "eta_stc": eta, "area": area, "Voc": Voc,
                          "Isc": Isc, "Vmp": Vmp, "Imp": Imp, "gamma": gamma_v, "NOCT": NOCT},
                "array": {"n_panels": n_panels, "n_series": n_series,
                          "n_parallel": n_par, "n_mppt": n_mppt},
                "losses": {"dc_total": dc_t/100, "ac_efficiency": ac_e/100,
                           "inverter_threshold": inv_thr_v, "p_rated": p_rat},
                "blynk": {"token": token, "server": server_b, "pin_temp": pin_t, "pin_irr": pin_i},
                "thresholds": {"pr_warning": pr_w, "pr_critical": pr_c,
                               "temp_cell_warning": tc_w, "temp_cell_critical": tc_c},
                "economics": cfg.get("economics", DEFAULT_CONFIG["economics"]),
            }
            try:
                with open("config.yaml", "w") as f:
                    yaml.dump(new_cfg, f, allow_unicode=True)
                st.session_state.config = new_cfg
                st.session_state.model = PVModel(new_cfg)
                st.session_state.fetcher = DataFetcher(new_cfg)
                st.success("✅ Configuration sauvegardée avec succès !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

        if reset:
            st.session_state.config = DEFAULT_CONFIG.copy()
            st.session_state.model = PVModel(DEFAULT_CONFIG)
            st.session_state.fetcher = DataFetcher(DEFAULT_CONFIG)
            st.success("🔄 Configuration réinitialisée aux valeurs par défaut.")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-REFRESH (60s)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="auto_refresh")
except ImportError:
    pass  # optional dependency


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#21262d;margin-top:30px">
<div style="text-align:center;font-size:11px;color:#8b949e;padding-bottom:10px">
  ☀️ PV Digital Twin – Smart Solar Monitoring &nbsp;|&nbsp; Mohammedia, Maroc &nbsp;|&nbsp;
  Modèle IEC 61215 / IEC 61724 &nbsp;|&nbsp; v1.0.0
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# REQUIREMENTS (reference)
# ─────────────────────────────────────────────────────────────────────────────
# streamlit>=1.32
# plotly>=5.18
# pandas>=2.0
# numpy>=1.26
# requests>=2.31
# pyyaml>=6.0
# streamlit-autorefresh>=0.0.1  (optionnel – auto-refresh 60s)
