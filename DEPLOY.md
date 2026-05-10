# GeoFense — Complete Production Deployment Guide
# Oracle Cloud Free VM + Cloudflare + Flutter APK

> **Cost: $0.00 forever.**
> This guide takes your GeoFense app from your Windows laptop to a live 24/7 production server.

---

## What You Get When Done

| Component             | URL / Access                          | Hosted On              |
|-----------------------|---------------------------------------|------------------------|
| Admin Panel           | `https://YOUR_DOMAIN/admin/`          | Oracle VM (Nginx)      |
| Flask API             | `https://YOUR_DOMAIN/api/`            | Oracle VM (Gunicorn)   |
| PostgreSQL Database   | Internal (no public access)           | Oracle VM              |
| Redis Cache           | Internal (no public access)           | Oracle VM              |
| Teacher Android App   | APK installed on phone                | Built on your laptop   |

---

## Architecture

```
Internet
    │
    ├── Admin on Laptop ────► https://YOUR_DOMAIN/admin/
    │                               │
    └── Teacher on Phone ──► https://YOUR_DOMAIN/api/
                                    │
                          ┌─────────▼──────────────┐
                          │   Oracle Cloud VM       │
                          │   Ubuntu 22.04 (ARM)    │
                          │   4 OCPU / 24GB RAM     │
                          │   100GB Disk — FREE     │
                          │                         │
                          │  ┌─────────────────┐    │
                          │  │ Nginx (80/443)   │    │
                          │  └────────┬────────┘    │
                          │           │              │
                          │  ┌────────▼────────┐    │
                          │  │ Flask/Gunicorn   │    │
                          │  └────────┬────────┘    │
                          │    ┌──────┴──────┐       │
                          │  ┌─▼──┐       ┌─▼────┐  │
                          │  │ DB │       │Redis │  │
                          │  └────┘       └──────┘  │
                          └────────────────────────-─┘
```

---

## Timeline

| Phase | Task                                   | Time Needed |
|-------|----------------------------------------|-------------|
| 1     | Create Oracle Cloud account + VM        | 20 minutes  |
| 2     | SSH into VM from Windows                | 5 minutes   |
| 3     | Install Docker on the VM                | 10 minutes  |
| 4     | Clone repo and configure `.env`         | 10 minutes  |
| 5     | Start the app with Docker Compose       | 10 minutes  |
| 6     | Point a domain + get HTTPS (SSL)        | 15 minutes  |
| 7     | Update Admin Panel API URL + push       | 5 minutes   |
| 8     | Update Flutter app URL + build APK      | 10 minutes  |
| 9     | Set up GitHub auto-deploy (optional)    | 10 minutes  |
| **Total** |                                    | **~1.5 hrs** |

---

## ═══════════════════════════════════════════════════════
## PHASE 1 — Create Oracle Cloud Account + Free VM
## ═══════════════════════════════════════════════════════

### 1.1 — Sign Up

