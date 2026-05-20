import 'dart:math' show sqrt;

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

/// Robust multi-layer pre-scan gate using Google ML Kit Face Detection.
///
/// Criteria that must ALL pass before capture is triggered:
///
///  1. **Face detected**
///     - ML Kit minFaceSize ≥ 0.35 (35 % of short axis)
///     - Bounding-box area ≥ 14 % and ≤ 70 % of frame (not too far, not too close)
///     - Face is not clipped at any edge (≥ 8 px margin on all sides)
///     - Yaw ≤ ±15°, Pitch ≤ ±12°  (straight-on only)
///     - Both eyes open probability ≥ 0.7
///     - trackingId confirmed (stable real face)
///
///  2. **Good lighting**
///     - Face region is split into 3 vertical zones (forehead / mid / chin).
///       Each zone mean brightness must be 90–210.
///     - Overall face-region stdDev ≥ 22 (real texture, not a flat printout).
///     - Zone-to-zone brightness difference ≤ 60 (catches harsh side-lighting).
///
///  3. **Face centered**
///     - Face centre within 40–60 % horizontal and 35–65 % vertical.
///
///  [stabilityRequired] consecutive passing frames are required before
///  [allGood] flips true. Any single failing frame hard-resets the counter.
class FaceScanService {
  FaceDetector? _detector;
  bool _isProcessing = false;

  /// Consecutive all-good frames needed before reporting ready.
  static const int stabilityRequired = 5;

  int _consecutivePassing = 0;
  FaceScanStatus _lastStatus = const FaceScanStatus();

  int get consecutivePassing => _consecutivePassing;

  void init() {
    if (kIsWeb) return;
    _detector = FaceDetector(
      options: FaceDetectorOptions(
        performanceMode: FaceDetectorMode.accurate,
        enableClassification: true, // provides eye-open probability
        enableTracking: true,
        minFaceSize: 0.35, // at least 35 % of shorter image dimension
      ),
    );
    _consecutivePassing = 0;
  }

