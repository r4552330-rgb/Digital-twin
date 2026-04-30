"""
PV Digital Twin - Smart Solar Monitoring
Dashboard Streamlit principal — v2.0 avec section mesures réelles + EMS.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import os
import time
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yaml

try:
    from model import PVModel
    from data import DataFetcher
except ModuleNotFoundError as exc:
    st.set_page_config(page_title="PV Digital Twin", layout="wide")
    st.error("Impossible d'importer `model.py` ou `data.py`. Placez les fichiers dans le même dossier.")
    st.exception(exc)
    st.stop()

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PV Digital Twin – Smart Solar Monitoring",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# DEFAULT CONFIG
# ─────────────────────────────────────────────────────────────
DEFAULT_CONFIG: dict[str, Any] = {
    "site": {"lat": 33.6, "lon": -7.6, "alt": 56, "tilt": 31, "azimuth": 180,
             "tz": "Africa/Casablanca", "name": "Mohammedia"},
    "panel": {"Pmp": 330, "eta_stc": 0.17, "area": 1.939, "Voc": 40.0, "Isc": 9.0,
              "Vmp": 33.0, "Imp": 8.5, "gamma": -0.004, "NOCT": 45},
    "array": {"n_panels": 12, "n_series": 6, "n_parallel": 2, "n_mppt": 1},
    "losses": {"dc_total": 0.10, "ac_efficiency": 0.96, "inverter_threshold": 0.05, "p_rated": 4.0},
    "blynk": {"token": "", "server": "blynk.cloud", "pin_temp": "V0", "pin_irr": "V1"},
    "thresholds": {"pr_warning": 0.75, "pr_critical": 0.65, "temp_cell_warning": 55, "temp_cell_critical": 70},
    "economics": {"co2_factor": 0.233, "tarif": 1.32, "tree_co2": 21.77},
    "ems": {
        "loads": [
            {"id": "L1", "name": "Climatisation", "p_kw": 1.2, "active": True},
            {"id": "L2", "name": "Eclairage", "p_kw": 0.3, "active": True},
            {"id": "L3", "name": "Prises", "p_kw": 0.5, "active": False},
            {"id": "L4", "name": "Pompe eau", "p_kw": 0.8, "active": True},
        ],
        "relays": [
            {"id": "R1", "name": "Relais reseau", "state": True},
            {"id": "R2", "name": "Delestage L3", "state": False},
            {"id": "R3", "name": "Alarme", "state": False},
        ],
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        return deepcopy(DEFAULT_CONFIG)
    try:
        with open(path, encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
        return deep_merge(DEFAULT_CONFIG, user)
    except Exception as exc:
        st.warning(f"config.yaml illisible, valeurs par defaut utilisees : {exc}")
        return deepcopy(DEFAULT_CONFIG)


def save_config(cfg: dict, path: str = "config.yaml") -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "data_mode" not in st.session_state:
    st.session_state.data_mode = "simulation"
if "config" not in st.session_state:
    st.session_state.config = load_config()
if "model" not in st.session_state:
    st.session_state.model = PVModel(st.session_state.config)
if "fetcher" not in st.session_state:
    st.session_state.fetcher = DataFetcher(st.session_state.config)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "sensor_status" not in st.session_state:
    st.session_state.sensor_status = {
        "blynk": "unknown",
        "open_meteo": "unknown",
        "last_error": "",
        "last_real_G": None,
        "last_real_T": None,
        "last_real_ts": None,
    }
if "ems_state" not in st.session_state:
    st.session_state.ems_state = deepcopy(st.session_state.config.get("ems", DEFAULT_CONFIG["ems"]))

cfg   = st.session_state.config
model = st.session_state.model
fetcher = st.session_state.fetcher

# ─────────────────────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────────────────────
THEMES = {
    "light": {
        "bg_main": "#f6f8fb", "bg_card": "#ffffff", "bg_card2": "#eef4fb",
        "sidebar": "#f8fbff", "border": "#d7e1ec", "grid": "#e5ebf2",
        "text_main": "#111827", "text_muted": "#5f6b7a",
        "shadow": "0 2px 12px rgba(17,24,39,.07)",
    },
    "dark": {
        "bg_main": "#0d1117", "bg_card": "#161b22", "bg_card2": "#1c2230",
        "sidebar": "#0d1117", "border": "#30363d", "grid": "#21262d",
        "text_main": "#e6edf3", "text_muted": "#8b949e",
        "shadow": "none",
    },
}
TH = THEMES["dark" if st.session_state.dark_mode else "light"]

GREEN  = "#50c878"
ORANGE = "#f0a500"
RED    = "#e74c3c"
BLUE   = "#2d8cff"
CYAN   = "#00bcd4"

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

:root {{
  --bg-main:   {TH['bg_main']};
  --bg-card:   {TH['bg_card']};
  --bg-card2:  {TH['bg_card2']};
  --sidebar:   {TH['sidebar']};
  --border:    {TH['border']};
  --grid:      {TH['grid']};
  --text-main: {TH['text_main']};
  --text-muted:{TH['text_muted']};
  --shadow:    {TH['shadow']};
  --green:#50c878; --orange:#f0a500; --red:#e74c3c; --blue:#2d8cff; --cyan:#00bcd4;
}}

*, *::before, *::after {{ box-sizing: border-box; }}
.stApp {{ background: var(--bg-main) !important; color: var(--text-main) !important; font-family: 'Inter', sans-serif; }}
header[data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
.main .block-container {{ padding: .8rem 1.4rem 2rem; max-width: 100%; }}
[data-testid="stSidebar"] {{ background: var(--sidebar) !important; border-right: 1px solid var(--border); }}
[data-testid="stSidebar"] > div {{ padding: 0 !important; }}

.pv-card {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; box-shadow: var(--shadow); padding: 14px 16px; margin-bottom: 12px;
}}
.pv-card-title {{
  font-family: 'Rajdhani', sans-serif; font-size: 13px; font-weight: 700;
  letter-spacing: 1.2px; text-transform: uppercase; color: var(--blue);
  padding-bottom: 7px; margin-bottom: 10px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}}

/* badges */
.badge {{
  display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 700;
  letter-spacing: .5px; border-radius: 20px; padding: 3px 9px; text-transform: uppercase;
}}
.badge::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }}
.badge-connected  {{ background: rgba(80,200,120,.12);  color: #50c878; border: 1px solid rgba(80,200,120,.3); }}
.badge-error      {{ background: rgba(231,76,60,.12);   color: #e74c3c; border: 1px solid rgba(231,76,60,.3); }}
.badge-simulation {{ background: rgba(45,140,255,.10);  color: #2d8cff; border: 1px solid rgba(45,140,255,.25); }}
.badge-unknown    {{ background: rgba(143,148,158,.10); color: #8b949e; border: 1px solid rgba(143,148,158,.25); }}
.badge-fallback   {{ background: rgba(240,165,0,.10);   color: #f0a500; border: 1px solid rgba(240,165,0,.25); }}

/* source tag */
.src-tag {{
  font-size: 9px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase;
  border-radius: 4px; padding: 2px 6px;
}}
.src-real {{ background:rgba(80,200,120,.18); color:#50c878; }}
.src-sim  {{ background:rgba(45,140,255,.12); color:#2d8cff; }}
.src-fb   {{ background:rgba(240,165,0,.12);  color:#f0a500; }}

/* mode bar */
.mode-bar {{
  display: flex; align-items: center; gap: 10px; background: var(--bg-card);
  border: 1px solid var(--border); border-radius: 10px; padding: 10px 16px; margin-bottom: 14px;
  font-size: 13px;
}}

/* measurement row */
.meas-row {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px;
}}
.meas-row:last-child {{ border-bottom: none; }}
.meas-label {{ color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing:.5px; }}
.meas-value {{ font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 600; }}
.meas-na {{ color: var(--text-muted) !important; font-size: 13px !important; font-style: italic; }}

/* kpi bar */
.kpi-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
.kpi-mini {{ background: var(--bg-card2); border: 1px solid var(--border); border-radius: 8px; flex: 1; min-width: 80px; padding: 8px 12px; }}
.kpi-mini .kl {{ color:var(--text-muted);font-size:10px;letter-spacing:.5px;text-transform:uppercase; }}
.kpi-mini .kv {{ font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700; }}
.kpi-mini .ku {{ color:var(--text-muted);font-size:10px; }}

/* energy flow */
.energy-flow {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; padding: 6px 0; }}
.flow-box {{ background: var(--bg-card2); border: 1px solid var(--border); border-radius: 10px; flex: 1; min-width: 72px; padding: 10px; text-align: center; }}
.flow-box .fb-label {{ color:var(--text-muted);font-size:10px;letter-spacing:.5px;text-transform:uppercase; }}
.flow-box .fb-value {{ font-family:'Rajdhani',sans-serif;font-size:16px;font-weight:700; }}
.flow-arrow {{ color:var(--green);flex-shrink:0;font-size:18px; }}

/* EMS */
.ems-conn-box {{
  background: var(--bg-card2); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px; height: 100%;
}}
.relay-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
.relay-on  {{ background: #50c878; box-shadow: 0 0 6px #50c878; }}
.relay-off {{ background: var(--border); }}

/* alarm */
.alarm-row {{ display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }}
.alarm-title {{ color:var(--text-main);font-size:12px;font-weight:600; }}
.alarm-sub   {{ color:var(--text-muted);font-size:10px; }}
.alarm-meta  {{ color:var(--text-muted);font-size:10px;margin-left:auto;text-align:right; }}

/* forecast */
.fc-card {{ background:var(--bg-card2);border:1px solid var(--border);border-radius:8px;min-width:70px;padding:8px 10px;text-align:center; }}
.fc-time {{ color:var(--text-muted);font-size:11px; }}
.fc-temp {{ color:var(--text-main);font-family:'Rajdhani';font-size:18px; }}
.fc-rad  {{ color:var(--orange);font-size:10px; }}

/* streamlit metric */
[data-testid="stMetric"] {{ background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;box-shadow:var(--shadow); }}
[data-testid="stMetricLabel"] {{ color:var(--text-muted)!important;font-size:11px!important;letter-spacing:.8px;text-transform:uppercase; }}
[data-testid="stMetricValue"] {{ color:var(--text-main)!important;font-family:'Rajdhani';font-size:26px!important; }}
[data-testid="stTabs"] button {{ color:var(--text-muted)!important;font-size:12px!important;font-weight:700; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:var(--blue)!important;border-bottom-color:var(--blue)!important; }}
.stButton>button {{ background:var(--bg-card2)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text-main)!important;font-size:13px!important;font-weight:600!important;padding:7px 14px!important; }}
.stButton>button:hover {{ color:var(--blue)!important;border-color:var(--blue)!important; }}
.stDownloadButton>button {{ background:var(--bg-card2)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text-main)!important; }}
input,textarea,select,[data-baseweb="select"]>div {{ background:var(--bg-card2)!important;color:var(--text-main)!important;border-color:var(--border)!important; }}
[data-testid="stDataFrame"] {{ background:var(--bg-card);border:1px solid var(--border);border-radius:8px; }}

.sidebar-logo {{ padding:20px 16px 14px;border-bottom:1px solid var(--border);margin-bottom:8px; }}
.sidebar-logo h2 {{ color:var(--text-main);font-family:'Rajdhani';font-size:18px;font-weight:700;margin:4px 0 2px; }}
.sidebar-logo p  {{ color:var(--orange);font-size:11px;letter-spacing:.5px;margin:0; }}
.sidebar-info {{ background:var(--bg-card);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow);color:var(--text-muted);font-size:11px;line-height:1.7;margin:12px 10px;padding:10px 14px; }}
.sidebar-info strong {{ color:var(--text-main);font-size:12px; }}

hr {{ border-color:var(--border)!important; }}
::-webkit-scrollbar {{ width:5px;height:5px; }}
::-webkit-scrollbar-track {{ background:var(--bg-main); }}
::-webkit-scrollbar-thumb {{ background:var(--border);border-radius:10px; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def card_open(title: str) -> None:
    st.markdown(f'<div class="pv-card"><div class="pv-card-title">{title}</div>', unsafe_allow_html=True)

def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)

def apply_layout(fig: go.Figure, **kw) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TH["text_main"], size=11, family="Inter"),
        margin=dict(l=40, r=20, t=30, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(color=TH["text_main"])),
        **kw,
    )
    fig.update_xaxes(gridcolor=TH["grid"], color=TH["text_main"], zeroline=False)
    fig.update_yaxes(gridcolor=TH["grid"], color=TH["text_main"], zeroline=False)
    return fig

def format_power(kW: float) -> str:
    return f"{kW/1000:.2f} MW" if kW >= 1000 else f"{kW:.2f} kW"

def format_energy(kWh: float) -> str:
    if kWh >= 1e6: return f"{kWh/1e6:.2f} GWh"
    if kWh >= 1000: return f"{kWh/1000:.2f} MWh"
    return f"{kWh:.1f} kWh"

def format_co2(kg: float) -> str:
    return f"{kg/1000:.2f} t CO2" if kg >= 1000 else f"{kg:.1f} kg CO2"

def format_currency(mad: float) -> str:
    return f"{mad:,.0f} MAD"

def get_performance_color(pr: float) -> str:
    if pr >= 0.80: return GREEN
    if pr >= 0.75: return ORANGE
    if pr >= 0.65: return "#e67e22"
    return RED

def get_temp_color(temp: float) -> str:
    if temp < 45: return GREEN
    if temp < 55: return ORANGE
    if temp < 70: return "#e67e22"
    return RED

def compute_savings(energy_kWh: float, config: dict) -> dict:
    eco = config["economics"]
    co2 = energy_kWh * eco["co2_factor"]
    return {"co2_kg": co2, "mad": energy_kWh * eco["tarif"], "trees": co2 / eco["tree_co2"]}

def diagnose(pr: float, temp_cell: float, thresholds: dict) -> list:
    alerts = []
    if pr < thresholds["pr_critical"]:
        alerts.append(("error", f"PR critique : {pr*100:.1f}% < {thresholds['pr_critical']*100:.0f}%"))
    elif pr < thresholds["pr_warning"]:
        alerts.append(("warning", f"PR degrade : {pr*100:.1f}% < {thresholds['pr_warning']*100:.0f}%"))
    if temp_cell > thresholds["temp_cell_critical"]:
        alerts.append(("error", f"T cellule critique : {temp_cell:.1f}C"))
    elif temp_cell > thresholds["temp_cell_warning"]:
        alerts.append(("warning", f"T cellule elevee : {temp_cell:.1f}C"))
    return alerts

def daily_energy(df: pd.DataFrame) -> float:
    return float(df["P_ac_kW"].mean() * 24)

WEATHER_ICONS = {0:"(sun)",1:"(sun-cloud)",2:"(cloud-sun)",3:"(cloud)",45:"(fog)",51:"(drizzle)",61:"(rain)",80:"(shower)",95:"(storm)"}
def weather_icon(code): return ""  # plain text for safety
def weather_label(code):
    labels = {0:"Ensoleille",1:"Principalement ensoleille",2:"Partiellement nuageux",
              3:"Couvert",45:"Brumeux",51:"Bruine legere",61:"Pluie legere",80:"Averses",95:"Orageux"}
    c = int(code or 0)
    for k in sorted(labels, reverse=True):
        if c >= k: return labels[k]
    return "Ensoleille"

# ─────────────────────────────────────────────────────────────
# DATA ACQUISITION
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def try_fetch_blynk(token: str, server: str, pin_T: str, pin_G: str):
    if not token:
        return None, None, False, "Token Blynk non configure"
    try:
        import requests
        def get_pin(pin):
            r = requests.get(f"https://{server}/{token}/get/{pin}", timeout=5)
            r.raise_for_status()
            return float(r.json()[0])
        T = get_pin(pin_T)
        G = get_pin(pin_G)
        if G < 0 or G > 1500 or T < -20 or T > 80:
            return None, None, False, f"Valeurs hors plage: G={G:.1f}, T={T:.1f}"
        return G, T, True, ""
    except Exception as e:
        return None, None, False, str(e)[:80]

@st.cache_data(ttl=900, show_spinner=False)
def try_fetch_weather():
    try:
        import requests
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude":33.6,"longitude":-7.6,"current_weather":True,
                    "hourly":"shortwave_radiation,temperature_2m,windspeed_10m",
                    "forecast_days":7,"timezone":"Africa/Casablanca"},
            timeout=8
        )
        data = r.json()
        cw = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        now_h = datetime.now().hour
        rads = hourly.get("shortwave_radiation", [])
        temps = hourly.get("temperature_2m", [])
        return {
            "T": cw.get("temperature", 25.0), "G": float(rads[now_h]) if now_h < len(rads) else 650.0,
            "wind": cw.get("windspeed", 0.0), "code": cw.get("weathercode", 0),
            "hourly": hourly, "source": "Open-Meteo", "ok": True,
        }
    except Exception as e:
        return {"T":25.0,"G":650.0,"wind":10.0,"code":0,"hourly":{},"source":"Erreur","ok":False,"error":str(e)[:60]}

def get_simulation_data() -> tuple[float, float]:
    now = datetime.now()
    h = now.hour + now.minute/60 + now.second/3600
    rng = np.random.default_rng(int(now.timestamp()) // 60)
    G = float(max(0, 880 * np.sin(np.pi*(h-6)/12) + rng.normal(0,25))) if 6<=h<=18 else 0.0
    T = float(25 + 7*np.sin(np.pi*(h-10)/14) + rng.normal(0,.8)) if 6<=h<=18 else 20.0
    return G, T

def acquire_data():
    ss = st.session_state.sensor_status
    blynk = cfg["blynk"]

    if st.session_state.data_mode == "real":
        G, T, ok, err = try_fetch_blynk(
            blynk.get("token",""), blynk.get("server","blynk.cloud"),
            blynk.get("pin_temp","V0"), blynk.get("pin_irr","V1")
        )
        if ok:
            ss["blynk"] = "connected"
            ss["last_real_G"] = G
            ss["last_real_T"] = T
            ss["last_real_ts"] = datetime.now()
            ss["last_error"] = ""
            return G, T, "Blynk ESP32", "real"
        else:
            ss["blynk"] = "error"
            ss["last_error"] = err
            wd = try_fetch_weather()
            if wd["ok"]:
                ss["open_meteo"] = "connected"
                return wd["G"], wd["T"], "Open-Meteo (fallback)", "fallback"
            else:
                ss["open_meteo"] = "error"
                G_s, T_s = get_simulation_data()
                return G_s, T_s, "Simulation (fallback)", "fallback"
    else:
        wd = try_fetch_weather()
        ss["open_meteo"] = "connected" if wd["ok"] else "error"
        ss["blynk"] = "unknown"
        G_s, T_s = get_simulation_data()
        return G_s, T_s, "Simulation", "sim"

def refresh_data():
    st.cache_data.clear()
    st.session_state.last_refresh = datetime.now()
    st.rerun()

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div style="font-size:32px">&#9728;</div>
      <h2>PV Digital Twin</h2>
      <p>Smart Solar Monitoring</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Dark" if not st.session_state.dark_mode else "Light",
                     use_container_width=True, key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_b:
        btn_lbl = "Mode Reel" if st.session_state.data_mode=="simulation" else "Mode Sim"
        if st.button(btn_lbl, use_container_width=True, key="mode_quick"):
            st.session_state.data_mode = "real" if st.session_state.data_mode=="simulation" else "simulation"
            st.cache_data.clear()
            st.rerun()

    p_kwp = cfg["panel"]["Pmp"] * cfg["array"]["n_panels"] / 1000
    st.markdown(f"""
    <div class="sidebar-info">
      <strong>{cfg['site'].get('name','Mohammedia')}, Maroc</strong><br>
      {p_kwp:.2f} kWp DC | {cfg['losses']['p_rated']:.1f} kW AC<br>
      Janvier 2023 | {cfg['array']['n_panels']} panneaux | {cfg['array']['n_mppt']} MPPT
    </div>
    """, unsafe_allow_html=True)

    # Sensor status
    ss = st.session_state.sensor_status
    blynk_cls = f"badge-{ss['blynk']}"
    om_cls    = f"badge-{ss['open_meteo']}"
    mode_cls  = "badge-simulation" if st.session_state.data_mode=="simulation" else "badge-connected"
    st.markdown(f"""
    <div style="padding:6px 10px 4px;">
      <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Statut capteurs</div>
      <span class="badge {blynk_cls}">Blynk {ss['blynk']}</span>&nbsp;
      <span class="badge {om_cls}" style="margin-top:4px">Open-Meteo {ss['open_meteo']}</span>
    </div>
    """, unsafe_allow_html=True)
    if ss["last_error"]:
        st.markdown(f'<div style="font-size:10px;color:#e74c3c;padding:0 10px 6px;word-break:break-word;">{ss["last_error"]}</div>',
                    unsafe_allow_html=True)

    nav_options = [
        "Vue d'ensemble",
        "Mesures Reelles",
        "EMS",
        "Jumeau numerique",
        "Performance",
        "Equipements",
        "Alarmes",
        "Analyses",
        "Rapports",
        "Meteo",
        "Parametres",
    ]
    page = st.radio("Navigation", nav_options, label_visibility="collapsed")
    st.markdown("---")
    if st.button("Rafraichir", use_container_width=True):
        refresh_data()
    st.caption(f"MaJ: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# ─────────────────────────────────────────────────────────────
# ACQUIRE LIVE DATA
# ─────────────────────────────────────────────────────────────
G_live, T_live, source_label, mode_tag = acquire_data()
weather_data = try_fetch_weather()

result_live = model.compute(G_live, T_live)
P_ac    = float(result_live["P_ac_kW"])
P_dc    = float(result_live["P_dc_kW"])
T_cell  = float(result_live["T_cell"])
PR      = float(result_live["PR"])
eta     = float(result_live["eta"])
eta_inv = float(result_live["eta_inv"])

df_day = model.compute_series(seed=int(datetime.now().strftime("%Y%m%d")))
energy_day_kWh   = daily_energy(df_day)
energy_total_kWh = energy_day_kWh * 365 * 3
savings_total    = compute_savings(energy_total_kWh, cfg)
alerts           = diagnose(PR, T_cell, cfg["thresholds"])

ems = st.session_state.ems_state
active_loads  = [l for l in ems["loads"] if l["active"]]
total_load_kW = sum(l["p_kw"] for l in active_loads)
net_export_kW = max(0, P_ac - total_load_kW)
net_import_kW = max(0, total_load_kW - P_ac)

# ─────────────────────────────────────────────────────────────
# MODE BAR (shown on all pages)
# ─────────────────────────────────────────────────────────────
is_real    = (st.session_state.data_mode == "real")
mode_color = GREEN if (is_real and mode_tag=="real") else ORANGE if mode_tag=="fallback" else BLUE
mode_dot   = f'<span style="font-size:12px;color:{mode_color};">&#9679;</span>'
mode_text  = ("Mode Reel — donnees capteurs" if (is_real and mode_tag=="real") else
              "Mode Reel — fallback simulation" if mode_tag=="fallback" else
              "Mode Simulation")
src_cls    = "src-real" if mode_tag=="real" else "src-fb" if mode_tag=="fallback" else "src-sim"
alert_html = (f'<span style="font-size:11px;color:{ORANGE};margin-left:12px;">'
              f'{len(alerts)} alerte(s)</span>' if alerts else "")

st.markdown(f"""
<div class="mode-bar">
  {mode_dot}
  <span style="font-weight:600;color:{mode_color};">{mode_text}</span>
  <span class="src-tag {src_cls}">{source_label}</span>
  <span style="margin-left:auto;font-size:11px;color:var(--text-muted);">{datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}</span>
  {alert_html}
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# PAGE: VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════════
if page == "Vue d'ensemble":

    hc1, hc2, hc3 = st.columns([2, 5, 3])
    with hc1:
        w_temp = weather_data.get("T", T_live)
        w_G    = weather_data.get("G", G_live)
        w_lbl  = weather_label(weather_data.get("code",0))
        st.markdown(f"""
        <div style="text-align:center;padding:14px 10px;background:var(--bg-card);
             border:1px solid var(--border);border-radius:12px;">
          <div style="font-size:42px;line-height:1;">&#9728;</div>
          <div style="font-family:'Rajdhani';font-size:30px;font-weight:700;color:var(--text-main)">{w_temp:.1f}&deg;C</div>
          <div style="font-size:12px;color:var(--text-muted)">{w_lbl}</div>
          <div style="font-size:11px;color:#f0a500;margin-top:4px">{w_G:.0f} W/m&sup2;</div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:3px">{source_label}</div>
        </div>""", unsafe_allow_html=True)

    with hc2:
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Puissance AC", format_power(P_ac), f"{P_ac/cfg['losses']['p_rated']*100:.0f}% capacite")
        k2.metric("Production jour", format_energy(energy_day_kWh))
        k3.metric("Production totale", format_energy(energy_total_kWh))
        k4.metric("CO2 evite", format_co2(savings_total["co2_kg"]), f"arbres: {savings_total['trees']:.0f}")

    with hc3:
        st.date_input("Date", datetime.now().date(), label_visibility="collapsed")
        st.selectbox("Periode", ["Aujourd'hui","Semaine","Mois","Annee"], label_visibility="collapsed")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([6,4])

    with col_left:
        card_open("Jumeau numerique - Vue 3D")
        sc1, sc2 = st.columns([3,1])
        with sc2:
            st.radio("Vue", ["Vue libre","Irradiance","Temperature","Production","Pertes"],
                     label_visibility="collapsed", key="scene_view")
            st.markdown(f"""<div style="font-size:10px;line-height:2;margin-top:8px">
              <span style="color:{GREEN}">&#9679;</span> Normal<br>
              <span style="color:{ORANGE}">&#9679;</span> Attention<br>
              <span style="color:{RED}">&#9679;</span> Alarme<br>
              <span style="color:{BLUE}">&#9679;</span> Maintenance</div>""", unsafe_allow_html=True)
        with sc1:
            if os.path.exists("assets/Scene_enset.png"):
                st.image("assets/Scene_enset.png", use_container_width=True)
            else:
                st.markdown(f"""<div style="height:260px;border:1px solid var(--border);border-radius:10px;
                    background:linear-gradient(135deg,var(--bg-card2),var(--bg-card));
                    display:flex;align-items:center;justify-content:center;">
                    <div style="text-align:center">
                    <div style="font-size:54px">&#9728;</div>
                    <div style="font-size:12px;color:var(--text-muted)">assets/Scene_enset.png</div>
                    <div style="font-size:11px;color:{GREEN};margin-top:4px">12 panneaux actifs</div>
                    </div></div>""", unsafe_allow_html=True)

        tc_c = get_temp_color(T_cell)
        pr_c = get_performance_color(PR)
        st.markdown(f"""<div class="kpi-bar">
          <div class="kpi-mini"><div class="kl">T Cellule</div>
            <div class="kv" style="color:{tc_c}">{T_cell:.1f}</div><div class="ku">deg C</div></div>
          <div class="kpi-mini"><div class="kl">Rendement</div>
            <div class="kv" style="color:{BLUE}">{eta*100:.1f}%</div><div class="ku">eta panneau</div></div>
          <div class="kpi-mini"><div class="kl">Perf. Ratio</div>
            <div class="kv" style="color:{pr_c}">{PR*100:.1f}%</div><div class="ku">PR actuel</div></div>
          <div class="kpi-mini"><div class="kl">Charge EMS</div>
            <div class="kv" style="color:{ORANGE}">{total_load_kW:.2f}</div><div class="ku">kW</div></div>
        </div>""", unsafe_allow_html=True)
        card_close()

        card_open("Production & Performance")
        t1,t2,t3,t4 = st.tabs(["Jour","Semaine","Mois","Annee"])
        with t1:
            c1,c2,c3 = st.columns(3)
            rs = energy_day_kWh / p_kwp if p_kwp > 0 else 0
            c1.metric("Production", format_energy(energy_day_kWh))
            c2.metric("Rend. specifique", f"{rs:.2f} kWh/kWp")
            c3.metric("PR moyen", f"{df_day['PR'].mean()*100:.1f}%")
            fig_p = make_subplots(specs=[[{"secondary_y":True}]])
            fig_p.add_trace(go.Scatter(x=df_day["hour"],y=df_day["P_ac_kW"],name="P_ac (kW)",
                fill="tozeroy",line=dict(color=GREEN,width=2),fillcolor="rgba(80,200,120,0.12)"),secondary_y=False)
            fig_p.add_trace(go.Scatter(x=df_day["hour"],y=df_day["G"],name="G (W/m2)",
                line=dict(color=ORANGE,width=1.5,dash="dot")),secondary_y=True)
            fig_p.update_yaxes(title_text="P_ac (kW)",secondary_y=False)
            fig_p.update_yaxes(title_text="G (W/m2)",secondary_y=True)
            st.plotly_chart(apply_layout(fig_p,height=220),use_container_width=True,config={"displayModeBar":False})
        with t2:
            days7 = [(datetime.now()-timedelta(days=6-i)).strftime("%d/%m") for i in range(7)]
            e7 = [daily_energy(model.compute_series(seed=i*77)) for i in range(7)]
            fig_w = go.Figure(go.Bar(x=days7,y=e7,marker_color=GREEN,opacity=0.85))
            st.plotly_chart(apply_layout(fig_w,height=200),use_container_width=True,config={"displayModeBar":False})
        with t3:
            months = ["Jan","Fev","Mar","Avr","Mai","Jun","Jul","Aou","Sep","Oct","Nov","Dec"]
            ey = [daily_energy(model.compute_series(seed=i*1000))*30 for i in range(12)]
            fig_m = go.Figure(go.Bar(x=months,y=ey,marker_color=BLUE,opacity=0.75))
            st.plotly_chart(apply_layout(fig_m,height=200),use_container_width=True,config={"displayModeBar":False})
        with t4:
            st.info("Connecter une source de donnees historiques.")
        card_close()

        card_open("Courbe I-V instantanee")
        iv_data = model.compute_iv_curve(G=G_live if G_live>10 else 800, T_amb=T_live)
        fig_iv = make_subplots(specs=[[{"secondary_y":True}]])
        fig_iv.add_trace(go.Scatter(x=iv_data["V"],y=iv_data["I"],name="I(V)",line=dict(color=BLUE,width=2)),secondary_y=False)
        fig_iv.add_trace(go.Scatter(x=iv_data["V"],y=iv_data["P"]/1000,name="P(V) kW",
            line=dict(color=GREEN,width=2,dash="dash")),secondary_y=True)
        fig_iv.add_trace(go.Scatter(x=[iv_data["V_mpp"]],y=[iv_data["I_mpp"]],name="MPP",mode="markers",
            marker=dict(color=RED,size=11,symbol="star")),secondary_y=False)
        fig_iv.update_yaxes(title_text="Courant (A)",secondary_y=False)
        fig_iv.update_yaxes(title_text="Puissance (kW)",secondary_y=True)
        st.plotly_chart(apply_layout(fig_iv,height=200),use_container_width=True,config={"displayModeBar":False})
        ic1,ic2,ic3 = st.columns(3)
        ic1.metric("P_mpp",f"{iv_data['P_mpp']/1000:.2f} kW")
        ic2.metric("V_mpp",f"{iv_data['V_mpp']:.1f} V")
        ic3.metric("I_mpp",f"{iv_data['I_mpp']:.2f} A")
        card_close()

        card_open("Comparaison Performance 7 jours")
        tabs7 = st.tabs(["PR","Production specifique","Irradiance"])
        days7lbl = [(datetime.now()-timedelta(days=6-i)).strftime("%d/%m") for i in range(7)]
        pr7 = [model.compute_series(seed=i*77)["PR"].mean() for i in range(7)]
        with tabs7[0]:
            fig7 = go.Figure()
            fig7.add_trace(go.Scatter(x=days7lbl,y=[p*100 for p in pr7],name="PR Reel",line=dict(color=GREEN,width=2)))
            fig7.add_trace(go.Scatter(x=days7lbl,y=[p*105 for p in pr7],name="PR Attendu",line=dict(color=ORANGE,width=2,dash="dash")))
            st.plotly_chart(apply_layout(fig7,height=190),use_container_width=True,config={"displayModeBar":False})
        with tabs7[1]:
            pspec = [daily_energy(model.compute_series(seed=i*77))/p_kwp for i in range(7)]
            fig7b = go.Figure(go.Scatter(x=days7lbl,y=pspec,name="kWh/kWp",line=dict(color=BLUE,width=2)))
            st.plotly_chart(apply_layout(fig7b,height=190),use_container_width=True,config={"displayModeBar":False})
        with tabs7[2]:
            g7 = [model.compute_series(seed=i*77)["G"].max() for i in range(7)]
            fig7c = go.Figure(go.Bar(x=days7lbl,y=g7,marker_color=ORANGE,opacity=0.85))
            st.plotly_chart(apply_layout(fig7c,height=190),use_container_width=True,config={"displayModeBar":False})
        card_close()

    with col_right:
        card_open("Flux d'energie")
        load_pct = P_ac / cfg["losses"]["p_rated"] * 100 if cfg["losses"]["p_rated"] > 0 else 0
        arr_c = GREEN if load_pct>80 else ORANGE if load_pct>50 else RED
        export_color = GREEN if net_export_kW > 0 else RED
        st.markdown(f"""
        <div class="energy-flow">
          <div class="flow-box"><div style="font-size:22px">&#9728;</div>
            <div class="fb-label">Generateur</div>
            <div class="fb-value" style="color:{ORANGE}">{G_live:.0f}<br><span style="font-size:10px">W/m2</span></div></div>
          <div class="flow-arrow" style="color:{arr_c}">&#9658;</div>
          <div class="flow-box"><div style="font-size:22px">&#128267;</div>
            <div class="fb-label">DC</div>
            <div class="fb-value" style="color:{BLUE}">{P_dc:.2f}<br><span style="font-size:10px">kW</span></div></div>
          <div class="flow-arrow" style="color:{arr_c}">&#9658;</div>
          <div class="flow-box"><div style="font-size:22px">&#9889;</div>
            <div class="fb-label">AC</div>
            <div class="fb-value" style="color:{GREEN}">{P_ac:.2f}<br><span style="font-size:10px">kW</span></div></div>
          <div class="flow-arrow" style="color:{arr_c}">&#9658;</div>
          <div class="flow-box"><div style="font-size:22px">&#127981;</div>
            <div class="fb-label">Reseau</div>
            <div class="fb-value" style="color:{export_color}">{net_export_kW:.2f}<br><span style="font-size:10px">kW exp.</span></div></div>
        </div>
        <div style="font-size:11px;color:{RED};margin-top:4px;">
          Pertes DC: {P_dc*cfg['losses']['dc_total']:.3f} kW &nbsp;|&nbsp; Pertes onduleur: {max(0,P_dc-P_ac):.3f} kW
        </div>
        <div style="font-size:11px;color:{ORANGE};margin-top:3px;">
          Charge: {total_load_kW:.2f} kW &nbsp;|&nbsp;
          {'Export' if net_export_kW>0 else 'Import'}: <span style="color:{export_color};font-weight:600">{max(net_export_kW,net_import_kW):.2f} kW</span>
        </div>
        """, unsafe_allow_html=True)
        card_close()

        card_open("Repartition des pertes")
        irr_loss  = max(0,(1-eta/cfg["panel"]["eta_stc"])*P_dc*0.6)*100/max(P_dc,0.001) if G_live>0 else 6.2
        temp_loss = abs(cfg["panel"]["gamma"]*(T_cell-25))*100 if G_live>0 else 4.1
        loss_v = [max(0,irr_loss),max(0,temp_loss),cfg["losses"]["dc_total"]*100,
                  (1-eta_inv)*100 if eta_inv>0 else 4.0, 0.5, 1.9, 1.7, 2.0]
        loss_l = ["Irradiance","Temperature","DC","Onduleur","Cables","Mismatch","Ombrage","Autres"]
        loss_c = [BLUE,GREEN,RED,ORANGE,"#f39c12","#9b59b6","#1abc9c",TH["text_muted"]]
        total_l = sum(loss_v)
        fig_loss = go.Figure(go.Pie(labels=loss_l,values=loss_v,marker_colors=loss_c,hole=0.52,textinfo="none"))
        fig_loss.add_annotation(text=f"<b>{total_l:.1f}%</b>",x=0.5,y=0.5,
            font=dict(size=14,color=RED),showarrow=False)
        st.plotly_chart(apply_layout(fig_loss,height=180,showlegend=True,
            margin=dict(l=0,r=0,t=10,b=10)),use_container_width=True,config={"displayModeBar":False})
        card_close()

        card_open("Diagnostic automatique")
        if not alerts:
            st.success("Systeme nominal — tous parametres dans les limites")
        else:
            for lvl, msg in alerts:
                st.error(msg) if lvl=="error" else st.warning(msg)
        s = compute_savings(energy_day_kWh, cfg)
        sc1,sc2,sc3 = st.columns(3)
        sc1.metric("Economies/j", format_currency(s["mad"]))
        sc2.metric("CO2/j", format_co2(s["co2_kg"]))
        sc3.metric("Arbres eq.", f"{s['trees']:.2f}")
        card_close()

        card_open("Alarmes recentes")
        alarm_list = [{"icon":"&#9632;","title":"Defaut comm. INV-01","sub":"Onduleur #01",
                        "time":"10:15","status":"Non acquittee","color":RED}]
        for lvl,msg in alerts:
            alarm_list.append({"icon":"&#9650;","title":msg,"sub":"Auto-detecte",
                "time":datetime.now().strftime("%H:%M"),"status":"Auto",
                "color":ORANGE if lvl=="warning" else RED})
        for alm in alarm_list[:3]:
            st.markdown(f"""<div class="alarm-row">
              <div style="font-size:16px;color:{alm['color']}">{alm['icon']}</div>
              <div><div class="alarm-title">{alm['title']}</div><div class="alarm-sub">{alm['sub']}</div></div>
              <div class="alarm-meta">{alm['time']}<br>
                <span style="color:{alm['color']};font-weight:600">{alm['status']}</span></div>
            </div>""", unsafe_allow_html=True)
        card_close()

        card_open("Meteo & Previsions")
        now_h = datetime.now().hour
        fc_slots = [
            {"time": datetime.now().strftime("%H:%M"), "temp": weather_data.get("T",T_live), "G": G_live},
            {"time": f"{(now_h+3)%24:02d}:00", "temp": weather_data.get("T",25)+1, "G": 900},
            {"time": f"{(now_h+6)%24:02d}:00", "temp": weather_data.get("T",25)+3, "G": 950},
            {"time": f"{(now_h+9)%24:02d}:00", "temp": weather_data.get("T",25)+1, "G": 750},
        ]
        fc_c = st.columns(len(fc_slots))
        for i, fc in enumerate(fc_slots):
            with fc_c[i]:
                st.markdown(f"""<div class="fc-card">
                  <div class="fc-time">{fc['time']}</div>
                  <div style="font-size:20px">&#9728;</div>
                  <div class="fc-temp">{fc['temp']:.0f}&deg;C</div>
                  <div class="fc-rad">{fc['G']:.0f} W/m&sup2;</div></div>""", unsafe_allow_html=True)
        card_close()