1. Go to **https://cloud.oracle.com**
2. Click **"Start for free"**
3. Fill in your details — enter a **valid credit card** (you will NOT be billed; it's for identity verification only)
4. Verify your email and phone number

### 1.2 — Choose Your Home Region

> ⚠️ **CRITICAL**: You choose your region ONCE. You cannot change it later.

When asked to choose a region, select:
- **`ap-mumbai-1`** (Mumbai) — best latency for India
- OR **`ap-hyderabad-1`** (Hyderabad) — also good

### 1.3 — Create the VM Instance

1. In the Oracle Cloud Console, go to:
   **☰ Menu → Compute → Instances → Create Instance**

2. Set the following:

   | Field           | Value                                  |
   |-----------------|----------------------------------------|
   | Name            | `geoface-server`                       |
   | Image           | **Ubuntu 22.04** (click Change Image)  |
   | Shape           | **VM.Standard.A1.Flex** (Always Free)  |
   | OCPU            | **4**                                  |
   | Memory (GB)     | **24**                                 |

3. Scroll down to **"Add SSH keys"**:
   - Click **"Generate a key pair for me"**
   - Download **both** the private key (`.key`) and public key (`.pub`)
   - Save the `.key` file somewhere safe, e.g. `C:\Users\shanif\Downloads\geoface-oracle.key`

4. Scroll down to **"Boot volume"**:
   - Check **"Specify a custom boot volume size"**
   - Set to **100 GB**

5. Click **"Create"**

6. Wait about 2 minutes. Your VM will appear with a **Public IP address** — copy it (e.g. `152.67.100.50`)

### 1.4 — Open Firewall Ports in Oracle Console

By default Oracle blocks everything except port 22. You must open ports 80 and 443:

1. Go to: **☰ Menu → Networking → Virtual Cloud Networks**
2. Click your VCN (there should be one auto-created)
3. Click **"Subnets"** → Click the subnet
4. Click **"Security Lists"** → Click **"Default Security List"**
5. Click **"Add Ingress Rules"** and add TWO rules:

   **Rule 1 — HTTP:**
   | Field           | Value         |
   |-----------------|---------------|
   | Source CIDR     | `0.0.0.0/0`   |
   | IP Protocol     | TCP           |
   | Destination Port| `80`          |

   **Rule 2 — HTTPS:**
   | Field           | Value         |
   |-----------------|---------------|
   | Source CIDR     | `0.0.0.0/0`   |
   | IP Protocol     | TCP           |
   | Destination Port| `443`         |

6. Click **"Add Ingress Rules"** to save

---

## ═══════════════════════════════════════════════════════
## PHASE 2 — SSH Into The VM From Your Windows Laptop
## ═══════════════════════════════════════════════════════

### 2.1 — Fix the Key File Permissions (Windows)

Open **PowerShell** on your laptop and run:

```powershell
# Give the key file the right permissions (Windows needs this)
icacls "C:\Users\shanif\Downloads\geoface-oracle.key" /inheritance:r /grant:r "$env:USERNAME:R"
```

### 2.2 — Connect via SSH

```powershell
# Replace 152.67.100.50 with YOUR actual Oracle VM public IP
ssh -i "C:\Users\shanif\Downloads\geoface-oracle.key" ubuntu@152.67.100.50
```

- Type **`yes`** when asked about the fingerprint
- You are now inside the Oracle VM!

### 2.3 — Save SSH Shortcut (Optional but Recommended)

Create/edit the file `C:\Users\shanif\.ssh\config` with Notepad:

```
Host geoface
    HostName 152.67.100.50
    User ubuntu
    IdentityFile C:\Users\shanif\Downloads\geoface-oracle.key
```

Now you can just type `ssh geoface` from any terminal.

---

## ═══════════════════════════════════════════════════════
## PHASE 3 — Install Docker on the Oracle VM
## ═══════════════════════════════════════════════════════

> Run ALL of these commands inside the Oracle VM terminal (after SSH)

### 3.1 — Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2 — Install Docker (One Command)

```bash
curl -fsSL https://get.docker.com | sh
```

### 3.3 — Add Your User to Docker Group

```bash
sudo usermod -aG docker ubuntu
newgrp docker
```

### 3.4 — Install Docker Compose

```bash
sudo apt install -y docker-compose-plugin
```

### 3.5 — Verify Installation

```bash
docker --version
docker compose version
```

You should see version numbers printed for both.

### 3.6 — Open Ubuntu's Internal Firewall

Oracle VMs have a second firewall inside Ubuntu itself. Open it:

```bash
sudo apt install -y iptables-persistent

sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

sudo netfilter-persistent save
```

---

## ═══════════════════════════════════════════════════════
## PHASE 4 — Clone the Repo and Configure Environment
## ═══════════════════════════════════════════════════════

> Still inside the Oracle VM terminal

### 4.1 — Clone the GitHub Repository

```bash
cd /home/ubuntu
git clone https://github.com/ShanuZz334/GeoFensing.git geoface
cd geoface
```

### 4.2 — Create the Production `.env` File

```bash
nano .env
```

Copy-paste this EXACTLY (fill in the values in `< >`):

```env
# ==============================================================================
# GeoFace — Production Environment Variables
# ==============================================================================

# ── Flask ──────────────────────────────────────────────────────────────────────
FLASK_ENV=production
# Generate a random 32+ char string — change this!
SECRET_KEY=bX9mK5qW2xL1vC7hJ4yP3tR6zF0aN8c4dE2gH5jM7

# ── JWT ────────────────────────────────────────────────────────────────────────
# Generate another random 32+ char string — change this!
JWT_SECRET_KEY=z7X9qP2vL4mW8kF1hC5yN3bR6tJ0xM9cA2eG4jL6

# ── Database (PostgreSQL inside Docker) ────────────────────────────────────────
POSTGRES_USER=geoface_user
POSTGRES_PASSWORD=v4K9mP2qW8xN1tF7
POSTGRES_DB=geoface_db
DATABASE_URL=postgresql://geoface_user:v4K9mP2qW8xN1tF7@db:5432/geoface_db

# ── Redis (inside Docker) ─────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Geofencing (LPU / Your College) ──────────────────────────────────────────
GEOFENCE_POLYGON="[[31.24363,75.70081],[31.247,75.69853],[31.24904,75.6987],[31.2555,75.70113],[31.25988,75.70582],[31.26022,75.70624],[31.26046,75.70661],[31.25847,75.70741],[31.25632,75.70648],[31.25451,75.70514],[31.25399,75.70619],[31.25082,75.70627]]"
GEOFENCE_BUFFER_METERS=15
COLLEGE_LATITUDE=31.2536
COLLEGE_LONGITUDE=75.7037

# ── Admin ─────────────────────────────────────────────────────────────────────
HEAD_ADMIN_NAME=Admin
HEAD_ADMIN_REG_NO=123456
ADMIN_PASSWORD=admin@2000

# ── CORS — Replace with your actual domain after getting one ──────────────────
ALLOWED_ORIGINS=https://YOUR_DOMAIN

# ── Server ────────────────────────────────────────────────────────────────────
PORT=5000
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=gevent
GUNICORN_TIMEOUT=120
GUNICORN_BIND=0.0.0.0:5000
GUNICORN_LOG_LEVEL=info

# ── Email Alerts (Optional) ───────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
```

Save: press **Ctrl+X**, then **Y**, then **Enter**

---

## ═══════════════════════════════════════════════════════
## PHASE 5 — Build and Start the App
## ═══════════════════════════════════════════════════════

> Still on the Oracle VM

### 5.1 — Start All Services

```bash
cd /home/ubuntu/geoface
docker compose up -d --build
```

This will:
- Build the Flask API Docker image (takes ~3–5 minutes first time)
- Pull PostgreSQL and Redis images
- Start Nginx as the reverse proxy
- Set everything to restart automatically on reboot

### 5.2 — Watch the Startup Logs

```bash
docker compose logs -f
```

Wait until you see `geoface_api ... gunicorn ... Booting worker`. Press Ctrl+C to exit logs.

### 5.3 — Verify All Services Are Healthy

```bash
docker compose ps
```

You should see all 4 services with status `Up (healthy)`:
```
NAME               STATUS
geoface_proxy      Up (healthy)
geoface_api        Up (healthy)
geoface_db         Up (healthy)
geoface_redis      Up (healthy)
```

### 5.4 — Quick Test

```bash
# Test via the public IP (replace with your actual IP)
curl http://152.67.100.50/health
# Expected output: healthy
```

If it prints `healthy`, the app is running! 🎉

---

## ═══════════════════════════════════════════════════════
## PHASE 6 — Set Up HTTPS with a Free Domain + SSL
## ═══════════════════════════════════════════════════════

You need a domain name to get HTTPS. Here are free options:

### Option A — Free .tk Domain (Freenom)
1. Go to **https://www.freenom.com**
2. Search for a name like `geoface-lpu`
3. Choose a `.tk` or `.ml` extension
4. Register for FREE for 12 months (renewable)

### Option B — Free Subdomain (No domain needed at all)
Use **DuckDNS** (completely free):
1. Go to **https://www.duckdns.org**
2. Sign in with Google
3. Create a subdomain like `geoface-lpu.duckdns.org`
4. Set it to your Oracle VM IP

---

### 6.1 — Point Your Domain to the Oracle VM IP

In your domain's DNS settings, create an A record:

```
Type: A
Name: @  (or blank, for root domain)
Value: 152.67.100.50  (your Oracle VM public IP)
TTL: 300
```

Wait 5–10 minutes for DNS to propagate.

Test it:
```bash
# On your laptop PowerShell
nslookup yourdomain.tk
# Should show your Oracle VM IP
```

### 6.2 — Install Certbot and Get Free SSL Certificate

On the Oracle VM:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Get the certificate (replace `yourdomain.tk` with your actual domain):

```bash
sudo certbot --nginx -d yourdomain.tk
```

Follow the prompts:
- Enter your email address
- Type `Y` to agree to terms
- Type `N` for sharing your email with EFF

Certbot will automatically update your Nginx config with HTTPS!

### 6.3 — Test HTTPS

```bash
curl https://yourdomain.tk/health
# Should print: healthy
```

SSL auto-renews every 90 days — no action needed.

---

## ═══════════════════════════════════════════════════════
## PHASE 7 — Update Admin Panel API URL
## ═══════════════════════════════════════════════════════

> Do this on YOUR LAPTOP (not the VM)

### 7.1 — Update api.js

Open `admin/js/api.js` in VS Code.

Find line 5:
```javascript
const API_BASE = '/api'; // Production-ready (proxied via Nginx)
```

The admin panel is served by the **same Nginx server** as the API, so `/api` already works correctly via the reverse proxy. **No change needed if you are accessing `https://yourdomain.tk/admin/`.**

> ✅ The `/api` path works because Nginx on the VM routes `/api/` to Flask automatically. The admin HTML + JS are served from the same domain, so relative paths work.

### 7.2 — Update CORS in .env on the VM

SSH back into the VM and update the `.env` to allow your domain:

```bash
ssh geoface
cd /home/ubuntu/geoface
nano .env
```

Find the line:
```
ALLOWED_ORIGINS=https://YOUR_DOMAIN
```

Change it to:
```
ALLOWED_ORIGINS=https://yourdomain.tk
```

Save and restart:
```bash
docker compose restart api
```

---

## ═══════════════════════════════════════════════════════
## PHASE 8 — Build the Flutter Android APK
## ═══════════════════════════════════════════════════════

> Do this on YOUR LAPTOP in VS Code terminal

### 8.1 — Update the API Base URL in Flutter

Open `mobile/lib/core/constants/api_constants.dart`:

```dart
// Current (line 8):
static const String baseUrl = '/api';

// Change to:
static const String baseUrl = 'https://yourdomain.tk/api';
```

### 8.2 — Get Dependencies

```powershell
cd mobile
flutter pub get
```

### 8.3 — Build the APK

```powershell
flutter build apk --release
```

This takes about 2–3 minutes.

Your APK will be at:
```
mobile\build\app\outputs\flutter-apk\app-release.apk
```

### 8.4 — Install on Android Phones (Teacher Devices)

**Method 1 — USB Cable:**
1. Connect phone to laptop
2. Enable "USB Debugging" on the phone
3. Run: `flutter install` (installs automatically)

**Method 2 — Share the file:**
1. Send the APK via WhatsApp, Google Drive, or email
2. On the phone, tap the file
3. If prompted, go to **Settings → Security → Allow from this source**
4. Tap Install

---

## ═══════════════════════════════════════════════════════
## PHASE 9 — Auto-Deploy on Git Push (GitHub Actions)
## ═══════════════════════════════════════════════════════

Every time you `git push` from your laptop, the server automatically updates.

### 9.1 — Create the GitHub Actions Workflow

Create this file on your laptop: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: SSH into VM and deploy
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.ORACLE_VM_IP }}
          username: ubuntu
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd /home/ubuntu/geoface
            git pull origin main
            docker compose up -d --build --no-deps api proxy
            echo "Deployment complete at $(date)"
