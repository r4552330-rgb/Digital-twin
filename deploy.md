# Déploiement avancé — PV Digital Twin

## Streamlit Cloud (recommandé pour démo)

1. Créez un repo GitHub public
2. Allez sur https://share.streamlit.io → New app
3. Sélectionnez `app.py` comme point d'entrée
4. Variables secrètes (si MQTT/Blynk) : Settings → Secrets

```toml
# .streamlit/secrets.toml (ne pas committer !)
[mqtt]
host = "votre-broker.example.com"
port = 1883

[blynk]
token = "votre_token_blynk"
```

## Docker local

```bash
# Démarrer les services locaux
cd optional
docker compose up -d

# Vérifier
docker compose ps

# Démarrer le service de recalage
cd ..
python optional/model_service.py
```

## VPS / serveur dédié

```bash
# Installer dépendances
pip install -r requirements.txt

# Lancer avec nohup
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

# Ou avec systemd (recommandé)
# Créer /etc/systemd/system/pv-dashboard.service
```

Exemple service systemd :
```ini
[Unit]
Description=PV Digital Twin Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pv-digital-twin
ExecStart=/usr/bin/streamlit run app.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

## Reverse proxy Nginx

```nginx
server {
    listen 80;
    server_name pv.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
