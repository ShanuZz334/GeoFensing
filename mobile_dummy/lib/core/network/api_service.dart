import 'dart:async';

import '../constants/api_constants.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  ApiService._();
  static final ApiService _instance = ApiService._();
  static ApiService get instance => _instance;

  final _storage = const FlutterSecureStorage();

  Future<String?> _getToken() => _storage.read(key: ApiConstants.tokenKey);

  // Mock latency for realism
  Future<void> _delay() => Future.delayed(const Duration(milliseconds: 800));

  /// POST /login
  Future<ApiResponse> login(String regNo, String password, String deviceId) async {
    await _delay();
    return ApiResponse.success({
      'token': 'dummy_jwt_token',
      'teacher': {
        'teacher_id': '1',
        'full_name': 'Ms. Divya Nair',
        'reg_no': regNo.isNotEmpty ? regNo : 'TCH003',
        'department': 'Electronics',
        'role': 'teacher',
        'email': 'divyan@geoface.edu.in',
        'phone_no': '+91 9876543210',
        'is_active': true,
        'has_face_encoding': true,
        'profile_pic': 'https://i.pravatar.cc/150?img=23',
        'monthly_allotted_leaves': 3,
        'monthly_allotted_half_leaves': 4,
        'extra_monthly_leaves': 0,
        'extra_half_monthly_leaves': 0,
      }
    });
  }

  /// POST /logout
  Future<void> logout() async {
    await _delay();
    // Do nothing, just simulate delay
  }

  /// POST /reset-password
  Future<ApiResponse> resetPassword(String regNo, String totp, String newPassword) async {
    await _delay();
    return ApiResponse.success({'message': 'Password reset successfully'});
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
    await _delay();
    
    // Always succeed in dummy mode
    return ApiResponse.success({
      'status': 'success',
      'action_type': 'check_in',
      'reason': 'Verification successful (Dummy Mode)',
      'attendance_mark': 'present',
      'log': {
        'id': 999,
        'timestamp': DateTime.now().toIso8601String(),
        'status': 'success',
        'reason': 'Verification successful',
        'action_type': 'check_in',
        'latitude': latitude,
        'longitude': longitude,
        'frames_count': frames.length,
      }
    });
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
    await _delay();
    return ApiResponse.success({
      'message': 'Setup completed successfully (Dummy)',
      'teacher': {
        'teacher_id': '1',
        'full_name': fullName.isNotEmpty ? fullName : 'Ms. Divya Nair',
        'reg_no': 'TCH003',
        'department': department.isNotEmpty ? department : 'Electronics',
        'role': role.isNotEmpty ? role : 'teacher',
        'email': email.isNotEmpty ? email : 'divyan@geoface.edu.in',
        'phone_no': phoneNo.isNotEmpty ? phoneNo : '+91 9876543210',
        'is_active': true,
        'has_face_encoding': true,
        'profile_pic': 'https://i.pravatar.cc/150?img=23',
      }
    });
  }

  /// PATCH /profile/update
  Future<ApiResponse> updateProfile({
    String? email,
    String? phoneNo,
    String? password,
    String? profilePicBase64,
  }) async {
    await _delay();
    return ApiResponse.success({
      'message': 'Profile updated successfully',
      'teacher': {
        'teacher_id': '1',
        'full_name': 'Ms. Divya Nair',
        'reg_no': 'TCH003',
        'department': 'Electronics',
        'role': 'teacher',
        'email': email ?? 'divyan@geoface.edu.in',
        'phone_no': phoneNo ?? '+91 9876543210',
        'is_active': true,
        'has_face_encoding': true,
        'profile_pic': 'https://i.pravatar.cc/150?img=23',
      }
    });
  }

  /// GET /attendance
  Future<ApiResponse> getAttendance() async {
    await _delay();
    final now = DateTime.now();
    return ApiResponse.success({
      'page': 1,
      'pages': 1,
      'total': 15,
      'logs': List.generate(15, (index) {
        final isSuccess = index % 4 != 3; // 1 out of 4 is failure
        final isCheckOut = index % 2 != 0;
        return {
          'id': '${100 + index}',
          'teacher_id': '1',
          'teacher_name': 'Ms. Divya Nair',
          'reg_no': 'TCH003',
          'profile_pic': 'https://i.pravatar.cc/150?img=23',
          'timestamp': now.subtract(Duration(days: index ~/ 2, hours: isCheckOut ? 8 : 0)).toIso8601String(),
          'status': isSuccess ? 'success' : 'failure',
          'reason': isSuccess ? 'Verification successful' : 'Liveness check failed',
          'action_type': isCheckOut ? 'check_out' : 'check_in',
          'attendance_mark': isSuccess ? 'present' : null,
          'latitude': 31.2536 + (index * 0.0001),
          'longitude': 75.7037 + (index * 0.0001),
          'frames_count': isSuccess ? 5 : 2,
        };
      })
    });
  }

  /// GET /attendance/stats
  Future<ApiResponse> getAttendanceStats() async {
    await _delay();
    return ApiResponse.success({
      'attendance_percentage': 92.5,
      'successful_scans': 142,
      'failed_scans': 8,
      'current_streak': 15,
      'longest_streak': 28,
      'recent_trend': 'up',
      'remaining_leaves': 1,
      'remaining_half_leaves': 2,
    });
  }

  /// GET /me
  Future<ApiResponse> fetchMe() async {
    await _delay();
    return ApiResponse.success({
      'teacher': {
        'teacher_id': '1',
        'full_name': 'Ms. Divya Nair',
        'reg_no': 'TCH003',
        'department': 'Electronics',
        'role': 'teacher',
        'email': 'divyan@geoface.edu.in',
        'phone_no': '+91 9876543210',
        'is_active': true,
        'has_face_encoding': true,
        'profile_pic': 'https://i.pravatar.cc/150?img=23',
        'monthly_allotted_leaves': 3,
        'monthly_allotted_half_leaves': 4,
        'extra_monthly_leaves': 0,
        'extra_half_monthly_leaves': 0,
      }
    });
  }

  /// GET /settings
  Future<ApiResponse> getSettings() async {
    await _delay();
    return ApiResponse.success({
      'demo_mode': false,
      'attendance_rules': {
        'class_start': '09:00',
        'class_end': '17:00',
        'half_day_limit': '13:00',
        'absent_limit': '14:30',
        'half_day_checkout_limit': '14:00',
        'anytime_checkout_full_day': false,
        'min_working_hours': 4,
      },
      'verification_limits': {
        'max_checkin_attempts': 5,
        'max_checkout_attempts': 10,
        'totp_duration': 300,
      },
      'monthly_allotted_leaves': 3,
      'monthly_allotted_half_leaves': 4,
      'semester_start_date': '2025-07-01',
      'semester_end_date': '2025-11-30',
      'support_contact': {
        'email': 'admin@geoface.edu.in',
        'phone': '+91 98765 43210',
      },
      'geofence_config': {
        'mode': 1,
        'main_polygon': [
          [31.2560, 75.7037],
          [31.2548, 75.7075],
          [31.2512, 75.7075],
          [31.2500, 75.7037],
          [31.2512, 75.6999],
          [31.2548, 75.6999],
        ],
        'sub_polygons': [],
        'checkpoints': [],
      }
    });
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