```

### 9.2 — Add Secrets to GitHub

1. Go to: **https://github.com/ShanuZz334/GeoFensing**
2. Click **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"** and add:

   | Secret Name      | Value                                          |
   |------------------|------------------------------------------------|
   | `ORACLE_VM_IP`   | Your VM's public IP (e.g. `152.67.100.50`)     |
   | `ORACLE_SSH_KEY` | Contents of your `.key` file (open in Notepad, copy all) |

### 9.3 — Push to Test

```powershell
# On your laptop
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions auto-deploy"
git push
```

Go to GitHub → **Actions tab** — you should see it deploying. ✅

---

## ═══════════════════════════════════════════════════════
## DAILY MANAGEMENT COMMANDS
## ═══════════════════════════════════════════════════════

SSH into the VM first: `ssh geoface`

```bash
# ── Check Status ──────────────────────────────────────────────────────────────
docker compose ps

# ── Live Logs ─────────────────────────────────────────────────────────────────
docker compose logs -f          # All services
docker compose logs -f api      # Only Flask API
docker compose logs -f db       # Only database

# ── Restart Services ──────────────────────────────────────────────────────────
docker compose restart          # Restart all
docker compose restart api      # Restart only Flask

# ── Update from GitHub ────────────────────────────────────────────────────────
cd /home/ubuntu/geoface
git pull origin main
docker compose up -d --build

