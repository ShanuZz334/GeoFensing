import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/painting.dart' show Size, Rect;
import 'package:flutter/services.dart' show WriteBuffer;
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

/// Detailed result from a single analysis frame.
class FaceScanStatus {
  final bool faceDetected;
  final bool goodLighting;
  final bool faceCentered;

  /// Human-readable hint for why a check is failing.
  final String? hint;

  const FaceScanStatus({
    this.faceDetected = false,
    this.goodLighting = false,
    this.faceCentered = false,
    this.hint,
  });

  bool get allGood => faceDetected && goodLighting && faceCentered;

  @override
  String toString() =>
      'FaceScanStatus(detected=$faceDetected, lit=$goodLighting, centered=$faceCentered, hint=$hint)';
}

/// Strict pre-scan gate using Google ML Kit Face Detection.
///
/// Criteria that must ALL pass before capture is triggered:
///   1. **Face detected** — a sufficiently large, forward-facing face
///      (yaw ≤ ±25°, pitch ≤ ±20°, face area ≥ 8 % of frame)
///   2. **Good lighting** — face-region average brightness 80–220 AND
///      pixel standard-deviation ≥ 15 (ensures contrast, not a flat blob)
///   3. **Face centered** — face center within 35–65 % H and 30–70 % V
///
/// [stabilityRequired] consecutive passing frames are needed before
/// [allGood] flips to true, preventing single-lucky-frame triggers.
class FaceScanService {
  FaceDetector? _detector;
  bool _isProcessing = false;

  /// How many consecutive frames must pass all checks before reporting ready.
  static const int stabilityRequired = 3;

  /// Running count of consecutive all-good frames.
  int _consecutivePassing = 0;

  /// Last stable fully-passing status (for callers to inspect mid-stream).
  FaceScanStatus _lastStatus = const FaceScanStatus();

  /// Expose the stability count so the UI can show "Hold steady (2/3)…"
  int get consecutivePassing => _consecutivePassing;

  void init() {
    if (kIsWeb) return;
    _detector = FaceDetector(
      options: FaceDetectorOptions(
        // Use the accurate (CNN-based) model — slower but dramatically better
        // at rejecting partial faces/foreheads.
        performanceMode: FaceDetectorMode.accurate,
        enableClassification: true,
        // Enable head-angle metadata.
        enableTracking: true,
        // Minimum fraction of the shorter image dimension that the face must
        // span — 0.25 = at least 25 % of the frame short-axis.
        minFaceSize: 0.25,
      ),
    );
    _consecutivePassing = 0;
  }

  Future<FaceScanStatus> analyze(
      CameraImage image, CameraDescription cam) async {
    if (kIsWeb) {
      // Web simulation — always green (used in browser testing only).
      return const FaceScanStatus(
          faceDetected: true, goodLighting: true, faceCentered: true);
    }
    if (_isProcessing || _detector == null) return _lastStatus;
    _isProcessing = true;

    try {
      final inputImage = _buildInputImage(image, cam);
      if (inputImage == null) return _lastStatus;

      final faces = await _detector!.processImage(inputImage);

      // ── Coordinate-space correction ────────────────────────────────────
      // CameraImage.width/height are in the RAW sensor frame (typically
      // landscape on Android). ML Kit, however, returns bounding boxes in
      // the SCREEN-UPRIGHT frame because we pass the rotation metadata.
      // When the sensor is rotated 90° or 270° (all normal Android phones)
      // the width/height axes are transposed relative to what the user sees.
      // We must swap them before computing any screen-space fractions.
      final imgW = image.width.toDouble();
      final imgH = image.height.toDouble();
      final bool sensorRotated =
          cam.sensorOrientation == 90 || cam.sensorOrientation == 270;
      // effectiveW = screen-space horizontal extent
      // effectiveH = screen-space vertical extent
      final double effectiveW = sensorRotated ? imgH : imgW;
      final double effectiveH = sensorRotated ? imgW : imgH;

      if (faces.isEmpty) {
        _consecutivePassing = 0;
        final bright = _checkFrameLighting(image, null, imgW, imgH);
        final status = FaceScanStatus(
          faceDetected: false,
          goodLighting: bright,
          faceCentered: false,
          hint: 'No face found — position your full face in the circle',
        );
        _lastStatus = status;
        return status;
      }

      // Pick the largest face in the frame (in case multiple are detected).
      final face = faces.reduce((a, b) =>
          (a.boundingBox.width * a.boundingBox.height) >
                  (b.boundingBox.width * b.boundingBox.height)
              ? a
              : b);

      final box = face.boundingBox;

      // ── 1. Face quality checks ──────────────────────────────────────────
      final String? faceHint = _faceQualityHint(face, box, effectiveW, effectiveH);
      final bool faceGood = faceHint == null;

      // ── 2. Lighting on face region ──────────────────────────────────────
      // _checkFrameLighting works in raw sensor pixel space — pass raw dims.
      final bool lit = _checkFrameLighting(image, box, imgW, imgH);

      // ── 3. Centering (screen-space) ────────────────────────────────────
      final faceCx = box.left + box.width / 2;
      final faceCy = box.top + box.height / 2;
      final bool centered = (faceCx / effectiveW) >= 0.35 &&
          (faceCx / effectiveW) <= 0.65 &&
          (faceCy / effectiveH) >= 0.30 &&
          (faceCy / effectiveH) <= 0.70;

      // Build hint string for the worst failing check.
      String? hint;
      if (!faceGood) {
        hint = faceHint;
      } else if (!lit) {
        hint = 'Improve lighting — move to a brighter area';
      } else if (!centered) {
        hint = 'Centre your face in the circle';
      }

      final allPass = faceGood && lit && centered;

      // ── Stability gate ──────────────────────────────────────────────────
      if (allPass) {
        _consecutivePassing++;
      } else {
        _consecutivePassing = 0;
      }

      // Only report allGood after [stabilityRequired] consecutive passes.
      final stableGood = _consecutivePassing >= stabilityRequired;

      final status = FaceScanStatus(
        faceDetected: stableGood ? true : faceGood,
        goodLighting: stableGood ? true : lit,
        faceCentered: stableGood ? true : centered,
        hint: stableGood ? null : hint,
      );
      _lastStatus = status;
      return status;
    } catch (e) {
      debugPrint('[FaceScanService] analyze error: $e');
      return _lastStatus;
    } finally {
      _isProcessing = false;
    }
  }

