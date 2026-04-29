import math
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── PATHS ───────────────────────────────────
BASE = Path(__file__).parent
ASSETS = BASE / "assets"

scene_img = ASSETS / "Scene_enset.png"

# ── CONFIG ──────────────────────────────────
with open(BASE / "config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

pv = PVModel(config)
fetcher = DataFetcher(config)

# ── PAGE CONFIG ─────────────────────────────
st.set_page_config(layout="wide")

# ── DARK MODE STATE ─────────────────────────
if "dark" not in st.session_state:
    st.session_state.dark = False

def toggle_theme():
    st.session_state.dark = not st.session_state.dark

# ── THEME COLORS ────────────────────────────
if st.session_state.dark:
    BG = "#0f172a"
    CARD = "#1e293b"
    TEXT = "#f1f5f9"
    SUB = "#94a3b8"
else:
    BG = "#f5f7fb"
    CARD = "#ffffff"
    TEXT = "#111827"
    SUB = "#6b7280"

# ── CSS GLOBAL ──────────────────────────────
st.markdown(f"""
<style>
body {{
    background-color: {BG};
    color: {TEXT};
}}

.block-container {{
    padding: 1rem 2rem;
}}

.card {{
    background: {CARD};
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}

.sidebar {{
    background: {CARD};
}}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────
with st.sidebar:
    st.markdown("### PV Digital Twin")
    st.write("Smart Solar Monitoring")

    st.button("Toggle Theme", on_click=toggle_theme)

    st.markdown("---")
    st.write("Site :", config["site"]["name"])

# ── DATA ───────────────────────────────────
data = fetcher.get_data()
res = pv.compute(data["irradiance"], data["temperature"])

now = datetime.now()

# ── HEADER KPI ─────────────────────────────
st.markdown("## Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div class='card'><b>Puissance AC</b><h2>{res['p_ac_kw']:.2f} kW</h2></div>", unsafe_allow_html=True)

c2.markdown(f"<div class='card'><b>Performance Ratio</b><h2>{res.get('performance_ratio',0):.2f}</h2></div>", unsafe_allow_html=True)

c3.markdown(f"<div class='card'><b>Temp cellule</b><h2>{res['temp_cell']} °C</h2></div>", unsafe_allow_html=True)

c4.markdown(f"<div class='card'><b>Irradiance</b><h2>{data['irradiance']} W/m²</h2></div>", unsafe_allow_html=True)

# ── MAIN LAYOUT ────────────────────────────
left, right = st.columns([3,2])

# ═════════ LEFT ═════════
with left:
    st.markdown("### Jumeau numérique")

    st.image(str(scene_img), use_container_width=True)

    st.markdown("### Flux d'énergie")

    f1, f2, f3, f4 = st.columns(4)

    f1.markdown(f"<div class='card'>PV<br><b>{res['p_dc_kw']:.2f} kW</b></div>", unsafe_allow_html=True)
    f2.markdown(f"<div class='card'>Onduleur<br><b>{res['p_ac_kw']:.2f} kW</b></div>", unsafe_allow_html=True)
    f3.markdown(f"<div class='card'>Batterie<br><b>0.00 kW</b></div>", unsafe_allow_html=True)
    f4.markdown(f"<div class='card'>Réseau<br><b>{res['p_ac_kw']:.2f} kW</b></div>", unsafe_allow_html=True)

# ═════════ RIGHT ═════════
with right:
    st.markdown("### Production & Performance")

    hours = list(range(24))
    prod = []

    for h in hours:
        if 6 <= h <= 18:
            irr = 900 * math.sin(math.pi * (h - 6) / 12)
        else:
            irr = 0

        sim = pv.compute(irr, 25)
        prod.append(sim["p_ac_kw"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hours,
        y=prod,
        fill='tozeroy',
        line=dict(color="#22c55e")
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Informations")

    st.write("Source :", data["source"])
    st.write("Température :", data["temperature"])
    st.write("Heure :", now.strftime("%H:%M:%S"))