# ═══════════════════════════════════════════════════════════════
# PAGE: MESURES REELLES
# ═══════════════════════════════════════════════════════════════
elif page == "Mesures Reelles":

    st.markdown("## Mesures Reelles & Capteurs")
    ss = st.session_state.sensor_status

    # Control bar
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2,2,2,2])
    with ctrl1:
        new_mode = st.toggle("Mode Reel (capteurs actifs)", value=(st.session_state.data_mode=="real"), key="real_toggle")
        if new_mode != (st.session_state.data_mode=="real"):
            st.session_state.data_mode = "real" if new_mode else "simulation"
            st.cache_data.clear()
            st.rerun()
    with ctrl2:
        b_cls = f"badge-{ss['blynk']}"
        st.markdown(f'<div style="margin-top:8px"><span class="badge {b_cls}">Blynk {ss["blynk"]}</span></div>',
                    unsafe_allow_html=True)
    with ctrl3:
        o_cls = f"badge-{ss['open_meteo']}"
        st.markdown(f'<div style="margin-top:8px"><span class="badge {o_cls}">Open-Meteo {ss["open_meteo"]}</span></div>',
                    unsafe_allow_html=True)
    with ctrl4:
        if st.button("Tester connexion", key="test_conn"):
            st.cache_data.clear()
            st.session_state.sensor_status["blynk"] = "unknown"
            st.session_state.sensor_status["open_meteo"] = "unknown"
            st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Connection status cards
    card_open("Statut des connexions")
    cs1, cs2, cs3 = st.columns(3)

    def conn_card(col, title, subtitle, status, detail1, detail2, extra_html=""):
        b_c = GREEN if status=="connected" else RED if status=="error" else ORANGE if status=="fallback" else TH["text_muted"]
        ico = "&#10003;" if status=="connected" else "&#10007;" if status=="error" else "&#9679;"
        lbl = "Connecte" if status=="connected" else "Erreur" if status=="error" else "Fallback" if status=="fallback" else "Inconnu"
        b_cls = f"badge-{status}"
        with col:
            st.markdown(f"""
            <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:10px;
                 padding:14px;border-left:4px solid {b_c};">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <div style="font-size:18px;font-weight:700;color:{b_c};">{ico}</div>
                <div style="flex:1;">
                  <div style="font-weight:700;font-size:13px;color:var(--text-main);">{title}</div>
                  <div style="font-size:11px;color:var(--text-muted);">{subtitle}</div>
                </div>
                <span class="badge {b_cls}">{lbl}</span>
              </div>
              <div style="font-size:11px;color:var(--text-muted);">{detail1}</div>
              <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{detail2}</div>
              {extra_html}
            </div>""", unsafe_allow_html=True)

    last_ts = ss["last_real_ts"].strftime("%H:%M:%S") if ss["last_real_ts"] else "--"
    err_html = (f'<div style="font-size:10px;color:{RED};margin-top:6px;">{ss["last_error"]}</div>'
                if ss["last_error"] and ss["blynk"]=="error" else "")
    conn_card(cs1, "Blynk ESP32", cfg["blynk"].get("server","blynk.cloud"), ss["blynk"],
              f"Derniere donnee: {last_ts}", f"Pins: T={cfg['blynk'].get('pin_temp','V0')} | G={cfg['blynk'].get('pin_irr','V1')}", err_html)
    conn_card(cs2, "Open-Meteo API", "api.open-meteo.com", ss["open_meteo"],
              f"Lat: {cfg['site']['lat']} | Lon: {cfg['site']['lon']}", "TTL cache: 15 min")
    conn_card(cs3, "Moteur Simulation", "IEC 61215 / IEC 61724",
              "simulation" if mode_tag in ("sim","fallback") else "unknown",
              "Sinusoide solaire + bruit gaussien", "Fallback automatique si capteurs off")
    card_close()

    # Sensor readings + gauges
    mr_left, mr_right = st.columns([5,4])

    with mr_left:
        card_open("Mesures des capteurs")
        st.markdown(f"""<div style="font-size:11px;color:var(--text-muted);margin-bottom:12px;
             background:var(--bg-card2);border-radius:6px;padding:8px 12px;border:1px solid var(--border);">
          Les valeurs en <span style="color:{GREEN};font-weight:600">vert</span> proviennent des capteurs reels.
          Les valeurs en <span style="color:{BLUE};font-weight:600">bleu</span> sont calculees par le modele.
          Les valeurs en <span style="color:{ORANGE};font-weight:600">orange</span> sont des fallbacks.
          "<span style="color:var(--text-muted);">--</span>" indique une donnee non disponible.
        </div>""", unsafe_allow_html=True)

        def meas_row(label, value, unit, tag, hint=""):
            val_color = GREEN if tag=="real" else BLUE if tag=="sim" else ORANGE if tag=="fallback" else TH["text_muted"]
            tag_cls   = "src-real" if tag=="real" else "src-fb" if tag=="fallback" else "src-sim"
            tag_txt   = "reel" if tag=="real" else "fallback" if tag=="fallback" else "sim"
            na_class  = " meas-na" if value=="--" else ""
            return f"""<div class="meas-row">
              <div>
                <div class="meas-label">{label}</div>
                {"<div style='font-size:10px;color:var(--text-muted);margin-top:1px;'>"+hint+"</div>" if hint else ""}
              </div>
              <div style="display:flex;align-items:center;gap:8px;">
                <span class="src-tag {tag_cls}">{tag_txt}</span>
                <span class="meas-value{na_class}" style="color:{val_color};">{value}</span>
                <span style="font-size:12px;color:var(--text-muted);">{unit}</span>
              </div>
            </div>"""

        # Determine source for each sensor
        if ss["last_real_G"] is not None and mode_tag=="real":
            irr_v, irr_tag = f"{ss['last_real_G']:.1f}", "real"
        elif mode_tag=="fallback":
            irr_v, irr_tag = f"{G_live:.1f}", "fallback"
        elif G_live > 0:
            irr_v, irr_tag = f"{G_live:.1f}", "sim"
        else:
            irr_v, irr_tag = "--", "sim"

        if ss["last_real_T"] is not None and mode_tag=="real":
            temp_v, temp_tag = f"{ss['last_real_T']:.1f}", "real"
        elif mode_tag=="fallback":
            temp_v, temp_tag = f"{T_live:.1f}", "fallback"
        else:
            temp_v, temp_tag = f"{T_live:.1f}", "sim"

        rows = [
            ("Irradiance (POA)",      irr_v,              "W/m2",  irr_tag,  "Capteur ESP32 broche V1"),
            ("Temperature ambiante",  temp_v,             "C",     temp_tag, "Capteur ESP32 broche V0"),
            ("Temperature cellule",   f"{T_cell:.1f}",    "C",     "sim",    "Calcule NOCT (IEC 61215)"),
            ("Puissance DC",          f"{P_dc:.3f}",      "kW",    "sim",    "Modele PV"),
            ("Puissance AC",          f"{P_ac:.3f}",      "kW",    "sim",    "Modele PV"),
            ("Performance Ratio",     f"{PR*100:.1f}",    "%",     "sim",    "IEC 61724"),
            ("Rendement panneau",     f"{eta*100:.2f}",   "%",     "sim",    "Corrige temperature"),
            ("Rendement onduleur",    f"{eta_inv*100:.1f}","%",    "sim",    "Courbe charge"),
            ("Charge totale EMS",     f"{total_load_kW:.2f}","kW", "sim",    "Somme charges actives"),
            ("Export reseau",         f"{net_export_kW:.3f}","kW", "sim",    "P_ac - Charges"),
        ]

        rows_html = "".join(meas_row(*r) for r in rows)
        st.markdown(rows_html, unsafe_allow_html=True)
        card_close()

    with mr_right:
        card_open("Indicateurs temps reel")
        fig_gauges = make_subplots(rows=2, cols=2,
            specs=[[{"type":"indicator"},{"type":"indicator"}],
                   [{"type":"indicator"},{"type":"indicator"}]],
            vertical_spacing=0.08, horizontal_spacing=0.04)

        def add_gauge(row, col, val, title, max_v, bar_color):
            fig_gauges.add_trace(go.Indicator(
                mode="gauge+number",
                value=val,
                title={"text":title,"font":{"size":10,"color":TH["text_muted"]}},
                number={"font":{"size":15,"color":TH["text_main"]}},
                gauge={"axis":{"range":[0,max_v],"tickfont":{"size":8,"color":TH["text_muted"]}},
                       "bar":{"color":bar_color,"thickness":.22},
                       "bgcolor":"rgba(0,0,0,0)","bordercolor":TH["border"],
                       "threshold":{"line":{"color":bar_color,"width":2},"thickness":.65,"value":val*0.95}},
            ), row=row, col=col)

        add_gauge(1,1, G_live,      "Irradiance<br>W/m2",       1200,  ORANGE)
        add_gauge(1,2, P_ac,        "Puissance AC<br>kW",        cfg["losses"]["p_rated"], GREEN)
        add_gauge(2,1, PR*100,      "Perf. Ratio<br>%",          100,   get_performance_color(PR))
        add_gauge(2,2, T_cell,      "T Cellule<br>deg C",        90,    get_temp_color(T_cell))

        apply_layout(fig_gauges, height=290, margin=dict(l=8,r=8,t=15,b=8))
        st.plotly_chart(fig_gauges, use_container_width=True, config={"displayModeBar":False})
        card_close()

        card_open("Historique capteurs")
        if ss["last_real_ts"]:
            age = (datetime.now() - ss["last_real_ts"]).total_seconds()
            age_str = f"{int(age//60)}m {int(age%60)}s" if age > 60 else f"{int(age)}s"
            st.markdown(f"""
            <div style="background:rgba(80,200,120,.07);border:1px solid rgba(80,200,120,.2);
                 border-radius:8px;padding:12px 14px;margin-bottom:10px;">
              <div style="font-size:10px;color:{GREEN};font-weight:700;letter-spacing:.5px;margin-bottom:8px;">DERNIERE MESURE REELLE</div>
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span style="color:var(--text-muted)">Irradiance</span>
                <span style="font-family:'JetBrains Mono';color:{GREEN};font-weight:600;">{ss['last_real_G']:.1f} W/m2</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:13px;">
                <span style="color:var(--text-muted)">Temperature</span>
                <span style="font-family:'JetBrains Mono';color:{GREEN};font-weight:600;">{ss['last_real_T']:.1f} C</span>
              </div>
              <div style="font-size:10px;color:var(--text-muted);margin-top:8px;">Il y a {age_str}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:rgba(45,140,255,.06);border:1px solid rgba(45,140,255,.2);
                 border-radius:8px;padding:14px;text-align:center;color:var(--text-muted);font-size:12px;">
              Aucune mesure reelle disponible<br>
              <span style="font-size:10px;">Configurez le token Blynk dans Parametres</span>
            </div>""", unsafe_allow_html=True)

        # Trend sparkline
        st.markdown(f"<div style='font-size:11px;color:var(--text-muted);margin-top:10px;margin-bottom:4px;'>Tendance G (24h)</div>",
                    unsafe_allow_html=True)
        h_arr = np.arange(0, 24, 0.5)
        rng   = np.random.default_rng(42)
        G_tr  = np.array([max(0, 880*np.sin(np.pi*(h-6)/12)+rng.normal(0,20)) if 6<=h<=18 else 0 for h in h_arr])
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Scatter(x=h_arr, y=G_tr, fill="tozeroy",
            line=dict(color=ORANGE,width=1.5), fillcolor="rgba(240,165,0,0.1)", name="G sim"))
        if ss["last_real_G"] is not None:
            now_frac = datetime.now().hour + datetime.now().minute/60
            fig_tr.add_trace(go.Scatter(x=[now_frac], y=[ss["last_real_G"]],
                mode="markers", marker=dict(color=GREEN,size=10), name="G reel"))
        fig_tr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=110, margin=dict(l=28,r=8,t=4,b=22), showlegend=True,
            legend=dict(font=dict(size=9,color=TH["text_muted"]),bgcolor="rgba(0,0,0,0)",x=0,y=1))
        fig_tr.update_xaxes(gridcolor=TH["grid"],tickvals=[0,6,12,18,24],
                             ticktext=["0h","6h","12h","18h","24h"],color=TH["text_muted"],tickfont=dict(size=9))
        fig_tr.update_yaxes(gridcolor=TH["grid"],color=TH["text_muted"],tickfont=dict(size=9))
        st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar":False})
        card_close()


