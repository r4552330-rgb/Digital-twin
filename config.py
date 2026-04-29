# config.yaml
site:
  latitude: 33.6
  longitude: -7.6
  altitude: 56
  name: "Centrale PV Demo"
  n_panels: 12
  series_per_string: 6
  strings_per_mppt: 2
  n_mppt: 1

panel:
  pmp_stc: 330.0       # W
  area_m2: 1.939        # m²
  eta_stc: 0.170        # rendement STC
  voc: 40.0             # V
  isc: 9.0              # A
  vmp: 33.0             # V
  imp: 8.5              # A
  gamma_pmp: -0.0040    # -0.4%/K
  beta_voc: -0.0034
  alpha_isc: 0.0005
  noct: 45              # °C

losses:
  dc_total: 0.10        # pertes DC totales (fraction)
  ac_efficiency: 0.96   # rendement onduleur (corrigé !)

ems:
  mqtt_broker: "localhost"
  mqtt_port: 1883
  mqtt_topic_telemetry: "esp32/telemetry"
  mqtt_topic_command: "esp32/command"
  blynk_api_key: ""     # optionnel, si vous gardez Blynk
  open_meteo_interval_min: 15
