import math
import base64
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── CONFIG ──────────────────────────────────────────────────────────────────
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

pv      = PVModel(config)
fetcher = DataFetcher(config)

st.set_page_config(
    page_title="PV Digital Twin",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── HELPER : encode image en base64 ─────────────────────────────────────────
def img_b64(filename: str) -> str:
    p = Path(__file__).parent / "assets" / filename
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode()

def img_tag(filename: str, style: str = "") -> str:
    b64 = img_b64(filename)
    if not b64:
        return ""
    return f'<img src="data:image/png;base64,{b64}" style="{style}"/>'

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "page"   not in st.session_state: st.session_state.page   = "Vue d'ensemble"
if "period" not in st.session_state: st.session_state.period = "Jour"

# ── CSS GLOBAL — thème sombre cohérent ──────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"] {
    background-color: #060f1e !important;
    color: #e2e8f0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0d1b2e !important;
    border-right: 1px solid #1e3a5f !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* Forcer tous les textes sidebar en clair */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #94a3b8 !important;
}

/* ── Boutons navigation sidebar ── */
[data-testid="stSidebar"] button {
    background-color: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    text-align: left !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    margin-bottom: 4px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] button:hover {
    background-color: #1e3a5f !important;
    color: #60a5fa !important;
    border-color: #3b82f6 !important;
}
[data-testid="stSidebar"] button:focus,
[data-testid="stSidebar"] button:active {
    background-color: #1e3a5f !important;
    color: #60a5fa !important;
    border-color: #3b82f6 !important;
    box-shadow: none !important;
}

/* ── Selectbox sidebar ── */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1e3a5f !important;
    border-color: #334155 !important;
    color: #94a3b8 !important;
}

/* ── Masquer éléments Streamlit par défaut ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

/* ── Main container ── */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    background-color: #060f1e !important;
}

/* ── Colonnes sans gap visible ── */
div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

/* ── Plotly transparent ── */
.js-plotly-plot .plotly, .plot-container { background: transparent !important; }