# ═══════════════════════════════════════════════════════════════
# PAGE: EMS
# ═══════════════════════════════════════════════════════════════
elif page == "EMS":
    st.markdown("## Gestion de l'Energie (EMS)")

    ems = st.session_state.ems_state
    ec1, ec2 = st.columns([5,4])

    with ec1:
        card_open("Bilan de puissance instantane")
        bc1,bc2,bc3,bc4 = st.columns(4)
        bc1.metric("Production PV", f"{P_ac:.2f} kW")
        bc2.metric("Consommation", f"{total_load_kW:.2f} kW")
        delta = P_ac - total_load_kW
        bc3.metric("Bilan reseau", f"{abs(delta):.2f} kW", "Export" if delta>=0 else "Import")
        bc4.metric("Autoconsommation",
                   f"{min(100,P_ac/total_load_kW*100):.0f}%" if total_load_kW>0 else "--")

        # Sankey energy flow
        pv_to_load = min(P_ac, total_load_kW)
        pv_export  = max(0, P_ac - total_load_kW)
        grid_import = max(0, total_load_kW - P_ac)
        san_sources = [0, 0]
        san_targets = [1, 2]
        san_values  = [pv_to_load, pv_export]
        san_colors  = ["rgba(80,200,120,0.35)", "rgba(45,140,255,0.35)"]
        if grid_import > 0:
            san_sources += [3]
            san_targets += [1]
            san_values  += [grid_import]
            san_colors  += ["rgba(231,76,60,0.35)"]
        fig_san = go.Figure(go.Sankey(
            node=dict(pad=14, thickness=14,
                line=dict(color=TH["border"], width=0.5),
                label=["PV", "Charges", "Export reseau", "Import reseau"],
                color=[GREEN, ORANGE, BLUE, RED]),
            link=dict(source=san_sources, target=san_targets,
                      value=[max(0.001,v) for v in san_values], color=san_colors)
        ))
        apply_layout(fig_san, height=220, margin=dict(l=4,r=4,t=8,b=8))
        st.plotly_chart(fig_san, use_container_width=True, config={"displayModeBar":False})
        card_close()

        card_open("Gestion des charges")
        st.markdown(f"<div style='font-size:11px;color:var(--text-muted);margin-bottom:10px;'>Activez/desactivez les charges pour optimiser l'autoconsommation</div>",
                    unsafe_allow_html=True)
        for i, load in enumerate(ems["loads"]):
            lc1, lc2 = st.columns([5,1])
            with lc1:
                new_active = st.checkbox(
                    f"{load['name']}  —  {load['p_kw']:.1f} kW",
                    value=load["active"],
                    key=f"load_{load['id']}"
                )
                ems["loads"][i]["active"] = new_active
            with lc2:
                color  = GREEN if new_active else TH["text_muted"]
                st.markdown(f"<div style='font-size:11px;font-weight:700;color:{color};padding-top:6px;'>{'ON' if new_active else 'OFF'}</div>",
                             unsafe_allow_html=True)

        new_active_loads = [l for l in ems["loads"] if l["active"]]
        new_load_kw = sum(l["p_kw"] for l in new_active_loads)
        st.markdown(f"""<div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:8px;
             padding:10px 14px;margin-top:8px;display:flex;justify-content:space-between;font-size:13px;">
          <span style="color:var(--text-muted)">Total actif:</span>
          <span style="font-family:'JetBrains Mono';color:{ORANGE};font-weight:600;">{new_load_kw:.2f} kW</span>
        </div>""", unsafe_allow_html=True)
        card_close()

    with ec2:
        card_open("Gestion des relais")
        for i, relay in enumerate(ems["relays"]):
            rc1, rc2 = st.columns([4,2])
            with rc1:
                new_state = st.toggle(relay["name"], value=relay["state"], key=f"relay_{relay['id']}")
                ems["relays"][i]["state"] = new_state
            with rc2:
                dot_cls = "relay-on" if new_state else "relay-off"
                r_color = GREEN if new_state else TH["text_muted"]
                st.markdown(f"""<div style="display:flex;align-items:center;gap:6px;padding-top:4px;">
                  <div class="relay-dot {dot_cls}"></div>
                  <span style="font-size:11px;color:{r_color};font-weight:700;">{'FERME' if new_state else 'OUVERT'}</span>
                </div>""", unsafe_allow_html=True)
        card_close()

        card_open("Repartition de l'energie")
        autoconso = min(P_ac, total_load_kW)
        fig_ems = go.Figure(go.Pie(
            labels=["Autoconsomme","Exporte","Importe"],
            values=[max(0.001,autoconso), max(0.001,net_export_kW), max(0.001,net_import_kW)],
            marker_colors=[GREEN, BLUE, RED], hole=0.55,
            textinfo="label+percent", textfont_size=11,
        ))
        fig_ems.add_annotation(text=f"<b>{P_ac:.2f} kW</b>",
            x=0.5, y=0.5, font=dict(size=12, color=TH["text_main"]), showarrow=False)
        apply_layout(fig_ems, height=220, showlegend=False, margin=dict(l=8,r=8,t=8,b=8))
        st.plotly_chart(fig_ems, use_container_width=True, config={"displayModeBar":False})
        card_close()

        card_open("Resume EMS")
        def ems_kv(label, val, col=None):
            c = col or TH["text_main"]
            st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:6px 0;
              border-bottom:1px solid var(--border);font-size:12px;">
              <span style="color:var(--text-muted)">{label}</span>
              <span style="font-family:'JetBrains Mono';color:{c};font-weight:600;">{val}</span>
            </div>""", unsafe_allow_html=True)
        ems_kv("Production PV", f"{P_ac:.3f} kW", GREEN)
        ems_kv("Consommation", f"{total_load_kW:.3f} kW", ORANGE)
        ems_kv("Autoconsommation", f"{min(100,autoconso/P_ac*100):.1f}%" if P_ac>0 else "--", CYAN)
        ems_kv("Export reseau", f"{net_export_kW:.3f} kW", BLUE)
        ems_kv("Import reseau", f"{net_import_kW:.3f} kW", RED if net_import_kW>0 else TH["text_muted"])
        ems_kv("Relais actifs", f"{sum(1 for r in ems['relays'] if r['state'])}/{len(ems['relays'])}")
        card_close()


# ═══════════════════════════════════════════════════════════════
# REMAINING PAGES
# ═══════════════════════════════════════════════════════════════
elif page == "Jumeau numerique":
    st.markdown("## Jumeau Numerique")
    c1,c2 = st.columns([3,2])
    with c1:
        card_open("Vue 3D interactive")
        if os.path.exists("assets/Scene_enset.png"):
            st.image("assets/Scene_enset.png", use_container_width=True)
        else:
            st.markdown(f"""<div style="height:400px;border:1px solid var(--border);border-radius:10px;
                background:linear-gradient(135deg,var(--bg-card2),var(--bg-card));
                display:flex;align-items:center;justify-content:center;">
                <div style="text-align:center"><div style="font-size:64px">&#9728;</div>
                <div style="font-size:12px;color:var(--text-muted)">assets/Scene_enset.png</div>
                <div style="font-size:11px;color:{GREEN};margin-top:4px">12 panneaux actifs</div></div></div>""",
                unsafe_allow_html=True)
        card_close()
    with c2:
        card_open("Parametres temps reel")
        mrt = [
            ("Irradiance", f"{G_live:.0f} W/m2", mode_tag=="real"),
            ("T ambiante", f"{T_live:.1f} C", mode_tag=="real"),
            ("T cellule", f"{T_cell:.1f} C", False),
            ("P_dc", f"{P_dc:.3f} kW", False),
            ("P_ac", f"{P_ac:.3f} kW", False),
            ("PR", f"{PR*100:.1f}%", False),
            ("eta panneau", f"{eta*100:.2f}%", False),
            ("eta onduleur", f"{eta_inv*100:.1f}%", False),
        ]
        for lbl, val, is_r in mrt:
            vc = GREEN if is_r else BLUE
            tc = "src-real" if is_r else "src-sim"
            tt = "reel" if is_r else "sim"
            st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:7px 0;
              border-bottom:1px solid var(--border);font-size:13px;">
              <span style="color:var(--text-muted)">{lbl}</span>
              <div style="display:flex;align-items:center;gap:8px;">
                <span class="src-tag {tc}">{tt}</span>
                <strong style="color:{vc};font-family:'JetBrains Mono';">{val}</strong>
              </div></div>""", unsafe_allow_html=True)
        card_close()
        card_open("Localisation")
        st.map(pd.DataFrame({"lat":[cfg["site"]["lat"]],"lon":[cfg["site"]["lon"]]}), zoom=10)
        card_close()

