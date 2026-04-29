import math
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

# ── MOCK CLASSES (since model.py and data.py aren't provided) ─────────────────

class PVModel:
    def __init__(self, config):
        self.config = config

    def compute(self, irradiance, temperature):
        """Simulate PV power computation"""
        n_panels = self.config.get("array", {}).get("n_panels", 20)
        pmp_stc = self.config.get("panel", {}).get("pmp_stc", 450)
        ac_eff = self.config.get("losses", {}).get("ac_efficiency", 0.97)
        dc_loss = self.config.get("losses", {}).get("dc_total", 0.03)

        # Simplified PV model
        p_dc = n_panels * pmp_stc * (irradiance / 1000) * (1 - 0.004 * (temperature - 25)) / 1000
        p_ac = p_dc * ac_eff * (1 - dc_loss)

        # Performance ratio
        pr = 0.82 + 0.05 * (irradiance / 1000)

        return {
            "p_dc_kw": max(0, p_dc),
            "p_ac_kw": max(0, p_ac),
            "performance_ratio": min(0.99, max(0.5, pr))
        }

class DataFetcher:
    def __init__(self, config):
        self.config = config

    def get_data(self):
        """Simulate fetching real-time data"""
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            irr = 800 * math.sin(math.pi * (hour - 6) / 12) + 50
        else:
            irr = 0
        return {
            "irradiance": irr,
            "temperature": 25 + 5 * math.sin(math.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 20
        }

# ── CONFIG ─────────────────────────────────────────────────────────────────

BASE_PATH = Path(__file__).parent
config_path = BASE_PATH / "config.yaml"

if not config_path.exists():
    # Create default config if not exists
    default_config = {
        "site": {"name": "Site Solaire Demo", "location": "Paris, France"},
        "array": {"n_panels": 20, "tilt": 30, "azimuth": 180},
        "panel": {"pmp_stc": 450, "voc": 45.8, "isc": 12.3},
        "losses": {"ac_efficiency": 0.97, "dc_total": 0.03, "soiling": 0.02},
        "inverter": {"p_rated_kw": 8.5, "efficiency": 0.98}
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, allow_unicode=True)

with open(config_path, encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Vérification minimale des sections
for section in ("site", "array", "panel", "losses"):
    if section not in config:
        st.error(f"Section '{section}' manquante dans config.yaml")
        st.stop()

# ── INITIALISATION ─────────────────────────────────────────────────────────

pv = PVModel(config)
fetcher = DataFetcher(config)

st.set_page_config(
    page_title="PV Digital Twin",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SESSION STATE ──────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "Vue d'ensemble"
if "period" not in st.session_state:
    st.session_state.period = "Jour"

# ── CSS ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background-color: #020617 !important;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
        text-align: left !important;
        padding: 0.5rem 1rem !important;
        font-size: 13px !important;
        width: 100% !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }
    /* Remove default margins */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1400px !important;
    }
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 0 0.5rem 1rem 0.5rem;">
        <div style="color: #f59e0b; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">PV</div>
        <div style="color: #94a3b8; font-size: 11px; font-weight: 500; letter-spacing: 0.05em; margin-top: 2px;">
            Digital Twin
        </div>
        <div style="color: #475569; font-size: 9px; margin-top: 4px;">
            Smart Solar Monitoring
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("Accueil", "Vue d'ensemble"),
        ("Jumeau", "Jumeau numerique"),
        ("Perf.", "Performance"),
        ("Equip.", "Equipements"),
        ("Alarmes", "Alarmes (2)"),
        ("Analyses", "Analyses"),
        ("Rapports", "Rapports"),
        ("Meteo", "Meteo"),
        ("Param.", "Parametres"),
    ]
    for label, name in nav_items:
        if st.button(label, key=f"nav_{name}"):
            st.session_state.page = name

    st.markdown("""
    <div style="margin-top:1.5rem; padding-top:1rem; border-top:1px solid #1e293b;">
        <div style="color:#475569!important; font-size:10px; text-transform:uppercase;
                    letter-spacing:.1em; padding:0 0.5rem; margin-bottom:0.4rem;">SITE</div>
    </div>""", unsafe_allow_html=True)

    # Affichage du nom du site
    st.markdown(f"""
    <div style="padding:0.3rem 0.5rem;">
        <div style="color:#94a3b8!important; font-size:13px; font-weight:600;">{config['site']['name']}</div>
    </div>""", unsafe_allow_html=True)

    # Capacité DC
    cap_dc = config["array"]["n_panels"] * config["panel"]["pmp_stc"] / 1000.0
    st.markdown(f"""
    <div style="padding:0.3rem 0.5rem;">
        <div style="color:#475569!important; font-size:10px;">Capacite DC</div>
        <div style="color:#94a3b8!important; font-size:13px; font-weight:600;">{cap_dc:.2f} kWp</div>
    </div>""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────

try:
    data = fetcher.get_data()
except Exception:
    data = {"irradiance": 0.0, "temperature": 25.0}

res = pv.compute(data["irradiance"], data["temperature"])
now = datetime.now()

hours = list(range(25))
p_ac_curve = []
irr_curve = []
for h in hours:
    if 6 <= h <= 18:
        irr = 900 * math.sin(math.pi * (h - 6) / 12)
    else:
        irr = 0.0
    irr_curve.append(max(0.0, irr))
    sim_res = pv.compute(irr, 25.0)
    p_ac_curve.append(sim_res["p_ac_kw"])

prod_jour_kwh = round(sum(p_ac_curve), 2)
co2_evite_kg = round(res["p_ac_kw"] * 0.7, 0)
rend_spec = round((prod_jour_kwh / cap_dc) if cap_dc > 0 else 0, 2)

meteo_label = "Ensoleille" if data["irradiance"] > 600 else ("Nuageux" if data["irradiance"] > 200 else "Couvert")
meteo_symbol = "☀️" if data["irradiance"] > 600 else ("⛅" if data["irradiance"] > 200 else "🌧️")

# Puissance nominale AC estimée
if "inverter" in config and "p_rated_kw" in config["inverter"]:
    p_rated_ac_kw = config["inverter"]["p_rated_kw"]
else:
    p_rated_ac_kw = cap_dc * config["losses"]["ac_efficiency"]

# ── BANDEAU HEADER ─────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #1e293b; border-radius: 12px;
            margin: 0 0 1rem 0; padding: 1rem 1.5rem;
            display: flex; justify-content: space-between; align-items: center;">
    <div>
        <div style="color: #f1f5f9; font-size: 18px; font-weight: 700;">
            {st.session_state.page}
        </div>
        <div style="color: #475569; font-size: 11px; margin-top: 2px;">
            {now.strftime("%d/%m/%Y %H:%M")} · {meteo_symbol} {meteo_label}
        </div>
    </div>
    <div style="text-align: right;">
        <div style="color: #22c55e; font-size: 20px; font-weight: 700;">
            {res["p_ac_kw"]:.2f} kW
        </div>
        <div style="color: #475569; font-size: 10px;">
            Puissance AC actuelle
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CORPS PRINCIPAL ─────────────────────────────────────────────────────────

col_left, col_right = st.columns([3, 2], gap="small")

# ═══════════════════════ COLONNE GAUCHE ════════════════════════════════════

with col_left:
    # ---- JUMEAU NUMÉRIQUE ----
    st.markdown("""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px;
                margin:0 0 0.5rem 0; padding:1rem 1rem 0.5rem;">
        <div style="color:#3b82f6; font-weight:700; font-size:12px; letter-spacing:.08em; margin-bottom:.8rem;">
            JUMEAU NUMERIQUE — VUE 3D
        </div>
    </div>""", unsafe_allow_html=True)

    # Menu vue
    vue_mode = st.selectbox(
        "Mode de visualisation",
        ["Vue libre", "Irradiance", "Temperature", "Production", "Pertes"],
        label_visibility="collapsed",
        key="vue_mode"
    )

    # Dessin SVG des panneaux
    n_panels = config["array"]["n_panels"]
    cols_pv, rows_pv = 4, math.ceil(n_panels / 4)
    status_colors = ["#22c55e"] * n_panels
    if n_panels > 2:
        status_colors[2] = "#f59e0b"

    panel_svg = ""
    for r in range(rows_pv):
        for c in range(4):
            idx = r * 4 + c
            if idx >= n_panels:
                break
            x = 30 + c * 88
            y = 20 + r * 58
            col_fill = "#1a3a6e" if status_colors[idx] == "#22c55e" else "#3a2a10"
            panel_svg += f"""
            <rect x="{x}" y="{y}" width="72" height="46" rx="3"
                  fill="{col_fill}" stroke="{status_colors[idx]}" stroke-width="1.2" opacity=".85"/>
            <line x1="{x+24}" y1="{y}" x2="{x+24}" y2="{y+46}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x+48}" y1="{y}" x2="{x+48}" y2="{y+46}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x}" y1="{y+15}" x2="{x+72}" y2="{y+15}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x}" y1="{y+31}" x2="{x+72}" y2="{y+31}" stroke="#2255aa" stroke-width=".5"/>
            <circle cx="{x+36}" cy="{y+23}" r="5" fill="{status_colors[idx]}" opacity=".9"/>
            <circle cx="{x+36}" cy="{y+23}" r="10" fill="{status_colors[idx]}" opacity=".2"/>
            """

    st.markdown(f"""
    <div style="background:#060f1e; border:1px solid #1e293b; border-radius:0 0 10px 10px;
                margin:0 0 0 0; padding:.5rem;">
        <svg viewBox="0 0 410 {rows_pv*58+80}" style="width:100%; border-radius:6px;">
            <rect width="410" height="{rows_pv*58+80}" fill="#060f1e"/>
            <rect x="0" y="{rows_pv*58+40}" width="410" height="40" fill="#0a1929" opacity=".6"/>
            <rect x="305" y="{rows_pv*58-30}" width="100" height="90" rx="4"
                  fill="#0f1f35" stroke="#1e3a5f" stroke-width="1"/>
            {panel_svg}
            <rect x="315" y="{rows_pv*58}" width="45" height="55" rx="4"
                  fill="#1e3a5f" stroke="#3b82f6" stroke-width="1"/>
            <text x="337" y="{rows_pv*58+35}" text-anchor="middle" fill="#60a5fa" font-size="7"
                  font-family="monospace">MPPT</text>
            <circle cx="337" cy="{rows_pv*58+18}" r="7" fill="#22c55e" opacity=".9"/>
        </svg>
        <div style="display:flex; gap:16px; padding:8px 12px; border-top:1px solid #1e293b;
                    font-size:11px; color:#94a3b8;">
            <span>🟢 Normal</span><span>🟡 Attention</span>
            <span>🔴 Alarme</span><span>🔵 Maintenance</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ---- FLUX D'ÉNERGIE ----
    st.markdown("""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px;
                margin:1rem 0 0.5rem 0; padding:1rem 1rem .8rem;">
        <div style="color:#3b82f6; font-weight:700; font-size:12px; letter-spacing:.08em; margin-bottom:.8rem;">
            FLUX D'ENERGIE
        </div>
    </div>""", unsafe_allow_html=True)

    flux_data = [
        ("☀️", "PANNEAUX PV", f"{res['p_dc_kw']:.2f} kW", "#f59e0b"),
        ("⚡", "MPPT / DC", f"{res['p_dc_kw']:.2f} kW", "#3b82f6"),
        ("🔌", "ONDULEUR", f"{res['p_ac_kw']:.2f} kW", "#8b5cf6"),
        ("🏠", "RESEAU", f"{res['p_ac_kw']:.2f} kW", "#22c55e"),
    ]
    fc = st.columns(4)
    for col, (sym, label, val, color) in zip(fc, flux_data):
        with col:
            st.markdown(f"""
            <div style="background:#060f1e; border:1px solid #1e293b; border-radius:10px;
                        padding:12px 8px; text-align:center; margin:0 2px 0 4px;">
                <div style="font-size:22px; margin-bottom:4px;">{sym}</div>
                <div style="color:#475569; font-size:9px; letter-spacing:.07em;">{label}</div>
                <div style="color:{color}; font-size:13px; font-weight:700; margin-top:3px;">{val}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════ COLONNE DROITE ════════════════════════════════════

with col_right:
    # ---- PRODUCTION & PERFORMANCE ----
    st.markdown("""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px;
                margin:0 0 0.5rem 0; padding:1rem 1rem 0.5rem;">
        <div style="color:#3b82f6; font-weight:700; font-size:12px; letter-spacing:.08em; margin-bottom:.8rem;">
            PRODUCTION & PERFORMANCE
        </div>
    </div>""", unsafe_allow_html=True)

    p_cols = st.columns(4)
    for col, period in zip(p_cols, ["Jour", "Semaine", "Mois", "Annee"]):
        with col:
            if st.button(period, key=f"p_{period}"):
                st.session_state.period = period

    m1, m2, m3 = st.columns(3)
    for col, label, val, unit in zip(
        [m1, m2, m3],
        ["Production", "Rendement specifique", "Performance Ratio"],
        [f"{prod_jour_kwh:.1f}", f"{rend_spec:.2f}", f"{res['performance_ratio']*100:.1f}"],
        ["kWh", "kWh/kWp", "%"],
    ):
        with col:
            st.markdown(f"""
            <div style="background:#060f1e; border-radius:8px; padding:10px 8px; margin:0 2px;">
                <div style="color:#64748b; font-size:9px; line-height:1.3;">{label}</div>
                <div style="color:#f1f5f9; font-size:18px; font-weight:700; line-height:1.1; margin-top:2px;">{val}</div>
                <div style="color:#64748b; font-size:9px;">{unit}</div>
            </div>""", unsafe_allow_html=True)

    # Production chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=p_ac_curve, name="Production (AC)",
        line=dict(color="#22c55e", width=2),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.07)", mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=[i/1000 for i in irr_curve], name="Irradiance (POA)",
        line=dict(color="#3b82f6", width=2, dash="dot"),
        yaxis="y2", mode="lines",
    ))
    fig.update_layout(
        height=210, margin=dict(l=5, r=5, t=5, b=25),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color="#94a3b8", size=9),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickfont=dict(color="#475569", size=8), gridcolor="#1e293b",
                   tickvals=[0, 4, 8, 12, 16, 20, 24],
                   ticktext=["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]),
        yaxis=dict(tickfont=dict(color="#475569", size=8), gridcolor="#1e293b"),
        yaxis2=dict(overlaying="y", side="right", tickfont=dict(color="#475569", size=8), showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---- RÉPARTITION DES PERTES ----
    st.markdown("""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px;
                margin:.5rem 0 0 0; padding:1rem 1rem .5rem;">
        <div style="color:#3b82f6; font-weight:700; font-size:12px; letter-spacing:.08em; margin-bottom:.5rem;">
            REPARTITION DES PERTES (AUJOURD'HUI)
        </div>
    </div>""", unsafe_allow_html=True)

    losses = [
        ("#f59e0b", "Pertes d'irradiance", 6.2),
        ("#3b82f6", "Pertes de temperature", 4.1),
        ("#8b5cf6", "Pertes onduleur", round((1 - config["losses"]["ac_efficiency"]) * 100, 1)),
        ("#ef4444", "Pertes DC cablage", round(config["losses"]["dc_total"] * 100, 1)),
    ]

    pd_col, leg_col = st.columns([1, 1])
    with pd_col:
        fig_pie = go.Figure(go.Pie(
            labels=[l[1] for l in losses],
            values=[l[2] for l in losses],
            hole=0.62,
            marker=dict(colors=[l[0] for l in losses]),
            textinfo="none",
        ))
        fig_pie.update_layout(
            height=155, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with leg_col:
        leg_html = "<div style='padding:6px 0;'>"
        for color, label, val in losses:
            leg_html += f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:7px;">
                <span style="display:flex; align-items:center; gap:5px; color:#94a3b8; font-size:10px;">
                    <span style="width:7px; height:7px; border-radius:50%; background:{color};
                                 display:inline-block; flex-shrink:0;"></span>{label}</span>
                <span style="color:#f1f5f9; font-size:11px; font-weight:600;">{val}%</span>
            </div>"""
        leg_html += "</div>"
        st.markdown(leg_html, unsafe_allow_html=True)
