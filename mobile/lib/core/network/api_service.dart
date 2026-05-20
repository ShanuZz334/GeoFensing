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
  Future<ApiResponse> login(String regNo, String password, String deviceId) async {
    try {
      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.login}'),
            headers: _baseHeaders(),
            body: jsonEncode({'reg_no': regNo, 'password': password, 'device_id': deviceId}),
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

  /// POST /logout
  Future<void> logout() async {
    try {
      final token = await _getToken();
      if (token == null) return;
      await http.post(
        Uri.parse('${ApiConstants.baseUrl}/logout'),
        headers: _baseHeaders(auth: true, token: token),
      ).timeout(const Duration(seconds: 5));
    } catch (_) {
      // Ignore errors during logout (e.g. no connection)
    }
  }

  /// POST /reset-password
  Future<ApiResponse> resetPassword(String regNo, String totp, String newPassword) async {
    try {
      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}/reset-password'),
            headers: _baseHeaders(),
            body: jsonEncode({
              'reg_no': regNo,
              'totp': totp,
              'new_password': newPassword,
            }),
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
    bool bypassLimits = false,
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
      if (bypassLimits) body['bypass_limits'] = true;

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

  /// PATCH /complete_setup
  Future<ApiResponse> completeSetup({
    required String fullName,
    required String email,
    required String department,
    required String role,
    required String phoneNo,
    required String newPassword,
    required String profilePicBase64,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse.error('Not authenticated');

      final body = {
        'full_name': fullName,
        'email': email,
        'department': department,
        'role': role,
        'phone_no': phoneNo,
        'new_password': newPassword,
        'profile_pic': profilePicBase64,
      };

      final response = await http
          .patch(
            Uri.parse('${ApiConstants.baseUrl}/complete_setup'),
            headers: _baseHeaders(auth: true, token: token),
            body: jsonEncode(body),
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

  /// PATCH /profile/update
  Future<ApiResponse> updateProfile({
    String? email,
    String? phoneNo,
    String? password,
    String? profilePicBase64,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse.error('Not authenticated');

      final body = <String, dynamic>{};
      if (email != null) body['email'] = email;
      if (phoneNo != null) body['phone_no'] = phoneNo;
      if (password != null) body['password'] = password;
      if (profilePicBase64 != null) body['profile_pic'] = profilePicBase64;

      final response = await http
          .patch(
            Uri.parse('${ApiConstants.baseUrl}/profile/update'),
            headers: _baseHeaders(auth: true, token: token),
            body: jsonEncode(body),
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

  /// GET /attendance/stats
  Future<ApiResponse> getAttendanceStats() async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse.error('Not authenticated');

      final response = await http
          .get(
            Uri.parse('${ApiConstants.baseUrl}/attendance/stats'),
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

  /// GET /settings
  Future<ApiResponse> getSettings() async {
    try {
      final response = await http
          .get(
            Uri.parse('${ApiConstants.baseUrl}/settings'),
            headers: _baseHeaders(),
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