elif page == "Performance":
    st.markdown("## Performance")
    tab_d, tab_w, tab_m, tab_y = st.tabs(["Jour","Semaine","Mois","Annee"])
    def render_perf_tab(df, mult):
        c1,c2,c3,c4 = st.columns(4)
        energy = float(df["P_ac_kW"].mean()*mult)
        c1.metric("Energie", format_energy(energy))
        c2.metric("PR moyen", f"{df['PR'].mean()*100:.1f}%")
        c3.metric("eta moyen", f"{df['eta'].mean()*100:.2f}%")
        c4.metric("Heures soleil", f"{(df['G']>50).sum()*0.25:.1f}h")
        fig2 = make_subplots(specs=[[{"secondary_y":True}]])
        fig2.add_trace(go.Scatter(x=df["hour"],y=df["P_ac_kW"],name="P_ac (kW)",
            fill="tozeroy",line=dict(color=GREEN,width=2),fillcolor="rgba(80,200,120,.12)"),secondary_y=False)
        fig2.add_trace(go.Scatter(x=df["hour"],y=df["G"],name="G (W/m2)",
            line=dict(color=ORANGE,width=1.5,dash="dot")),secondary_y=True)
        fig2.update_yaxes(title_text="P_ac (kW)",secondary_y=False)
        fig2.update_yaxes(title_text="G (W/m2)",secondary_y=True)
        st.plotly_chart(apply_layout(fig2,height=250),use_container_width=True,config={"displayModeBar":False})
        st.dataframe(df[["hour","G","T_amb","T_cell","P_dc_kW","P_ac_kW","PR","eta_inv"]].round(3),
                     use_container_width=True, height=200)
    with tab_d: render_perf_tab(df_day, 24)
    with tab_w:
        df_w = pd.concat([model.compute_series(seed=i*77) for i in range(7)],ignore_index=True)
        render_perf_tab(df_w, 24*7)
    with tab_m:
        df_m = model.compute_series(hours=np.arange(0,24*30,.5),seed=999)
        render_perf_tab(df_m, 24*30)
    with tab_y: st.info("Connecter une source de donnees historiques.")

