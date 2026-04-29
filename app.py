import math
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── CHEMIN ASSETS ─────────────────────────────
BASE_PATH = Path(__file__).parent
ASSETS = BASE_PATH / "assets"

scene_img = ASSETS / "Scene_enset.png"
pv_img = ASSETS / "PV.png"
inv_img = ASSETS / "onduleur.png"
grid_img = ASSETS / "Grid.png"
battery_img = ASSETS / "Battry.png"
load_img = ASSETS / "Charge.png"

# ── CONFIG ───────────────────────────────────
config_path = BASE_PATH / "config.yaml"

with open(config_path, encoding="utf-8") as f:
    config = yaml.safe_load(f)

for section in ("site", "panel", "losses"):
    if section not in config:
        st.error(f"Section '{section}' manquante")
        st.stop()

# ── INIT ─────────────────────────────────────
pv = PVModel(config)
fetcher = DataFetcher(config)

st.set_page_config(layout="wide")

# ── STYLE ────────────────────────────────────
st.markdown("""
<style>
body { background-color:#f5f7fb; }
.card {
    background:white;
    padding:15px;
    border-radius:12px;
    box-shadow:0 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────
data = fetcher.get_data()
res = pv.compute(data["irradiance"], data["temperature"])

now = datetime.now()

# ── HEADER KPI ───────────────────────────────
st.title("PV Digital Twin")

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div class='card'><b>Puissance AC</b><h2>{res['p_ac_kw']} kW</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='card'><b>PR AC</b><h2>{res['pr_ac']}</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='card'><b>Temp cellule</b><h2>{res['temp_cell']} °C</h2></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='card'><b>Irradiance</b><h2>{data['irradiance']} W/m²</h2></div>", unsafe_allow_html=True)

# ── LAYOUT ───────────────────────────────────
col_left, col_right = st.columns([3,2])

# ════════════ GAUCHE ════════════
with col_left:
    st.subheader("Jumeau numérique")

    # Image réelle
    st.image(str(scene_img), use_container_width=True)

    # Flux énergie
    st.subheader("Flux énergie")

    fc = st.columns(4)

    icons = [pv_img, inv_img, battery_img, grid_img]
    labels = ["PV", "Onduleur", "Batterie", "Réseau"]
    values = [res["p_dc_kw"], res["p_ac_kw"], 0, res["p_ac_kw"]]

    for col, icon, label, val in zip(fc, icons, labels, values):
        with col:
            st.image(str(icon), width=60)
            st.write(label)
            st.write(f"{val:.2f} kW")

# ════════════ DROITE ════════════
with col_right:
    st.subheader("Production")

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
        fill='tozeroy',
        name="Production"
    ))

    fig.update_layout(
        margin=dict(l=0,r=0,t=30,b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Infos
    st.subheader("Données")
    st.write(f"Source : {data['source']}")
    st.write(f"Heure : {now.strftime('%H:%M:%S')}")
