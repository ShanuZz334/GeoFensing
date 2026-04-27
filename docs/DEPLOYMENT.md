# GeoFace Faculty Authentication System — Deployment Guide

## Option A: AWS EC2 Deployment

### 1. Launch EC2 Instance

- **AMI:** Ubuntu 22.04 LTS
- **Instance type:** t3.medium (2 vCPU, 4 GB RAM) minimum
- **Security Group:** Open ports 80, 443, 22
- **Storage:** 20 GB SSD

### 2. Server Initial Setup

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3.11 python3.11-venv python3-pip \
    nginx git cmake libopenblas-dev liblapack-dev \
    libx11-dev libgtk-3-dev postgresql-client

# Install certbot for SSL
sudo apt-get install -y certbot python3-certbot-nginx
```

### 3. Clone & Configure App

```bash
cd /var/www
sudo git clone https://github.com/your-org/geoface.git
sudo chown -R ubuntu:ubuntu geoface
cd geoface/backend

python3.11 -m venv .venv
source .venv/bin/activate
pip install dlib==19.24.4      # native compile – takes ~10 min on t3.medium
pip install -r requirements.txt

# Download dlib model
mkdir -p models && cd models
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
cd ..

# Environment
cp .env.example .env
nano .env   # Fill production values
```

### 4. Gunicorn Systemd Service

```bash
sudo nano /etc/systemd/system/geoface.service
```

```ini
[Unit]
Description=GeoFace Faculty Authentication API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/geoface/backend
Environment="FLASK_ENV=production"
EnvironmentFile=/var/www/geoface/backend/.env
ExecStart=/var/www/geoface/backend/.venv/bin/gunicorn \
    --config gunicorn.conf.py \
    "run:app"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable geoface
sudo systemctl start geoface
sudo systemctl status geoface
```

### 5. Nginx Configuration

```bash
sudo cp /var/www/geoface/backend/nginx.conf \
       /etc/nginx/sites-available/geoface

# Update domain name in the config
sudo nano /etc/nginx/sites-available/geoface

sudo ln -s /etc/nginx/sites-available/geoface \
           /etc/nginx/sites-enabled/

sudo nginx -t && sudo systemctl reload nginx
```

Add rate limit zones to `/etc/nginx/nginx.conf` inside `http {}`:
```nginx
limit_req_zone $binary_remote_addr zone=login:10m  rate=5r/m;
limit_req_zone $binary_remote_addr zone=verify:10m rate=20r/m;
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d api.geoface.yourdomain.com
# Auto-renew is configured automatically
```

### 7. Deploy Admin Panel

```bash
sudo mkdir -p /var/www/geoface-admin
sudo cp -r /var/www/geoface/admin/* /var/www/geoface-admin/
sudo chown -R www-data:www-data /var/www/geoface-admin
```

---

## Option B: Render.com Deployment

### Backend (Web Service)

1. Connect GitHub repo at https://dashboard.render.com/
2. **Build Command:**
   ```bash
   pip install cmake dlib==19.24.4 && pip install -r requirements.txt && \
   mkdir -p models && cd models && \
   wget -q http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 && \
   bunzip2 shape_predictor_68_face_landmarks.dat.bz2 && cd ..
   ```
3. **Start Command:**
   ```bash
   gunicorn --config gunicorn.conf.py "run:app"
   ```
4. **Plan:** Standard ($7/mo) — needed for face_recognition CPU workload
5. Add all `.env` vars in Render's "Environment" tab.

### Database (PostgreSQL)

1. Create a **Render PostgreSQL** instance (or use **Neon.tech**)
2. Copy the `DATABASE_URL` → set in backend environment

### Admin Panel (Static Site)

1. Add `admin/` as a separate **Static Site** on Render
2. No build command needed

---

## Database Setup (Production)

```bash
# Apply schema to production DB
psql $DATABASE_URL -f database/schema.sql
```

---

## Environment Variables — Production Checklist

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | ✓ | 32+ random chars |
| `JWT_SECRET_KEY` | ✓ | Different from SECRET_KEY |
| `DATABASE_URL` | ✓ | Full PostgreSQL URL |
| `ADMIN_EMAIL` | ✓ | Admin panel login email |
| `ADMIN_PASSWORD` | ✓ | Strong password |
| `COLLEGE_LATITUDE` | Optional | Default: 10.8505 |
| `COLLEGE_LONGITUDE` | Optional | Default: 76.2711 |
| `GEOFENCE_RADIUS_METERS` | Optional | Default: 200 |
| `ALLOWED_ORIGINS` | ✓ | Your domain(s) |

---

## Mobile App — Production Build

### Update API URL
```dart
// lib/core/constants/api_constants.dart
static const String baseUrl = 'https://api.geoface.yourdomain.com';
```

### Android (APK/AAB)
```bash
cd GeoFense/mobile

# Create key store (first time)
keytool -genkey -v -keystore android/app/geoface-release.jks \
  -alias geoface -keyalg RSA -keysize 2048 -validity 10000

# Build signed APK
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk

# Build AAB (for Play Store)
flutter build appbundle --release
```

### iOS
```bash
flutter build ipa
# Archive in Xcode → Distribute App → App Store Connect
```

---

## Monitoring & Logs

```bash
# View Gunicorn logs
sudo journalctl -u geoface -f

# Nginx access/error logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status geoface
```

## Performance Tuning

For 50+ concurrent users on t3.medium:
- `GUNICORN_WORKERS=5` (2×CPU+1)
- `GUNICORN_WORKER_CLASS=gevent`
- `GUNICORN_WORKER_CONNECTIONS=500`
- Limit `MAX_FRAMES=15` for faster pipeline on lower-spec machines
- Enable `face_recognition` caching if processing the same teacher repeatedly