elif page == "Equipements":
    st.markdown("## Equipements")
    equip_data = [
        {"id":"INV-01","type":"Onduleur","etat":"ALARME","P":"0.0 kW","T":"--","note":"Defaut comm."},
        {"id":"INV-02","type":"Onduleur","etat":"NORMAL","P":f"{P_ac:.2f} kW","T":f"{T_cell:.1f}C","note":"OK"},
        {"id":"PNL-01","type":"Panneau","etat":"NORMAL","P":f"{P_dc/12:.3f} kW","T":f"{T_cell:.1f}C","note":"OK"},
        {"id":"PNL-02","type":"Panneau","etat":"ATTENTION","P":f"{P_dc/12*.9:.3f} kW","T":f"{T_cell+5:.1f}C","note":"T elevee"},
        {"id":"MPPT-01","type":"MPPT","etat":"NORMAL","P":f"{P_dc:.2f} kW","T":"--","note":"OK"},
        {"id":"MET-01","type":"Station","etat":"MAINTENANCE","P":"--","T":f"{T_live:.1f}C","note":"Calibration"},
    ]
    st.dataframe(pd.DataFrame(equip_data), use_container_width=True, height=280)

elif page == "Alarmes":
    st.markdown("## Alarmes")
    alarm_full = [
        {"Priorite":"CRITIQUE","Description":"Defaut comm. INV-01","Equipement":"Onduleur #01","Heure":"10:15","Etat":"Non acquittee"},
        {"Priorite":"ATTENTION","Description":"T cellule elevee","Equipement":"PNL-02","Heure":datetime.now().strftime("%H:%M"),"Etat":"Auto"},
    ]
    for lvl,msg in alerts:
        alarm_full.append({"Priorite":"CRITIQUE" if lvl=="error" else "ATTENTION",
            "Description":msg,"Equipement":"Systeme","Heure":datetime.now().strftime("%H:%M"),"Etat":"Auto"})
    st.dataframe(pd.DataFrame(alarm_full), use_container_width=True)
    a1,a2,a3,a4 = st.columns(4)
    a1.metric("Total",len(alarm_full))
    a2.metric("Critiques",sum(1 for a in alarm_full if a["Priorite"]=="CRITIQUE"))
    a3.metric("Attention",sum(1 for a in alarm_full if a["Priorite"]=="ATTENTION"))
    a4.metric("Non acquittees",sum(1 for a in alarm_full if "Non" in a["Etat"]))

