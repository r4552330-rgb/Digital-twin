import math
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── PATH ─────────────────────────────────────
BASE = Path(__file__).parent
ASSETS = BASE / "assets"

scene_img = ASSETS / "Scene_enset.png"

# ── CONFIG ───────────────────────────────────
with open(BASE / "config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

pv = PVModel(config)
fetcher = DataFetcher(config)

# ── THEME ────────────────────────────────────
if "dark" not in st.session_state:
    st.session_state.dark = False

def toggle_theme():
    st.session_state.dark = not st.session_state.dark

if st.session_state.dark:
    BG = "#0f172a"
    CARD = "#1e293b"
    TEXT = "#f1f5f9"
else:
    BG = "#f5f7fb"
    CARD = "#ffffff"
    TEXT = "#111827"

# ── CSS ──────────────────────────────────────
st.markdown(f"""
<style>
body {{ background:{BG}; color:{TEXT}; }}
.block-container {{ padding:1rem 1.5rem; }}
.card {{
    background:{CARD};
    padding:14px;
    border-radius:12px;
    box-shadow:0 3px 10px rgba(0,0,0,0.05);
}}
.sidebar-content {{ background:{CARD}; }}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.markdown("## PV Digital Twin")
    st.write("Smart Monitoring")

    st.button("Dark Mode", on_click=toggle_theme)

    st.markdown("---")
    menu = [
        "Vue d'ensemble",
        "Jumeau numérique",
        "Performance",
        "Equipements",
        "Alarmes",
        "Analyses",
    ]

    page = st.radio("Navigation", menu)

# ── DATA ─────────────────────────────────────
data = fetcher.get_data()
res = pv.compute(data["irradiance"], data["temperature"])
now = datetime.now()

# ── HEADER KPI ───────────────────────────────
st.markdown("### Vue globale")

k1, k2, k3, k4 = st.columns(4)

k1.markdown(f"<div class='card'><b>Puissance AC</b><h2>{res['p_ac_kw']:.2f} kW</h2></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='card'><b>Production jour</b><h2>{res['p_ac_kw']*5:.2f} kWh</h2></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='card'><b>PR</b><h2>{res.get('performance_ratio',0):.2f}</h2></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='card'><b>Temp cellule</b><h2>{res['temp_cell']} °C</h2></div>", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL ─────────────────────────
left, right = st.columns([3,2])

# ═════════ LEFT ═════════
with left:

    st.markdown("### Jumeau numérique")

    st.image(str(scene_img), use_container_width=True)

    st.markdown("### Flux énergie")

    f1, f2, f3, f4 = st.columns(4)

    f1.markdown(f"<div class='card'>PV<br><b>{res['p_dc_kw']:.2f}</b></div>", unsafe_allow_html=True)
    f2.markdown(f"<div class='card'>Onduleur<br><b>{res['p_ac_kw']:.2f}</b></div>", unsafe_allow_html=True)
    f3.markdown(f"<div class='card'>Charge<br><b>0.00</b></div>", unsafe_allow_html=True)
    f4.markdown(f"<div class='card'>Réseau<br><b>{res['p_ac_kw']:.2f}</b></div>", unsafe_allow_html=True)

    # état équipements
    st.markdown("### Etat équipements")

    fig_pie = go.Figure(go.Pie(
        labels=["Normal","Attention","Alarme"],
        values=[80,15,5],
        hole=0.6
    ))

    st.plotly_chart(fig_pie, use_container_width=True)

# ═════════ RIGHT ═════════
with right:

    st.markdown("### Production & Performance")

    hours = list(range(24))
    prod = []

    for h in hours:
        if 6 <= h <= 18:
            irr = 900 * math.sin(math.pi*(h-6)/12)
        else:
            irr = 0

        sim = pv.compute(irr, 25)
        prod.append(sim["p_ac_kw"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hours,
        y=prod,
        fill='tozeroy'
    ))

    st.plotly_chart(fig, use_container_width=True)

    # pertes
    st.markdown("### Pertes")

    fig_loss = go.Figure(go.Pie(
        labels=["Température","Câbles","Onduleur"],
        values=[4,2,3]
    ))

    st.plotly_chart(fig_loss, use_container_width=True)

    # alarmes
    st.markdown("### Alarmes")

    st.write("• Défaut onduleur")
    st.write("• Température élevée")

# ── FOOTER ───────────────────────────────────
st.markdown(f"""
<div style='text-align:center;font-size:12px;color:gray;margin-top:20px;'>
PV Digital Twin — {now.strftime("%d/%m/%Y %H:%M:%S")}
</div>
""", unsafe_allow_html=True)
