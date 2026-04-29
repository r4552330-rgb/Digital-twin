"""
PV Digital Twin - Dashboard Streamlit
Point d'entrée principal
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from config import CONFIG, SITE, THRESHOLDS
from model import PVModel
from data import DataFetcher
from utils import format_power, format_energy, get_performance_color, cache_ttl

# ─── Configuration de la page ────────────────────────────────────────────────
st.set_page_config(
    page_title="PV Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personnalisé ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

  html, body, [class*="css"] {
      font-family: 'Syne', sans-serif;
  }

  .metric-card {
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
      margin-bottom: 1rem;
  }

  .metric-title {
      font-size: 0.75rem;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: 600;
      margin-bottom: 0.3rem;
  }

  .metric-value {
      font-family: 'Space Mono', monospace;
      font-size: 2rem;
      font-weight: 700;
      color: #f8fafc;
      line-height: 1;
  }

  .metric-unit {
      font-size: 0.9rem;
      color: #94a3b8;
      margin-left: 4px;
  }

  .metric-delta {
      font-size: 0.8rem;
      margin-top: 0.4rem;
  }

  .status-badge {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }

  .status-ok { background: #14532d; color: #4ade80; }
  .status-warn { background: #713f12; color: #fbbf24; }
  .status-crit { background: #7f1d1d; color: #f87171; }

  .section-header {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #475569;
      border-bottom: 1px solid #1e293b;
      padding-bottom: 0.5rem;
      margin: 1.5rem 0 1rem 0;
  }

  .stTabs [data-baseweb="tab-list"] {
      gap: 8px;
      background: transparent;
  }

  .stTabs [data-baseweb="tab"] {
      background: #1e293b;
      border-radius: 8px;
      border: 1px solid #334155;
      color: #94a3b8;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      padding: 0.5rem 1rem;
  }

  .stTabs [aria-selected="true"] {
      background: #0ea5e9 !important;
      color: white !important;
      border-color: #0ea5e9 !important;
  }

  .header-container {
      background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%);
      border-bottom: 1px solid #1e293b;
      padding: 1rem 0 0.5rem 0;
      margin-bottom: 1.5rem;
  }

  .site-tag {
      background: #0f2a1a;
      color: #4ade80;
      border: 1px solid #166534;
      border-radius: 6px;
      padding: 2px 8px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.1em;
  }
</style>
""", unsafe_allow_html=True)


# ─── Initialisation ───────────────────────────────────────────────────────────
@st.cache_resource
def get_model():
    return PVModel(CONFIG)

@st.cache_resource
def get_fetcher():
    return DataFetcher(CONFIG)


model = get_model()
fetcher = get_fetcher()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ PV Digital Twin")
    st.markdown(f"<span class='site-tag'>LIVE</span> **{SITE['name']}**", unsafe_allow_html=True)
    st.markdown(f"📍 {SITE['location']}")
    st.divider()

    st.markdown("#### Paramètres de simulation")
    irradiance_manual = st.slider("Irradiance (W/m²)", 0, 1200, 800, 10)
    temp_manual = st.slider("Température ambiante (°C)", -10, 50, 25, 1)
    use_live = st.toggle("Utiliser données météo live", value=True)

    st.divider()
    st.markdown("#### Horizon temporel")
    time_range = st.selectbox("Afficher", ["24 dernières heures", "7 derniers jours", "30 derniers jours"])

    st.divider()
    auto_refresh = st.toggle("Rafraîchissement auto (60s)", value=False)
    if auto_refresh:
        st.info("🔄 Prochain rafraîchissement dans 60s")

    st.divider()
    st.markdown(
        "<div style='font-size:0.7rem;color:#475569;'>PV Digital Twin v1.0<br>"
        f"Capacité installée : {SITE['capacity_kwp']} kWp<br>"
        f"Panneau : {CONFIG['panel']['model']}</div>",
        unsafe_allow_html=True
    )