elif page == "Analyses":
    st.markdown("## Analyses Avancees")
    a1,a2 = st.columns(2)
    with a1: g_s = st.slider("Irradiance (W/m2)",100,1000,int(G_live or 800),50)
    with a2: t_s = st.slider("Temperature ambiante (C)",0,45,int(T_live or 25),1)
    iv2 = model.compute_iv_curve(G=g_s, T_amb=t_s)
    fig_iv2 = make_subplots(specs=[[{"secondary_y":True}]])
    fig_iv2.add_trace(go.Scatter(x=iv2["V"],y=iv2["I"],name="I(V)",line=dict(color=BLUE,width=2)),secondary_y=False)
    fig_iv2.add_trace(go.Scatter(x=iv2["V"],y=iv2["P"]/1000,name="P(V) kW",
        line=dict(color=GREEN,width=2,dash="dash")),secondary_y=True)
    fig_iv2.add_trace(go.Scatter(x=[iv2["V_mpp"]],y=[iv2["I_mpp"]],mode="markers",
        marker=dict(color=RED,size=11,symbol="star"),name="MPP"),secondary_y=False)
    fig_iv2.update_yaxes(title_text="Courant (A)",secondary_y=False)
    fig_iv2.update_yaxes(title_text="Puissance (kW)",secondary_y=True)
    st.plotly_chart(apply_layout(fig_iv2,height=300,
        title_text=f"G={g_s} W/m2 | T={t_s}C | MPP={iv2['P_mpp']/1000:.2f} kW"),
        use_container_width=True, config={"displayModeBar":False})

