/// GeoFace App Configuration
///
/// [kDemoEnabled] controls whether the Demo Mode toggle is visible in the UI.
///
/// ┌─────────────────────────────────────────────────────────────┐
/// │  FOR RELEASE / TEACHER BUILD  →  set kDemoEnabled = false   │
/// │  FOR YOUR PERSONAL ADMIN BUILD → set kDemoEnabled = true    │
/// └─────────────────────────────────────────────────────────────┘
///
/// This is a compile-time constant, so when false the entire demo
/// UI tree is dead-code-eliminated from the release APK.
const bool kDemoEnabled = false;
