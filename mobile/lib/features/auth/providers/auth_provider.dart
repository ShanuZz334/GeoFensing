import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/network/api_service.dart';
import '../../../core/constants/api_constants.dart';
import '../models/user_model.dart';

enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

class AuthProvider extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();

  AuthStatus _status = AuthStatus.initial;
  UserModel? _currentUser;
  String? _errorMessage;
  String? _token;

  AuthStatus get status => _status;
  UserModel? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;
  String? get token => _token;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  AuthProvider() {
    _restoreSession();
  }

  /// Clear persisted session on app launch to enforce security
  Future<void> _restoreSession() async {
    _status = AuthStatus.loading;
    notifyListeners();

    try {
      // Tighten security: require login on every app start
      await _storage.deleteAll();
      _token = null;
      _currentUser = null;
      _status = AuthStatus.unauthenticated;
    } catch (_) {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  /// POST /login
  Future<bool> login(String regNo, String password) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    final response = await ApiService.instance.login(regNo.trim(), password);

    if (response.success && response.data != null) {
      final data = response.data!;
      _token = data['token'] as String;
      _currentUser = UserModel.fromJson(
        data['teacher'] as Map<String, dynamic>,
      );

      // Persist securely
      await _storage.write(key: ApiConstants.tokenKey, value: _token);
      await _storage.write(
        key: ApiConstants.teacherKey,
        value: jsonEncode(_currentUser!.toJson()),
      );

      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } else {
      _errorMessage = response.errorMessage ?? 'Login failed';
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    }
  }

  /// PATCH /complete_setup
  Future<bool> completeSetup({
    required String fullName,
    required String email,
    required String department,
    required String newPassword,
    required String profilePicBase64,
  }) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    final response = await ApiService.instance.completeSetup(
      fullName: fullName,
      email: email,
      department: department,
      newPassword: newPassword,
      profilePicBase64: profilePicBase64,
    );

    if (response.success && response.data != null) {
      final data = response.data!;
      _currentUser = UserModel.fromJson(
        data['teacher'] as Map<String, dynamic>,
      );

      // Update persisted teacher info
      await _storage.write(
        key: ApiConstants.teacherKey,
        value: jsonEncode(_currentUser!.toJson()),
      );

      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } else {
      _errorMessage = response.errorMessage ?? 'Setup failed';
      _status = AuthStatus.authenticated; // Keep authenticated, just show error
      notifyListeners();
      return false;
    }
  }

  /// Sign out and clear secure storage
  Future<void> logout() async {
    await _storage.deleteAll();
    _token = null;
    _currentUser = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