elif page == "Rapports":
    st.markdown("## Rapports")
    rt = st.selectbox("Type", ["Rapport journalier","Hebdomadaire","Mensuel"])
    e_r = energy_day_kWh if "jour" in rt.lower() else energy_day_kWh*7 if "hebdo" in rt.lower() else energy_day_kWh*30
    s_r = compute_savings(e_r, cfg)
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Energie", format_energy(e_r))
    r2.metric("PR moyen", f"{df_day['PR'].mean()*100:.1f}%")
    r3.metric("Economies", format_currency(s_r["mad"]))
    r4.metric("CO2 evite", format_co2(s_r["co2_kg"]))
    csv_b = df_day.to_csv(index=False).encode("utf-8")
    st.download_button("Telecharger CSV", data=csv_b,
        file_name=f"rapport_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

elif page == "Meteo":
    st.markdown("## Meteo & Previsions")
    wc1,wc2 = st.columns([2,4])
    with wc1:
        card_open("Conditions actuelles")
        st.markdown(f"""<div style="text-align:center">
          <div style="font-size:48px">&#9728;</div>
          <div style="font-family:'Rajdhani';font-size:34px;font-weight:700">{weather_data.get('T',T_live):.1f}&deg;C</div>
          <div style="color:var(--text-muted);font-size:12px">{weather_label(weather_data.get('code',0))}</div>
          <div style="font-size:12px;color:#f0a500;margin-top:6px">{weather_data.get('G',G_live):.0f} W/m&sup2;</div>
          <div style="font-size:10px;color:#50c878;margin-top:4px">{weather_data.get('source','Simulation')}</div>
        </div>""", unsafe_allow_html=True)
        card_close()
    with wc2:
        hourly = weather_data.get("hourly", {})
        rads  = hourly.get("shortwave_radiation", [max(0,880*np.sin(np.pi*(h-6)/12)) if 6<=h<=18 else 0 for h in range(24)])[:24]
        temps = hourly.get("temperature_2m", [25+5*np.sin(np.pi*(h-10)/14) for h in range(24)])[:24]
        labels_h = [f"{h:02d}:00" for h in range(24)]
        fig_wm = make_subplots(specs=[[{"secondary_y":True}]])
        fig_wm.add_trace(go.Scatter(x=labels_h,y=rads,name="Irradiance",fill="tozeroy",
            line=dict(color=ORANGE,width=2),fillcolor="rgba(240,165,0,.10)"),secondary_y=False)
        fig_wm.add_trace(go.Scatter(x=labels_h,y=temps,name="Temperature",
            line=dict(color=RED,width=2)),secondary_y=True)
        fig_wm.update_yaxes(title_text="W/m2",secondary_y=False)
        fig_wm.update_yaxes(title_text="C",secondary_y=True)
        st.plotly_chart(apply_layout(fig_wm,height=300),use_container_width=True,config={"displayModeBar":False})
    st.map(pd.DataFrame({"lat":[cfg["site"]["lat"]],"lon":[cfg["site"]["lon"]]}), zoom=9)

elif page == "Parametres":
    st.markdown("## Parametres du systeme")
    with st.form("config_form"):
        tabs_cfg = st.tabs(["Site","Panneau","Array","Pertes","Blynk","Seuils"])
        with tabs_cfg[0]:
            c1,c2 = st.columns(2)
            with c1:
                lat = st.number_input("Latitude", value=float(cfg["site"]["lat"]))
                lon = st.number_input("Longitude", value=float(cfg["site"]["lon"]))
                alt = st.number_input("Altitude (m)", value=int(cfg["site"]["alt"]))
            with c2:
                tilt = st.number_input("Tilt (deg)", value=int(cfg["site"]["tilt"]))
                azimuth = st.number_input("Azimuth (deg)", value=int(cfg["site"]["azimuth"]))
        with tabs_cfg[1]:
            c1,c2,c3 = st.columns(3)
            with c1:
                Pmp = st.number_input("Pmp (W)", value=float(cfg["panel"]["Pmp"]))
                eta_s = st.number_input("eta STC", value=float(cfg["panel"]["eta_stc"]),format="%.3f")
                area  = st.number_input("Aire (m2)", value=float(cfg["panel"]["area"]),format="%.3f")
            with c2:
                Voc = st.number_input("Voc (V)", value=float(cfg["panel"]["Voc"]))
                Isc = st.number_input("Isc (A)", value=float(cfg["panel"]["Isc"]))
                Vmp = st.number_input("Vmp (V)", value=float(cfg["panel"]["Vmp"]))
            with c3:
                Imp   = st.number_input("Imp (A)", value=float(cfg["panel"]["Imp"]))
                gamma = st.number_input("gamma (/C)", value=float(cfg["panel"]["gamma"]),format="%.4f")
                NOCT  = st.number_input("NOCT (C)", value=float(cfg["panel"]["NOCT"]))
        with tabs_cfg[2]:
            np_cfg = st.number_input("Nb panneaux", value=int(cfg["array"]["n_panels"]))
            ns_cfg = st.number_input("En serie", value=int(cfg["array"]["n_series"]))
            npar   = st.number_input("Strings //", value=int(cfg["array"]["n_parallel"]))
            nm     = st.number_input("MPPT", value=int(cfg["array"]["n_mppt"]))
        with tabs_cfg[3]:
            dc_t = st.slider("Pertes DC (%)",0,30,int(cfg["losses"]["dc_total"]*100))
            ac_e = st.slider("Rendement AC (%)",85,100,int(cfg["losses"]["ac_efficiency"]*100))
            p_r  = st.number_input("P_rated (kW)", value=float(cfg["losses"]["p_rated"]))
        with tabs_cfg[4]:
            token  = st.text_input("Token Blynk", value=cfg["blynk"].get("token",""),type="password")
            server = st.text_input("Serveur", value=cfg["blynk"].get("server","blynk.cloud"))
            pin_t  = st.text_input("Pin Temperature", value=cfg["blynk"].get("pin_temp","V0"))
            pin_g  = st.text_input("Pin Irradiance",  value=cfg["blynk"].get("pin_irr","V1"))
            st.info("Renseignez le token Blynk pour activer le mode reel. Sans token, le mode simulation est utilise.")
        with tabs_cfg[5]:
            pr_w  = st.slider("PR warning",0.5,0.95,float(cfg["thresholds"]["pr_warning"]))
            pr_c2 = st.slider("PR critique",0.4,0.85,float(cfg["thresholds"]["pr_critical"]))
            tc_w  = st.slider("T cellule warning (C)",40,80,int(cfg["thresholds"]["temp_cell_warning"]))
            tc_c  = st.slider("T cellule critique (C)",50,90,int(cfg["thresholds"]["temp_cell_critical"]))

        sb1,sb2 = st.columns(2)
        save  = sb1.form_submit_button("Sauvegarder", use_container_width=True)
        reset = sb2.form_submit_button("Reinitialiser", use_container_width=True)
        if save:
            new_cfg = deep_merge(cfg, {
                "site":{"lat":lat,"lon":lon,"alt":alt,"tilt":tilt,"azimuth":azimuth},
                "panel":{"Pmp":Pmp,"eta_stc":eta_s,"area":area,"Voc":Voc,"Isc":Isc,
                          "Vmp":Vmp,"Imp":Imp,"gamma":gamma,"NOCT":NOCT},
                "array":{"n_panels":int(np_cfg),"n_series":int(ns_cfg),
                          "n_parallel":int(npar),"n_mppt":int(nm)},
                "losses":{"dc_total":dc_t/100,"ac_efficiency":ac_e/100,"p_rated":p_r},
                "blynk":{"token":token,"server":server,"pin_temp":pin_t,"pin_irr":pin_g},
                "thresholds":{"pr_warning":pr_w,"pr_critical":pr_c2,
                               "temp_cell_warning":tc_w,"temp_cell_critical":tc_c},
            })
            try:
                save_config(new_cfg)
                st.session_state.config = new_cfg
                st.session_state.model  = PVModel(new_cfg)
                st.session_state.fetcher = DataFetcher(new_cfg)
                st.cache_data.clear()
                st.success("Configuration sauvegardee.")
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur : {exc}")
        if reset:
            st.session_state.config  = deepcopy(DEFAULT_CONFIG)
            st.session_state.model   = PVModel(st.session_state.config)
            st.session_state.fetcher = DataFetcher(st.session_state.config)
            st.cache_data.clear()
            st.success("Reinitialise.")
            st.rerun()

# ─────────────────────────────────────────────────────────────
# AUTO-REFRESH
# ─────────────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="auto_refresh")
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:var(--border);margin-top:30px">
<div style="text-align:center;font-size:11px;color:var(--text-muted);padding-bottom:10px">
  PV Digital Twin — Smart Solar Monitoring &nbsp;|&nbsp; Mohammedia, Maroc &nbsp;|&nbsp;
  Modele IEC 61215 / IEC 61724 &nbsp;|&nbsp; v2.0.0
</div>
""", unsafe_allow_html=True)

# requirements:
# streamlit>=1.32
# plotly>=5.18
# pandas>=2.0
# numpy>=1.26
# requests>=2.31
# pyyaml>=6.0
# streamlit-autorefresh>=0.0.1  (optionnel)
