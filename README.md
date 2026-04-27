# GeoFace Faculty Authentication System

> Production-ready college faculty verification using **real-time face recognition + GPS geofencing**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.19-blue)](https://flutter.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791)](https://postgresql.org)

---

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│  Flutter Mobile App                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │  Login   │→│  Camera   │→│  Result Screen       │  │
│  │  Screen  │  │ + GPS     │  │  ✓ Success / ✗ Fail │  │
│  └──────────┘  └───────────┘  └──────────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS POST /verify
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Flask Backend API (Gunicorn + Nginx)                    │
│                                                          │
│  1. JWT Validation       4. Face Recognition            │
│  2. Replay Attack Guard  5. Liveness Detection          │
│  3. GPS Geofencing       6. Attendance Logging          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  PostgreSQL DB      │
              │  teachers           │
              │  attendance_logs    │
              └─────────────────────┘
```

## Features

| Feature | Implementation |
|---|---|
| Face Authentication | `face_recognition` + OpenCV HOG detector |
| Liveness Detection | EAR blink (dlib 68-pt landmarks) + head movement |
| GPS Geofencing | Haversine formula, 200m campus radius |
| Replay Attack Guard | UNIX timestamp freshness ≤30s |
| Authentication | JWT (24h expiry) + bcrypt password hashing |
| Admin Panel | Web-based, live webcam face capture, Chart.js stats |
| Mobile App | Flutter, camera + GPS, dark mode, animated UI |

## Project Structure

```
GeoFense/
├── backend/          Flask API + AI services
│   ├── app/
│   │   ├── models/   Teacher, AttendanceLog (SQLAlchemy)
│   │   ├── routes/   auth.py, verify.py, admin.py
│   │   └── services/ face_service, geo_service, liveness_service, jwt_service
│   ├── database/     schema.sql (PostgreSQL)
│   └── docs/
├── mobile/           Flutter app (Android + iOS)
│   └── lib/
│       ├── features/ auth/, verification/
│       └── core/     theme, network, constants
├── admin/            Web admin panel (HTML/CSS/JS)
└── docs/             API.md, SETUP.md, DEPLOYMENT.md
```

## Quick Start

See [docs/SETUP.md](docs/SETUP.md) for full instructions.

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install dlib==19.24.4 && pip install -r requirements.txt
cp .env.example .env   # Fill in your values
python run.py

# Flutter app
cd mobile && flutter pub get && flutter run

# Admin panel
cd admin && python -m http.server 8080
```

## College GPS Coordinates

| Setting | Value |
|---|---|
| College Center | lat: **10.8505**, lon: **76.2711** |
| Allowed Radius | **200 meters** |

To change the coordinates, update `COLLEGE_LATITUDE` and `COLLEGE_LONGITUDE` in `.env`.

## License

MIT — for educational and institutional use.
