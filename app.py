import streamlit as st
import yaml
from model import PVModel
from data import DataFetcher
import plotly.graph_objects as go

# ── CONFIG ─────────────────────────────
with open("config.yaml") as f:
    config = yaml.safe_load(f)

pv = PVModel(config)
fetcher = DataFetcher(config)

st.set_page_config(layout="wide")

# ── DARK MODE TOGGLE ───────────────────
if "dark" not in st.session_state:
    st.session_state.dark = False

col_toggle, _ = st.columns([1, 10])
with col_toggle:
    if st.button("Toggle Theme"):
        st.session_state.dark = not st.session_state.dark

# ── CSS ───────────────────────────────
if st.session_state.dark:
    bg = "#0e1117"
    card = "#1c1f26"
    text = "white"
else:
    bg = "#f5f7fb"
    card = "white"
    text = "#111"

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
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
}}

.sidebar .sidebar-content {{
    background: {card};
}}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────
st.sidebar.title("PV Digital Twin")
st.sidebar.selectbox("Site", ["Centrale PV Demo"])
st.sidebar.write("Capacité:", "4 kW")

# ── DATA ─────────────────────────────
data = fetcher.get_data()
res = pv.compute(data["irradiance"], data["temperature"])

# ── HEADER KPI ───────────────────────
st.title("Dashboard PV")

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div class='card'><h4>Puissance AC</h4><h2>{res['p_ac_kw']} kW</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='card'><h4>PR AC</h4><h2>{res['pr_ac']}</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='card'><h4>Temp cellule</h4><h2>{res['temp_cell']} °C</h2></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='card'><h4>Irradiance</h4><h2>{data['irradiance']} W/m²</h2></div>", unsafe_allow_html=True)

# ── GRAPH ─────────────────────────────
st.markdown("### Production")

x = list(range(24))
y = [pv.compute(max(0, 900 * __import__("math").sin(__import__("math").pi*(h-6)/12)), 25)["p_ac_kw"] for h in x]

fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, fill='tozeroy'))

fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    template="plotly_dark" if st.session_state.dark else "plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ── INFO ─────────────────────────────
st.markdown("### Données")
st.write(data)