  /// Returns null if the face passes all quality gates; otherwise a hint string.
  String? _faceQualityHint(
      Face face, Rect box, double imgW, double imgH) {
    // -- Minimum face area ------------------------------------------------
    // Face bounding box must cover at least 8% of total frame area.
    final frameArea = imgW * imgH;
    final faceArea = box.width * box.height;
    if (faceArea / frameArea < 0.08) {
      return 'Move closer — face is too small in frame';
    }

    // -- Head pose (yaw / pitch) ------------------------------------------
    // ML Kit provides Euler angles for detected faces.
    // Yaw  (Y axis): left/right rotation — forehead tilts look like high yaw.
    // Pitch (X axis): up/down tilt — looking up shows forehead.
    final yaw = face.headEulerAngleY; // degrees, + = face right
    final pitch = face.headEulerAngleX; // degrees, + = face up

    if (yaw != null && yaw.abs() > 25.0) {
      return 'Face the camera directly — too much side rotation';
    }
    if (pitch != null && pitch.abs() > 20.0) {
      return 'Hold phone level — too much up/down tilt';
    }

    // -- Tracking stability -----------------------------------------------
    // If tracking ID is null the detector is not confident it's a stable face.
    if (face.trackingId == null) {
      return 'Hold still — face not yet tracked';
    }

    return null; // all good
  }

  /// Checks brightness and contrast.
  ///
  /// When [faceBox] is provided the check is restricted to the face region
  /// on the Y-plane, giving a much more relevant result than the whole frame.
  static bool _checkFrameLighting(
      CameraImage image, Rect? faceBox, double imgW, double imgH) {
    try {
      final yPlane = image.planes.first;
      final bytes = yPlane.bytes;
      final stride = yPlane.bytesPerRow;
      if (bytes.isEmpty) return true;

      int sum = 0;
      int count = 0;

      if (faceBox != null) {
        // Sample within the face bounding box on the Y-plane.
        final x0 = (faceBox.left.clamp(0, imgW - 1)).toInt();
        final y0 = (faceBox.top.clamp(0, imgH - 1)).toInt();
        final x1 = (faceBox.right.clamp(0, imgW)).toInt();
        final y1 = (faceBox.bottom.clamp(0, imgH)).toInt();

        // Sample every 4th pixel for performance.
        for (int row = y0; row < y1; row += 4) {
          for (int col = x0; col < x1; col += 4) {
            final idx = row * stride + col;
            if (idx >= 0 && idx < bytes.length) {
              sum += bytes[idx] & 0xFF;
              count++;
            }
          }
        }
      } else {
        // Full-frame fallback (no face detected yet).
        final step = (bytes.length / 300).floor().clamp(1, bytes.length);
        for (int i = 0; i < bytes.length; i += step) {
          sum += bytes[i] & 0xFF;
          count++;
        }
      }

      if (count == 0) return true;
      final avg = sum / count;

      // ── Brightness range ──────────────────────────────────────────────
      // 80–220: reject very dark faces and blown-out / over-exposed scenes.
      if (avg < 80 || avg > 220) return false;

      // ── Contrast (standard deviation) ────────────────────────────────
      // A low std-dev means the face region is a flat uniform blob —
      // typical of a completely dark or completely white frame, or a
      // printed photo held very close to the camera.
      double sqSum = 0;
      if (faceBox != null) {
        final x0 = (faceBox.left.clamp(0, imgW - 1)).toInt();
        final y0 = (faceBox.top.clamp(0, imgH - 1)).toInt();
        final x1 = (faceBox.right.clamp(0, imgW)).toInt();
        final y1 = (faceBox.bottom.clamp(0, imgH)).toInt();
        for (int row = y0; row < y1; row += 4) {
          for (int col = x0; col < x1; col += 4) {
            final idx = row * stride + col;
            if (idx >= 0 && idx < bytes.length) {
              final diff = (bytes[idx] & 0xFF) - avg;
              sqSum += diff * diff;
              // count is already computed above
            }
          }
        }
      } else {
        final step = (bytes.length / 300).floor().clamp(1, bytes.length);
        for (int i = 0; i < bytes.length; i += step) {
          final diff = (bytes[i] & 0xFF) - avg;
          sqSum += diff * diff;
        }
      }
      final stdDev = (count > 0) ? (sqSum / count) : 0;
      // Require stdDev >= 15² = 225 variance → stdDev(raw) ≥ 15
      if (stdDev < 225) return false;

      return true;
    } catch (_) {
      return true;
    }
  }

