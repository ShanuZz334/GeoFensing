# GeoFace System Diagrams

Below are the architectural and workflow diagrams for the GeoFace attendance system.

## Fig. 1. Comparison of Traditional Attendance Systems and Proposed GeoFace System

```text
┌────────────────────────────────────────────────────────┐
│  Traditional Attendance System                         │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ Employee/ │→ │ Manual Log/ │→ │ Local Database/  │  │
│  │ Student   │  │ ID Card     │  │ Admin Reporting  │  │
│  └───────────┘  └──────┬──────┘  └──────────────────┘  │
│                        │                               │
│                   [Issues: Proxy, Queues, Hardware]    │
└────────────────────────────────────────────────────────┘
                              VS
┌────────────────────────────────────────────────────────┐
│  Proposed GeoFace System                               │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ User with │→ │ GeoFace App │→ │ Live Admin       │  │
│  │ Smartphone│  │ (GPS + Face)│  │ Dashboard        │  │
│  └───────────┘  └──────┬──────┘  └───────▲──────────┘  │
│                        │                 │             │
│                        ▼                 │             │
│               ┌─────────────────┐        │             │
│               │ Cloud Backend   │────────┘             │
│               │ (Geofencing &   │                      │
│               │  Face AI DB)    │                      │
│               └─────────────────┘                      │
└────────────────────────────────────────────────────────┘
```

---

## Fig. 2. GeoFace System Architecture Diagram

```text
┌─────────────────────────┐         ┌────────────────────────┐
│      Client Layer       │         │    Admin Interface     │
│  ┌───────────────────┐  │         │  ┌──────────────────┐  │
│  │ Flutter Mobile App│  │         │  │ React/Vue Web App│  │
│  └────────┬──────────┘  │         │  └────────┬─────────┘  │
└───────────┼─────────────┘         └───────────┼────────────┘
            │ HTTPS / REST API                  │ HTTPS
            ▼                                   ▼
┌────────────────────────────────────────────────────────────┐
│                  Nginx Reverse Proxy                       │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  Backend Services (Flask/Django)           │
│                                                            │
│  ┌───────────────┐ ┌────────────────┐ ┌─────────────────┐  │
│  │ Auth Service  │ │ Geofence Logic │ │ Face Rec Engine │  │
│  └───────────────┘ └────────────────┘ └─────────────────┘  │
└──────────────┬─────────────────────────────────┬───────────┘
               │ Read/Write                      │ Fast I/O
               ▼                                 ▼
┌─────────────────────────────┐    ┌─────────────────────────┐
│     PostgreSQL Database     │    │      Redis Cache        │
│  - Users & Profiles         │    │  - Session tokens       │
│  - Geofence Coordinates     │    │  - Rate limiting        │
│  - Attendance Logs          │    │                         │
└─────────────────────────────┘    └─────────────────────────┘
```

---

## Fig. 3. GeoFace Authentication Workflow

```text
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Location Check (Mobile)                       │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │ Request      │────►│ Capture Device GPS Lat/Lng   │  │
│  │ Check-in     │     └──────────────┬───────────────┘  │
│  └──────────────┘                    │                  │
└──────────────────────────────────────┼──────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Geofence Validation (Backend API)             │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │ Retrieve     │◄────│ Validate User Location       │  │
│  │ Geofence DB  │     │ against Target Radius        │  │
│  └──────────────┘     └──────────────┬───────────────┘  │
└──────────────────────────────────────┼──────────────────┘
                                       │
                     ┌─────────────────┴──────────────────┐
                 [Fail]                                 [Pass]
                   ▼                                      ▼
        ┌───────────────────┐               ┌───────────────────────────┐
        │ ✗ Check-in Denied │               │ Phase 3: Biometric Capture│
        │ (Outside Area)    │               │ ┌───────────────────────┐ │
        └───────────────────┘               │ │ Prompt & Capture Face │ │
                                            │ └───────────┬───────────┘ │
                                            └─────────────┼─────────────┘
                                                          │ HTTPS POST
                                                          ▼
┌───────────────────────────────────────────────────────────────────────┐
│  Phase 4: Face Recognition & Logging (Backend API + Database)         │
│  ┌────────────────┐    ┌─────────────────┐    ┌────────────────────┐  │
│  │ Process Image  │───►│ DB Compare Face │───►│ Log Attendance     │  │
│  │ (AI Engine)    │    │ Vector / Profile│    │ Record on Success  │  │
│  └────────────────┘    └─────────────────┘    └─────────┬──────────┘  │
└─────────────────────────────────────────────────────────┼─────────────┘
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │  ✓ Success UI Shown       │
                                            │    to User                │
                                            └───────────────────────────┘
```

---

## Fig. 4. Geofencing and Location Validation Model

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Start Location Check                                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Obtain Device Coordinates: (UserLat, UserLng)            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Fetch Target Geofence Area: (TargetLat, TargetLng)       │
│    Allowed Radius: X meters                                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Calculate Distance via Haversine Formula                 │
│    Distance = R * c (where R = Earth's radius)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    ┌──────────┴───────────┐
                    │ Is Distance <= Radius?│
                    └────┬────────────┬────┘
                         │            │
                    [YES]│            │[NO]
                         ▼            ▼
┌─────────────────────────┐          ┌────────────────────────┐
│ Location Valid          │          │ Location Invalid       │
│ Proceed to Face Scan    │          │ Reject Check-in Attempt│
└─────────────────────────┘          └────────────────────────┘
```
