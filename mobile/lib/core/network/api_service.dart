import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants/api_constants.dart';

/// Centralized HTTP client that automatically injects the JWT Authorization
/// header and parses JSON responses.
class ApiService {
  ApiService._();
  static final ApiService _instance = ApiService._();
  static ApiService get instance => _instance;

  final _storage = const FlutterSecureStorage();

  Future<String?> _getToken() => _storage.read(key: ApiConstants.tokenKey);

  Map<String, String> _baseHeaders({bool auth = false, String? token}) {
    final headers = {'Content-Type': 'application/json'};
    if (auth && token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  /// POST /login
  Future<ApiResponse> login(String email, String regNo, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.login}'),
            headers: _baseHeaders(),
            body: jsonEncode({'email': email, 'reg_no': regNo, 'password': password}),
          )
          .timeout(ApiConstants.connectTimeout);

      return _parse(response);
    } on SocketException {
      return ApiResponse.error('No internet connection');
    } on TimeoutException {
      return ApiResponse.error('Server timeout. Please try again.');
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  /// POST /verify
  Future<ApiResponse> verify({
    required List<String> frames,
    required double latitude,
    required double longitude,
    required double timestamp,
    double? demoLat,
    double? demoLng,
    double? demoRadius,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse.error('Not authenticated');

      final body = {
        'frames': frames,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': timestamp,
      };

      if (demoLat != null) body['demo_lat'] = demoLat;
      if (demoLng != null) body['demo_lng'] = demoLng;
      if (demoRadius != null) body['demo_radius'] = demoRadius;

      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.verify}'),
            headers: _baseHeaders(auth: true, token: token),
            body: jsonEncode(body),
          )
          .timeout(ApiConstants.verifyTimeout);

      return _parse(response);
    } on SocketException {
      return ApiResponse.error('No internet connection');
    } on TimeoutException {
      return ApiResponse.error('Verification timed out. Please retry.');
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  /// GET /attendance
  Future<ApiResponse> getAttendance() async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse.error('Not authenticated');

      final response = await http
          .get(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.attendance}'),
            headers: _baseHeaders(auth: true, token: token),
          )
          .timeout(ApiConstants.connectTimeout);

      return _parse(response);
    } on SocketException {
      return ApiResponse.error('No internet connection');
    } on TimeoutException {
      return ApiResponse.error('Server timeout. Please try again.');
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  ApiResponse _parse(http.Response response) {
    try {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return ApiResponse.success(body);
      } else {
        final error = body['error'] ?? body['reason'] ?? 'Server error ${response.statusCode}';
        return ApiResponse.error(error.toString());
      }
    } catch (_) {
      return ApiResponse.error('Invalid server response');
    }
  }
}

class ApiResponse {
  final bool success;
  final Map<String, dynamic>? data;
  final String? errorMessage;

  const ApiResponse._({required this.success, this.data, this.errorMessage});

  factory ApiResponse.success(Map<String, dynamic> data) =>
      ApiResponse._(success: true, data: data);

  factory ApiResponse.error(String message) =>
      ApiResponse._(success: false, errorMessage: message);
}
