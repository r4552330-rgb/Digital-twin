"""
PV Digital Twin - Smart Solar Monitoring
Dashboard Streamlit principal.

Architecture:
- model.py : classe PVModel
- data.py  : classe DataFetcher
- app.py   : interface utilisateur, configuration, cache, pages
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import os
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
    st.set_page_config(page_title="PV Digital Twin", page_icon="☀️", layout="wide")
    st.error(
        "Impossible d'importer `model.py` ou `data.py`. "
        "Placez `app.py`, `model.py` et `data.py` dans le même dossier."
    )
    st.exception(exc)
    st.stop()


# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PV Digital Twin - Smart Solar Monitoring",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# DEFAULT CONFIG + LOADER
# -----------------------------------------------------------------------------
DEFAULT_CONFIG: dict[str, Any] = {
    "site": {
        "lat": 33.6,
        "lon": -7.6,
        "alt": 56,
        "tilt": 31,
        "azimuth": 180,
        "tz": "Africa/Casablanca",
        "name": "Mohammedia",
    },
    "panel": {
        "Pmp": 330,
        "eta_stc": 0.17,
        "area": 1.939,
        "Voc": 40.0,
        "Isc": 9.0,
        "Vmp": 33.0,
        "Imp": 8.5,
        "gamma": -0.004,
        "NOCT": 45,
    },
    "array": {"n_panels": 12, "n_series": 6, "n_parallel": 2, "n_mppt": 1},
    "losses": {
        "dc_total": 0.10,
        "ac_efficiency": 0.96,
        "inverter_threshold": 0.05,
        "p_rated": 4.0,
    },
    "blynk": {"token": "", "server": "blynk.cloud", "pin_temp": "V0", "pin_irr": "V1"},
    "thresholds": {
        "pr_warning": 0.75,
        "pr_critical": 0.65,
        "temp_cell_warning": 55,
        "temp_cell_critical": 70,
    },
    "economics": {"co2_factor": 0.233, "tarif": 1.32, "tree_co2": 21.77},
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    if not os.path.exists(path):
        return deepcopy(DEFAULT_CONFIG)

    try:
        with open(path, encoding="utf-8") as file:
            user_config = yaml.safe_load(file) or {}
        return deep_merge(DEFAULT_CONFIG, user_config)
    except Exception as exc:
        st.warning(f"config.yaml illisible, valeurs par défaut utilisées : {exc}")
        return deepcopy(DEFAULT_CONFIG)


def save_config(config: dict[str, Any], path: str = "config.yaml") -> None:
    with open(path, "w", encoding="utf-8") as file:
        yaml.safe_dump(config, file, allow_unicode=True, sort_keys=False)


# -----------------------------------------------------------------------------
# THEME
# -----------------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

THEMES = {
    "light": {
        "bg_main": "#f6f8fb",
        "bg_card": "#ffffff",
        "bg_card2": "#eef4fb",
        "sidebar": "#f8fbff",
        "border": "#d7e1ec",
        "grid": "#e5ebf2",
        "text_main": "#111827",
        "text_muted": "#5f6b7a",
        "shadow": "0 10px 28px rgba(17, 24, 39, .06)",
    },
    "dark": {
        "bg_main": "#0d1117",
        "bg_card": "#161b22",
        "bg_card2": "#1c2230",
        "sidebar": "#0d1117",
        "border": "#30363d",
        "grid": "#21262d",
        "text_main": "#e6edf3",
        "text_muted": "#8b949e",
        "shadow": "none",
    },
}

THEME = THEMES["dark" if st.session_state.dark_mode else "light"]


def inject_css() -> None:
    st.markdown(
        f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

  :root {{
    --bg-main: {THEME['bg_main']};
    --bg-card: {THEME['bg_card']};
    --bg-card2: {THEME['bg_card2']};
    --sidebar: {THEME['sidebar']};
    --border: {THEME['border']};
    --grid: {THEME['grid']};
    --text-main: {THEME['text_main']};
    --text-muted: {THEME['text_muted']};
    --shadow: {THEME['shadow']};
    --green: #50c878;
    --orange: #f0a500;
    --red: #e74c3c;
    --blue: #2d8cff;
    --cyan: #00bcd4;
    --font-main: 'Inter', sans-serif;
    --font-head: 'Rajdhani', sans-serif;
  }}

  .stApp {{
    background: var(--bg-main) !important;
    color: var(--text-main) !important;
    font-family: var(--font-main);
  }}

  header[data-testid="stHeader"],
  [data-testid="stToolbar"] {{
    display: none !important;
  }}

  .main .block-container {{
    padding: 1rem 1.5rem 2rem;
    max-width: 100%;
  }}

  [data-testid="stSidebar"] {{
    background: var(--sidebar) !important;
    border-right: 1px solid var(--border);
  }}

  [data-testid="stSidebar"] > div {{
    padding: 0 !important;
  }}

  h1, h2, h3, h4, h5, h6, p, label, span, div {{
    color: inherit;
  }}

  .pv-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
    padding: 14px 16px;
    margin-bottom: 12px;
  }}

  .pv-card-title {{
    font-family: var(--font-head);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--blue);
    padding-bottom: 7px;
    margin-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }}

  [data-testid="stMetric"] {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    box-shadow: var(--shadow);
  }}

  [data-testid="stMetricLabel"] {{
    color: var(--text-muted) !important;
    font-size: 11px !important;
    letter-spacing: .8px;
    text-transform: uppercase;
  }}

  [data-testid="stMetricValue"] {{
    color: var(--text-main) !important;
    font-family: var(--font-head);
    font-size: 26px !important;
  }}

  [data-testid="stMetricDelta"] {{
    font-size: 11px !important;
  }}

  [data-testid="stTabs"] button {{
    color: var(--text-muted) !important;
    font-size: 12px !important;
    font-weight: 700;
    border-bottom: 2px solid transparent;
  }}

  [data-testid="stTabs"] button[aria-selected="true"] {{
    color: var(--blue) !important;
    border-bottom-color: var(--blue) !important;
  }}

  [data-testid="stRadio"] label {{
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px !important;
    padding: 7px 10px;
  }}

  [data-testid="stRadio"] label:hover {{
    background: var(--bg-card2);
  }}

  .stButton > button,
  .stDownloadButton > button,
  button[kind="secondary"] {{
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-main) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 7px 14px !important;
  }}

  .stButton > button:hover,
  .stDownloadButton > button:hover {{
    color: var(--blue) !important;
    border-color: var(--blue) !important;
  }}

  input, textarea, select,
  [data-baseweb="select"] > div {{
    background: var(--bg-card2) !important;
    color: var(--text-main) !important;
    border-color: var(--border) !important;
  }}

  [data-testid="stDataFrame"],
  [data-testid="stTable"] {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
  }}

  .sidebar-logo {{
    padding: 20px 16px 14px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
  }}

  .sidebar-logo h2 {{
    color: var(--text-main);
    font-family: var(--font-head);
    font-size: 18px;
    font-weight: 700;
    margin: 4px 0 2px;
  }}

  .sidebar-logo p {{
    color: var(--orange);
    font-size: 11px;
    letter-spacing: .5px;
    margin: 0;
  }}

  .sidebar-info {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow);
    color: var(--text-muted);
    font-size: 11px;
    line-height: 1.7;
    margin: 12px 10px;
    padding: 10px 14px;
  }}

  .sidebar-info strong {{
    color: var(--text-main);
    font-size: 12px;
  }}

  .weather-card {{
    text-align: center;
    padding: 16px 10px;
    background: var(--bg-card2);
    border-radius: 10px;
    border: 1px solid var(--border);
  }}

  .weather-icon {{ font-size: 40px; }}
  .weather-temp {{
    color: var(--text-main);
    font-family: var(--font-head);
    font-size: 30px;
    margin: 4px 0;
  }}
  .weather-sub {{ color: var(--text-muted); font-size: 11px; }}

  .kpi-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }}

  .kpi-mini {{
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    flex: 1;
    min-width: 84px;
    padding: 8px 12px;
  }}

  .kpi-mini .kl {{
    color: var(--text-muted);
    font-size: 10px;
    letter-spacing: .5px;
    text-transform: uppercase;
  }}

  .kpi-mini .kv {{
    font-family: var(--font-head);
    font-size: 20px;
    font-weight: 700;
  }}

  .kpi-mini .ku {{
    color: var(--text-muted);
    font-size: 10px;
  }}

  .energy-flow {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px 0;
  }}

  .flow-box {{
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px;
    flex: 1;
    min-width: 80px;
    padding: 10px 12px;
    text-align: center;
  }}

  .flow-box .fb-label {{
    color: var(--text-muted);
    font-size: 10px;
    letter-spacing: .5px;
    text-transform: uppercase;
  }}

  .flow-box .fb-value {{
    font-family: var(--font-head);
    font-size: 16px;
    font-weight: 700;
  }}

  .flow-arrow {{
    color: var(--green);
    flex-shrink: 0;
    font-size: 18px;
  }}

  .alarm-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }}

  .alarm-icon {{ flex-shrink: 0; font-size: 16px; margin-top: 2px; }}
  .alarm-title {{ color: var(--text-main); font-size: 12px; font-weight: 600; }}
  .alarm-sub {{ color: var(--text-muted); font-size: 10px; }}
  .alarm-meta {{ color: var(--text-muted); font-size: 10px; margin-left: auto; text-align: right; }}

  .fc-card {{
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    min-width: 70px;
    padding: 8px 10px;
    text-align: center;
  }}

  .fc-time {{ color: var(--text-muted); font-size: 11px; }}
  .fc-temp {{ color: var(--text-main); font-family: var(--font-head); font-size: 18px; }}
  .fc-rad {{ color: var(--orange); font-size: 10px; }}

  hr {{ border-color: var(--border) !important; }}
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg-main); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 10px; }}
</style>
""",
        unsafe_allow_html=True,
    )


