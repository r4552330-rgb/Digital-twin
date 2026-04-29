"""
config.py — Configuration centralisée du Digital Twin PV
Modifiez ce fichier pour adapter le dashboard à votre installation.
"""

# ─── Site photovoltaïque ──────────────────────────────────────────────────────
SITE = {
    "name": "ENSET Mohammedia — Toiture PV",
    "location": "Mohammedia, Maroc",
    "latitude": 33.686,
    "longitude": -7.383,
    "timezone": "Africa/Casablanca",
    "capacity_kwp": 10.0,          # Puissance crête installée (kWp)
    "n_panels": 25,                # Nombre total de panneaux
    "series_per_string": 5,        # Panneaux en série par string
    "strings_per_mppt": 5,         # Strings en parallèle par MPPT
    "n_mppt": 1,                   # Nombre de trackers MPPT
    "commissioning_date": "2023-09-01",
}

# ─── Panneau PV ───────────────────────────────────────────────────────────────
PANEL = {
    "model": "Jinko Solar JKM400M-72HL4",
    "pmp_stc": 400,        # Puissance MPP STC (W)
    "voc": 49.5,           # Tension circuit ouvert STC (V)
    "isc": 10.2,           # Courant court-circuit STC (A)
    "vmp": 41.8,           # Tension MPP STC (V)
    "imp": 9.57,           # Courant MPP STC (A)
    "eta_stc": 0.205,      # Rendement STC (20.5%)
    "area_m2": 1.954,      # Surface active (m²)
    "noct": 45,            # NOCT (°C)
    "alpha_isc": 0.00048,  # Coefficient T° courant (/°C)
    "beta_voc": -0.00280,  # Coefficient T° tension (/°C)
    "gamma_pmp": -0.00350, # Coefficient T° puissance (/°C)
    "degradation_annual": 0.005,  # Dégradation annuelle (0.5%/an)
}

# ─── Onduleur ─────────────────────────────────────────────────────────────────
INVERTER = {
    "model": "Huawei SUN2000-10KTL-M1",
    "p_rated_kw": 10.0,
    "eta_euro": 0.977,     # Rendement européen
    "mppt_range_v": (200, 560),   # Plage tension MPPT
    "p_own_consumption_w": 25,    # Consommation propre
}

# ─── Pertes système ───────────────────────────────────────────────────────────
LOSSES = {
    "dc_wiring": 0.01,        # Câblage DC (1%)
    "mismatch": 0.02,         # Mismatch panneaux (2%)
    "soiling": 0.015,         # Salissures (1.5%)
    "shading": 0.005,         # Ombrage résiduel (0.5%)
    "dc_total": 0.05,         # Total pertes DC = somme ci-dessus
    "ac_wiring": 0.005,       # Câblage AC (0.5%)
    "transformer": 0.02,      # Transformateur (2%)
}

# ─── MQTT (optionnel) ─────────────────────────────────────────────────────────
MQTT = {
    "enabled": False,          # Mettre True pour activer
    "host": "localhost",
    "port": 1883,
    "username": "",
    "password": "",
    "topics": {
        "irradiance": "pv/sensors/irradiance",
        "temp_module": "pv/sensors/temp_module",
        "p_dc": "pv/inverter/p_dc",
        "p_ac": "pv/inverter/p_ac",
        "energy_day": "pv/inverter/energy_day",
    },
}

# ─── Blynk IoT (optionnel) ───────────────────────────────────────────────────
BLYNK = {
    "enabled": False,
    "token": "YOUR_BLYNK_TOKEN",
    "server": "https://blynk.cloud",
    "virtual_pins": {
        "irradiance": "V0",
        "temp_module": "V1",
        "p_dc": "V2",
        "p_ac": "V3",
    },
}

# ─── Seuils d'alerte ─────────────────────────────────────────────────────────
THRESHOLDS = {
    "pr_warning": 0.70,          # PR < 70% → alerte orange
    "pr_critical": 0.55,         # PR < 55% → alerte rouge
    "temp_cell_warning": 70,     # T° cellule > 70°C → alerte orange
    "temp_cell_critical": 85,    # T° cellule > 85°C → alerte rouge
    "irradiance_min": 50,        # En dessous → nuit / pas de production
    "energy_min_daily_kwh": 5,   # Production journalière minimale attendue
}

# ─── Agrégation CONFIG ────────────────────────────────────────────────────────
CONFIG = {
    "site": SITE,
    "panel": PANEL,
    "inverter": INVERTER,
    "losses": LOSSES,
    "mqtt": MQTT,
    "blynk": BLYNK,
}
