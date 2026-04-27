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
  double _progress = 0.0;

  List<AttendanceLogModel> _history = [];
  bool _isLoadingHistory = false;

  VerificationStatus get status => _status;
  String get statusMessage => _statusMessage;
  VerificationModel? get result => _result;
  CameraController? get cameraController => _cameraController;
  double get progress => _progress;
  List<AttendanceLogModel> get history => _history;
  bool get isLoadingHistory => _isLoadingHistory;
  bool get isBusy =>
      _status == VerificationStatus.recording ||
      _status == VerificationStatus.processing ||
      _status == VerificationStatus.uploading;

  // ── Camera Setup ──────────────────────────────────────────────────────────

  Future<void> initCamera() async {
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

    _cameraController = CameraController(
      selected,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );
    await _cameraController!.initialize();
    notifyListeners();
  }

  void disposeCamera() {
    _cameraController?.dispose();
    _cameraController = null;
  }

  // ── Demo Mode ─────────────────────────────────────────────────────────────
  bool _demoMode = false;
  double? _demoLat;
  double? _demoLng;
  double? _demoRadius;

  bool get demoMode => _demoMode;
  double? get demoLat => _demoLat;
  double? get demoLng => _demoLng;
  double? get demoRadius => _demoRadius;

  void setDemoMode({
    required bool enabled,
    double? lat,
    double? lng,
    double? radius,
  }) {
    _demoMode = enabled;
    _demoLat = lat;
    _demoLng = lng;
    _demoRadius = radius;
    notifyListeners();
  }

  Future<void> fetchHistory() async {
    _isLoadingHistory = true;
    notifyListeners();

    final response = await ApiService.instance.getAttendance();
    if (response.success && response.data != null) {
      final list = response.data!['logs'] as List? ?? [];
      _history = list.map((e) => AttendanceLogModel.fromJson(e as Map<String, dynamic>)).toList();
    }
    
    _isLoadingHistory = false;
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

    _setStatus(VerificationStatus.recording, 'Get ready...');

    // ── 2. Start capturing frames & GPS simultaneously ─────────────────────
    final frameCaptureFuture = _captureFrames();
    final gpsFuture = _getGPS();

    final frames = await frameCaptureFuture;
    final position = await gpsFuture;

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
      latitude: position.latitude,
      longitude: position.longitude,
      timestamp: timestamp,
      demoLat: _demoMode ? _demoLat : null,
      demoLng: _demoMode ? _demoLng : null,
      demoRadius: _demoMode ? _demoRadius : null,
    );

    _progress = 1.0;

    if (response.success && response.data != null) {
      _result = VerificationModel.fromJson(response.data!);
      final newStatus = _result!.isSuccess
          ? VerificationStatus.success
          : VerificationStatus.failure;
      _setStatus(newStatus, _result!.reason);
    } else {
      _setStatus(VerificationStatus.error, response.errorMessage ?? 'Verification failed');
    }
    
    // Automatically refresh logs history
    fetchHistory();
  }

  /// Capture directional frames securely
  Future<List<String>> _captureFrames() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return [];
    }

    final List<String> base64Frames = [];

    // 1. Turn Left
    _statusMessage = 'Turn Left ◄';
    notifyListeners();
    await Future.delayed(const Duration(seconds: 3));
    _progress = 0.10;
    notifyListeners();

    // 2. Look Straight
    _statusMessage = 'Look Straight ▲';
    notifyListeners();
    await Future.delayed(const Duration(seconds: 3));
    _progress = 0.20;
    notifyListeners();

    // 3. Turn Right
    _statusMessage = 'Turn Right ►';
    notifyListeners();
    await Future.delayed(const Duration(seconds: 3));
    _progress = 0.30;
    notifyListeners();

    // 4. Cool-off time
    _statusMessage = 'Hold still for verification...';
    notifyListeners();
    await Future.delayed(const Duration(seconds: 4));
    _progress = 0.40;
    notifyListeners();

    // 5. Image Capture
    for (int i = 0; i < 3; i++) {
      if (_cameraController == null) break;
      try {
        final xFile = await _cameraController!.takePicture();
        final bytes = await xFile.readAsBytes();
        final compressed = _compressFrame(bytes);
        if (compressed != null) base64Frames.add(base64Encode(compressed));
        _progress = 0.40 + (i + 1) * 0.03;
        notifyListeners();
      } catch (_) {}
    }

    return base64Frames;
  }

  Uint8List? _compressFrame(Uint8List rawBytes) {
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
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );
    } catch (_) {
      return null;
    }
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