# ─── Récupération des données ─────────────────────────────────────────────────
@st.cache_data(ttl=cache_ttl(300))
def load_weather():
    return fetcher.get_weather_data()

@st.cache_data(ttl=cache_ttl(60))
def load_history(days=1):
    return fetcher.get_historical_data(days=days)


with st.spinner("Chargement des données météo..."):
    weather = load_weather()
    irr = weather.get("irradiance", irradiance_manual) if use_live else irradiance_manual
    temp = weather.get("temperature", temp_manual) if use_live else temp_manual


# ─── Calcul modèle PV ────────────────────────────────────────────────────────
result = model.compute(irradiance=irr, temp_ambient=temp)
p_actual = result["p_dc_kw"]
p_ref = result["p_ref_kw"]
pr = result["performance_ratio"]
eta = result["efficiency"]
t_cell = result["temp_cell"]


# ─── En-tête ─────────────────────────────────────────────────────────────────
col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
with col_h1:
    st.markdown(f"## ⚡ PV Digital Twin — {SITE['name']}")
    st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')} — {SITE['location']}*")
with col_h2:
    pr_color = get_performance_color(pr, THRESHOLDS)
    st.markdown(f"""
    <div class='metric-card' style='border-color:{pr_color};'>
        <div class='metric-title'>Performance Ratio</div>
        <div class='metric-value' style='color:{pr_color};'>{pr:.1%}<span class='metric-unit'></span></div>
    </div>
    """, unsafe_allow_html=True)
with col_h3:
    irr_status = "OK" if irr > 100 else "FAIBLE"
    irr_class = "status-ok" if irr > 100 else "status-warn"
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Irradiance <span class='{irr_class} status-badge'>{irr_status}</span></div>
        <div class='metric-value'>{irr:.0f}<span class='metric-unit'>W/m²</span></div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")

# ─── KPIs principaux ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Puissance & Énergie</div>", unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)

kpis = [
    ("Puissance DC (modèle)", format_power(p_actual), "kW", f"Réf: {format_power(p_ref)} kW"),
    ("Température cellule", f"{t_cell:.1f}", "°C", f"Ambiante: {temp:.1f}°C"),
    ("Rendement panneau", f"{eta:.1f}", "%", f"STC: {CONFIG['panel']['eta_stc']*100:.1f}%"),
    ("Énergie aujourd'hui", format_energy(p_actual * 5.2), "kWh", "Estimation journalière"),
    ("CO₂ évité", f"{p_actual * 5.2 * 0.233:.1f}", "kg", "Facteur réseau Maroc"),
]

for col, (title, val, unit, sub) in zip([k1, k2, k3, k4, k5], kpis):
    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>{title}</div>
            <div class='metric-value'>{val}<span class='metric-unit'>{unit}</span></div>
            <div class='metric-delta' style='color:#64748b;'>{sub}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── Graphiques ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Analyse temporelle</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Puissance", "🌡️ Températures", "⚡ Courbe I-V", "📊 Bilan"])

with tab1:
    days_map = {"24 dernières heures": 1, "7 derniers jours": 7, "30 derniers jours": 30}
    days = days_map[time_range]

    # Génération de données simulées pour la démo
    hours = pd.date_range(end=datetime.now(), periods=days * 24, freq="h")
    np.random.seed(42)
    irr_series = np.clip(
        500 * np.sin(np.pi * ((hours.hour - 6) / 12)) + np.random.normal(0, 30, len(hours)),
        0, None
    )
    p_series = model.compute_series(irr_series, temp + np.random.normal(0, 2, len(hours)))

    df = pd.DataFrame({
        "Heure": hours,
        "Puissance DC (kW)": p_series["p_dc_kw"],
        "Puissance de référence (kW)": p_series["p_ref_kw"],
    }).set_index("Heure")

    st.line_chart(df, color=["#0ea5e9", "#f97316"])

