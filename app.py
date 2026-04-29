import math
from pathlib import Path
from datetime import datetime

import streamlit as st
import yaml
import plotly.graph_objects as go

from model import PVModel
from data import DataFetcher

# ── CONSTANTES ─────────────────────────────────────────
BASE = Path(__file__).parent
ASSETS = BASE / "assets"
SCENE_IMG = ASSETS / "Scene_enset.png"
CONFIG_PATH = BASE / "config.yaml"

# ── CONFIGURATION ──────────────────────────────────────
with open(CONFIG_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

pv = PVModel(config)
fetcher = DataFetcher(config)

# ── THÈME ─────────────────────────────────────────────
if "dark" not in st.session_state:
    st.session_state.dark = True   # thème sombre par défaut (cohérent avec l'ancien dashboard)

def toggle_theme():
    st.session_state.dark = not st.session_state.dark

# Appliquer les couleurs selon le thème
if st.session_state.dark:
    BG = "#0f172a"
    CARD_BG = "#1e293b"
    TEXT = "#f1f5f9"
    SECONDARY = "#94a3b8"
    ACCENT = "#f59e0b"
    GREEN = "#4ade80"
    BLUE = "#3b82f6"
    RED = "#ef4444"
else:
    BG = "#f8fafc"
    CARD_BG = "#ffffff"
    TEXT = "#0f172a"
    SECONDARY = "#64748b"
    ACCENT = "#d97706"
    GREEN = "#16a34a"
    BLUE = "#2563eb"
    RED = "#dc2626"

# ── CSS GLOBAL ─────────────────────────────────────────
st.markdown(f"""
<style>
body, .stApp {{
    background-color: {BG};
    color: {TEXT};
}}
.block-container {{
    padding: 1rem 2rem;
}}
.card {{
    background-color: {CARD_BG};
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 0.8rem;
}}
.metric-label {{
    font-size: 0.8rem;
    color: {SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.metric-value {{
    font-size: 2rem;
    font-weight: 700;
    color: {TEXT};
    line-height: 1.2;
}}
.sidebar .sidebar-content {{
    background-color: {CARD_BG};
}}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☀️ PV Digital Twin")
    st.caption("Smart Solar Monitoring")

    st.button(
        "🌙 Mode sombre" if not st.session_state.dark else "☀️ Mode clair",
        on_click=toggle_theme,
        use_container_width=True
    )

    st.divider()

    menu = st.radio(
        "Navigation",
        ["Vue d'ensemble", "Jumeau numérique", "Performance", "Équipements", "Alarmes", "Analyses"],
        index=0,
        key="nav_menu"
    )

    st.divider()
    st.markdown(f"**Site** : {config['site']['name']}")
    cap_dc = config["array"]["n_panels"] * config["panel"]["pmp_stc"] / 1000.0
    st.metric("Capacité DC", f"{cap_dc:.2f} kWp")

# ── RÉCUPÉRATION DES DONNÉES ──────────────────────────
try:
    data = fetcher.get_data()
except Exception:
    data = {"irradiance": 0.0, "temperature": 25.0}

res = pv.compute(data["irradiance"], data["temperature"])
now = datetime.now()

# ── PAGE PRINCIPALE (Vue d'ensemble) ───────────────────
if menu == "Vue d'ensemble":
    st.markdown("## Vue globale")

    # Météo et indicateurs principaux
    meteo_label = "Ensoleillé" if data["irradiance"] > 600 else ("Nuageux" if data["irradiance"] > 200 else "Couvert")
    meteo_emoji = "☀️" if data["irradiance"] > 600 else ("⛅" if data["irradiance"] > 200 else "☁️")

    col_meteo, col_pac, col_prod, col_pr = st.columns(4)

    with col_meteo:
        st.markdown(f"<div class='card' style='text-align:center;'>"
                    f"<div style='font-size:2.5rem;'>{meteo_emoji}</div>"
                    f"<div class='metric-label'>{meteo_label}</div>"
                    f"<div class='metric-value'>{data['temperature']:.1f}°C</div>"
                    f"<div class='metric-label'>Irradiance {data['irradiance']:.0f} W/m²</div>"
                    f"</div>", unsafe_allow_html=True)

    with col_pac:
        st.markdown(f"<div class='card'>"
                    f"<div class='metric-label'>Puissance AC</div>"
                    f"<div class='metric-value'>{res['p_ac_kw']:.2f} kW</div>"
                    f"</div>", unsafe_allow_html=True)

    with col_prod:
        # Production journalière estimée (cumul horaire simulé)
        prod_jour = 0
        for h in range(24):
            irr = 900 * math.sin(math.pi * (h - 6) / 12) if 6 <= h <= 18 else 0
            prod_jour += pv.compute(irr, 25)["p_ac_kw"]
        st.markdown(f"<div class='card'>"
                    f"<div class='metric-label'>Production jour</div>"
                    f"<div class='metric-value'>{prod_jour:.1f} kWh</div>"
                    f"</div>", unsafe_allow_html=True)

    with col_pr:
        pr = res.get('performance_ratio', 0)
        st.markdown(f"<div class='card'>"
                    f"<div class='metric-label'>Performance Ratio</div>"
                    f"<div class='metric-value'>{pr:.2f}</div>"
                    f"</div>", unsafe_allow_html=True)

    # ── CORPS PRINCIPAL ───────────────────────────────
    col_left, col_right = st.columns([3, 2], gap="medium")

    with col_left:
        st.markdown("### Jumeau numérique")
        # Affichage de la scène avec des indicateurs de statut superposés
        if SCENE_IMG.exists():
            st.image(str(SCENE_IMG), use_container_width=True)
        else:
            st.warning("Image de scène introuvable. Placez 'Scene_enset.png' dans le dossier assets.")
            # Version SVG de secours (dessin simplifié des panneaux)
            # (Vous pouvez intégrer le SVG des panneaux ici si besoin)

        st.markdown("### Flux d'énergie")
        flux_cols = st.columns(4)
        flux_data = [
            ("PV", f"{res['p_dc_kw']:.2f} kW", GREEN),
            ("Onduleur", f"{res['p_ac_kw']:.2f} kW", BLUE),
            ("Charge", "0.00 kW", SECONDARY),
            ("Réseau", f"{res['p_ac_kw']:.2f} kW", GREEN if res['p_ac_kw'] > 0 else SECONDARY),
        ]
        for col, (label, val, colr) in zip(flux_cols, flux_data):
            col.markdown(f"""
            <div class='card' style='text-align:center;'>
                <div style='color:{colr}; font-size:1.2rem; font-weight:600;'>{label}</div>
                <div style='font-size:1.5rem; font-weight:700; margin-top:4px;'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

        # État des équipements (donut)
        st.markdown("### État des équipements")
        # Calcul basé sur un état fictif pour l'exemple :
        # On peut simuler un état par panneau avec le modèle, ici on utilise un résumé global
        fig_state = go.Figure(go.Pie(
            labels=["Normal", "Attention", "Alarme"],
            values=[10, 2, 0],      # 12 panneaux, 2 en attention (ex. panneau 2)
            hole=0.6,
            marker=dict(colors=[GREEN, ACCENT, RED]),
            textinfo="none"
        ))
        fig_state.update_layout(
            margin=dict(l=0, r=0, t=10, b=10),
            height=200,
            paper_bgcolor=CARD_BG,
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(orientation="h", font=dict(color=SECONDARY))
        )
        st.plotly_chart(fig_state, width="stretch")

    with col_right:
        st.markdown("### Production & Performance")

        # Courbe de puissance journalière simulée
        hours = list(range(24))
        prod_curve = []
        irr_curve = []
        for h in hours:
            irr = 900 * math.sin(math.pi * (h - 6) / 12) if 6 <= h <= 18 else 0
            irr_curve.append(max(0, irr))
            sim = pv.compute(irr, 25)
            prod_curve.append(sim["p_ac_kw"])

        fig_prod = go.Figure()
        fig_prod.add_trace(go.Scatter(
            x=hours, y=prod_curve,
            fill='tozeroy',
            line=dict(color=GREEN),
            name="Production (kW)"
        ))
        fig_prod.add_trace(go.Scatter(
            x=hours, y=[i/1000 for i in irr_curve],
            yaxis="y2",
            line=dict(color=BLUE, dash="dot"),
            name="Irradiance / 1000"
        ))
        fig_prod.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickvals=[0,6,12,18,24], ticktext=["00h","06h","12h","18h","24h"]),
            yaxis=dict(title="kW"),
            yaxis2=dict(overlaying="y", side="right", title="W/m²"),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_prod, width="stretch")

        # Pertes calculées à partir de la config
        st.markdown("### Répartition des pertes")
        pertes = {
            "Température": round(pv.compute(1000, 25)["p_ac_kw"] - pv.compute(1000, 45)["p_ac_kw"], 2),  # effet T
            "Câblage DC": round(config["losses"]["dc_total"] * 100, 1),
            "Onduleur": round((1 - config["losses"]["ac_efficiency"]) * 100, 1),
        }
        fig_pertes = go.Figure(go.Pie(
            labels=list(pertes.keys()),
            values=list(pertes.values()),
            hole=0.4,
            marker=dict(colors=[ACCENT, BLUE, RED])
        ))
        fig_pertes.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(font=dict(color=SECONDARY))
        )
        st.plotly_chart(fig_pertes, width="stretch")

        # Alarmes factices
        st.markdown("### Alarmes récentes")
        st.markdown(f"""
        <div class='card'>
            <div style='color:{RED}; font-weight:600;'>⚠️ Défaut onduleur</div>
            <div style='color:{SECONDARY}; font-size:0.8rem;'>Aujourd'hui 08:23</div>
        </div>
        <div class='card'>
            <div style='color:{ACCENT}; font-weight:600;'>Température cellule élevée</div>
            <div style='color:{SECONDARY}; font-size:0.8rem;'>Aujourd'hui 12:05</div>
        </div>
        """, unsafe_allow_html=True)

# ── PIED DE PAGE ────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center; color:{SECONDARY}; font-size:0.8rem; margin-top:2rem;'>
    PV Digital Twin v2.1 — {config["site"]["name"]} — {now.strftime("%d/%m/%Y %H:%M:%S")}
</div>
""", unsafe_allow_html=True)
