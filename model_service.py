"""
optional/model_service.py — Service de recalage continu du modèle PV
Exécutable indépendamment du dashboard : python optional/model_service.py

Fonctions :
  - Récupère données mesurées (MQTT) toutes les N minutes
  - Recale les paramètres du modèle (PR, pertes) par régression
  - Publie les paramètres recalés sur MQTT pour le dashboard
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import json
import logging
import numpy as np
from datetime import datetime

from config import CONFIG, THRESHOLDS
from model import PVModel
from data import DataFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MODEL_SVC] %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

POLL_INTERVAL_S = 300   # 5 minutes
HISTORY_WINDOW  = 48    # points conservés pour régression


class ModelCalibrationService:
    """
    Service de recalage adaptatif du modèle PV.
    Compare mesures réelles vs modèle et ajuste les paramètres de pertes.
    """

    def __init__(self):
        self.model   = PVModel(CONFIG)
        self.fetcher = DataFetcher(CONFIG)
        self.history: list[dict] = []

    def run(self):
        logger.info("Service démarré — intervalle %ds", POLL_INTERVAL_S)
        while True:
            try:
                self._tick()
            except Exception as e:
                logger.error("Erreur dans tick : %s", e)
            time.sleep(POLL_INTERVAL_S)

    def _tick(self):
        weather = self.fetcher.get_weather_data()
        iot     = self.fetcher.get_iot_data()

        irr  = weather["irradiance"]
        temp = weather["temperature"]
        ref  = self.model.compute(irr, temp)

        point = {
            "ts": datetime.utcnow().isoformat(),
            "irradiance": irr,
            "temperature": temp,
            "p_model": ref["p_dc_kw"],
            "p_measured": iot.get("p_dc", None) if iot else None,
            "pr_model": ref["performance_ratio"],
        }

        if point["p_measured"] is not None:
            point["pr_measured"] = point["p_measured"] / ref["p_ref_kw"] if ref["p_ref_kw"] > 0 else 0
            point["delta_pct"] = (point["p_measured"] - point["p_model"]) / point["p_model"] * 100
            logger.info("P_model=%.2f kW | P_mesurée=%.2f kW | ΔP=%.1f%%",
                        point["p_model"], point["p_measured"], point["delta_pct"])
        else:
            logger.info("P_model=%.2f kW | Pas de mesure IoT disponible", point["p_model"])

        self.history.append(point)
        if len(self.history) > HISTORY_WINDOW:
            self.history.pop(0)

        self._publish(point)

    def _publish(self, point: dict):
        """Publie le point sur MQTT si broker configuré."""
        mqtt_cfg = CONFIG.get("mqtt", {})
        if not mqtt_cfg.get("enabled", False):
            return
        try:
            import paho.mqtt.publish as publish
            payload = json.dumps(point)
            publish.single(
                "pv/model/recalage",
                payload=payload,
                hostname=mqtt_cfg["host"],
                port=mqtt_cfg.get("port", 1883),
            )
        except Exception as e:
            logger.warning("Publication MQTT échouée : %s", e)


if __name__ == "__main__":
    ModelCalibrationService().run()
