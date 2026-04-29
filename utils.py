"""
utils.py — Fonctions utilitaires du Digital Twin PV
"""

import time
from typing import Union


# ─── Formatage des valeurs ────────────────────────────────────────────────────

def format_power(kw: float, decimals: int = 2) -> str:
    """Formate une puissance en kW avec adaptation kW/MW."""
    if kw >= 1000:
        return f"{kw/1000:.{decimals}f} MW"
    return f"{kw:.{decimals}f}"


def format_energy(kwh: float, decimals: int = 1) -> str:
    """Formate une énergie en kWh avec adaptation MWh."""
    if kwh >= 1000:
        return f"{kwh/1000:.{decimals}f} MWh"
    return f"{kwh:.{decimals}f}"


def format_currency(amount: float, currency: str = "MAD") -> str:
    """Formate un montant monétaire."""
    return f"{amount:,.0f} {currency}"


def format_co2(kg: float) -> str:
    """Formate une quantité de CO₂ en kg ou tonnes."""
    if kg >= 1000:
        return f"{kg/1000:.2f} t CO₂"
    return f"{kg:.1f} kg CO₂"


# ─── Couleurs de performance ──────────────────────────────────────────────────

def get_performance_color(pr: float, thresholds: dict) -> str:
    """
    Retourne une couleur hex selon le Performance Ratio.

    - Vert   : PR ≥ seuil warning
    - Orange : PR entre critical et warning
    - Rouge  : PR < seuil critical
    """
    if pr >= thresholds["pr_warning"]:
        return "#4ade80"   # vert
    elif pr >= thresholds["pr_critical"]:
        return "#fbbf24"   # orange
    else:
        return "#f87171"   # rouge


def get_temp_color(temp_c: float, thresholds: dict) -> str:
    """Couleur selon la température de cellule."""
    if temp_c >= thresholds["temp_cell_critical"]:
        return "#f87171"
    elif temp_c >= thresholds["temp_cell_warning"]:
        return "#fbbf24"
    return "#4ade80"


# ─── Cache TTL ────────────────────────────────────────────────────────────────

def cache_ttl(seconds: int) -> int:
    """
    Compatibilité avec st.cache_data(ttl=...).
    Retourne le TTL en secondes.
    """
    return seconds


# ─── Constantes physiques & facteurs ─────────────────────────────────────────

CONSTANTS = {
    # Facteur d'émission CO₂ réseau Maroc (kgCO₂/kWh) — ONEE 2022
    "co2_factor_ma": 0.233,

    # Tarif électricité moyen réseau Maroc (MAD/kWh) — BT 2024
    "electricity_tariff_mad": 1.32,

    # Irradiation globale horizontale annuelle Mohammedia (kWh/m²/an)
    "ghi_annual_mohammedia": 1890,

    # Durée de vie typique installation PV (ans)
    "lifetime_years": 25,
}


# ─── Calcul économique ────────────────────────────────────────────────────────

def compute_savings(energy_kwh: float, tariff: float = None) -> dict:
    """
    Calcule les économies et le CO₂ évité pour une quantité d'énergie produite.

    Args:
        energy_kwh : énergie produite (kWh)
        tariff     : tarif électricité (MAD/kWh), utilise valeur par défaut si None

    Returns:
        dict avec savings_mad, co2_avoided_kg, trees_equivalent
    """
    if tariff is None:
        tariff = CONSTANTS["electricity_tariff_mad"]

    savings = energy_kwh * tariff
    co2 = energy_kwh * CONSTANTS["co2_factor_ma"]
    trees = co2 / 21.77  # 1 arbre absorbe ≈ 21.77 kgCO₂/an

    return {
        "savings_mad": round(savings, 2),
        "co2_avoided_kg": round(co2, 2),
        "trees_equivalent": round(trees, 1),
    }


# ─── Diagnostic simple ────────────────────────────────────────────────────────

def diagnose(pr: float, temp_cell: float, thresholds: dict) -> list[dict]:
    """
    Génère une liste de diagnostics basés sur les paramètres actuels.

    Returns:
        Liste de dicts : {level, message, recommendation}
    """
    alerts = []

    if pr < thresholds["pr_critical"]:
        alerts.append({
            "level": "CRITIQUE",
            "message": f"Performance Ratio très bas : {pr:.1%}",
            "recommendation": "Vérifier ombrage, salissures importantes ou défaut d'onduleur.",
        })
    elif pr < thresholds["pr_warning"]:
        alerts.append({
            "level": "ATTENTION",
            "message": f"Performance Ratio dégradé : {pr:.1%}",
            "recommendation": "Planifier un nettoyage et vérifier les connexions DC.",
        })

    if temp_cell >= thresholds["temp_cell_critical"]:
        alerts.append({
            "level": "CRITIQUE",
            "message": f"Température cellule critique : {temp_cell:.1f}°C",
            "recommendation": "Vérifier la ventilation et l'état des panneaux.",
        })
    elif temp_cell >= thresholds["temp_cell_warning"]:
        alerts.append({
            "level": "ATTENTION",
            "message": f"Température cellule élevée : {temp_cell:.1f}°C",
            "recommendation": "Pertes thermiques importantes, performances réduites normalement.",
        })

    return alerts
