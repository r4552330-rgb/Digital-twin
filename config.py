site:
  latitude: 33.6
  longitude: -7.6
  altitude: 56
  name: "Centrale PV Demo"
  tz: "Africa/Casablanca"
  tilt: 31
  azimuth: 180

  n_panels: 12
  series_per_string: 6
  strings_per_mppt: 2
  n_mppt: 1

panel:
  pmp_stc: 330.0
  area_m2: 1.939
  eta_stc: 0.170
  voc: 40.0
  isc: 9.0
  vmp: 33.0
  imp: 8.5
  gamma_pmp: -0.0040
  beta_voc: -0.0034
  alpha_isc: 0.0005
  noct: 45

losses:
  dc_total: 0.10
  ac_efficiency: 0.96
  inverter_threshold_kw: 0.05

inverter:
  p_rated_kw: 4.0

ems:
  mqtt_broker: "localhost"
  mqtt_port: 1883
  mqtt_topic_telemetry: "esp32/telemetry"
  mqtt_topic_command: "esp32/command"
  blynk_api_key: ""
  open_meteo_interval_min: 15
