// GeoFace Faculty Authentication System - API Constants

import '../services/remote_config_service.dart';

class ApiConstants {
  ApiConstants._();

  // ── Base URL ──────────────────────────────────────────────────────────────
  // Permanent Institutional URL. Pointing directly to our Cloudflare Tunnel.
  static String get baseUrl => 'https://api.praxistrade.website/api';

  // ── Endpoints ──────────────────────────────────────────────────────────────
  static const String login = '/login';
  static const String verify = '/verify';
  static const String health = '/health';
  static const String attendance = '/attendance';

  // ── Timeouts ──────────────────────────────────────────────────────────────
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration verifyTimeout = Duration(seconds: 90); // AI pipeline

  // ── Secure Storage Keys ───────────────────────────────────────────────────
  static const String tokenKey = 'auth_token';
  static const String teacherKey = 'teacher_data';

  // ── Verification Settings ─────────────────────────────────────────────────
  static const int recordDurationSeconds = 3;
  static const int targetFPS = 4;
  static const int maxFrames = 12;
  static const int jpegQuality = 75; // JPEG compression quality (0-100)
}