/* ── Boutons période (hors sidebar) ── */
.main button {
    background-color: transparent !important;
    color: #64748b !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    transition: all 0.15s ease !important;
}
.main button:hover {
    background-color: #1e3a5f !important;
    color: #f1f5f9 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #060f1e; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
data = fetcher.get_data()
res  = pv.compute(data["irradiance"], data["temperature"])
now  = datetime.now()

hours      = list(range(25))
p_ac_curve = [
    pv.compute(900 * math.sin(math.pi * (h-6) / 12) if 6 <= h <= 18 else 0.0, 25)["p_ac_kw"]
    for h in hours
]
irr_curve  = [max(0.0, 950 * math.sin(math.pi * (h-6) / 12)) if 6 <= h <= 18 else 0.0 for h in hours]

cap_dc     = config["array"]["n_panels"] * config["panel"]["pmp_stc"] / 1000
prod_jour  = round(sum(p_ac_curve) / 1000, 2)
co2_evite  = round(res["p_ac_kw"] * 0.7, 0)
rend_spec  = round(prod_jour * 1000 / (cap_dc * 1000), 2) if cap_dc > 0 else 0

irr = data["irradiance"]
meteo_label = "Ensoleille" if irr > 600 else ("Nuageux" if irr > 200 else "Couvert")
meteo_icon  = "assets/PV.png" if irr > 600 else "assets/PV.png"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    logo_scene = img_tag("Scene_enset.png", "width:100%;border-radius:8px;margin-bottom:8px;")
    st.markdown(f"""
    <div style='padding:1rem;border-bottom:1px solid #1e3a5f;margin-bottom:1rem;'>
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>
            <div style='width:40px;height:40px;background:#1e3a5f;border:2px solid #f59e0b;
                        border-radius:8px;display:flex;align-items:center;justify-content:center;'>
                <span style='color:#f59e0b;font-size:18px;font-weight:700;'>PV</span>
            </div>
            <div>
                <div style='color:#f1f5f9!important;font-weight:600;font-size:14px;'>PV Digital Twin</div>
                <div style='color:#475569!important;font-size:10px;'>Smart Solar Monitoring</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("Vue d'ensemble",  "[H]"),
        ("Jumeau numerique","[D]"),
        ("Performance",     "[P]"),
        ("Equipements",     "[E]"),
        ("Alarmes (2)",     "[A]"),
        ("Analyses",        "[N]"),
        ("Rapports",        "[R]"),
        ("Meteo",           "[W]"),
        ("Parametres",      "[S]"),
    ]
    for name, _ in nav_items:
        if st.button(name, key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name

    st.markdown("""
    <div style='margin-top:1.5rem;padding-top:1rem;border-top:1px solid #1e3a5f;'>
        <div style='color:#334155!important;font-size:10px;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:6px;'>SITE</div>
    </div>""", unsafe_allow_html=True)
    st.selectbox("", [config["site"]["name"]], label_visibility="collapsed")
    st.markdown(f"""
    <div style='padding:6px 2px;'>
        <div style='color:#475569!important;font-size:10px;'>Capacite DC</div>
        <div style='color:#94a3b8!important;font-size:13px;font-weight:600;'>{cap_dc:.2f} MWp</div>
    </div>""", unsafe_allow_html=True)

# ── HEADER KPI ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:#0d1b2e;padding:.8rem 2rem;display:flex;align-items:center;
            border-bottom:1px solid #1e3a5f;flex-wrap:wrap;gap:.5rem;'>

    <div style='display:flex;align-items:center;gap:14px;padding-right:2rem;
                border-right:1px solid #1e3a5f;margin-right:2rem;min-width:170px;'>
        <div style='width:42px;height:42px;background:#1e3a5f;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;font-size:22px;'>
            {"☀" if irr > 600 else ("⛅" if irr > 200 else "☁")}
        </div>
        <div>
            <div style='color:#94a3b8;font-size:12px;font-weight:500;'>{meteo_label}</div>
            <div style='color:#f59e0b;font-size:22px;font-weight:700;line-height:1.1;'>
                {data["temperature"]:.0f}°C</div>
            <div style='color:#475569;font-size:10px;'>Irradiance {data["irradiance"]:.0f} W/m²</div>
        </div>
    </div>

    <div style='padding:0 2rem;border-right:1px solid #1e3a5f;margin-right:2rem;'>
        <div style='color:#475569;font-size:9px;text-transform:uppercase;letter-spacing:.08em;'>Puissance AC</div>
        <div style='color:#4ade80;font-size:24px;font-weight:700;line-height:1.1;'>{res["p_ac_kw"]}</div>
        <div style='color:#475569;font-size:9px;'>{res["p_ac_kw"]/config["inverter"]["p_rated_kw"]*100:.0f}% de la capacite</div>
    </div>

    <div style='padding:0 2rem;border-right:1px solid #1e3a5f;margin-right:2rem;'>
        <div style='color:#475569;font-size:9px;text-transform:uppercase;letter-spacing:.08em;'>Production du jour</div>
        <div style='color:#f1f5f9;font-size:24px;font-weight:700;line-height:1.1;'>{prod_jour}</div>
        <div style='color:#475569;font-size:9px;'>MWh</div>
    </div>

    <div style='padding:0 2rem;border-right:1px solid #1e3a5f;margin-right:2rem;'>
        <div style='color:#475569;font-size:9px;text-transform:uppercase;letter-spacing:.08em;'>Production totale</div>
        <div style='color:#f1f5f9;font-size:24px;font-weight:700;line-height:1.1;'>{res["p_ac_kw"]*1.25:.2f}</div>
        <div style='color:#475569;font-size:9px;'>GWh</div>
    </div>

    <div style='padding:0 2rem;border-right:1px solid #1e3a5f;margin-right:2rem;'>
        <div style='color:#475569;font-size:9px;text-transform:uppercase;letter-spacing:.08em;'>CO2 evite</div>
        <div style='color:#f1f5f9;font-size:24px;font-weight:700;line-height:1.1;'>{co2_evite:.0f}</div>
        <div style='color:#475569;font-size:9px;'>t</div>
    </div>

    <div style='margin-left:auto;text-align:right;'>
        <div style='color:#94a3b8;font-size:12px;'>{now.strftime("%d %b %Y")}</div>
        <div style='color:#f59e0b;font-size:20px;font-weight:700;font-family:monospace;letter-spacing:.05em;'>
            {now.strftime("%H:%M:%S")}</div>
        <div style='margin-top:6px;'>
            <span style='background:#1e3a5f;color:#94a3b8;border:1px solid #334155;
                         border-radius:6px;padding:3px 10px;font-size:11px;'>Aujourd'hui ▾</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CORPS ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="small")

# ═══════════ GAUCHE ══════════════════════════════════════════════════════════
with col_left:

    # Entête section jumeau
    st.markdown("""
    <div style='background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px 12px 0 0;
                margin:1rem 0 0 1rem;padding:.8rem 1rem;
                display:flex;justify-content:space-between;align-items:center;'>
        <span style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.09em;'>
            JUMEAU NUMERIQUE — VUE 3D</span>
        <div style='display:flex;gap:8px;'>
            <div style='width:20px;height:20px;border-radius:50%;border:2px solid #3b82f6;'></div>
            <div style='width:20px;height:20px;border-radius:50%;border:2px solid #334155;'></div>
            <div style='width:20px;height:20px;border-radius:50%;border:2px solid #334155;'></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Dropdown vue
    vue_col, _ = st.columns([1, 3])
    with vue_col:
        st.selectbox("", ["Vue libre", "Irradiance", "Temperature", "Production", "Pertes"],
                     label_visibility="collapsed", key="vue_mode")

    # Photo réelle du site
    scene_b64 = img_b64("Scene_enset.png")
    if scene_b64:
        st.markdown(f"""
        <div style='margin:0 0 0 1rem;border:1px solid #1e3a5f;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;'>
            <img src="data:image/png;base64,{scene_b64}"
                 style='width:100%;display:block;max-height:340px;object-fit:cover;opacity:.9;'/>
            <div style='display:flex;gap:20px;padding:8px 14px;background:#0a1929;
                        border-top:1px solid #1e3a5f;font-size:11px;color:#64748b;'>
                <span style='display:flex;align-items:center;gap:5px;'>
                    <span style='width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;'></span>Normal
                </span>
                <span style='display:flex;align-items:center;gap:5px;'>
                    <span style='width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block;'></span>Attention
                </span>
                <span style='display:flex;align-items:center;gap:5px;'>
                    <span style='width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;'></span>Alarme
                </span>
                <span style='display:flex;align-items:center;gap:5px;'>
                    <span style='width:8px;height:8px;border-radius:50%;background:#3b82f6;display:inline-block;'></span>Maintenance
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── FLUX D'ENERGIE avec vraies images ─────────────────────────────────
    st.markdown("""
    <div style='background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px;
                margin:1rem 0 .5rem 1rem;padding:.8rem 1rem .6rem;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.09em;margin-bottom:.7rem;'>
            FLUX D'ENERGIE</div>
    </div>""", unsafe_allow_html=True)

    pv_b64   = img_b64("PV.png")
    inv_b64  = img_b64("onduleur.png")
    bat_b64  = img_b64("Battry.png")
    chg_b64  = img_b64("Charge.png")
    grid_b64 = img_b64("Grid.png")

    def flux_card(b64: str, label: str, value: str, color: str) -> str:
        img_html = f'<img src="data:image/png;base64,{b64}" style="width:60px;height:60px;object-fit:contain;margin-bottom:6px;"/>' if b64 else f'<div style="width:60px;height:60px;background:#1e3a5f;border-radius:8px;margin-bottom:6px;"></div>'
        return f"""
        <div style='background:#060f1e;border:1px solid #1e3a5f;border-radius:10px;
                    padding:14px 8px;text-align:center;flex:1;min-width:0;'>
            {img_html}
            <div style='color:#475569;font-size:9px;letter-spacing:.07em;text-transform:uppercase;'>{label}</div>
            <div style='color:{color};font-size:13px;font-weight:700;margin-top:3px;'>{value}</div>
        </div>"""

    arrow = "<div style='display:flex;align-items:center;padding:0 4px;'><div style='width:28px;height:2px;background:#1e3a5f;position:relative;'><div style='position:absolute;right:-4px;top:-4px;width:0;height:0;border-left:8px solid #3b82f6;border-top:5px solid transparent;border-bottom:5px solid transparent;'></div></div></div>"

    flux_html = f"""
    <div style='display:flex;align-items:center;gap:4px;margin:0 0 .5rem 1rem;padding:0 .5rem;'>
        {flux_card(pv_b64,   "Panneaux PV", f"{res['p_dc_kw']:.2f} kW", "#22c55e")}
        {arrow}
        {flux_card(inv_b64,  "Onduleur",    f"{res['p_ac_kw']:.2f} kW", "#3b82f6")}
        {arrow}
        {flux_card(bat_b64,  "Batterie",    "75 %",                      "#60a5fa")}
        {arrow}
        {flux_card(chg_b64,  "Charge",      f"{res['p_ac_kw']*0.6:.2f} kW", "#f59e0b")}
        {arrow}
        {flux_card(grid_b64, "Reseau",      f"{res['p_ac_kw']*0.4:.2f} kW", "#a78bfa")}
    </div>"""
    st.markdown(flux_html, unsafe_allow_html=True)

# ═══════════ DROITE ══════════════════════════════════════════════════════════
with col_right:

    st.markdown("""
    <div style='background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px 12px 0 0;
                margin:1rem 1rem 0 0;padding:.8rem 1rem;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.09em;'>
            PRODUCTION & PERFORMANCE</div>
    </div>""", unsafe_allow_html=True)

    # Onglets
    p_cols = st.columns(4)
    for col, period in zip(p_cols, ["Jour", "Semaine", "Mois", "Annee"]):
        with col:
            if st.button(period, key=f"p_{period}", use_container_width=True):
                st.session_state.period = period

    # Metriques
    m1, m2, m3 = st.columns(3)
    metrics = [
        ("Production",          f"{prod_jour}",                     "MWh"),
        ("Rendement specifique", f"{rend_spec}",                    "kWh/kWp"),
        ("Performance Ratio",   f"{res['performance_ratio']*100:.1f}", "%"),
    ]
    for col, (label, val, unit) in zip([m1, m2, m3], metrics):
        with col:
            st.markdown(f"""
            <div style='background:#060f1e;border:1px solid #1e3a5f;border-radius:8px;
                        padding:10px 8px;margin:0 2px;'>
                <div style='color:#475569;font-size:9px;line-height:1.3;'>{label}</div>
                <div style='color:#f1f5f9;font-size:18px;font-weight:700;line-height:1.1;margin-top:3px;'>{val}</div>
                <div style='color:#475569;font-size:9px;'>{unit}</div>
            </div>""", unsafe_allow_html=True)

    # Graphique production + irradiance
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
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,15,30,0.0)",
        legend=dict(orientation="h", y=1.1, x=0, font=dict(color="#64748b", size=9),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickfont=dict(color="#334155", size=8), gridcolor="#0d1b2e",
                   tickvals=[0,4,8,12,16,20,24],
                   ticktext=["00:00","04:00","08:00","12:00","16:00","20:00","24:00"]),
        yaxis=dict(tickfont=dict(color="#334155", size=8), gridcolor="#0d1b2e"),
        yaxis2=dict(overlaying="y", side="right",
                    tickfont=dict(color="#334155", size=8), showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Repartition pertes
    st.markdown("""
    <div style='background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px;
                margin:.5rem 1rem 0 0;padding:.8rem 1rem .5rem;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.09em;margin-bottom:.5rem;'>
            REPARTITION DES PERTES (AUJOURD'HUI)</div>
    </div>""", unsafe_allow_html=True)

    losses = [
        ("#f59e0b", "Pertes d'irradiance",   6.2),
        ("#3b82f6", "Pertes de temperature",  4.1),
        ("#8b5cf6", "Pertes onduleur",        round((1 - config["losses"]["ac_efficiency"]) * 100, 1)),
        ("#ef4444", "Pertes DC cablage",      round(config["losses"]["dc_total"] * 100, 1)),
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
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                <span style='display:flex;align-items:center;gap:5px;color:#64748b;font-size:10px;'>
                    <span style='width:7px;height:7px;border-radius:50%;background:{color};
                                 display:inline-block;flex-shrink:0;'></span>{label}</span>
                <span style='color:#f1f5f9;font-size:11px;font-weight:600;'>{val}%</span>
            </div>"""
        leg_html += "</div>"
        st.markdown(leg_html, unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:#0a1929;border-top:1px solid #1e3a5f;padding:.5rem 2rem;
            display:flex;justify-content:space-between;align-items:center;
            font-size:10px;color:#334155;'>
    <span>PV Digital Twin v2.0 — {config["site"]["name"]}</span>
    <span>Mis a jour : {now.strftime("%d/%m/%Y %H:%M:%S")} | Source : {data["source"]}</span>
</div>
""", unsafe_allow_html=True)
