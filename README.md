# ⚡ PV Digital Twin — Dashboard Streamlit

Dashboard de jumelage numérique pour installation photovoltaïque, déployable sur Streamlit Cloud.

## Structure

```
pv-digital-twin/
├── app.py           # Dashboard principal
├── model.py         # Modèle mathématique PV (SDM + correction IEC 61853)
├── data.py          # Sources données (Open-Meteo, MQTT, Blynk)
├── config.py        # Configuration centralisée
├── utils.py         # Utilitaires (format, couleurs, diagnostics)
├── requirements.txt
├── packages.txt
└── optional/
    ├── model_service.py   # Service de recalage continu
    ├── docker-compose.yml # Mosquitto + InfluxDB + Redis
    └── deploy.md
```

## Démarrage rapide

```bash
git clone https://github.com/votre-user/pv-digital-twin
cd pv-digital-twin
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement Streamlit Cloud

1. Pushez le repo sur GitHub
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io)
3. New app → sélectionnez `app.py`
4. Deploy

## Configuration

Éditez `config.py` pour adapter à votre site :
- Coordonnées GPS → données météo Open-Meteo automatiques
- Paramètres panneau (modèle, STC, coefficients T°)
- Topologie champ (nb panneaux, séries, parallèles)
- Seuils d'alerte Performance Ratio

## Sources de données

| Source | Usage | Clé API |
|--------|-------|---------|
| Open-Meteo | Météo temps réel & historique | ❌ Gratuit |
| MQTT (Mosquitto) | Capteurs IoT temps réel | optionnel |
| Blynk HTTP API | Capteurs IoT cloud | optionnel |

## Modèle mathématique

Le modèle PV implémente :
- Correction thermique IEC 61853 (modèle NOCT)
- Coefficient γ (puissance/température)
- Pertes DC : câblage + mismatch + salissures + ombrage
- Courbe I-V analytique (modèle Bishop simplifié)
- Performance Ratio normalisé

## Licence

MIT
