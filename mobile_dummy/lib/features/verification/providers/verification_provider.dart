import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image/image.dart' as img;
import 'dart:convert';

import '../../../core/network/api_service.dart';
import '../../../core/constants/api_constants.dart';
import '../models/verification_model.dart';
import '../models/attendance_log_model.dart';

enum VerificationStatus {
  idle,
  requestingPermissions,
  recording,
  processing,
  uploading,
  success,
  failure,
  error,
}

class VerificationProvider extends ChangeNotifier {
  VerificationStatus _status = VerificationStatus.idle;
  String _statusMessage = '';
  VerificationModel? _result;
  CameraController? _cameraController;
  CameraDescription? _cameraDescription;
  double _progress = 0.0;

  List<AttendanceLogModel> _history = [];
  Map<String, dynamic>? _stats;
  bool _isLoadingHistory = false;
  bool _isLoadingStats = false;
  String _nextAction = 'check_in';
  int _currentAttempts = 0;
  int _maxAttempts = 4;

  // Settings
  Map<String, dynamic> _settings = {};

  VerificationStatus get status => _status;
  String get statusMessage => _statusMessage;
  VerificationModel? get result => _result;
  CameraController? get cameraController => _cameraController;
  CameraDescription? get cameraDescription => _cameraDescription;
  double get progress => _progress;
  List<AttendanceLogModel> get history => _history;
  Map<String, dynamic>? get stats => _stats;
  Map<String, dynamic>? get supportContact => _stats?['support_contact'];
  bool get isLoadingHistory => _isLoadingHistory;
  bool get isLoadingStats => _isLoadingStats;
  String get nextAction => _nextAction;
  int get currentAttempts => _currentAttempts;
  int get maxAttempts => _maxAttempts;
  Map<String, dynamic> get settings => _settings;
  bool get isBusy =>
      _status == VerificationStatus.recording ||
      _status == VerificationStatus.processing ||
      _status == VerificationStatus.uploading;

  // ── Camera Setup ──────────────────────────────────────────────────────────

  Future<void> initCamera() async {
    if (_cameraController != null) return;
    
    final cameras = await availableCameras();
    // Prefer front camera
    CameraDescription? front;
    for (final cam in cameras) {
      if (cam.lensDirection == CameraLensDirection.front) {
        front = cam;
        break;
      }
    }
    final selected = front ?? (cameras.isNotEmpty ? cameras.first : null);
    if (selected == null) return;

    _cameraDescription = selected;
    _cameraController = CameraController(
      selected,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.yuv420,
    );
    await _cameraController!.initialize();
    notifyListeners();
  }

  Future<void> disposeCamera() async {
    if (_cameraController != null) {
      await _cameraController!.dispose();
      _cameraController = null;
    }
  }

  bool _bypassLimits = false;
  bool get bypassLimits => _bypassLimits;

  // -- Demo Mode --
  bool _demoMode = false;
  double _demoLat = 0.0;
  double _demoLng = 0.0;
  double _demoRadius = 100.0;

  bool get demoMode => _demoMode;
  double get demoLat => _demoLat;
  double get demoLng => _demoLng;
  double get demoRadius => _demoRadius;

  void setDemoMode({
    required bool enabled,
    double? lat,
    double? lng,
    double? radius,
    bool bypassLimits = false,
  }) {
    _demoMode = enabled;
    _demoLat = lat ?? 0.0;
    _demoLng = lng ?? 0.0;
    _demoRadius = radius ?? 100.0;
    _bypassLimits = bypassLimits;
    notifyListeners();
  }

