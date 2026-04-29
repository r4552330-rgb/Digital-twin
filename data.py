"""
data.py — Récupération des données externes
Sources :
  - Open-Meteo API  : météo temps réel & historique (gratuit, no key)
  - MQTT/Blynk      : données IoT capteurs (optionnel)
  - Fichiers locaux : CSV de fallback
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Agrégateur de données pour le Digital Twin PV."""

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_HIST = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, config: dict):
        self.cfg = config
        self.lat = config["site"]["latitude"]
        self.lon = config["site"]["longitude"]
        self._cache: dict = {}

    # ─── Météo temps réel ─────────────────────────────────────────────────
    def get_weather_data(self) -> dict:
        """
        Récupère les conditions météo actuelles via Open-Meteo.

        Returns:
            dict : irradiance (W/m²), temperature (°C), wind_speed (km/h),
                   cloud_cover (%), timestamp
        """
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": [
                "temperature_2m",
                "wind_speed_10m",
                "cloud_cover",
                "shortwave_radiation",
            ],
            "timezone": self.cfg["site"].get("timezone", "Africa/Casablanca"),
        }
        try:
            resp = requests.get(self.OPEN_METEO_URL, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json().get("current", {})
            return {
                "irradiance": data.get("shortwave_radiation", 0),
                "temperature": data.get("temperature_2m", 25),
                "wind_speed": data.get("wind_speed_10m", 0),
                "cloud_cover": data.get("cloud_cover", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "open-meteo",
            }
        except requests.RequestException as e:
            logger.warning(f"Open-Meteo indisponible : {e}. Données simulées utilisées.")
            return self._simulate_weather()

    # ─── Historique météo ─────────────────────────────────────────────────
    def get_historical_data(self, days: int = 7) -> pd.DataFrame:
        """
        Récupère l'historique météo horaire via Open-Meteo Archive.

        Args:
            days : nombre de jours d'historique

        Returns:
            DataFrame avec colonnes : datetime, irradiance, temperature, wind_speed
        """
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)

        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "hourly": ["temperature_2m", "shortwave_radiation", "wind_speed_10m"],
            "timezone": self.cfg["site"].get("timezone", "Africa/Casablanca"),
        }
        try:
            resp = requests.get(self.OPEN_METEO_HIST, params=params, timeout=12)
            resp.raise_for_status()
            hourly = resp.json().get("hourly", {})
            df = pd.DataFrame({
                "datetime": pd.to_datetime(hourly.get("time", [])),
                "irradiance": hourly.get("shortwave_radiation", []),
                "temperature": hourly.get("temperature_2m", []),
                "wind_speed": hourly.get("wind_speed_10m", []),
            })
            df["irradiance"] = df["irradiance"].clip(lower=0)
            return df
        except requests.RequestException as e:
            logger.warning(f"Open-Meteo Archive indisponible : {e}. Simulation.")
            return self._simulate_historical(days)

    # ─── MQTT / Blynk IoT (optionnel) ────────────────────────────────────
    def get_iot_data(self) -> Optional[dict]:
        """
        Lit les dernières valeurs depuis le broker MQTT ou l'API Blynk.
        Retourne None si le broker n'est pas configuré ou inaccessible.
        """
        broker_cfg = self.cfg.get("mqtt", {})
        if not broker_cfg.get("enabled", False):
            return None

        try:
            import paho.mqtt.client as mqtt
            data = {}
            client = mqtt.Client()

            def on_message(c, u, msg):
                data[msg.topic] = float(msg.payload.decode())

            client.on_message = on_message
            client.connect(broker_cfg["host"], broker_cfg.get("port", 1883), keepalive=5)

            topics = broker_cfg.get("topics", {})
            for key, topic in topics.items():
                client.subscribe(topic)

            client.loop_start()
            import time; time.sleep(2)
            client.loop_stop()
            client.disconnect()
            return data

        except Exception as e:
            logger.warning(f"MQTT inaccessible : {e}")
            return None

    # ─── Blynk HTTP API ───────────────────────────────────────────────────
    def get_blynk_data(self) -> Optional[dict]:
        """Lecture via l'API HTTP Blynk (alternative à MQTT)."""
        blynk = self.cfg.get("blynk", {})
        if not blynk.get("enabled", False):
            return None

        token = blynk.get("token", "")
        base = blynk.get("server", "https://blynk.cloud")
        pins = blynk.get("virtual_pins", {})

        results = {}
        for name, pin in pins.items():
            try:
                url = f"{base}/external/api/get?token={token}&{pin}"
                r = requests.get(url, timeout=5)
                results[name] = float(r.text)
            except Exception:
                pass
        return results if results else None

    # ─── Simulation fallback ──────────────────────────────────────────────
    def _simulate_weather(self) -> dict:
        """Données météo simulées si API indisponible."""
        hour = datetime.now().hour
        irr = max(0, 900 * np.sin(np.pi * (hour - 6) / 12) + np.random.normal(0, 20))
        return {
            "irradiance": round(irr, 1),
            "temperature": round(25 + np.random.normal(0, 3), 1),
            "wind_speed": round(abs(np.random.normal(10, 5)), 1),
            "cloud_cover": int(np.clip(np.random.normal(20, 20), 0, 100)),
            "timestamp": datetime.now().isoformat(),
            "source": "simulation",
        }

    def _simulate_historical(self, days: int) -> pd.DataFrame:
        """DataFrame simulé pour fallback."""
        hours = pd.date_range(end=datetime.utcnow(), periods=days * 24, freq="h")
        irr = np.clip(
            800 * np.sin(np.pi * ((hours.hour - 6) / 12)) + np.random.normal(0, 40, len(hours)),
            0, None,
        )
        return pd.DataFrame({
            "datetime": hours,
            "irradiance": irr,
            "temperature": 22 + 8 * np.sin(2 * np.pi * hours.hour / 24) + np.random.normal(0, 2, len(hours)),
            "wind_speed": np.abs(np.random.normal(10, 5, len(hours))),
        })
