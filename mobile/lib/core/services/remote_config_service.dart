// GeoFace Faculty Authentication System - Remote Config Service
// Fetches the live server URL from GitHub on every app start.
// To change the URL: just update config/app_config.json on GitHub.
// NO APK REBUILD NEEDED.

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class RemoteConfigService {
  RemoteConfigService._();

  // ── GitHub raw URL to your config file ─────────────────────────────────────
  // This is the public raw URL to config/app_config.json in your GitHub repo.
  static String get _configUrl =>
      'https://raw.githubusercontent.com/ShanuZz334/GeoFensing/main/config/app_config.json?v=${DateTime.now().millisecondsSinceEpoch}';

  // ── Fallback URL if GitHub is unreachable ───────────────────────────────────
  // This is used offline or if GitHub fetch fails.
  static const String _fallbackUrl = 'http://localhost/api';

  static const String _cacheKey = 'cached_base_url';
  static const _storage = FlutterSecureStorage();

  static String _baseUrl = _fallbackUrl;

  /// Call this once in main() before runApp().
  /// Fetches the latest URL from GitHub and caches it on device.
  static Future<void> initialize() async {
    // FORCE LOCALHOST FOR TESTING (Bypasses GitHub 429 errors and cache)
    _baseUrl = 'http://localhost/api';
    return;
    
    try {
      final response = await http
          .get(Uri.parse(_configUrl))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        String body = response.body;
        if (body.startsWith('\ufeff')) {
          body = body.substring(1);
        }
        final json = jsonDecode(body) as Map<String, dynamic>;
        final url = json['base_url'] as String?;
        if (url != null && url.isNotEmpty) {
          _baseUrl = url;
          // Cache on device so it works offline after first fetch
          try {
            await _storage.write(key: _cacheKey, value: url);
          } catch (_) {}
          return;
        }
      }
    } catch (_) {
      // GitHub unreachable — try cached URL from last successful fetch
    }

    // Try last cached URL
    try {
      final cached = await _storage.read(key: _cacheKey);
      if (cached != null && cached.isNotEmpty) {
        _baseUrl = cached;
      }
    } catch (_) {
      // Fallback to hardcoded URL on storage error
    }
  }

  /// The live base URL to use for all API calls.
  static String get baseUrl => _baseUrl;
}