inject_css()


# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------
WEATHER_ICONS = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    80: "🌦️",
    81: "🌧️",
    95: "⛈️",
}


def weather_icon(code: int | float | None) -> str:
    code_int = int(code) if code is not None else 0
    for key in sorted(WEATHER_ICONS, reverse=True):
        if code_int >= key:
            return WEATHER_ICONS[key]
    return "🌤️"


def weather_label(code: int | float | None) -> str:
    labels = {
        0: "Ensoleillé",
        1: "Principalement ensoleillé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brumeux",
        51: "Bruine légère",
        61: "Pluie légère",
        80: "Averses",
        95: "Orageux",
    }
    code_int = int(code) if code is not None else 0
    for key in sorted(labels, reverse=True):
        if code_int >= key:
            return labels[key]
    return "Ensoleillé"


def format_power(kW: float) -> str:
    return f"{kW / 1000:.2f} MW" if kW >= 1000 else f"{kW:.2f} kW"


def format_energy(kWh: float) -> str:
    if kWh >= 1e6:
        return f"{kWh / 1e6:.2f} GWh"
    if kWh >= 1000:
        return f"{kWh / 1000:.2f} MWh"
    return f"{kWh:.1f} kWh"


def format_co2(kg: float) -> str:
    return f"{kg / 1000:.2f} t CO₂" if kg >= 1000 else f"{kg:.1f} kg CO₂"


def format_currency(mad: float) -> str:
    return f"{mad:,.0f} MAD"


def get_performance_color(pr: float) -> str:
    if pr >= 0.80:
        return "#50c878"
    if pr >= 0.75:
        return "#f0a500"
    if pr >= 0.65:
        return "#e67e22"
    return "#e74c3c"


def get_temp_color(temp: float) -> str:
    if temp < 45:
        return "#50c878"
    if temp < 55:
        return "#f0a500"
    if temp < 70:
        return "#e67e22"
    return "#e74c3c"


def compute_savings(energy_kWh: float, config: dict[str, Any]) -> dict[str, float]:
    eco = config["economics"]
    co2 = energy_kWh * eco["co2_factor"]
    mad = energy_kWh * eco["tarif"]
    trees = co2 / eco["tree_co2"]
    return {"co2_kg": co2, "mad": mad, "trees": trees}


def diagnose(pr: float, temp_cell: float, thresholds: dict[str, Any]) -> list[tuple[str, str]]:
    alerts: list[tuple[str, str]] = []
    if pr < thresholds["pr_critical"]:
        alerts.append(("error", f"🔴 PR critique : {pr * 100:.1f}% < {thresholds['pr_critical'] * 100:.0f}%"))
    elif pr < thresholds["pr_warning"]:
        alerts.append(("warning", f"🟡 PR dégradé : {pr * 100:.1f}% < {thresholds['pr_warning'] * 100:.0f}%"))

    if temp_cell > thresholds["temp_cell_critical"]:
        alerts.append(("error", f"🔴 Température cellule critique : {temp_cell:.1f}°C"))
    elif temp_cell > thresholds["temp_cell_warning"]:
        alerts.append(("warning", f"🟡 Température cellule élevée : {temp_cell:.1f}°C"))
    return alerts


def apply_layout(fig: go.Figure, **kwargs: Any) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=THEME["text_main"], size=11, family="Inter"),
        margin=dict(l=40, r=20, t=30, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(color=THEME["text_main"])),
        **kwargs,
    )
    fig.update_xaxes(gridcolor=THEME["grid"], color=THEME["text_main"], zeroline=False)
    fig.update_yaxes(gridcolor=THEME["grid"], color=THEME["text_main"], zeroline=False)
    fig.update_annotations(font_color=THEME["text_main"])
    return fig