  Future<FaceScanStatus> analyze(
      CameraImage image, CameraDescription cam) async {
    if (kIsWeb) {
      return const FaceScanStatus(
          faceDetected: true, goodLighting: true, faceCentered: true);
    }
    if (_isProcessing || _detector == null) return _lastStatus;
    _isProcessing = true;

    try {
      final inputImage = _buildInputImage(image, cam);
      if (inputImage == null) return _lastStatus;

      final faces = await _detector!.processImage(inputImage);

      final imgW = image.width.toDouble();
      final imgH = image.height.toDouble();
      final bool sensorRotated =
          cam.sensorOrientation == 90 || cam.sensorOrientation == 270;
      final double effectiveW = sensorRotated ? imgH : imgW;
      final double effectiveH = sensorRotated ? imgW : imgH;

      if (faces.isEmpty) {
        _consecutivePassing = 0;
        final brightResult = _checkLightingMultiZone(
            image, null, imgW, imgH, sensorRotated);
        final status = FaceScanStatus(
          faceDetected: false,
          goodLighting: brightResult.passed,
          faceCentered: false,
          hint: 'No face detected — position your full face in frame',
        );
        _lastStatus = status;
        return status;
      }

      // Use largest face
      final face = faces.reduce((a, b) =>
          (a.boundingBox.width * a.boundingBox.height) >
                  (b.boundingBox.width * b.boundingBox.height)
              ? a
              : b);

      final box = face.boundingBox;

      // ── 1. Face quality ──────────────────────────────────────────────────
      final String? faceHint =
          _faceQualityHint(face, box, effectiveW, effectiveH);
      final bool faceGood = faceHint == null;

      // ── 2. Multi-zone lighting ───────────────────────────────────────────
      final LightingResult lighting =
          _checkLightingMultiZone(image, box, imgW, imgH, sensorRotated);
      final bool lit = lighting.passed;

      // ── 3. Centering — tighter: 40-60% H, 35-65% V ──────────────────────
      final faceCx = (box.left + box.width / 2) / effectiveW;
      final faceCy = (box.top + box.height / 2) / effectiveH;
      final bool centered =
          faceCx >= 0.40 && faceCx <= 0.60 && faceCy >= 0.35 && faceCy <= 0.65;

      // ── Hint priority: face first, then lighting, then centering ─────────
      String? hint;
      if (!faceGood) {
        hint = faceHint;
      } else if (!lit) {
        hint = lighting.hint;
      } else if (!centered) {
        final String h = faceCx < 0.40
            ? 'move right'
            : faceCx > 0.60
                ? 'move left'
                : '';
        final String v = faceCy < 0.35
            ? 'move down'
            : faceCy > 0.65
                ? 'move up'
                : '';
        final parts = [h, v].where((s) => s.isNotEmpty).join(' & ');
        hint = 'Centre your face — $parts';
      }

      final allPass = faceGood && lit && centered;

      // Hard reset on any failure — no decay tolerance
      if (allPass) {
        _consecutivePassing++;
      } else {
        _consecutivePassing = 0;
      }

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

  // ── Face quality gate ────────────────────────────────────────────────────

  String? _faceQualityHint(
      Face face, Rect box, double frameW, double frameH) {
    final frameArea = frameW * frameH;
    final faceArea = box.width * box.height;
    final faceRatio = faceArea / frameArea;

    // Too small — too far from camera
    if (faceRatio < 0.14) {
      return 'Move closer — face is too small';
    }

    // Too large — too close to camera (face fills > 70 % of frame)
    if (faceRatio > 0.70) {
      return 'Move back — face is too close';
    }

    // Face clipped at any edge (must have ≥ 8 px margin on all sides)
    const edge = 8.0;
    if (box.left < edge ||
        box.top < edge ||
        box.right > frameW - edge ||
        box.bottom > frameH - edge) {
      return 'Face is clipped — centre fully in frame';
    }

    // Head pose — yaw ±15°, pitch ±12°
    final yaw = face.headEulerAngleY;
    final pitch = face.headEulerAngleX;

    if (yaw != null && yaw.abs() > 15.0) {
      return 'Face the camera directly — too much side rotation';
    }
    if (pitch != null && pitch.abs() > 12.0) {
      return 'Hold phone level — too much up/down tilt';
    }

    // Eye openness — both eyes must be clearly open (≥ 0.70 probability)
    final leftEye = face.leftEyeOpenProbability;
    final rightEye = face.rightEyeOpenProbability;
    if (leftEye != null && leftEye < 0.70) {
      return 'Open both eyes fully';
    }
    if (rightEye != null && rightEye < 0.70) {
      return 'Open both eyes fully';
    }

    // Tracking stability — trackingId null means detector isn't confident
    if (face.trackingId == null) {
      return 'Hold still — face not yet tracked';
    }

    return null;
  }

  // ── Multi-zone lighting check ────────────────────────────────────────────

  LightingResult _checkLightingMultiZone(CameraImage image, Rect? faceBox,
      double imgW, double imgH, bool sensorRotated) {
    try {
      final yPlane = image.planes.first;
      final bytes = yPlane.bytes;
      final stride = yPlane.bytesPerRow;
      if (bytes.isEmpty) return LightingResult.pass();

      if (faceBox == null) {
        // Full-frame check when no face — just do overall brightness
        return _fullFrameLighting(bytes, stride);
      }

      // Map the screen-space bounding box to raw sensor pixel coordinates
      final Rect rawBox = sensorRotated
          ? Rect.fromLTRB(
              faceBox.top.clamp(0, imgH - 1),
              (imgW - faceBox.right).clamp(0, imgW - 1),
              faceBox.bottom.clamp(0, imgH),
              (imgW - faceBox.left).clamp(0, imgW),
            )
          : faceBox;

      final x0 = rawBox.left.toInt().clamp(0, imgW.toInt() - 1);
      final y0 = rawBox.top.toInt().clamp(0, imgH.toInt() - 1);
      final x1 = rawBox.right.toInt().clamp(0, imgW.toInt());
      final y1 = rawBox.bottom.toInt().clamp(0, imgH.toInt());

      if (x1 <= x0 || y1 <= y0) return LightingResult.pass();

      // Split vertically into 3 equal zones: forehead / mid-face / chin
      final zoneH = (y1 - y0) ~/ 3;
      if (zoneH < 4) return LightingResult.pass();

      final List<double> zoneMeans = [];
      double totalSum = 0;
      int totalCount = 0;

      for (int z = 0; z < 3; z++) {
        final zy0 = y0 + z * zoneH;
        final zy1 = (z == 2) ? y1 : zy0 + zoneH;
        int sum = 0;
        int count = 0;
        for (int row = zy0; row < zy1; row += 3) {
          for (int col = x0; col < x1; col += 3) {
            final idx = row * stride + col;
            if (idx >= 0 && idx < bytes.length) {
              final val = bytes[idx] & 0xFF;
              sum += val;
              count++;
              totalSum += val;
              totalCount++;
            }
          }
        }
        if (count == 0) return LightingResult.pass();
        final mean = sum / count;
        // Each zone must be 90–210
        if (mean < 90) {
          return LightingResult.fail(
              'Too dark — move to a brighter area');
        }
        if (mean > 210) {
          return LightingResult.fail(
              'Too bright / overexposed — reduce glare');
        }
        zoneMeans.add(mean);
      }

      // Zone uniformity: max difference ≤ 60 (catches harsh side-lighting)
      final zoneMax = zoneMeans.reduce((a, b) => a > b ? a : b);
      final zoneMin = zoneMeans.reduce((a, b) => a < b ? a : b);
      if (zoneMax - zoneMin > 60) {
        return LightingResult.fail(
            'Uneven lighting — face a uniform light source');
      }

      // Contrast: overall stdDev ≥ 22 (real skin texture vs. flat printout)
      if (totalCount == 0) return LightingResult.pass();
      final overallMean = totalSum / totalCount;
      double sqSum = 0;
      for (int row = y0; row < y1; row += 3) {
        for (int col = x0; col < x1; col += 3) {
          final idx = row * stride + col;
          if (idx >= 0 && idx < bytes.length) {
            final diff = (bytes[idx] & 0xFF) - overallMean;
            sqSum += diff * diff;
          }
        }
      }
      final stdDev = sqrt(sqSum / totalCount);
      if (stdDev < 22) {
        return LightingResult.fail(
            'Low contrast — ensure your face is well-lit');
      }

      return LightingResult.pass();
    } catch (_) {
      return LightingResult.pass();
    }
  }

  LightingResult _fullFrameLighting(Uint8List bytes, int stride) {
    try {
      final step = (bytes.length / 500).floor().clamp(1, bytes.length);
      int sum = 0;
      int count = 0;
      for (int i = 0; i < bytes.length; i += step) {
        sum += bytes[i] & 0xFF;
        count++;
      }
      if (count == 0) return LightingResult.pass();
      final avg = sum / count;
      if (avg < 70) return LightingResult.fail('Too dark — find better lighting');
      if (avg > 220) return LightingResult.fail('Too bright / overexposed');
      return LightingResult.pass();
    } catch (_) {
      return LightingResult.pass();
    }
  }

  // ── Input image builder ──────────────────────────────────────────────────

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
        final expectedLen = (w * h * 1.5).toInt();
        bytes = Uint8List(expectedLen);

        // Copy Y plane row by row (handles stride != width)
        final yPlane = image.planes[0];
        for (int r = 0; r < h; r++) {
          final srcOff = r * yPlane.bytesPerRow;
          final dstOff = r * w;
          bytes.setRange(dstOff, dstOff + w, yPlane.bytes, srcOff);
        }

        // Copy UV — NV21 expects interleaved V, U
        if (image.planes.length >= 3) {
          final uPlane = image.planes[1];
          final vPlane = image.planes[2];
          final uvStart = w * h;
          final uvRows = h ~/ 2;
          final uvCols = w ~/ 2;
          for (int r = 0; r < uvRows; r++) {
            for (int c = 0; c < uvCols; c++) {
              final uIdx =
                  r * uPlane.bytesPerRow + c * uPlane.bytesPerPixel!;
              final vIdx =
                  r * vPlane.bytesPerRow + c * vPlane.bytesPerPixel!;
              final dstIdx = uvStart + r * w + c * 2;
              if (dstIdx + 1 < expectedLen) {
                bytes[dstIdx] = vPlane.bytes[vIdx] & 0xFF;
                bytes[dstIdx + 1] = uPlane.bytes[uIdx] & 0xFF;
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

// ── Lightweight result wrapper for multi-zone lighting ───────────────────────

class LightingResult {
  final bool passed;
  final String? hint;
  const LightingResult._(this.passed, this.hint);
  factory LightingResult.pass() => const LightingResult._(true, null);
  factory LightingResult.fail(String hint) =>
      LightingResult._(false, hint);
}
