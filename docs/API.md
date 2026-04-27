# GeoFace Faculty Authentication System — API Reference

Base URL: `https://api.geoface.yourdomain.com`

All protected endpoints require the header:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Endpoints

### `GET /health`
Health check (public).

**Response 200**
```json
{
  "status": "healthy",
  "service": "GeoFace Faculty Authentication System",
  "timestamp": "2026-04-13T10:00:00+00:00"
}
```

---

### `POST /login`
Authenticate a teacher and receive a JWT.

**Request**
```json
{
  "email": "teacher@college.edu",
  "password": "YourPassword123"
}
```

**Response 200 — Success**
```json
{
  "token": "eyJhbGci...",
  "expires_in": 86400,
  "teacher": {
    "teacher_id": "uuid",
    "full_name": "Dr. Jane Smith",
    "email": "teacher@college.edu",
    "is_active": true,
    "has_face_encoding": true,
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**Response 400** — Validation error
```json
{ "error": "Invalid email format" }
```

**Response 401** — Wrong credentials
```json
{ "error": "Invalid credentials" }
```

---

### `POST /verify`
Run the full AI verification pipeline (JWT required).

**Headers**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request**
```json
{
  "frames":    ["<base64-jpeg>", "..."],
  "latitude":  10.8501,
  "longitude": 76.2714,
  "timestamp": 1712994533.123
}
```

| Field       | Type      | Description                               |
|-------------|-----------|-------------------------------------------|
| `frames`    | `string[]`| 1–25 base64-encoded JPEG frames           |
| `latitude`  | `number`  | Device GPS latitude                       |
| `longitude` | `number`  | Device GPS longitude                      |
| `timestamp` | `number`  | UNIX epoch seconds (must be ≤30s old)     |

**Response 200 — Verified**
```json
{
  "status": "success",
  "reason": "Verification successful",
  "timestamp": "2026-04-13T10:00:00+00:00",
  "details": {
    "face_distance":  0.3812,
    "face_frames":    22,
    "total_frames":   25,
    "gps_distance_m": 48.5
  }
}
```

**Response 200 — Rejected** (HTTP 200, status field = "failure")
```json
{
  "status": "failure",
  "reason": "Outside college premises (distance: 350m, allowed: 200m)",
  "timestamp": "2026-04-13T10:00:00+00:00"
}
```

**Possible failure reasons**

| Reason | Stage |
|--------|-------|
| `Outside college premises (distance: Xm, allowed: 200m)` | Geofencing |
| `Face not detected in enough frames (N/25, need 60%)` | Face detection |
| `Face mismatch (distance: 0.72, threshold: 0.6)` | Face recognition |
| `Liveness check failed: no blink detected` | Liveness |
| `Liveness check failed: no head movement detected` | Liveness |
| `Request timestamp is stale. Possible replay attack.` | Replay guard |

**Response 400** — Invalid payload
```json
{ "status": "failure", "reason": "GPS coordinates are required" }
```

**Response 401** — Invalid token
```json
{ "msg": "Token has expired" }
```

---

## Admin Endpoints

All admin endpoints require an admin JWT (from `POST /admin/login`).

### `POST /admin/login`
```json
// Request
{ "email": "admin@college.edu", "password": "AdminPass@123" }

// Response
{ "token": "...", "expires_in": 28800 }
```

### `GET /admin/teachers`
Returns all teachers.
```json
{
  "teachers": [{ "teacher_id": "...", "full_name": "...", ... }],
  "total": 12
}
```

### `POST /admin/teachers`
Register a new teacher.
```json
// Body
{
  "full_name": "Dr. John Doe",
  "email": "jdoe@college.edu",
  "password": "SecurePass@123",
  "face_encoding": [0.123, -0.456, ...]     // 128 floats (optional at registration)
}
```

### `PATCH /admin/teachers/<teacher_id>`
```json
{ "is_active": false }
{ "face_encoding": [...128 floats...] }
{ "full_name": "Updated Name" }
```

### `DELETE /admin/teachers/<teacher_id>`
Soft-deactivates the teacher.

### `GET /admin/attendance`
**Query params:** `page`, `per_page`, `status`, `teacher_id`, `date_from`, `date_to`
```json
{
  "logs": [{ "id": "...", "status": "success", "reason": "...", ... }],
  "total": 150,
  "page": 1,
  "pages": 6
}
```

### `GET /admin/stats`
Dashboard metrics.
```json
{
  "total_teachers": 24,
  "total_logs": 1450,
  "today_success": 18,
  "today_failure": 3,
  "overall_success_rate": 87.5,
  "failure_by_stage": {
    "geofence": 12,
    "face_recognition": 8,
    "liveness": 5
  }
}
```

### `POST /admin/encode-face`
```json
// Request (from webcam capture)
{ "image": "<base64-jpeg>" }

// Response
{ "encoding": [0.123, ...128 floats..., -0.456] }
```