def card_open(title: str) -> None:
    st.markdown('<div class="pv-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="pv-card-title">{title}</div>', unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder_3d(height: int = 260) -> None:
    if os.path.exists("assets/Scene_enset.png"):
        st.image("assets/Scene_enset.png", use_container_width=True)
        return

    st.markdown(
        f"""
        <div style="height:{height}px;border:1px solid var(--border);border-radius:10px;
                    background:linear-gradient(135deg,var(--bg-card2),var(--bg-card));
                    display:flex;align-items:center;justify-content:center;overflow:hidden">
          <div style="text-align:center">
            <div style="font-size:68px">🔆</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:8px">
              Vue 3D - assets/Scene_enset.png
            </div>
            <div style="font-size:11px;color:var(--green);margin-top:4px">● 12 panneaux actifs</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def daily_energy(df: pd.DataFrame) -> float:
    return float(df["P_ac_kW"].mean() * 24)


# -----------------------------------------------------------------------------
# SESSION STATE + CACHE
# -----------------------------------------------------------------------------
if "config" not in st.session_state:
    st.session_state.config = load_config()
if "model" not in st.session_state:
    st.session_state.model = PVModel(st.session_state.config)
if "fetcher" not in st.session_state:
    st.session_state.fetcher = DataFetcher(st.session_state.config)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

cfg = st.session_state.config
model = st.session_state.model
fetcher = st.session_state.fetcher


@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_data() -> tuple[float, float, str]:
    return st.session_state.fetcher.get_live()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_weather_data() -> dict[str, Any]:
    return st.session_state.fetcher.get_weather_full()


def refresh_data() -> None:
    st.cache_data.clear()
    st.session_state.last_refresh = datetime.now()
    st.rerun()


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
          <div style="font-size:32px">☀️</div>
          <h2>PV Digital Twin</h2>
          <p>Smart Solar Monitoring</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🌙 Dark mode" if not st.session_state.dark_mode else "☀️ White mode",
        use_container_width=True,
        key="theme_toggle",
    ):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    site_name = cfg["site"].get("name", "Mohammedia")
    n_panels = cfg["array"]["n_panels"]
    n_series = cfg["array"]["n_series"]
    n_parallel = cfg["array"]["n_parallel"]
    p_kwp = cfg["panel"]["Pmp"] * n_panels / 1000
    p_rated = cfg["losses"]["p_rated"]

    st.markdown(
        f"""
        <div class="sidebar-info">
          <strong>📍 {site_name}, Maroc</strong><br>
          {p_kwp:.2f} kWp DC &nbsp;|&nbsp; {p_rated:.1f} kW AC<br>
          Mise en service : Janvier 2023<br>
          {n_panels} panneaux PV &nbsp;|&nbsp; {cfg['array']['n_mppt']} MPPT<br>
          {n_series}s × {n_parallel}p &nbsp;|&nbsp; Tilt {cfg['site']['tilt']}° Az {cfg['site']['azimuth']}°
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown("---")
    if st.button("🔄 Rafraîchir données", use_container_width=True):
        refresh_data()
    st.caption(f"Dernière MàJ : {st.session_state.last_refresh.strftime('%H:%M:%S')}")


# -----------------------------------------------------------------------------
# CURRENT DATA
# -----------------------------------------------------------------------------
G_live, T_live, source_live = fetch_live_data()
weather_data = fetch_weather_data()
result_live = model.compute(G_live, T_live)

P_ac = float(result_live["P_ac_kW"])
P_dc = float(result_live["P_dc_kW"])
T_cell = float(result_live["T_cell"])
PR = float(result_live["PR"])
eta = float(result_live["eta"])
eta_inv = float(result_live["eta_inv"])

df_day = model.compute_series(seed=int(datetime.now().strftime("%Y%m%d")))
energy_day_kWh = daily_energy(df_day)
energy_total_kWh = energy_day_kWh * 365 * 3
savings_total = compute_savings(energy_total_kWh, cfg)
alerts = diagnose(PR, T_cell, cfg["thresholds"])


# -----------------------------------------------------------------------------
# CHART HELPERS
# -----------------------------------------------------------------------------
def chart_production(df: pd.DataFrame, title: str = "", height: int = 220) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["hour"],
            y=df["P_ac_kW"],
            name="P_ac (kW)",
            fill="tozeroy",
            line=dict(color="#50c878", width=2),
            fillcolor="rgba(80,200,120,0.15)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["hour"],
            y=df["G"],
            name="G (W/m²)",
            line=dict(color="#f0a500", width=1.5, dash="dot"),
        ),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="P_ac (kW)", secondary_y=False)
    fig.update_yaxes(title_text="G (W/m²)", secondary_y=True)
    return apply_layout(fig, height=height, title_text=title)


def chart_iv(G: float, T: float, height: int = 230) -> tuple[go.Figure, dict[str, Any]]:
    iv = model.compute_iv_curve(G=G if G > 10 else 800, T_amb=T)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=iv["V"], y=iv["I"], name="I(V)", line=dict(color="#2d8cff", width=2)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=iv["V"],
            y=iv["P"] / 1000,
            name="P(V) kW",
            line=dict(color="#50c878", width=2, dash="dash"),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=[iv["V_mpp"]],
            y=[iv["I_mpp"]],
            name="MPP",
            mode="markers+text",
            marker=dict(color="#e74c3c", size=11, symbol="star"),
            text=[f"MPP {iv['P_mpp'] / 1000:.2f} kW"],
            textposition="top right",
        ),
        secondary_y=False,
    )
    fig.update_yaxes(title_text="Courant (A)", secondary_y=False)
    fig.update_yaxes(title_text="Puissance (kW)", secondary_y=True)
    return apply_layout(fig, height=height), iv


def build_forecasts() -> list[dict[str, Any]]:
    now_h = datetime.now().hour
    forecasts = [
        {"time": f"{(now_h + 3) % 24:02d}:00", "icon": "🌤️", "temp": weather_data["T"] + 1, "G": 900},
        {"time": f"{(now_h + 6) % 24:02d}:00", "icon": "☀️", "temp": weather_data["T"] + 3, "G": 950},
        {"time": f"{(now_h + 9) % 24:02d}:00", "icon": "⛅", "temp": weather_data["T"] + 1, "G": 800},
    ]

    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", []) if hourly else []
    temps = hourly.get("temperature_2m", []) if hourly else []
    rads = hourly.get("shortwave_radiation", []) if hourly else []
    candidates = []
    wanted = {(now_h + 3) % 24, (now_h + 6) % 24, (now_h + 9) % 24}
    for idx, raw_time in enumerate(times[:36]):
        hour = int(raw_time[11:13]) if isinstance(raw_time, str) and len(raw_time) > 12 else None
        if hour in wanted:
            candidates.append(
                {
                    "time": f"{hour:02d}:00",
                    "icon": weather_icon(weather_data.get("code", 0)),
                    "temp": temps[idx] if idx < len(temps) else weather_data["T"],
                    "G": rads[idx] if idx < len(rads) else weather_data["G"],
                }
            )
    return candidates[:3] if candidates else forecasts