# ── Stop Everything ───────────────────────────────────────────────────────────
docker compose down

# ── System Health ─────────────────────────────────────────────────────────────
df -h          # Disk usage
free -h        # Memory usage
htop           # Live CPU / memory monitor (press q to exit)

# ── Database Backup ───────────────────────────────────────────────────────────
docker exec geoface_db pg_dump -U geoface_user geoface_db > backup_$(date +%F).sql
```

---

## ═══════════════════════════════════════════════════════
## TROUBLESHOOTING
## ═══════════════════════════════════════════════════════

### Problem: `curl http://YOUR_IP/health` times out
**Fix:** Check Oracle Security List — ports 80/443 must be open.
Also check iptables rules:
```bash
sudo iptables -L INPUT -n | grep -E "80|443"
```

### Problem: `docker compose up` fails with "port already in use"
**Fix:**
```bash
sudo lsof -i :80
sudo kill -9 <PID>
docker compose up -d
```

### Problem: API returns 500 errors
**Fix:** Check Flask logs:
```bash
docker compose logs api --tail=50
```

### Problem: App works on phone WiFi but not mobile data
**Fix:** Make sure you're using HTTPS with a real domain (not just an IP). Mobile data networks often block non-standard ports or plain HTTP.

### Problem: Face recognition fails / times out
**Fix:** The insightface model needs to load on first request. Allow 30–60 seconds on first run. Check:
```bash
docker compose logs api | grep -i "insightface\|model\|loaded"
```

