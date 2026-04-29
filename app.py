import math
from pathlib import Path
from datetime import datetime

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

st.set_page_config(
    page_title="PV Digital Twin",
    page_icon=":sun:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SESSION STATE ──────────────────────────────────────────────────────────
if "page"   not in st.session_state: st.session_state.page   = "Vue d'ensemble"
if "period" not in st.session_state: st.session_state.period = "Jour"

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background:#0f172a !important; border-right:1px solid #1e293b; }
[data-testid="stSidebar"] * { color:#94a3b8 !important; }
.main .block-container { padding:0 !important; max-width:100% !important; }
#MainMenu, footer, header { visibility:hidden; }
.stDeployButton { display:none; }
div[data-testid="stHorizontalBlock"] { gap:0 !important; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    # En-tête
    st.markdown("""
    <div style='padding:1.2rem 0.5rem 1.5rem;border-bottom:1px solid #1e293b;margin-bottom:1rem;'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <div style='width:38px;height:38px;background:#f59e0b;border-radius:8px;
                        display:flex;align-items:center;justify-content:center;'>PV</div>
            <div>
                <div style='color:#f1f5f9!important;font-weight:600;font-size:15px;'>PV Digital Twin</div>
                <div style='color:#64748b!important;font-size:11px;'>Smart Solar Monitoring</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("Accueil",   "Vue d'ensemble", False),
        ("Jumeau",    "Jumeau numérique", False),
        ("Perf.",     "Performance", False),
        ("Equip.",    "Equipements", False),
        ("Alarmes",   "Alarmes", True),
        ("Analyses",  "Analyses", False),
        ("Rapports",  "Rapports", False),
        ("Meteo",     "Meteo", False),
        ("Param.",    "Parametres", False),
    ]
    for label, name, has_badge in nav_items:
        button_label = f"{label}  [2]" if has_badge else label
        if st.button(button_label, key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name

    st.markdown("""<div style='margin-top:1.5rem;padding-top:1rem;border-top:1px solid #1e293b;'>
        <div style='color:#475569!important;font-size:10px;text-transform:uppercase;
                    letter-spacing:.1em;padding:0 0.5rem;margin-bottom:0.4rem;'>SITE</div>
    </div>""", unsafe_allow_html=True)

    st.selectbox("", [config["site"]["name"]], label_visibility="collapsed")
    cap_dc = config["site"]["n_panels"] * config["panel"]["pmp_stc"] / 1000
    st.markdown(f"""
    <div style='padding:0.3rem 0.5rem;'>
        <div style='color:#475569!important;font-size:10px;'>Capacite DC</div>
        <div style='color:#94a3b8!important;font-size:13px;font-weight:600;'>{cap_dc:.2f} MWp</div>
    </div>""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────
data = fetcher.get_data()
res  = pv.compute(data["irradiance"], data["temperature"])
now  = datetime.now()

hours     = list(range(25))
p_ac_curve = [
    pv.compute(900 * math.sin(math.pi * (h-6) / 12) if 6 <= h <= 18 else 0.0, 25)["p_ac_kw"]
    for h in hours
]
irr_curve = [max(0.0, 950 * math.sin(math.pi * (h-6) / 12)) if 6 <= h <= 18 else 0.0 for h in hours]

prod_jour  = round(sum(p_ac_curve) / 1000, 2)
co2_evite  = round(res["p_ac_kw"] * 0.7, 0)
rend_spec  = round(prod_jour * 1000 / (cap_dc * 1000), 2)

meteo_label = "Ensoleille" if data["irradiance"] > 600 else ("Nuageux" if data["irradiance"] > 200 else "Couvert")
meteo_symbol = "Soleil" if data["irradiance"] > 600 else ("Nuage" if data["irradiance"] > 200 else "Pluie")

# Puissance nominale AC estimée
p_rated_ac_kw = config["site"]["n_panels"] * config["panel"]["pmp_stc"] / 1000 * config["losses"]["ac_efficiency"]

# ── BANDEAU HEADER ─────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:#0f172a;padding:.9rem 2rem;display:flex;align-items:center;
            border-bottom:1px solid #1e293b;flex-wrap:wrap;gap:.5rem;'>
    <div style='display:flex;align-items:center;gap:12px;padding-right:2rem;
                border-right:1px solid #1e293b;margin-right:2rem;min-width:200px;'>
        <div style='font-size:34px;line-height:1;'>[{meteo_symbol}]</div>
        <div>
            <div style='color:#f1f5f9;font-weight:600;font-size:14px;'>{meteo_label}</div>
            <div style='color:#f59e0b;font-size:24px;font-weight:700;line-height:1.1;'>
                {data["temperature"]:.0f}°C</div>
            <div style='color:#64748b;font-size:10px;'>Irradiance {data["irradiance"]:.0f} W/m²</div>
        </div>
    </div>
    <div style='padding:0 2rem;border-right:1px solid #1e293b;margin-right:2rem;'>
        <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.06em;'>Puissance AC</div>
        <div style='color:#4ade80;font-size:26px;font-weight:700;line-height:1.1;'>{res["p_ac_kw"]}</div>
        <div style='color:#94a3b8;font-size:10px;'>{res["p_ac_kw"]/p_rated_ac_kw*100:.0f}% de la capacite</div>
    </div>
    <div style='padding:0 2rem;border-right:1px solid #1e293b;margin-right:2rem;'>
        <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.06em;'>Production du jour</div>
        <div style='color:#f1f5f9;font-size:26px;font-weight:700;line-height:1.1;'>{prod_jour}</div>
        <div style='color:#94a3b8;font-size:10px;'>MWh</div>
    </div>
    <div style='padding:0 2rem;border-right:1px solid #1e293b;margin-right:2rem;'>
        <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.06em;'>Production totale</div>
        <div style='color:#f1f5f9;font-size:26px;font-weight:700;line-height:1.1;'>{res["p_ac_kw"]*1.25:.2f}</div>
        <div style='color:#94a3b8;font-size:10px;'>GWh</div>
    </div>
    <div style='padding:0 2rem;border-right:1px solid #1e293b;margin-right:2rem;'>
        <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.06em;'>CO2 evite</div>
        <div style='color:#f1f5f9;font-size:26px;font-weight:700;line-height:1.1;'>{co2_evite:.0f}</div>
        <div style='color:#94a3b8;font-size:10px;'>t</div>
    </div>
    <div style='margin-left:auto;text-align:right;'>
        <div style='color:#94a3b8;font-size:12px;'>{now.strftime("%d %b %Y")}</div>
        <div style='color:#f59e0b;font-size:20px;font-weight:700;font-family:monospace;'>{now.strftime("%H:%M:%S")}</div>
        <div style='margin-top:6px;'>
            <select style='background:#1e293b;color:#94a3b8;border:1px solid #334155;
                           border-radius:6px;padding:2px 8px;font-size:11px;'>
                <option>Periode</option><option selected>Aujourd'hui</option>
                <option>Semaine</option><option>Mois</option>
            </select>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CORPS PRINCIPAL ─────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="small")

# ═══════════════════════ COLONNE GAUCHE ════════════════════════════════════
with col_left:
    # Jumeau numerique
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                margin:1rem 0 0 1rem;padding:1rem 1rem 0;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;'>
            <span style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.08em;'>
                JUMEAU NUMERIQUE — VUE 3D</span>
            <div style='display:flex;gap:8px;'>
                <div style='width:22px;height:22px;border-radius:50%;border:2px solid #3b82f6;'></div>
                <div style='width:22px;height:22px;border-radius:50%;border:2px solid #334155;'></div>
                <div style='width:22px;height:22px;border-radius:50%;border:2px solid #334155;'></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Dropdowns overlay simules
    overlay_cols = st.columns([1, 3])
    with overlay_cols[0]:
        vue_mode = st.selectbox("", ["Vue libre", "Irradiance", "Temperature", "Production", "Pertes"],
                                label_visibility="collapsed")

    # SVG panneau PV
    n = config["site"]["n_panels"]
    panel_svg = ""
    cols_pv, rows_pv = 4, math.ceil(n / 4)
    status_colors = ["#22c55e"] * n
    if n > 3: status_colors[2] = "#f59e0b"  # simuler 1 panneau en attention

    for r in range(rows_pv):
        for c in range(4):
            idx = r * 4 + c
            if idx >= n: break
            x, y = 30 + c * 88, 20 + r * 58
            col_fill = "#1a3a6e" if status_colors[idx] == "#22c55e" else "#3a2a10"
            panel_svg += f"""
            <rect x="{x}" y="{y}" width="72" height="46" rx="3"
                  fill="{col_fill}" stroke="{status_colors[idx]}" stroke-width="1.2" opacity=".85"/>
            <line x1="{x+24}" y1="{y}" x2="{x+24}" y2="{y+46}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x+48}" y1="{y}" x2="{x+48}" y2="{y+46}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x}"    y1="{y+15}" x2="{x+72}" y2="{y+15}" stroke="#2255aa" stroke-width=".5"/>
            <line x1="{x}"    y1="{y+31}" x2="{x+72}" y2="{y+31}" stroke="#2255aa" stroke-width=".5"/>
            <circle cx="{x+36}" cy="{y+23}" r="5" fill="{status_colors[idx]}" opacity=".9"/>
            <circle cx="{x+36}" cy="{y+23}" r="10" fill="{status_colors[idx]}" opacity=".2"/>
            """

    st.markdown(f"""
    <div style='background:#060f1e;border:1px solid #1e293b;border-radius:0 0 10px 10px;
                margin:0 0 0 1rem;padding:.5rem;'>
        <svg viewBox="0 0 410 {rows_pv*58+80}" style='width:100%;border-radius:6px;'>
            <rect width="410" height="{rows_pv*58+80}" fill="#060f1e"/>
            <rect x="0" y="{rows_pv*58+40}" width="410" height="40" fill="#0a1929" opacity=".6"/>
            <rect x="305" y="{rows_pv*58-30}" width="100" height="{rows_pv*58+30-rows_pv*58+60}" rx="4"
                  fill="#0f1f35" stroke="#1e3a5f" stroke-width="1"/>
            {panel_svg}
            <rect x="315" y="{rows_pv*58}" width="45" height="55" rx="4"
                  fill="#1e3a5f" stroke="#3b82f6" stroke-width="1"/>
            <text x="337" y="{rows_pv*58+35}" text-anchor="middle" fill="#60a5fa" font-size="7"
                  font-family="monospace">MPPT</text>
            <circle cx="337" cy="{rows_pv*58+18}" r="7" fill="#22c55e" opacity=".9"/>
        </svg>
        <div style='display:flex;gap:16px;padding:8px 12px;border-top:1px solid #1e293b;
                    font-size:11px;color:#94a3b8;'>
            <span>[Normal]</span><span>[Attention]</span>
            <span>[Alarme]</span><span>[Maintenance]</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Flux d'energie
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                margin:1rem 0 0.5rem 1rem;padding:1rem 1rem .8rem;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.08em;margin-bottom:.8rem;'>
            FLUX D'ENERGIE</div>
    </div>""", unsafe_allow_html=True)

    flux_data = [
        ("SOURCE", "PANNEAUX PV",  f"{res['p_dc_kw']:.2f} kW", "#f59e0b"),
        ("MPPT",   "MPPT / DC",    f"{res['p_dc_kw']:.2f} kW", "#3b82f6"),
        ("OND",    "ONDULEUR",     f"{res['p_ac_kw']:.2f} kW", "#8b5cf6"),
        ("RESEAU", "RESEAU",       f"{res['p_ac_kw']:.2f} kW", "#22c55e"),
    ]
    fc = st.columns(4)
    for col, (sym, label, val, color) in zip(fc, flux_data):
        with col:
            st.markdown(f"""
            <div style='background:#060f1e;border:1px solid #1e293b;border-radius:10px;
                        padding:12px 8px;text-align:center;margin:0 2px 0 4px;'>
                <div style='font-size:22px;margin-bottom:4px;'>{sym}</div>
                <div style='color:#475569;font-size:9px;letter-spacing:.07em;'>{label}</div>
                <div style='color:{color};font-size:13px;font-weight:700;margin-top:3px;'>{val}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════ COLONNE DROITE ════════════════════════════════════
with col_right:
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                margin:1rem 1rem 0 0;padding:1rem 1rem 0;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.08em;margin-bottom:.8rem;'>
            PRODUCTION & PERFORMANCE</div>
    </div>""", unsafe_allow_html=True)

    # Onglets periode
    p_cols = st.columns(4)
    for col, period in zip(p_cols, ["Jour", "Semaine", "Mois", "Annee"]):
        with col:
            if st.button(period, key=f"p_{period}", use_container_width=True):
                st.session_state.period = period

    # Metriques
    m1, m2, m3 = st.columns(3)
    for col, label, val, unit in zip(
        [m1, m2, m3],
        ["Production", "Rendement specifique", "Performance Ratio"],
        [f"{prod_jour}", f"{rend_spec}", f"{res['performance_ratio']*100:.1f}"],
        ["MWh", "kWh/kWp", "%"],
    ):
        with col:
            st.markdown(f"""
            <div style='background:#060f1e;border-radius:8px;padding:10px 8px;margin:0 2px;'>
                <div style='color:#64748b;font-size:9px;line-height:1.3;'>{label}</div>
                <div style='color:#f1f5f9;font-size:18px;font-weight:700;line-height:1.1;margin-top:2px;'>{val}</div>
                <div style='color:#64748b;font-size:9px;'>{unit}</div>
            </div>""", unsafe_allow_html=True)

    # Graphique courbes
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
                   tickvals=[0,4,8,12,16,20,24],
                   ticktext=["00:00","04:00","08:00","12:00","16:00","20:00","24:00"]),
        yaxis=dict(tickfont=dict(color="#475569", size=8), gridcolor="#1e293b"),
        yaxis2=dict(overlaying="y", side="right", tickfont=dict(color="#475569", size=8), showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Repartition des pertes
    st.markdown("""
    <div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;
                margin:.5rem 1rem 0 0;padding:1rem 1rem .5rem;'>
        <div style='color:#3b82f6;font-weight:700;font-size:12px;letter-spacing:.08em;margin-bottom:.5rem;'>
            REPARTITION DES PERTES (AUJOURD'HUI)</div>
    </div>""", unsafe_allow_html=True)

    losses = [
        ("#f59e0b", "Pertes d'irradiance",  6.2),
        ("#3b82f6", "Pertes de temperature", 4.1),
        ("#8b5cf6", "Pertes onduleur",       round((1 - config["losses"]["ac_efficiency"]) * 100, 1)),
        ("#ef4444", "Pertes DC cablage",     round(config["losses"]["dc_total"] * 100, 1)),
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
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;'>
                <span style='display:flex;align-items:center;gap:5px;color:#94a3b8;font-size:10px;'>
                    <span style='width:7px;height:7px;border-radius:50%;background:{color};
                                 display:inline-block;flex-shrink:0;'></span>{label}</span>
                <span style='color:#f1f5f9;font-size:11px;font-weight:600;'>{val}%</span>
            </div>"""
        leg_html += "</div>"
        st.markdown(leg_html, unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:#0a1929;border-top:1px solid #1e293b;padding:.5rem 2rem;
            display:flex;justify-content:space-between;align-items:center;
            margin-top:.5rem;font-size:10px;color:#475569;'>
    <span>PV Digital Twin v2.0 — {config["site"]["name"]}</span>
    <span>Mis a jour : {now.strftime("%d/%m/%Y %H:%M:%S")} | Source : Open-Meteo + IoT</span>
</div>
""", unsafe_allow_html=True)