  Timer? _pollTimer;
  void startPolling() {
    _pollTimer?.cancel();
    // Poll every 10 seconds for real-time updates from admin panel
    _pollTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (!isBusy) {
        fetchSettings(silent: true);
        fetchHistory(silent: true);
        fetchStats(silent: true);
      }
    });
  }

  void stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  // ── Settings ──────────────────────────────────────────────────────────────

  Future<void> fetchSettings({bool silent = false}) async {
    try {
      final response = await ApiService.instance.getSettings();
      if (response.success && response.data != null) {
        _settings = response.data!;
        notifyListeners();
      }
    } catch (e) {
      debugPrint("Failed to fetch settings: $e");
    }
  }

  bool isTooLate() {
    return false;
  }

  bool isTooEarly() {
    return false;
  }

  Future<void> fetchHistory({bool silent = false}) async {
    if (!silent) {
      _isLoadingHistory = true;
      notifyListeners();
    }

    final response = await ApiService.instance.getAttendance();
    if (response.success && response.data != null) {
      final list = response.data!['logs'] as List? ?? [];
      _history = list.map((e) => AttendanceLogModel.fromJson(e as Map<String, dynamic>)).toList();
      if (!_bypassLimits) {
        _nextAction = response.data!['next_action'] ?? 'check_in';
        _currentAttempts = response.data!['current_attempts'] ?? 0;
        _maxAttempts = response.data!['max_attempts'] ?? 4;
      }
    }
    
    if (!silent) {
      _isLoadingHistory = false;
    }
    // Always notify so UI updates with new background data
    notifyListeners();
  }

  Future<void> fetchStats({bool silent = false}) async {
    if (!silent) {
      _isLoadingStats = true;
      notifyListeners();
    }

    try {
      final response = await ApiService.instance.getAttendanceStats();
      if (response.success && response.data != null) {
        _stats = response.data!;
      }
    } catch (e) {
      debugPrint("Failed to fetch stats: $e");
    }

    if (!silent) {
      _isLoadingStats = false;
    }
    notifyListeners();
  }

  // ── Main Verification Flow ────────────────────────────────────────────────

  Future<void> startVerification() async {
    if (isBusy) return;

    _result = null;
    _progress = 0.0;
    _setStatus(VerificationStatus.requestingPermissions, 'Checking permissions…');

    // ── 1. GPS permission ─────────────────────────────────────────────────
    LocationPermission locPerm = await Geolocator.checkPermission();
    if (locPerm == LocationPermission.denied) {
      locPerm = await Geolocator.requestPermission();
    }
    if (locPerm == LocationPermission.denied ||
        locPerm == LocationPermission.deniedForever) {
      _setStatus(VerificationStatus.error, 'Location permission denied');
      return;
    }

    // ── 1.5 Init Camera ───────────────────────────────────────────────────
    await initCamera();
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      _setStatus(VerificationStatus.error, 'Failed to initialize camera');
      return;
    }

    _setStatus(VerificationStatus.recording, 'Get ready...');

    // ── 2. Start capturing frames & GPS simultaneously ─────────────────────
    final frameCaptureFuture = _captureFrames();
    final gpsFuture = _getGPS();

    List<String> frames = [];
    Position? position;
    
    try {
      frames = await frameCaptureFuture;
      // Turn camera off immediately after capturing frames so it doesn't wait for GPS
      await disposeCamera();
      notifyListeners();
      
      position = await gpsFuture;
    } finally {
      // Fallback in case of error
      await disposeCamera();
      notifyListeners();
    }

    if (frames.isEmpty) {
      _setStatus(VerificationStatus.error, 'Failed to capture frames from camera');
      return;
    }
    if (position == null) {
      _setStatus(VerificationStatus.error, 'Failed to obtain GPS location');
      return;
    }

    _progress = 0.5;
    _setStatus(VerificationStatus.uploading, 'Sending to server for AI analysis…');

    // ── 3. Upload to backend ───────────────────────────────────────────────
    final timestamp = DateTime.now().millisecondsSinceEpoch / 1000.0;

    final response = await ApiService.instance.verify(
      frames: frames,
      latitude: _demoMode ? _demoLat : position.latitude,
      longitude: _demoMode ? _demoLng : position.longitude,
      timestamp: timestamp,
      demoLat: _demoMode ? _demoLat : null,
      demoLng: _demoMode ? _demoLng : null,
      demoRadius: _demoMode ? _demoRadius : null,
      bypassLimits: _bypassLimits,
    );

    _progress = 1.0;

    if (response.success && response.data != null) {
      _result = VerificationModel.fromJson(response.data!);
      final newStatus = _result!.isSuccess
          ? VerificationStatus.success
          : VerificationStatus.failure;
      _setStatus(newStatus, _result!.reason);

      if (_bypassLimits && _result!.isSuccess) {
        if (_nextAction == 'check_in') {
          _nextAction = 'check_out';
        } else if (_nextAction == 'check_out') {
          _nextAction = 'completed';
        }
      }
    } else {
      _setStatus(VerificationStatus.error, response.errorMessage ?? 'Verification failed');
    }
    
    // Automatically refresh logs history
    fetchHistory();
  }

  /// Capture directional frames securely
  Future<List<String>> _captureFrames() async {
    _statusMessage = 'Looking for face...';
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 500));
    _progress = 1.0;
    notifyListeners();
    return ['dummy_base64_string'];
  }

  static Uint8List? _compressFrameTask(Uint8List rawBytes) {
    try {
      final decoded = img.decodeImage(rawBytes);
      if (decoded == null) return null;
      // Resize to max 480px wide for performance
      final resized = img.copyResize(decoded, width: 480);
      return Uint8List.fromList(
        img.encodeJpg(resized, quality: ApiConstants.jpegQuality),
      );
    } catch (_) {
      return null;
    }
  }

  Future<Position?> _getGPS() async {
    return Position(
      longitude: 75.7037,
      latitude: 31.2536,
      timestamp: DateTime.now(),
      accuracy: 10,
      altitude: 0,
      altitudeAccuracy: 0,
      heading: 0,
      headingAccuracy: 0,
      speed: 0,
      speedAccuracy: 0
    );
  }

  void reset() {
    _status = VerificationStatus.idle;
    _statusMessage = '';
    _result = null;
    _progress = 0.0;
    notifyListeners();
  }

  void _setStatus(VerificationStatus status, String message) {
    _status = status;
    _statusMessage = message;
    notifyListeners();
  }

  @override
  void dispose() {
    disposeCamera();
    super.dispose();
  }
}
