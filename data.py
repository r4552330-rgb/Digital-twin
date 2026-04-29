import logging
import requests
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Récupération des données pour Digital Twin PV :
    - Open-Meteo (irradiance, température)
    - Blynk (capteurs ESP32)
    """

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, config: dict):
        self.cfg = config
        self.lat = config["site"]["latitude"]
        self.lon = config["site"]["longitude"]
        self.tz = config["site"].get("tz", "Africa/Casablanca")

        blynk = config.get("blynk", {})
        self.blynk_token = blynk.get("token", "")
        self.blynk_server = blynk.get("server", "https://blynk.cloud")
        self.blynk_pins = blynk.get("virtual_pins", {})

    # ─────────────────────────────────────────────
    # 🌤️ 1. MÉTÉO (Open-Meteo)
    # ─────────────────────────────────────────────
    def get_weather(self) -> dict:
        try:
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "current": ["temperature_2m", "shortwave_radiation"],
                "timezone": self.tz,
            }
            r = requests.get(self.OPEN_METEO_URL, params=params, timeout=6)
            r.raise_for_status()
            data = r.json()["current"]
            return {
                "irradiance": data.get("shortwave_radiation", 0),
                "temperature": data.get("temperature_2m", 25),
                "timestamp": datetime.now().isoformat(),
                "source": "open-meteo",
            }
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.warning("Open-Meteo indisponible, fallback simulation : %s", e)
            return self._simulate_weather()

    # ─────────────────────────────────────────────
    # 📡 2. BLYNK (CAPTEURS ESP32)
    # ─────────────────────────────────────────────
    def get_blynk_data(self) -> dict:
        if not self.blynk_token:
            return {}

        results = {}
        for name, pin in self.blynk_pins.items():
            try:
                # ✅ URL Blynk correcte
                r = requests.get(
                    f"{self.blynk_server}/external/api/get",
                    params={"token": self.blynk_token, pin: ""},
                    timeout=5,
                )
                r.raise_for_status()
                results[name] = float(r.text)
            except (requests.RequestException, ValueError) as e:
                logger.warning("Blynk pin %s (%s) inaccessible : %s", pin, name, e)
                continue

        return results

    # ─────────────────────────────────────────────
    # 🔀 3. FUSION DONNÉES (PRIORITÉ CAPTEURS)
    # ─────────────────────────────────────────────
    def get_data(self) -> dict:
        weather = self.get_weather()
        blynk = self.get_blynk_data()

        irradiance = blynk.get("irradiance", weather["irradiance"])
        temperature = blynk.get("temperature", weather["temperature"])

        # Source précise : blynk total / partiel / météo
        if "irradiance" in blynk and "temperature" in blynk:
            source = "blynk"
        elif blynk:
            source = f"blynk+{weather['source']}"
        else:
            source = weather["source"]

        return {
            "irradiance": irradiance,
            "temperature": temperature,
            "source": source,
            "timestamp": weather["timestamp"],
        }

    # ─────────────────────────────────────────────
    # ⚠️ 4. FALLBACK SIMULATION
    # ─────────────────────────────────────────────
    def _simulate_weather(self) -> dict:
        now = datetime.now()
        h = now.hour

        # Soleil uniquement entre 6h et 18h
        if 6 <= h <= 18:
            G = 900 * np.sin(np.pi * (h - 6) / 12)
        else:
            G = 0.0

        T = 25 + np.random.normal(0, 2)

        return {
            "irradiance": round(float(G), 1),
            "temperature": round(float(T), 1),
            "timestamp": now.isoformat(),
            "source": "simulation",
        }
