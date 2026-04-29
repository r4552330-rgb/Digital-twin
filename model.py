"""
model.py — Modèle mathématique du générateur PV
Basé sur le modèle à 5 paramètres (SDM) simplifié + correction thermique IEC 61853
"""

import numpy as np
import pandas as pd
from typing import Union


class PVModel:
    """
    Modèle numérique du générateur PV.

    Paramètres d'entrée : irradiance (W/m²), température ambiante (°C)
    Sorties : puissance DC (kW), performance ratio, courbe I-V, etc.
    """

    def __init__(self, config: dict):
        self.cfg = config
        panel = config["panel"]
        site = config["site"]

        # Paramètres STC (Standard Test Conditions : 1000 W/m², 25°C)
        self.pmp_stc = panel["pmp_stc"]          # W par panneau
        self.voc_stc = panel["voc"]               # V
        self.isc_stc = panel["isc"]               # A
        self.vmp_stc = panel["vmp"]               # V
        self.imp_stc = panel["imp"]               # A
        self.eta_stc = panel["eta_stc"]           # rendement STC (fraction)
        self.area_m2 = panel["area_m2"]           # surface panneau

        # Coefficients de température
        self.alpha_isc = panel.get("alpha_isc", 0.0005)   # /°C (courant)
        self.beta_voc  = panel.get("beta_voc", -0.0034)   # /°C (tension)
        self.gamma_pmp = panel.get("gamma_pmp", -0.0040)  # /°C (puissance)

        # Modèle thermique NOCT
        self.noct = panel.get("noct", 45)          # °C

        # Topologie champ PV
        self.n_panels_total = site["n_panels"]
        self.n_series       = site["series_per_string"]
        self.n_parallel     = site["strings_per_mppt"] * site.get("n_mppt", 1)

        # Pertes DC (câblage, mismatch, salissures…)
        self.dc_losses = config.get("losses", {}).get("dc_total", 0.05)

    # ─── Température de cellule ────────────────────────────────────────────
    def cell_temperature(self, irradiance: float, temp_ambient: float) -> float:
        """Modèle NOCT simplifié : T_cell = T_amb + (NOCT-20)/800 * G"""
        return temp_ambient + (self.noct - 20) / 800 * irradiance

    # ─── Rendement corrigé température & irradiance ────────────────────────
    def efficiency(self, irradiance: float, temp_cell: float) -> float:
        """
        Rendement effectif en tenant compte de :
        - La correction thermique (γ·ΔT)
        - La correction basse irradiance (modèle linéaire simplifié)
        """
        delta_t = temp_cell - 25
        # Correction thermique
        eta_t = self.eta_stc * (1 + self.gamma_pmp * delta_t)
        # Correction basse irradiance (perte relative ≈ 3% à 200 W/m²)
        if irradiance < 200:
            eta_t *= max(0, irradiance / 200 * 0.97 + 0.03)
        return max(0, eta_t)

    # ─── Puissance DC d'un panneau ─────────────────────────────────────────
    def panel_power(self, irradiance: float, temp_cell: float) -> float:
        """Puissance MPP d'un panneau (W)"""
        if irradiance <= 0:
            return 0.0
        eta = self.efficiency(irradiance, temp_cell)
        return eta * self.area_m2 * irradiance

    # ─── Puissance du générateur PV complet ───────────────────────────────
    def compute(self, irradiance: float, temp_ambient: float) -> dict:
        """
        Calcul complet du générateur PV.

        Returns:
            dict avec p_dc_kw, p_ref_kw, performance_ratio, efficiency, temp_cell
        """
        t_cell = self.cell_temperature(irradiance, temp_ambient)
        p_panel = self.panel_power(irradiance, t_cell)
        p_dc_w = p_panel * self.n_panels_total * (1 - self.dc_losses)
        p_dc_kw = p_dc_w / 1000

        # Puissance de référence (STC linéaire)
        p_ref_kw = (self.pmp_stc * self.n_panels_total * irradiance / 1000) / 1000

        pr = p_dc_kw / p_ref_kw if p_ref_kw > 0 else 0.0
        eta = self.efficiency(irradiance, t_cell) * 100  # %

        return {
            "p_dc_kw": round(p_dc_kw, 3),
            "p_ref_kw": round(p_ref_kw, 3),
            "performance_ratio": round(pr, 4),
            "efficiency": round(eta, 2),
            "temp_cell": round(t_cell, 1),
            "irradiance": irradiance,
            "temp_ambient": temp_ambient,
        }

    # ─── Calcul vectorisé (séries temporelles) ────────────────────────────
    def compute_series(
        self,
        irradiance_arr: Union[np.ndarray, list],
        temp_arr: Union[np.ndarray, list],
    ) -> pd.DataFrame:
        """
        Calcul vectorisé pour une série temporelle.

        Args:
            irradiance_arr : tableau d'irradiance (W/m²)
            temp_arr       : tableau de températures ambiantes (°C)

        Returns:
            DataFrame avec colonnes p_dc_kw, p_ref_kw, performance_ratio, etc.
        """
        irr = np.asarray(irradiance_arr, dtype=float)
        tmp = np.asarray(temp_arr, dtype=float)

        t_cell = tmp + (self.noct - 20) / 800 * irr
        delta_t = t_cell - 25
        eta_t = self.eta_stc * (1 + self.gamma_pmp * delta_t)

        # Correction basse irradiance
        low_mask = irr < 200
        eta_t[low_mask] *= np.maximum(0, irr[low_mask] / 200 * 0.97 + 0.03)
        eta_t = np.maximum(0, eta_t)

        p_panel = eta_t * self.area_m2 * irr
        p_dc_kw = p_panel * self.n_panels_total * (1 - self.dc_losses) / 1000
        p_dc_kw = np.where(irr <= 0, 0, p_dc_kw)

        p_ref_kw = self.pmp_stc * self.n_panels_total * irr / 1_000_000
        pr = np.where(p_ref_kw > 0, p_dc_kw / p_ref_kw, 0.0)

        return pd.DataFrame({
            "p_dc_kw": p_dc_kw,
            "p_ref_kw": p_ref_kw,
            "performance_ratio": pr,
            "efficiency_pct": eta_t * 100,
            "temp_cell": t_cell,
        })

    # ─── Courbe I-V ───────────────────────────────────────────────────────
    def compute_iv_curve(self, v_range: np.ndarray) -> dict:
        """
        Modèle I-V simplifié à deux diodes (approche analytique).
        Retourne courant, puissance et point MPP pour un tableau de tensions.
        """
        # Paramètres normalisés au champ complet (série × parallèle)
        ns = self.n_series
        np_ = self.n_parallel

        voc = self.voc_stc * ns
        isc = self.isc_stc * np_
        vmp = self.vmp_stc * ns
        imp = self.imp_stc * np_

        # Facteur de forme
        ff = (vmp * imp) / (voc * isc)

        # Courbe I-V approchée (modèle Bishop simplifié)
        a = np.log(isc / (isc - imp) + 1e-10)  # paramètre de la diode
        rs = (voc - vmp) / imp                   # résistance série approchée

        current = isc * (1 - np.exp((v_range - voc + rs * isc) / (voc / a + rs * isc) * a))
        current = np.clip(current, 0, isc)
        power_kw = v_range * current / 1000

        idx_mpp = np.argmax(power_kw)

        return {
            "voltage": v_range,
            "current": current,
            "power_kw": power_kw,
            "p_mpp": round(power_kw[idx_mpp], 3),
            "v_mpp": round(v_range[idx_mpp], 1),
            "i_mpp": round(current[idx_mpp], 2),
            "fill_factor": round(ff, 3),
        }