---

## ═══════════════════════════════════════════════════════
## FINAL CHECKLIST
## ═══════════════════════════════════════════════════════

- [ ] Oracle Cloud account created
- [ ] VM.Standard.A1.Flex (4 OCPU, 24GB) created in Mumbai
- [ ] Port 80 and 443 opened in Oracle Security List
- [ ] SSH key downloaded and connected successfully
- [ ] Docker + Docker Compose installed on VM
- [ ] Ubuntu iptables opened for port 80/443
- [ ] Repo cloned to `/home/ubuntu/geoface`
- [ ] `.env` file created on VM with production values
- [ ] `docker compose up -d --build` ran successfully
- [ ] All 4 containers show `Up (healthy)` in `docker compose ps`
- [ ] `curl http://VM_IP/health` returns `healthy`
- [ ] Free domain registered + A record pointing to VM IP
- [ ] Certbot SSL certificate installed
- [ ] `curl https://yourdomain.tk/health` returns `healthy`
- [ ] `ALLOWED_ORIGINS` in `.env` updated to your domain
- [ ] Flutter `api_constants.dart` updated to `https://yourdomain.tk/api`
- [ ] Flutter APK built and installed on teacher phones
- [ ] Admin panel accessible at `https://yourdomain.tk/admin/`
- [ ] GitHub Actions auto-deploy set up (optional)

---

## Quick Reference — URLs After Deployment

| What             | URL                                   |
|------------------|---------------------------------------|
| Admin Panel      | `https://yourdomain.tk/admin/`        |
| Teacher Portal   | `https://yourdomain.tk/teacher/`      |
| API Health Check | `https://yourdomain.tk/health`        |
| API Root         | `https://yourdomain.tk/api/`          |

**Admin Login:**
- Registration No: `123456` (from `.env` HEAD_ADMIN_REG_NO)
- Password: `admin@2000` (from `.env` ADMIN_PASSWORD)

---

*Total cost: $0.00/month. Runs 24/7 without your laptop being on.*