  InputImage? _buildInputImage(CameraImage image, CameraDescription cam) {
    try {
      final rotation = _rotationFromSensor(cam.sensorOrientation);
      final isAndroid = defaultTargetPlatform == TargetPlatform.android;

      Uint8List bytes;
      InputImageFormat format;
      int bytesPerRow;

      if (isAndroid) {
        format = InputImageFormat.nv21;
        final w = image.width;
        final h = image.height;

        // Build a clean NV21 buffer: Y-plane then interleaved UV.
        final expectedLen = (w * h * 1.5).toInt();
        bytes = Uint8List(expectedLen);

        // Copy Y plane row by row (handles stride != width).
        final yPlane = image.planes[0];
        for (int r = 0; r < h; r++) {
          final srcOff = r * yPlane.bytesPerRow;
          final dstOff = r * w;
          bytes.setRange(
              dstOff, dstOff + w, yPlane.bytes, srcOff);
        }

        // Copy UV plane (planes[1] = U, planes[2] = V for YUV420)
        // NV21 expects interleaved V then U; swap appropriately.
        if (image.planes.length >= 3) {
          final uPlane = image.planes[1];
          final vPlane = image.planes[2];
          final uvStart = w * h;
          final uvRows = h ~/ 2;
          final uvCols = w ~/ 2;
          for (int r = 0; r < uvRows; r++) {
            for (int c = 0; c < uvCols; c++) {
              final uIdx = r * uPlane.bytesPerRow + c * uPlane.bytesPerPixel!;
              final vIdx = r * vPlane.bytesPerRow + c * vPlane.bytesPerPixel!;
              final dstIdx = uvStart + r * w + c * 2;
              if (dstIdx + 1 < expectedLen) {
                bytes[dstIdx] = vPlane.bytes[vIdx] & 0xFF; // V
                bytes[dstIdx + 1] = uPlane.bytes[uIdx] & 0xFF; // U
              }
            }
          }
        }
        bytesPerRow = w;
      } else {
        format = InputImageFormat.bgra8888;
        final allBytes = WriteBuffer();
        for (final p in image.planes) {
          allBytes.putUint8List(p.bytes);
        }
        bytes = allBytes.done().buffer.asUint8List();
        bytesPerRow = image.planes.first.bytesPerRow;
      }

      return InputImage.fromBytes(
        bytes: bytes,
        metadata: InputImageMetadata(
          size: Size(image.width.toDouble(), image.height.toDouble()),
          rotation: rotation,
          format: format,
          bytesPerRow: bytesPerRow,
        ),
      );
    } catch (e) {
      debugPrint('[FaceScanService] _buildInputImage error: $e');
      return null;
    }
  }

  InputImageRotation _rotationFromSensor(int deg) {
    switch (deg) {
      case 90:
        return InputImageRotation.rotation90deg;
      case 180:
        return InputImageRotation.rotation180deg;
      case 270:
        return InputImageRotation.rotation270deg;
      default:
        return InputImageRotation.rotation0deg;
    }
  }

  void reset() {
    _consecutivePassing = 0;
    _lastStatus = const FaceScanStatus();
  }

  Future<void> dispose() async {
    await _detector?.close();
    _detector = null;
  }
}
