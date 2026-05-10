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
  static const String _configUrl =
      'https://raw.githubusercontent.com/ShanuZz334/GeoFensing/main/config/app_config.json';

  // ── Fallback URL if GitHub is unreachable ───────────────────────────────────
  // This is used offline or if GitHub fetch fails.
  static const String _fallbackUrl = 'https://maui-bacon-tony-fri.trycloudflare.com/api';

  static const String _cacheKey = 'cached_base_url';
  static const _storage = FlutterSecureStorage();

  static String _baseUrl = _fallbackUrl;

  /// Call this once in main() before runApp().
  /// Fetches the latest URL from GitHub and caches it on device.
  static Future<void> initialize() async {
    try {
      final response = await http
          .get(Uri.parse(_configUrl))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        final url = json['base_url'] as String?;
        if (url != null && url.isNotEmpty) {
          _baseUrl = url;
          // Cache on device so it works offline after first fetch
          await _storage.write(key: _cacheKey, value: url);
          return;
        }
      }
    } catch (_) {
      // GitHub unreachable — try cached URL from last successful fetch
    }

    // Try last cached URL
    final cached = await _storage.read(key: _cacheKey);
    if (cached != null && cached.isNotEmpty) {
      _baseUrl = cached;
    }
    // else fall back to the hardcoded fallback above
  }

  /// The live base URL to use for all API calls.
  static String get baseUrl => _baseUrl;
}
