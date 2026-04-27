# GeoFace Faculty Authentication System — Setup Guide

## Prerequisites

### System Requirements
- Python 3.10+
- PostgreSQL 14+
- Flutter SDK 3.19+
- CMake 3.x (required by dlib)
- Git

---

## 1. Backend Setup

### 1.1 Clone & Prepare Virtual Environment

```bash
cd GeoFense/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 1.2 Install dlib (Platform-specific)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
pip install dlib==19.24.4
```

**macOS:**
```bash
brew install cmake
pip install dlib==19.24.4
```

**Windows:**
```powershell
# Install Visual Studio Build Tools first from:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Then:
pip install cmake
pip install dlib==19.24.4
```

### 1.3 Install All Dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Download dlib Shape Predictor Model

```bash
mkdir -p models
cd models

# Download from dlib.net
curl -L -o shape_predictor_68_face_landmarks.dat.bz2 \
  http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

# Extract (Linux/macOS)
bunzip2 shape_predictor_68_face_landmarks.dat.bz2

# Windows (using 7-Zip or bunzip2)
# 7z e shape_predictor_68_face_landmarks.dat.bz2

cd ..
```

### 1.5 Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
nano .env
```

Required values to set:
```
SECRET_KEY=<32+ random chars>
JWT_SECRET_KEY=<32+ random chars, different from above>
DATABASE_URL=postgresql://USER:PASS@HOST:5432/DBNAME
ADMIN_EMAIL=admin@yourcollege.edu
ADMIN_PASSWORD=<strong password>
```

### 1.6 Set Up PostgreSQL Database

```bash
# Create database
psql -U postgres -c "CREATE USER geoface_user WITH PASSWORD 'geoface_pass';"
psql -U postgres -c "CREATE DATABASE geoface_db OWNER geoface_user;"

# Apply schema
psql -U geoface_user -d geoface_db -f database/schema.sql
```

### 1.7 Run the Backend (Development)

```bash
export FLASK_ENV=development
python run.py
```

Server runs at `http://localhost:5000`

Test the health endpoint:
```bash
curl http://localhost:5000/health
```

---

## 2. Flutter App Setup

### 2.1 Install Flutter SDK
Follow: https://docs.flutter.dev/get-started/install

### 2.2 Verify Installation
```bash
flutter doctor
```

### 2.3 Set API URL

Edit `mobile/lib/core/constants/api_constants.dart`:
```dart
// For Android emulator testing (localhost mapping)
static const String baseUrl = 'http://10.0.2.2:5000';

// For production
static const String baseUrl = 'https://api.geoface.yourdomain.com';
```

### 2.4 Install Dependencies
```bash
cd GeoFense/mobile
flutter pub get
```

### 2.5 Run on Device/Emulator
```bash
flutter run
```

### 2.6 Build APK (Release)
```bash
flutter build apk --release
# APK at: build/app/outputs/flutter-apk/app-release.apk
```

### 2.7 Build iOS (macOS only)
```bash
flutter build ipa
```

---

## 3. Admin Panel Setup

The admin panel is purely static HTML/CSS/JS — no build step needed.

### 3.1 Update API Base URL

Edit `admin/js/api.js`:
```javascript
const API_BASE = 'https://api.geoface.yourdomain.com';
```

### 3.2 Serve Locally (optional)
```bash
cd GeoFense/admin
# Python simple server
python -m http.server 8080
# Open: http://localhost:8080
```

---

## 4. First Teacher Registration

1. Open Admin Panel (`/admin/teachers`)
2. Login with `ADMIN_EMAIL` / `ADMIN_PASSWORD`
3. Click **Register Teacher**
4. Fill name, email, password
5. Click **Open Camera** → position your face → **Capture Face**
6. Click **Register**

The teacher can now log in on the Flutter app.

---

## 5. Verify the Full Flow

```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@college.edu","password":"Pass@123"}'

# 2. Use returned token in Authorization header
TOKEN="eyJ..."
curl -X POST http://localhost:5000/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"frames":["<base64>"],"latitude":10.8505,"longitude":76.2711,"timestamp":'"$(date +%s)"'.0}'
```
