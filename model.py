# model.py — version corrigée
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Union


class PVModel:
    def __init__(self, config: dict):
        self.cfg = config
        panel = config["panel"]
        site  = config["site"]

        self.pmp_stc    = panel["pmp_stc"]
        self.eta_stc    = panel["eta_stc"]
        self.area_m2    = panel["area_m2"]
        self.gamma_pmp  = panel["gamma_pmp"]
        self.noct       = panel["noct"]
        self.voc_stc    = panel["voc"]
        self.isc_stc    = panel["isc"]
        self.vmp_stc    = panel["vmp"]
        self.imp_stc    = panel["imp"]

        self.n_panels_total = site["n_panels"]
        self.n_series       = site["series_per_string"]
        self.n_parallel     = site["strings_per_mppt"] * site.get("n_mppt", 1)

        # Vérification cohérence topologie
        assert self.n_series * self.n_parallel == self.n_panels_total, (
            f"Topologie incohérente : {self.n_series}s × {self.n_parallel}p "
            f"= {self.n_series * self.n_parallel} ≠ n_panels={self.n_panels_total}"
        )

        self.dc_losses       = config["losses"]["dc_total"]
        self.ac_efficiency   = config["losses"]["ac_efficiency"]
        self.p_inv_threshold = config["losses"].get("inverter_threshold_kw", 0.05)

        self._recalibration_factor  = 0.1
        self._last_recalibration    = None

    # ── Modèle thermique ─────────────────────────────────────────────────
    def cell_temperature(self, irradiance: float, temp_ambient: float) -> float:
        """IEC 61215 — modèle NOCT."""
        return temp_ambient + (self.noct - 20) / 800 * irradiance

    # ── Rendement panneau ────────────────────────────────────────────────
    def efficiency(self, irradiance: float, temp_cell: float) -> float:
        delta_t = temp_cell - 25
        eta = self.eta_stc * (1 + self.gamma_pmp * delta_t)
        if irradiance < 200:
            eta *= max(0.0, irradiance / 200 * 0.97 + 0.03)
        return max(0.0, eta)

    # ── Rendement onduleur (courbe simplifiée) ───────────────────────────
    def inverter_efficiency(self, p_dc_kw: float) -> float:
        """
        Modèle de rendement onduleur en fonction du taux de charge.
        Retourne 0 si p_dc < seuil de démarrage.
        """
        p_rated = self.cfg["inverter"]["p_rated_kw"]
        if p_dc_kw <= self.p_inv_threshold:
            return 0.0
        # Approximation polynomiale du rendement européen
        load_ratio = min(p_dc_kw / p_rated, 1.0)
        eta = self.ac_efficiency * (1 - 0.03 * (1 - load_ratio) ** 2)
        return max(0.0, min(1.0, eta))

    def panel_power(self, irradiance: float, temp_cell: float) -> float:
        if irradiance <= 0:
            return 0.0
        return self.efficiency(irradiance, temp_cell) * self.area_m2 * irradiance

    # ── Point de fonctionnement ──────────────────────────────────────────
    def compute(self, irradiance: float, temp_ambient: float) -> dict:
        """
        Calcule un point de fonctionnement instantané.
        PR défini en DC (IEC 61724) pour rester homogène avec p_ref_kw (STC DC).
        """
        t_cell   = self.cell_temperature(irradiance, temp_ambient)
        p_panel  = self.panel_power(irradiance, t_cell)
        p_dc_kw  = p_panel * self.n_panels_total * (1 - self.dc_losses) / 1000

        eta_inv  = self.inverter_efficiency(p_dc_kw)
        p_ac_kw  = p_dc_kw * eta_inv

        # PR DC : grandeurs homogènes (DC vs référence DC STC)
        p_ref_kw = self.pmp_stc * self.n_panels_total * irradiance / 1_000_000
        pr_dc    = p_dc_kw / p_ref_kw if p_ref_kw > 0 else 0.0

        return {
            "p_dc_kw":           round(p_dc_kw, 3),
            "p_ac_kw":           round(p_ac_kw, 3),
            "p_ref_kw":          round(p_ref_kw, 3),
            "performance_ratio": round(pr_dc, 4),   # PR DC normalisé IEC 61724
            "efficiency":        round(self.efficiency(irradiance, t_cell) * 100, 2),
            "inverter_eta":      round(eta_inv * 100, 1),
            "temp_cell":         round(t_cell, 1),
            "irradiance":        irradiance,
            "temp_ambient":      temp_ambient,
        }

    # ── Calcul vectorisé ─────────────────────────────────────────────────
    def compute_series(self,
                       irradiance_arr: Union[np.ndarray, list],
                       temp_arr: Union[np.ndarray, list]) -> pd.DataFrame:
        irr = np.asarray(irradiance_arr, dtype=float)
        tmp = np.asarray(temp_arr, dtype=float)

        t_cell  = tmp + (self.noct - 20) / 800 * irr
        delta_t = t_cell - 25
        eta_t   = self.eta_stc * (1 + self.gamma_pmp * delta_t)

        low_mask = irr < 200
        eta_t[low_mask] *= np.maximum(0, irr[low_mask] / 200 * 0.97 + 0.03)
        eta_t = np.maximum(0, eta_t)

        p_dc_kw = eta_t * self.area_m2 * irr * self.n_panels_total * (1 - self.dc_losses) / 1000
        p_dc_kw = np.where(irr <= 0, 0.0, p_dc_kw)

        # Rendement onduleur vectorisé
        p_rated = self.cfg["inverter"]["p_rated_kw"]
        load    = np.clip(p_dc_kw / p_rated, 0, 1)
        eta_inv = self.ac_efficiency * (1 - 0.03 * (1 - load) ** 2)
        eta_inv = np.where(p_dc_kw <= self.p_inv_threshold, 0.0, eta_inv)
        p_ac_kw = p_dc_kw * eta_inv

        p_ref_kw = self.pmp_stc * self.n_panels_total * irr / 1_000_000
        pr_dc    = np.where(p_ref_kw > 0, p_dc_kw / p_ref_kw, 0.0)  # PR DC

        return pd.DataFrame({
            "p_dc_kw":           p_dc_kw,
            "p_ac_kw":           p_ac_kw,
            "p_ref_kw":          p_ref_kw,
            "performance_ratio": pr_dc,
            "efficiency_pct":    eta_t * 100,
            "temp_cell":         t_cell,
            "inverter_eta_pct":  eta_inv * 100,
        })

    # ── Recalage adaptatif ───────────────────────────────────────────────
    def recalibrate(self, measured_p_ac_kw: float,
                    irradiance: float, temp_ambient: float):
        """
        Recalage EMA sur dc_losses à partir d'une mesure réelle.
        À appeler uniquement depuis model_service.py, pas depuis app.py.
        """
        if irradiance < 50 or measured_p_ac_kw <= 0:
            return  # Pas de recalage la nuit ou mesure nulle

        sim = self.compute(irradiance, temp_ambient)
        if sim["p_ac_kw"] <= 0:
            return

        correction = measured_p_ac_kw / sim["p_ac_kw"]
        # correction > 1 → modèle sous-estime → pertes DC trop élevées
        # correction < 1 → modèle surestime → pertes DC trop faibles
        target_losses = 1.0 - (1.0 - self.dc_losses) * correction
        target_losses = max(0.0, min(0.30, target_losses))  # bornes physiques [0%, 30%]

        # EMA : mise à jour progressive
        self.dc_losses += self._recalibration_factor * (target_losses - self.dc_losses)
        self._last_recalibration = datetime.now(timezone.utc).isoformat()

    # ── État sérialisable ────────────────────────────────────────────────
    def get_state(self) -> dict:
        return {
            "dc_losses":            self.dc_losses,
            "ac_efficiency":        self.ac_efficiency,
            "last_recalibration":   self._last_recalibration,
        }

    def set_state(self, state: dict):
        """Restaure un état sauvegardé (depuis Redis, fichier JSON, etc.)."""
        self.dc_losses             = state.get("dc_losses", self.dc_losses)
        self.ac_efficiency         = state.get("ac_efficiency", self.ac_efficiency)
        self._last_recalibration   = state.get("last_recalibration")

    # ── Courbe I-V ───────────────────────────────────────────────────────
    def compute_iv_curve(self, v_range: np.ndarray) -> dict:
        """Modèle I-V analytique du générateur PV complet."""
        ns, np_ = self.n_series, self.n_parallel
        voc = self.voc_stc * ns
        isc = self.isc_stc * np_
        vmp = self.vmp_stc * ns
        imp = self.imp_stc * np_

        a  = np.log(isc / (isc - imp) + 1e-10)
        rs = (voc - vmp) / imp
        current = isc * (1 - np.exp((v_range - voc + rs * isc) / (voc / a + rs * isc) * a))
        current = np.clip(current, 0, isc)
        power_kw = v_range * current / 1000
        idx = np.argmax(power_kw)

        return {
            "voltage": v_range, "current": current, "power_kw": power_kw,
            "p_mpp": round(power_kw[idx], 3),
            "v_mpp": round(v_range[idx], 1),
            "i_mpp": round(current[idx], 2),
        }