# -----------------------------------------------------------------------------
# PAGE: OVERVIEW
# -----------------------------------------------------------------------------
if page == "🏠 Vue d'ensemble":
    hc1, hc2, hc3 = st.columns([2, 5, 3])

    with hc1:
        w_icon = weather_icon(weather_data.get("code", 0))
        w_label = weather_label(weather_data.get("code", 0))
        w_temp = weather_data.get("T", T_live)
        w_rad = weather_data.get("G", G_live)
        st.markdown(
            f"""
            <div class="weather-card">
              <div class="weather-icon">{w_icon}</div>
              <div class="weather-temp">{w_temp:.1f}°C</div>
              <div style="font-size:12px;color:var(--text-main);margin-bottom:2px">{w_label}</div>
              <div class="weather-sub">Irradiance <strong style="color:var(--orange)">{w_rad:.0f} W/m²</strong></div>
              <div class="weather-sub" style="margin-top:4px;font-size:10px;color:var(--green)">● {source_live}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hc2:
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Puissance AC", format_power(P_ac), f"{P_ac / cfg['losses']['p_rated'] * 100:.0f}% capacité")
        kc2.metric("Production jour", format_energy(energy_day_kWh), "↑ aujourd'hui")
        kc3.metric("Production totale", format_energy(energy_total_kWh), "3 ans estimé")
        kc4.metric("CO₂ évité", format_co2(savings_total["co2_kg"]), f"🌳 {savings_total['trees']:.0f} arbres")

    with hc3:
        st.date_input("Date", datetime.now().date(), label_visibility="collapsed")
        st.selectbox("Période", ["Aujourd'hui", "Semaine", "Mois", "Année"], label_visibility="collapsed")
        st.caption(f"⏱️ {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([6, 4])

    with col_left:
        card_open("☀ Jumeau numérique - Vue 3D")
        scene_col, controls_col = st.columns([3, 1])
        with scene_col:
            render_placeholder_3d(260)
        with controls_col:
            st.radio(
                "Vue",
                ["Vue libre", "Irradiance", "Température", "Production", "Pertes"],
                label_visibility="collapsed",
                key="scene_view",
            )
            st.markdown(
                """
                <div style="font-size:10px;line-height:2;margin-top:8px">
                  <span style="color:#50c878">⬤</span> Normal<br>
                  <span style="color:#f0a500">⬤</span> Attention<br>
                  <span style="color:#e74c3c">⬤</span> Alarme<br>
                  <span style="color:#2d8cff">⬤</span> Maintenance
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="kpi-bar">
              <div class="kpi-mini">
                <div class="kl">T° Cellule</div>
                <div class="kv" style="color:{get_temp_color(T_cell)}">{T_cell:.1f}°</div>
                <div class="ku">°C</div>
              </div>
              <div class="kpi-mini">
                <div class="kl">Rendement</div>
                <div class="kv" style="color:#2d8cff">{eta * 100:.1f}%</div>
                <div class="ku">η panneau</div>
              </div>
              <div class="kpi-mini">
                <div class="kl">Perf. Ratio</div>
                <div class="kv" style="color:{get_performance_color(PR)}">{PR * 100:.1f}%</div>
                <div class="ku">PR actuel</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_close()

        card_open("📊 Production & Performance")
        t1, t2, t3, t4 = st.tabs(["Jour", "Semaine", "Mois", "Année"])
        with t1:
            c1, c2, c3 = st.columns(3)
            rs = energy_day_kWh / (cfg["panel"]["Pmp"] * cfg["array"]["n_panels"] / 1000)
            c1.metric("Production", format_energy(energy_day_kWh))
            c2.metric("Rend. spécifique", f"{rs:.2f} kWh/kWp")
            c3.metric("PR moyen", f"{df_day['PR'].mean() * 100:.1f}%")
            st.plotly_chart(chart_production(df_day), use_container_width=True, config={"displayModeBar": False})

        with t2:
            days = [(datetime.now() - timedelta(days=6 - i)).strftime("%d/%m") for i in range(7)]
            e_week = [daily_energy(model.compute_series(seed=i * 77)) for i in range(7)]
            fig_w = go.Figure(go.Bar(x=days, y=e_week, marker_color="#50c878", opacity=0.85))
            st.plotly_chart(apply_layout(fig_w, height=220), use_container_width=True, config={"displayModeBar": False})

        with t3:
            e_month = [daily_energy(model.compute_series(seed=i * 100)) for i in range(1, 31)]
            fig_m = go.Figure(go.Bar(x=list(range(1, 31)), y=e_month, marker_color="#2d8cff", opacity=0.75))
            st.plotly_chart(apply_layout(fig_m, height=220), use_container_width=True, config={"displayModeBar": False})

        with t4:
            months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
            e_year = [daily_energy(model.compute_series(seed=i * 1000)) * 30 for i in range(12)]
            fig_y = go.Figure(go.Bar(x=months, y=e_year, marker_color="#f0a500", opacity=0.85))
            st.plotly_chart(apply_layout(fig_y, height=220), use_container_width=True, config={"displayModeBar": False})
        card_close()

        card_open("⚡ Courbe I-V instantanée")
        fig_iv, iv = chart_iv(G_live, T_live)
        st.plotly_chart(fig_iv, use_container_width=True, config={"displayModeBar": False})
        c1, c2, c3 = st.columns(3)
        c1.metric("P_mpp", f"{iv['P_mpp'] / 1000:.2f} kW")
        c2.metric("V_mpp", f"{iv['V_mpp']:.1f} V")
        c3.metric("I_mpp", f"{iv['I_mpp']:.2f} A")
        card_close()

        card_open("📉 Comparaison Performance 7 jours")
        tabs7 = st.tabs(["PR", "Production spécifique", "Irradiance"])
        days7 = [(datetime.now() - timedelta(days=6 - i)).strftime("%d/%m") for i in range(7)]
        pr7 = [model.compute_series(seed=i * 77)["PR"].mean() for i in range(7)]
        with tabs7[0]:
            fig7 = go.Figure()
            fig7.add_trace(go.Scatter(x=days7, y=[p * 100 for p in pr7], name="PR Réel", line=dict(color="#50c878", width=2)))
            fig7.add_trace(go.Scatter(x=days7, y=[p * 105 for p in pr7], name="PR Attendu", line=dict(color="#f0a500", width=2, dash="dash")))
            st.plotly_chart(apply_layout(fig7, height=190), use_container_width=True, config={"displayModeBar": False})
        with tabs7[1]:
            pspec = [daily_energy(model.compute_series(seed=i * 77)) / p_kwp for i in range(7)]
            fig7b = go.Figure(go.Scatter(x=days7, y=pspec, name="kWh/kWp", line=dict(color="#2d8cff", width=2)))
            st.plotly_chart(apply_layout(fig7b, height=190), use_container_width=True, config={"displayModeBar": False})
        with tabs7[2]:
            g7 = [model.compute_series(seed=i * 77)["G"].max() for i in range(7)]
            fig7c = go.Figure(go.Bar(x=days7, y=g7, marker_color="#f0a500", opacity=0.85))
            st.plotly_chart(apply_layout(fig7c, height=190), use_container_width=True, config={"displayModeBar": False})
        card_close()

    with col_right:
        card_open("⚡ Flux d'énergie")
        dc_loss_kW = P_dc * cfg["losses"]["dc_total"]
        inv_loss_kW = max(0, P_dc - P_ac)
        load_pct = P_ac / cfg["losses"]["p_rated"] * 100 if cfg["losses"]["p_rated"] > 0 else 0
        arrow_color = "#50c878" if load_pct > 80 else "#f0a500" if load_pct > 50 else "#e74c3c"
        st.markdown(
            f"""
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
                <div class="fb-value" style="color:#2d8cff">{P_dc:.2f}<br><span style="font-size:11px">kW</span></div>
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
                <div class="fb-value" style="color:var(--text-main)">{P_ac:.2f}<br><span style="font-size:11px">kW</span></div>
              </div>
            </div>
            <div style="font-size:11px;color:#e74c3c;margin-top:4px">
              ⬇️ Pertes DC : {dc_loss_kW:.3f} kW &nbsp;|&nbsp; ⬇️ Pertes onduleur : {inv_loss_kW:.3f} kW
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_close()

        card_open("📉 Répartition des pertes")
        if G_live > 0:
            p_irr = max(0, (1 - eta / cfg["panel"]["eta_stc"]) * P_dc * 0.6) * 100 / max(P_dc, 0.001)
            p_temp = abs(cfg["panel"]["gamma"] * (T_cell - 25)) * 100
            p_dc = cfg["losses"]["dc_total"] * 100
            p_inv = (1 - eta_inv) * 100 if eta_inv > 0 else 5
            p_cable = 0.5
            p_other = max(0, 100 - p_irr - p_temp - p_dc - p_inv - p_cable)
            loss_vals = [p_irr, p_temp, p_dc, p_inv, p_cable, p_other]
        else:
            loss_vals = [6.2, 4.1, 10.0, 4.0, 0.5, 2.0]
        loss_labels = ["Irradiance", "Température", "DC", "Onduleur", "Câbles", "Autres"]
        loss_colors = ["#2d8cff", "#50c878", "#e74c3c", "#f0a500", "#f39c12", "#7f8c8d"]
        fig_loss = go.Figure(
            go.Pie(labels=loss_labels, values=loss_vals, marker_colors=loss_colors, hole=0.52, textinfo="none")
        )
        fig_loss.add_annotation(
            text=f"<b>{sum(loss_vals):.1f}%</b>",
            x=0.5,
            y=0.5,
            font=dict(size=14, color="#e74c3c"),
            showarrow=False,
        )
        st.plotly_chart(
            apply_layout(fig_loss, height=180, showlegend=True, margin=dict(l=0, r=0, t=10, b=10)),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        card_close()

        card_open("🩺 Diagnostic automatique")
        if not alerts:
            st.success("✅ Système nominal - tous les paramètres dans les limites")
        else:
            for level, msg in alerts:
                st.error(msg) if level == "error" else st.warning(msg)
        day_savings = compute_savings(energy_day_kWh, cfg)
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Économies", format_currency(day_savings["mad"]))
        sc2.metric("CO₂ évité", format_co2(day_savings["co2_kg"]))
        sc3.metric("🌳 Arbres", f"{day_savings['trees']:.2f}")
        card_close()

        card_open("🔔 Alarmes récentes")
        alarm_list = [
            {
                "icon": "🔴",
                "title": "Défaut communication INV-01",
                "sub": "Onduleur #01",
                "time": "10:15",
                "status": "Non acquittée",
                "color": "#e74c3c",
            }
        ]
        for level, message in alerts:
            alarm_list.append(
                {
                    "icon": "🟡" if level == "warning" else "🔴",
                    "title": message,
                    "sub": "Auto-détecté",
                    "time": datetime.now().strftime("%H:%M"),
                    "status": "Auto",
                    "color": "#f0a500" if level == "warning" else "#e74c3c",
                }
            )
        for alarm in alarm_list[:3]:
            alarm_color = alarm["color"]
            st.markdown(
                f"""
                <div class="alarm-row">
                  <div class="alarm-icon">{alarm['icon']}</div>
                  <div>
                    <div class="alarm-title">{alarm['title']}</div>
                    <div class="alarm-sub">{alarm['sub']}</div>
                  </div>
                  <div class="alarm-meta">
                    {alarm['time']}
                    <span style="display:block;color:{alarm_color};font-weight:600">{alarm['status']}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        card_close()

        card_open("🌤️ Météo & Prévisions")
        forecasts = build_forecasts()
        fc_cols = st.columns(len(forecasts))
        for index, forecast in enumerate(forecasts):
            with fc_cols[index]:
                st.markdown(
                    f"""
                    <div class="fc-card">
                      <div class="fc-time">{forecast['time']}</div>
                      <div style="font-size:22px">{forecast['icon']}</div>
                      <div class="fc-temp">{forecast['temp']:.0f}°C</div>
                      <div class="fc-rad">{forecast['G']:.0f} W/m²</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        card_close()


# -----------------------------------------------------------------------------
# PAGE: DIGITAL TWIN
# -----------------------------------------------------------------------------
elif page == "🧊 Jumeau numérique":
    st.markdown("## 🧊 Jumeau Numérique")
    c1, c2 = st.columns([3, 2])
    with c1:
        card_open("Vue 3D interactive")
        render_placeholder_3d(420)
        card_close()
    with c2:
        card_open("Paramètres temps réel")
        metrics = [
            ("☀️ Irradiance", f"{G_live:.0f} W/m²"),
            ("🌡️ T° ambiante", f"{T_live:.1f}°C"),
            ("🔥 T° cellule", f"{T_cell:.1f}°C"),
            ("⚡ P_dc", f"{P_dc:.3f} kW"),
            ("🔌 P_ac", f"{P_ac:.3f} kW"),
            ("📊 PR", f"{PR * 100:.1f}%"),
            ("η panneau", f"{eta * 100:.2f}%"),
            ("η onduleur", f"{eta_inv * 100:.1f}%"),
        ]
        for label, value in metrics:
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;padding:7px 0;
                            border-bottom:1px solid var(--border);font-size:13px">
                  <span style="color:var(--text-muted)">{label}</span>
                  <strong style="color:var(--text-main)">{value}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
        card_close()

        card_open("📍 Localisation")
        loc_df = pd.DataFrame({"lat": [cfg["site"]["lat"]], "lon": [cfg["site"]["lon"]]})
        st.map(loc_df, zoom=10)
        card_close()


# -----------------------------------------------------------------------------
# PAGE: PERFORMANCE
# -----------------------------------------------------------------------------
elif page == "📈 Performance":
    st.markdown("## 📈 Performance")
    tab_d, tab_w, tab_m, tab_y = st.tabs(["Jour", "Semaine", "Mois", "Année"])

    def render_perf_tab(df: pd.DataFrame, label: str, multiplier: float) -> None:
        c1, c2, c3, c4 = st.columns(4)
        energy = float(df["P_ac_kW"].mean() * multiplier)
        c1.metric("Énergie", format_energy(energy))
        c2.metric("PR moyen", f"{df['PR'].mean() * 100:.1f}%")
        c3.metric("η moyen", f"{df['eta'].mean() * 100:.2f}%")
        c4.metric("Heures soleil", f"{(df['G'] > 50).sum() * 0.25:.1f}h")
        st.plotly_chart(
            chart_production(df, f"Production & Irradiance - {label}", 290),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        fig_pr = go.Figure(
            go.Bar(
                x=df["hour"],
                y=df["PR"] * 100,
                marker_color=[get_performance_color(p) for p in df["PR"]],
            )
        )
        st.plotly_chart(
            apply_layout(fig_pr, height=210, title_text="Performance Ratio (PR)"),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.dataframe(
            df[["hour", "G", "T_amb", "T_cell", "P_dc_kW", "P_ac_kW", "PR", "eta_inv"]].round(3),
            use_container_width=True,
            height=220,
        )

    with tab_d:
        render_perf_tab(df_day, "Jour", 24)
    with tab_w:
        df_week = pd.concat([model.compute_series(seed=i * 77) for i in range(7)], ignore_index=True)
        render_perf_tab(df_week, "Semaine", 24 * 7)
    with tab_m:
        df_month = model.compute_series(hours=np.arange(0, 24 * 30, 0.5), seed=999)
        render_perf_tab(df_month, "Mois", 24 * 30)
    with tab_y:
        df_year = pd.concat([model.compute_series(seed=i * 1000) for i in range(12)], ignore_index=True)
        render_perf_tab(df_year, "Année", 24 * 365)


# -----------------------------------------------------------------------------
# PAGE: EQUIPMENT
# -----------------------------------------------------------------------------
elif page == "⚙️ Équipements":
    st.markdown("## ⚙️ État des Équipements")
    equip_data = [
        {"id": "INV-01", "type": "Onduleur", "état": "🔴 Alarme", "P": "0.0 kW", "T": "—", "note": "Défaut comm."},
        {"id": "INV-02", "type": "Onduleur", "état": "🟢 Normal", "P": f"{P_ac:.2f} kW", "T": f"{T_cell:.1f}°C", "note": "OK"},
        {"id": "PNL-01", "type": "Panneau", "état": "🟢 Normal", "P": f"{P_dc / 12:.3f} kW", "T": f"{T_cell:.1f}°C", "note": "OK"},
        {"id": "PNL-02", "type": "Panneau", "état": "🟡 Attention", "P": f"{P_dc / 12 * .9:.3f} kW", "T": f"{T_cell + 5:.1f}°C", "note": "T° élevée"},
        {"id": "MPPT-01", "type": "MPPT", "état": "🟢 Normal", "P": f"{P_dc:.2f} kW", "T": "—", "note": "OK"},
        {"id": "MET-01", "type": "Station", "état": "🔵 Maintenance", "P": "—", "T": f"{T_live:.1f}°C", "note": "Calibration"},
    ]
    st.dataframe(pd.DataFrame(equip_data), use_container_width=True, height=300)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        card_open("Distribution des états")
        eq_counts = {"Normal": 5, "Attention": 1, "Alarme": 1, "Maintenance": 1}
        fig_e = go.Figure(
            go.Pie(
                labels=list(eq_counts.keys()),
                values=list(eq_counts.values()),
                marker_colors=["#50c878", "#f0a500", "#e74c3c", "#2d8cff"],
                hole=0.5,
            )
        )
        st.plotly_chart(apply_layout(fig_e, height=240, showlegend=True), use_container_width=True, config={"displayModeBar": False})
        card_close()
    with col_e2:
        card_open("Production par panneau")
        panels = [f"PNL-{i + 1:02d}" for i in range(cfg["array"]["n_panels"])]
        rng = np.random.default_rng(7)
        prods = [P_dc / cfg["array"]["n_panels"] * (1 + rng.normal(0, 0.05)) for _ in panels]
        colors = ["#50c878" if p > P_dc / cfg["array"]["n_panels"] * 0.9 else "#f0a500" for p in prods]
        fig_pan = go.Figure(go.Bar(x=panels, y=prods, marker_color=colors))
        st.plotly_chart(apply_layout(fig_pan, height=240), use_container_width=True, config={"displayModeBar": False})
        card_close()


# -----------------------------------------------------------------------------
# PAGE: ALARMS
# -----------------------------------------------------------------------------
elif page == "🔔 Alarmes":
    st.markdown("## 🔔 Gestion des Alarmes")
    alarm_full = [
        {"Priorité": "🔴 CRITIQUE", "Description": "Défaut communication INV-01", "Équipement": "Onduleur #01", "Heure": "10:15", "État": "Non acquittée"},
        {"Priorité": "🟡 ATTENTION", "Description": "Température cellule élevée", "Équipement": "PNL-02", "Heure": datetime.now().strftime("%H:%M"), "État": "Auto"},
        {"Priorité": "🟡 ATTENTION", "Description": "PR dégradé < seuil", "Équipement": "Système", "Heure": datetime.now().strftime("%H:%M"), "État": "Auto"},
        {"Priorité": "ℹ️ INFO", "Description": "Irradiance capteur météo anormale", "Équipement": "MET-01", "Heure": "09:20", "État": "Acquittée"},
    ]
    for level, message in alerts:
        alarm_full.append(
            {
                "Priorité": "🔴 CRITIQUE" if level == "error" else "🟡 ATTENTION",
                "Description": message,
                "Équipement": "Système",
                "Heure": datetime.now().strftime("%H:%M"),
                "État": "Auto",
            }
        )
    st.dataframe(pd.DataFrame(alarm_full), use_container_width=True)
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Total", len(alarm_full))
    a2.metric("Critiques", sum(1 for a in alarm_full if "CRITIQUE" in a["Priorité"]))
    a3.metric("Attention", sum(1 for a in alarm_full if "ATTENTION" in a["Priorité"]))
    a4.metric("Non acquittées", sum(1 for a in alarm_full if "Non" in a["État"]))


# -----------------------------------------------------------------------------
# PAGE: ANALYSIS
# -----------------------------------------------------------------------------
elif page == "🔍 Analyses":
    st.markdown("## 🔍 Analyses Avancées")
    st.markdown("### 📐 Courbe I-V interactive")
    a1, a2 = st.columns(2)
    with a1:
        g_slider = st.slider("Irradiance (W/m²)", 100, 1000, int(G_live or 800), 50)
    with a2:
        t_slider = st.slider("T° ambiante (°C)", 0, 45, int(T_live or 25), 1)
    fig_iv2, iv2 = chart_iv(g_slider, t_slider, 330)
    fig_iv2.update_layout(title_text=f"G={g_slider} W/m² | T={t_slider}°C | MPP={iv2['P_mpp'] / 1000:.2f} kW")
    st.plotly_chart(fig_iv2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    st.markdown("### 📊 Analyse de sensibilité")
    sa1, sa2 = st.columns(2)
    with sa1:
        dc_losses = st.slider("Pertes DC (%)", 0, 30, int(cfg["losses"]["dc_total"] * 100), 1)
    with sa2:
        ac_eff = st.slider("Rendement AC (%)", 85, 100, int(cfg["losses"]["ac_efficiency"] * 100), 1)
    cfg_tmp = deep_merge(cfg, {"losses": {"dc_total": dc_losses / 100, "ac_efficiency": ac_eff / 100}})
    model_tmp = PVModel(cfg_tmp)
    r_sens = model_tmp.compute(G_live or 800, T_live or 25)
    r_nom = model.compute(G_live or 800, T_live or 25)
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("P_ac", f"{r_sens['P_ac_kW']:.3f} kW", f"{r_sens['P_ac_kW'] - r_nom['P_ac_kW']:+.3f} kW")
    sc2.metric("PR", f"{r_sens['PR'] * 100:.1f}%", f"{(r_sens['PR'] - r_nom['PR']) * 100:+.1f}%")
    sc3.metric("Pertes DC", f"{dc_losses}%")
    sc4.metric("η AC", f"{ac_eff}%")

    st.markdown("---")
    st.markdown("### 🔧 Recalage adaptatif")
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        p_measured = st.number_input("P_ac mesurée (kW)", 0.0, 5.0, float(P_ac), 0.01)
    with rc2:
        st.markdown("<br>", unsafe_allow_html=True)
        do_recal = st.button("⚙️ Recalibrer")
    if do_recal and G_live > 0:
        old_losses = model.dc_losses if hasattr(model, "dc_losses") else cfg["losses"]["dc_total"]
        new_losses = model.recalibrate(p_measured, G_live, T_live)
        st.success(f"Recalibration : pertes DC {old_losses * 100:.2f}% → {new_losses * 100:.2f}%")
    elif do_recal:
        st.warning("Irradiance nulle, recalibration impossible.")


# -----------------------------------------------------------------------------
# PAGE: REPORTS
# -----------------------------------------------------------------------------
elif page == "📄 Rapports":
    st.markdown("## 📄 Rapports")
    report_type = st.selectbox("Type de rapport", ["Rapport journalier", "Hebdomadaire", "Mensuel"])
    with st.expander(f"📋 {report_type} - {datetime.now().strftime('%d/%m/%Y')}", expanded=True):
        e_report = energy_day_kWh if "journalier" in report_type.lower() else energy_day_kWh * 7 if "hebdo" in report_type.lower() else energy_day_kWh * 30
        report_savings = compute_savings(e_report, cfg)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Énergie produite", format_energy(e_report))
        r2.metric("PR moyen", f"{df_day['PR'].mean() * 100:.1f}%")
        r3.metric("Économies", format_currency(report_savings["mad"]))
        r4.metric("CO₂ évité", format_co2(report_savings["co2_kg"]))

        summary_df = pd.DataFrame(
            {
                "Indicateur": ["Énergie (kWh)", "PR moyen (%)", "η moyen (%)", "Heures soleil"],
                "Valeur": [
                    f"{e_report:.1f}",
                    f"{df_day['PR'].mean() * 100:.1f}",
                    f"{df_day['eta'].mean() * 100:.2f}",
                    f"{(df_day['G'] > 50).sum() * 0.25:.1f}",
                ],
            }
        )
        st.table(summary_df)

        periods = ["J-6", "J-5", "J-4", "J-3", "J-2", "J-1", "Auj"]
        prod_vals = [daily_energy(model.compute_series(seed=i * 77)) for i in range(7)]
        fc_vals = [p * 1.08 for p in prod_vals]
        fig_report = go.Figure()
        fig_report.add_trace(go.Bar(name="Production réelle", x=periods, y=prod_vals, marker_color="#50c878", opacity=0.85))
        fig_report.add_trace(go.Bar(name="Prévision", x=periods, y=fc_vals, marker_color="#2d8cff", opacity=0.55))
        fig_report.update_layout(barmode="group")
        st.plotly_chart(
            apply_layout(fig_report, height=260, title_text="Production vs Prévision (kWh)"),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    csv_df = df_day.copy()
    csv_df["date"] = datetime.now().strftime("%Y-%m-%d")
    st.download_button(
        "📥 Télécharger CSV",
        data=csv_df.to_csv(index=False).encode("utf-8"),
        file_name=f"rapport_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# -----------------------------------------------------------------------------
# PAGE: WEATHER
# -----------------------------------------------------------------------------
elif page == "🌤️ Météo":
    st.markdown("## 🌤️ Météo & Prévisions")
    wc1, wc2, wc3 = st.columns([2, 3, 2])
    with wc1:
        card_open("Conditions actuelles")
        st.markdown(
            f"""
            <div style="text-align:center">
              <div style="font-size:60px">{weather_icon(weather_data.get('code', 0))}</div>
              <div style="font-family:'Rajdhani';font-size:36px;font-weight:700;color:var(--text-main)">
                {weather_data.get('T', T_live):.1f}°C
              </div>
              <div style="color:var(--text-muted);font-size:13px">{weather_label(weather_data.get('code', 0))}</div>
              <hr style="border-color:var(--border);margin:10px 0">
              <div style="font-size:12px;color:#f0a500">☀️ {weather_data.get('G', G_live):.0f} W/m²</div>
              <div style="font-size:12px;color:#2d8cff">💨 {weather_data.get('wind', 0):.1f} km/h</div>
              <div style="font-size:10px;color:#50c878;margin-top:6px">Source: {weather_data.get('source', source_live)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_close()

    with wc2:
        hourly = weather_data.get("hourly", {})
        if hourly and "shortwave_radiation" in hourly:
            times_h = hourly.get("time", [])[:24]
            rads = hourly.get("shortwave_radiation", [])[:24]
            temps = hourly.get("temperature_2m", [])[:24]
            labels_h = [value[11:16] if isinstance(value, str) and len(value) > 12 else str(value) for value in times_h]
        else:
            labels_h = [f"{h:02d}:00" for h in range(24)]
            rads = [max(0, 900 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0 for h in range(24)]
            temps = [25 + 5 * np.sin(np.pi * (h - 10) / 14) for h in range(24)]
        fig_weather = make_subplots(specs=[[{"secondary_y": True}]])
        fig_weather.add_trace(
            go.Scatter(
                x=labels_h,
                y=rads,
                name="Irradiance",
                fill="tozeroy",
                line=dict(color="#f0a500", width=2),
                fillcolor="rgba(240,165,0,0.12)",
            ),
            secondary_y=False,
        )
        fig_weather.add_trace(
            go.Scatter(x=labels_h, y=temps, name="Température", line=dict(color="#e74c3c", width=2)),
            secondary_y=True,
        )
        fig_weather.update_yaxes(title_text="Irradiance W/m²", secondary_y=False)
        fig_weather.update_yaxes(title_text="T° (°C)", secondary_y=True)
        st.plotly_chart(
            apply_layout(fig_weather, height=300, title_text="Prévisions horaires 24h"),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with wc3:
        card_open("📍 Localisation")
        loc_df = pd.DataFrame({"lat": [cfg["site"]["lat"]], "lon": [cfg["site"]["lon"]]})
        st.map(loc_df, zoom=9)
        st.markdown(
            f"""
            <div style="font-size:11px;color:var(--text-muted);margin-top:6px">
              {site_name}, Maroc<br>
              Lat {cfg['site']['lat']} | Lon {cfg['site']['lon']}<br>
              Alt {cfg['site']['alt']}m | Tilt {cfg['site']['tilt']}° | Az {cfg['site']['azimuth']}°
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_close()

    st.markdown("### Prévisions 7 jours")
    days_fc = [(datetime.now() + timedelta(days=i)).strftime("%a %d/%m") for i in range(7)]
    rng = np.random.default_rng(21)
    max_temps = [weather_data.get("T", T_live) + rng.normal(0, 3) for _ in range(7)]
    min_temps = [temp - rng.uniform(5, 10) for temp in max_temps]
    g_fc = [rng.uniform(600, 950) for _ in range(7)]
    df_fc = pd.DataFrame(
        {
            "Jour": days_fc,
            "Icône": ["☀️", "🌤️", "⛅", "☀️", "🌦️", "☀️", "🌤️"],
            "T max (°C)": [f"{t:.1f}" for t in max_temps],
            "T min (°C)": [f"{t:.1f}" for t in min_temps],
            "Irradiance (W/m²)": [f"{g:.0f}" for g in g_fc],
        }
    )
    st.dataframe(df_fc, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# PAGE: SETTINGS
# -----------------------------------------------------------------------------
elif page == "⚙️ Paramètres":
    st.markdown("## ⚙️ Paramètres du système")
    with st.form("config_form"):
        tabs_cfg = st.tabs(["📍 Site", "🔆 Panneau", "🔌 Array", "📉 Pertes", "📡 Blynk", "🚨 Seuils"])

        with tabs_cfg[0]:
            c1, c2 = st.columns(2)
            with c1:
                lat = st.number_input("Latitude", value=float(cfg["site"]["lat"]))
                lon = st.number_input("Longitude", value=float(cfg["site"]["lon"]))
                alt = st.number_input("Altitude (m)", value=int(cfg["site"]["alt"]))
            with c2:
                tilt = st.number_input("Tilt (°)", value=int(cfg["site"]["tilt"]))
                azimuth = st.number_input("Azimuth (°)", value=int(cfg["site"]["azimuth"]))
                timezone = st.text_input("Timezone", value=cfg["site"]["tz"])

        with tabs_cfg[1]:
            c1, c2, c3 = st.columns(3)
            with c1:
                Pmp = st.number_input("Pmp (W)", value=float(cfg["panel"]["Pmp"]))
                eta_stc = st.number_input("η STC", value=float(cfg["panel"]["eta_stc"]), format="%.3f")
                area = st.number_input("Aire (m²)", value=float(cfg["panel"]["area"]), format="%.3f")
            with c2:
                Voc = st.number_input("Voc (V)", value=float(cfg["panel"]["Voc"]))
                Isc = st.number_input("Isc (A)", value=float(cfg["panel"]["Isc"]))
                Vmp = st.number_input("Vmp (V)", value=float(cfg["panel"]["Vmp"]))
            with c3:
                Imp = st.number_input("Imp (A)", value=float(cfg["panel"]["Imp"]))
                gamma = st.number_input("γ_pmp (/°C)", value=float(cfg["panel"]["gamma"]), format="%.4f")
                NOCT = st.number_input("NOCT (°C)", value=float(cfg["panel"]["NOCT"]))

        with tabs_cfg[2]:
            n_panels_cfg = st.number_input("Nombre panneaux", value=int(cfg["array"]["n_panels"]))
            n_series_cfg = st.number_input("Panneaux en série", value=int(cfg["array"]["n_series"]))
            n_parallel_cfg = st.number_input("Strings parallèle", value=int(cfg["array"]["n_parallel"]))
            n_mppt_cfg = st.number_input("MPPT", value=int(cfg["array"]["n_mppt"]))

        with tabs_cfg[3]:
            dc_total = st.slider("Pertes DC totales (%)", 0, 30, int(cfg["losses"]["dc_total"] * 100))
            ac_efficiency = st.slider("Rendement AC (%)", 85, 100, int(cfg["losses"]["ac_efficiency"] * 100))
            inverter_threshold = st.number_input("Seuil onduleur (kW)", value=float(cfg["losses"]["inverter_threshold"]))
            p_rated_cfg = st.number_input("P_rated (kW)", value=float(cfg["losses"]["p_rated"]))

        with tabs_cfg[4]:
            token = st.text_input("Blynk Token", value=cfg["blynk"].get("token", ""), type="password")
            server = st.text_input("Serveur Blynk", value=cfg["blynk"].get("server", "blynk.cloud"))
            pin_temp = st.text_input("Pin Température", value=cfg["blynk"].get("pin_temp", "V0"))
            pin_irr = st.text_input("Pin Irradiance", value=cfg["blynk"].get("pin_irr", "V1"))

        with tabs_cfg[5]:
            pr_warning = st.slider("PR warning", 0.5, 0.95, float(cfg["thresholds"]["pr_warning"]))
            pr_critical = st.slider("PR critique", 0.4, 0.85, float(cfg["thresholds"]["pr_critical"]))
            tc_warning = st.slider("T° cellule warning (°C)", 40, 80, int(cfg["thresholds"]["temp_cell_warning"]))
            tc_critical = st.slider("T° cellule critique (°C)", 50, 90, int(cfg["thresholds"]["temp_cell_critical"]))

        sb1, sb2 = st.columns(2)
        save = sb1.form_submit_button("💾 Sauvegarder", use_container_width=True)
        reset = sb2.form_submit_button("🔄 Réinitialiser", use_container_width=True)

        if save:
            new_cfg = {
                "site": {
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "tilt": tilt,
                    "azimuth": azimuth,
                    "tz": timezone,
                    "name": cfg["site"].get("name", "Mohammedia"),
                },
                "panel": {
                    "Pmp": Pmp,
                    "eta_stc": eta_stc,
                    "area": area,
                    "Voc": Voc,
                    "Isc": Isc,
                    "Vmp": Vmp,
                    "Imp": Imp,
                    "gamma": gamma,
                    "NOCT": NOCT,
                },
                "array": {
                    "n_panels": int(n_panels_cfg),
                    "n_series": int(n_series_cfg),
                    "n_parallel": int(n_parallel_cfg),
                    "n_mppt": int(n_mppt_cfg),
                },
                "losses": {
                    "dc_total": dc_total / 100,
                    "ac_efficiency": ac_efficiency / 100,
                    "inverter_threshold": inverter_threshold,
                    "p_rated": p_rated_cfg,
                },
                "blynk": {"token": token, "server": server, "pin_temp": pin_temp, "pin_irr": pin_irr},
                "thresholds": {
                    "pr_warning": pr_warning,
                    "pr_critical": pr_critical,
                    "temp_cell_warning": tc_warning,
                    "temp_cell_critical": tc_critical,
                },
                "economics": cfg.get("economics", DEFAULT_CONFIG["economics"]),
            }
            try:
                save_config(new_cfg)
                st.session_state.config = new_cfg
                st.session_state.model = PVModel(new_cfg)
                st.session_state.fetcher = DataFetcher(new_cfg)
                st.cache_data.clear()
                st.success("✅ Configuration sauvegardée avec succès.")
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur de sauvegarde : {exc}")

        if reset:
            st.session_state.config = deepcopy(DEFAULT_CONFIG)
            st.session_state.model = PVModel(st.session_state.config)
            st.session_state.fetcher = DataFetcher(st.session_state.config)
            st.cache_data.clear()
            st.success("🔄 Configuration réinitialisée.")
            st.rerun()


# -----------------------------------------------------------------------------
# AUTO-REFRESH OPTIONAL
# -----------------------------------------------------------------------------
try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=60_000, key="auto_refresh")
except ImportError:
    pass


# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown(
    """
    <hr style="border-color:var(--border);margin-top:30px">
    <div style="text-align:center;font-size:11px;color:var(--text-muted);padding-bottom:10px">
      ☀️ PV Digital Twin - Smart Solar Monitoring &nbsp;|&nbsp; Mohammedia, Maroc &nbsp;|&nbsp;
      Modèle IEC 61215 / IEC 61724 &nbsp;|&nbsp; v1.0.0
    </div>
    """,
    unsafe_allow_html=True,
)
