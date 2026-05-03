# GeoFense Biometric Attendance System
**Full Project Specification & Feature Report**

---

## 1. Executive Summary
**GeoFense** (formerly known under the working title *GeoFace*) is a full-stack, enterprise-grade attendance verification system specifically tailored for institutional settings (e.g., LPU). It relies on two fundamental pillars of security: **Facial Biometrics** and **Geofencing**.

The system securely verifies the identity of the user via high-dimensional facial embeddings and simultaneously guarantees that the user is physically located within the designated institutional boundaries. The ecosystem comprises a Dockerized backend API, a modern JavaScript/HTML Admin portal, and a cross-platform Flutter mobile application.

---

## 2. Core Modules & Architecture

### 2.1 Backend API Layer
- **Framework:** Python / Flask
- **Database:** PostgreSQL (with SQLAlchemy ORM)
- **Containerization:** Fully containerized using Docker & Docker Compose for rapid, consistent deployments.
- **Biometric Engine:** Integrated with the **InsightFace** library (using the `buffalo_l` 512-dimensional embedding model) for robust face detection, extraction, and comparison.
- **Geospatial Engine:** Utilizes polygon-based point-in-polygon logic to determine if latitude/longitude coordinates fall strictly within boundaries defined by the administrators.
- **Authentication:** JWT-based stateless authentication with Hardware/Device ID binding for mobile clients to prevent account sharing and spoofing.

### 2.2 Administrator Portal
- **Tech Stack:** Vanilla JavaScript, HTML5, CSS3.
- **Map Integration:** Leaflet.js integration allowing administrators to visually draw, edit, and save complex polygonal geofences.
- **Dashboard:** Interactive analytics and summary charts (using Chart.js) depicting daily check-in successes, failures, and flagged attempts.
- **Design System:** Custom Dark Theme UI with bespoke asynchronous Modals (`uiAlert`, `uiConfirm`), completely eliminating native browser dialogs.

### 2.3 Mobile Teacher Application
- **Tech Stack:** Flutter / Dart (Supports both Android/iOS and Web compiling).
- **Core Capabilities:** Real-time camera feeds, device location access, secure local storage for JWT tokens, and device identifiers.
- **Branding:** Customized "LPU" branding with signature Deep Violet gradients.
- **User Experience:** Provides direct feedback on verification status, failure limits, and support contact details upon lockout.

---

## 3. Comprehensive Feature Specifications

### 3.1 Security & Verification
*   **Dual-Factor Verification:** Every check-in/out attempt requires both a matching face (cosine similarity > threshold) and a valid GPS coordinate within the geofence.
*   **Device Binding:** The system binds the user's login to a unique Device ID to ensure attendance cannot be spoofed by sharing credentials across multiple devices.
*   **Limit Enforcement:** To prevent brute-forcing of the biometric system:
    *   Maximum Failed Check-Ins (default: 4 attempts).
    *   Maximum Failed Check-Outs (default: 10 attempts).
    *   Upon exhaustion, the user is locked out and directed to contact support.

### 3.2 Time-Based Attendance Rules
The system autonomously resolves whether a teacher gets a **Full Day**, **Half Day**, or **Absent** mark based on configurable timestamps:
*   **Class Start Time:** The designated beginning of the day.
*   **Half-Day Check-in Limit:** Scanning *after* this time automatically grants only a Half Day. Scanning slightly before might flag the user for manual review.
*   **Absent Check-in Limit:** Scanning *after* this time results in an automatic Absent mark.
*   **Anytime Check-out Flag:** If toggled ON, the user receives their designated day-mark regardless of when they leave.
*   **Half-Day Check-out Limit:** If "Anytime Check-out" is OFF, checking out *before* this time penalizes the user with a Half Day.

### 3.3 Dynamic Settings & Configuration
Administrators can modify system behaviors *without* redeploying or restarting the backend servers.
*   Modifiable settings include Class Start Time, limits for Check-ins/Check-outs, and precise Geofence Polygon coordinates.
*   These settings are intercepted on the fly by the verification pipeline.

### 3.4 Attendance Aggregation & Conflict Resolution
*   **Daily Roll-Up:** The backend parses raw `/admin/attendance/logs` into a clean, consolidated history per teacher per day, keeping track of their *last successful* action (Check-in vs Check-out).
*   **Flagged Statuses:** Marginal cases (e.g., late arrivals) are categorized as "Flagged". Administrators can manually review these in the portal and click a button to resolve them as Present, Half Day, or Absent.
*   **CSV Export:** Total logs can be downloaded directly from the Admin Panel for external payroll/HR processing.

### 3.5 UI / UX Polish & Optimization
*   **Premium Map Markers:** Admin maps feature custom 3D HTML divIcons with pulsing animations for Check-ins (Violet), Check-outs (Purple), and Failures (Red).
*   **Seamless Gradients:** Mobile screens use optimized `Positioned.fill` linear gradients ensuring 60fps animations.
*   **Asynchronous UX:** Admin actions feature non-blocking, Promise-based modal interactions (`await uiConfirm`) maintaining a sleek, application-like feel.

---

## 4. Operational Requirements & Scaling
*   **Biometric Models:** Requires mounting the InsightFace `buffalo_l` model inside the container to avoid runtime downloads.
*   **Environment Validation:** Deployment mandates Docker Compose with sufficient resources (min 2GB RAM for Python ML dependencies like `onnxruntime`).
*   **Database Scaling:** Relational tables natively support indexing on `teacher_id` and `timestamp` for scaling queries over 10,000+ daily log entries.

---
*Generated by System - GeoFense Engineering Documentation*
