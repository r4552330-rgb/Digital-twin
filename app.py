import math
from pathlib import Path

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── CONFIG ─────────────────────────────────────────────────────────────────
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

pv      = PVModel(config)
fetcher = DataFetcher(config)

st.set_page_config(page_title="PV Digital Twin", layout="wide")

# ── DARK MODE ──────────────────────────────────────────────────────────────
if "dark" not in st.session_state:
    st.session_state.dark = False

col_toggle, _ = st.columns([1, 10])
with col_toggle:
    if st.button("🌙 Thème"):
        st.session_state.dark = not st.session_state.dark

dark = st.session_state.dark
bg   = "#0e1117" if dark else "#f5f7fb"
card = "#1c1f26" if dark else "white"
text = "white"   if dark else "#111"

st.markdown(f"""
<style>
body {{
    background-color: {bg};
    color: {text};
}}
.block-container {{
    padding: 2rem;
}}
.card {{
    background: {card};
    color: {text};
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 0.5rem;
}}
.card h4 {{
    margin: 0 0 8px 0;
    font-size: 0.85rem;
    opacity: 0.6;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.card h2 {{
    margin: 0;
    font-size: 1.8rem;
}}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────
st.sidebar.title("⚡ PV Digital Twin")
st.sidebar.selectbox("Site", [config["site"]["name"]])
st.sidebar.write(f"Capacité : {config['inverter']['p_rated_kw']} kW")
st.sidebar.write(f"Panneaux : {config['array']['n_panels']} × {config['panel']['pmp_stc']} Wc")
st.sidebar.write(f"Localisation : {config['site']['latitude']}°N, {config['site']['longitude']}°E")

# ── DATA ───────────────────────────────────────────────────────────────────
data = fetcher.get_data()
res  = pv.compute(data["irradiance"], data["temperature"])

# ── KPI ────────────────────────────────────────────────────────────────────
st.title("Dashboard PV")

c1, c2, c3, c4 = st.columns(4)

c1.markdown(
    f"<div class='card'><h4>Puissance AC</h4><h2>{res['p_ac_kw']} kW</h2></div>",
    unsafe_allow_html=True
)
c2.markdown(
    f"<div class='card'><h4>Performance Ratio</h4><h2>{res['performance_ratio']:.2%}</h2></div>",
    unsafe_allow_html=True
)
c3.markdown(
    f"<div class='card'><h4>Temp. cellule</h4><h2>{res['temp_cell']} °C</h2></div>",
    unsafe_allow_html=True
)
c4.markdown(
    f"<div class='card'><h4>Irradiance</h4><h2>{data['irradiance']} W/m²</h2></div>",
    unsafe_allow_html=True
)

# ── GRAPHIQUE PRODUCTION JOURNALIÈRE ──────────────────────────────────────
st.markdown("### Production journalière estimée")

x = list(range(24))
y = [
    pv.compute(
        900 * math.sin(math.pi * (h - 6) / 12) if 6 <= h <= 18 else 0.0,
        25
    )["p_ac_kw"]
    for h in x
]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x, y=y,
    fill="tozeroy",
    name="P_AC (kW)",
    line=dict(color="#f59e0b", width=2),
    fillcolor="rgba(245,158,11,0.15)"
))
fig.update_layout(
    xaxis_title="Heure",
    yaxis_title="Puissance AC (kW)",
    xaxis=dict(tickmode="linear", tick0=0, dtick=2),
    margin=dict(l=0, r=0, t=30, b=0),
    template="plotly_dark" if dark else "plotly_white",
)
st.plotly_chart(fig, use_container_width=True)

# ── DÉTAILS ────────────────────────────────────────────────────────────────
with st.expander("Détails du calcul"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Puissance DC", f"{res['p_dc_kw']} kW")
        st.metric("Rendement panneau", f"{res['efficiency']} %")
        st.metric("Rendement onduleur", f"{res['inverter_eta']} %")
    with col_b:
        st.metric("Puissance référence STC", f"{res['p_ref_kw']} kW")
        st.metric("Source données", data["source"])
        st.metric("Timestamp", data["timestamp"])