with tab2:
    df_temp = pd.DataFrame({
        "Heure": hours,
        "T° ambiante (°C)": temp + np.random.normal(0, 3, len(hours)),
        "T° cellule PV (°C)": t_cell + np.random.normal(0, 4, len(hours)),
    }).set_index("Heure")
    st.line_chart(df_temp, color=["#22d3ee", "#ef4444"])

with tab3:
    # Courbe I-V théorique
    v_range = np.linspace(0, CONFIG["panel"]["voc"] * SITE["strings_per_mppt"], 200)
    iv = model.compute_iv_curve(v_range)
    df_iv = pd.DataFrame({"Tension (V)": v_range, "Courant (A)": iv["current"]})
    st.markdown("**Courbe I-V du générateur PV** — conditions actuelles")
    st.area_chart(df_iv.set_index("Tension (V)"), color=["#a78bfa"])

    mpp_col, voc_col, isc_col = st.columns(3)
    with mpp_col:
        st.metric("P_MPP", f"{iv['p_mpp']:.2f} kW")
    with voc_col:
        st.metric("V_MPP", f"{iv['v_mpp']:.1f} V")
    with isc_col:
        st.metric("I_MPP", f"{iv['i_mpp']:.2f} A")

with tab4:
    monthly = pd.DataFrame({
        "Mois": ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"],
        "Production (kWh)": [320, 380, 510, 580, 640, 680, 710, 690, 580, 470, 350, 290],
        "Référence Météo (kWh)": [340, 390, 520, 590, 650, 695, 720, 700, 590, 480, 360, 300],
    }).set_index("Mois")
    st.bar_chart(monthly, color=["#0ea5e9", "#475569"])


# ─── Schéma synoptique ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Schéma synoptique</div>", unsafe_allow_html=True)

s1, s2, s3, s4, s5 = st.columns([2, 1, 2, 1, 2])

def synoptic_box(col, icon, title, value, unit, color="#0ea5e9"):
    with col:
        st.markdown(f"""
        <div style='background:#0f172a;border:1px solid {color};border-radius:10px;padding:1rem;text-align:center;'>
            <div style='font-size:2rem;'>{icon}</div>
            <div style='font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin:4px 0;'>{title}</div>
            <div style='font-family:Space Mono,monospace;font-size:1.3rem;color:{color};font-weight:700;'>{value}<span style='font-size:0.8rem;color:#64748b;'> {unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

synoptic_box(s1, "🌞", "Générateur PV", format_power(p_actual), "kW", "#fbbf24")
with s2:
    st.markdown("<div style='text-align:center;padding-top:2.5rem;font-size:1.5rem;color:#334155;'>→</div>", unsafe_allow_html=True)
synoptic_box(s3, "⚡", "Onduleur", format_power(p_actual * 0.97), "kW AC", "#0ea5e9")
with s4:
    st.markdown("<div style='text-align:center;padding-top:2.5rem;font-size:1.5rem;color:#334155;'>→</div>", unsafe_allow_html=True)
synoptic_box(s5, "🏗️", "Réseau / Charge", format_power(p_actual * 0.97), "kW", "#4ade80")


# ─── Alertes ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Alertes & Diagnostics</div>", unsafe_allow_html=True)

alerts = []
if pr < THRESHOLDS["pr_critical"]:
    alerts.append(("🔴", "CRITIQUE", f"Performance Ratio très faible : {pr:.1%}", "status-crit"))
elif pr < THRESHOLDS["pr_warning"]:
    alerts.append(("🟡", "ATTENTION", f"Performance Ratio dégradé : {pr:.1%}", "status-warn"))

if t_cell > THRESHOLDS["temp_cell_warning"]:
    alerts.append(("🟡", "ATTENTION", f"Température cellule élevée : {t_cell:.1f}°C", "status-warn"))

if not alerts:
    st.success("✅ Tous les paramètres sont dans les plages normales.")
else:
    for icon, level, msg, cls in alerts:
        st.warning(f"{icon} **[{level}]** {msg}")


# ─── Auto-refresh ─────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
