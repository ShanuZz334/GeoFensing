import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:camera/camera.dart';
import 'package:percent_indicator/percent_indicator.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'dart:math' as math;

import '../providers/verification_provider.dart';
import '../../../core/theme/app_theme.dart';

class VerificationScreen extends StatefulWidget {
  const VerificationScreen({super.key});

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> with SingleTickerProviderStateMixin {
  bool _cameraReady = false;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _initCamera();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  Future<void> _initCamera() async {
    final provider = context.read<VerificationProvider>();
    await provider.initCamera();
    if (mounted) setState(() => _cameraReady = true);
  }

  Future<void> _onStartPressed() async {
    final provider = context.read<VerificationProvider>();
    await provider.startVerification();

    if (!mounted) return;
    if (provider.status == VerificationStatus.success ||
        provider.status == VerificationStatus.failure ||
        provider.status == VerificationStatus.error) {
      Navigator.pushReplacementNamed(context, '/result');
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    context.read<VerificationProvider>().disposeCamera();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Consumer<VerificationProvider>(
        builder: (context, provider, _) {
          final isRecording = provider.status == VerificationStatus.recording;

          return Stack(
            children: [
              // ── Camera Preview ─────────────────────────────────────────
              if (_cameraReady &&
                  provider.cameraController != null &&
                  provider.cameraController!.value.isInitialized)
                _CameraPreviewWidget(controller: provider.cameraController!)
              else
                Container(
                  color: Colors.black,
                  child: const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        CircularProgressIndicator(color: Color(0xFF9F00FF)),
                        SizedBox(height: 16),
                        Text('Initializing camera...',
                            style: TextStyle(color: Colors.white70, fontSize: 14)),
                      ],
                    ),
                  ),
                ),

              // ── Face Oval Overlay ───────────────────────────────────────
              AnimatedBuilder(
                animation: _pulseController,
                builder: (context, child) {
                  return CustomPaint(
                    size: MediaQuery.of(context).size,
                    painter: _OvalOverlayPainter(
                      primaryColor: _ovalColor(provider.status),
                      pulseValue: isRecording ? 0.0 : _pulseController.value,
                      isRecording: isRecording,
                    ),
                  );
                },
              ),

              // ── Scanning Line ──────────────────────────────────────────
              if (isRecording)
                _ScanningLine(
                  top: MediaQuery.of(context).size.height * 0.15,
                  bottom: MediaQuery.of(context).size.height * 0.65,
                ),

              // ── Top bar ────────────────────────────────────────────────
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back_ios_new_rounded,
                            color: Colors.white, size: 20),
                        onPressed: () => Navigator.pop(context),
                      ),
                      const Expanded(
                        child: Text(
                          'Face Verification',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 17,
                          ),
                        ),
                      ),
                      const SizedBox(width: 48),
                    ],
                  ),
                ),
              ),

              // ── Bottom Panel ───────────────────────────────────────────
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: _BottomPanel(
                  provider: provider,
                  onStartPressed: _onStartPressed,
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Color _ovalColor(VerificationStatus status) {
    switch (status) {
      case VerificationStatus.recording:
        return AppTheme.primary;
      case VerificationStatus.uploading:
      case VerificationStatus.processing:
        return Colors.amber;
      case VerificationStatus.success:
        return AppTheme.success;
      case VerificationStatus.failure:
      case VerificationStatus.error:
        return AppTheme.error;
      default:
        return Colors.white.withValues(alpha: 0.8);
    }
  }
}

// ── Scanning Line Animation ───────────────────────────────────────────────────

class _ScanningLine extends StatelessWidget {
  final double top;
  final double bottom;
  const _ScanningLine({required this.top, required this.bottom});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: top,
      left: MediaQuery.of(context).size.width * 0.15,
      right: MediaQuery.of(context).size.width * 0.15,
      child: Container(
        height: 3,
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withValues(alpha: 0.5),
              blurRadius: 10,
              spreadRadius: 2,
            ),
          ],
          gradient: LinearGradient(
            colors: [
              AppTheme.primary.withValues(alpha: 0.0),
              AppTheme.primary,
              AppTheme.primary.withValues(alpha: 0.0),
            ],
          ),
        ),
      ),
    )
        .animate(onPlay: (c) => c.repeat())
        .moveY(begin: 0, end: bottom - top, duration: 2.seconds, curve: Curves.easeInOut);
  }
}

// ── Camera Preview ────────────────────────────────────────────────────────────

class _CameraPreviewWidget extends StatelessWidget {
  const _CameraPreviewWidget({required this.controller});
  final CameraController controller;

  @override
  Widget build(BuildContext context) {
    return Builder(
      builder: (ctx) {
        double ratio = controller.value.aspectRatio;
        if (MediaQuery.of(ctx).size.height > MediaQuery.of(ctx).size.width && ratio > 1.0) {
          ratio = 1.0 / ratio;
        }
        return SizedBox.expand(
          child: FittedBox(
            fit: BoxFit.cover,
            child: SizedBox(
              width: 100 * ratio,
              height: 100,
              child: CameraPreview(controller),
            ),
          ),
        );
      },
    );
  }
}

// ── Oval Overlay ──────────────────────────────────────────────────────────────

class _OvalOverlayPainter extends CustomPainter {
  final Color primaryColor;
  final double pulseValue;
  final bool isRecording;

  _OvalOverlayPainter({
    required this.primaryColor,
    required this.pulseValue,
    required this.isRecording,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height * 0.38;
    
    // Improved proportions: wider oval (more circle-like)
    final rx = size.width * 0.35;
    final ry = rx * 1.35; // Fixed aspect ratio instead of screen-dependent height

    final ovalRect = Rect.fromCenter(center: Offset(cx, cy), width: rx * 2, height: ry * 2);

    final overlayPath = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addOval(ovalRect)
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(overlayPath, Paint()..color = Colors.black.withValues(alpha: 0.7));

    // Outer glow pulse
    if (!isRecording) {
      final pulsePaint = Paint()
        ..color = primaryColor.withValues(alpha: 0.3 * (1 - pulseValue))
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0 + (8.0 * pulseValue);
      canvas.drawOval(
        Rect.fromCenter(center: Offset(cx, cy), width: (rx * 2) + (12 * pulseValue), height: (ry * 2) + (12 * pulseValue)),
        pulsePaint,
      );
    }

    // Main border
    canvas.drawOval(
      ovalRect,
      Paint()
        ..color = primaryColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.0,
    );

    // Corner guides for premium look
    final guidePaint = Paint()
      ..color = primaryColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5.0
      ..strokeCap = StrokeCap.round;

    const angle = 0.35;
    canvas.drawArc(ovalRect, -math.pi / 2 - angle, angle * 2, false, guidePaint); // Top
    canvas.drawArc(ovalRect, math.pi / 2 - angle, angle * 2, false, guidePaint);  // Bottom
    canvas.drawArc(ovalRect, 0 - angle, angle * 2, false, guidePaint);            // Right
    canvas.drawArc(ovalRect, math.pi - angle, angle * 2, false, guidePaint);      // Left
  }

  @override
  bool shouldRepaint(_OvalOverlayPainter old) => 
    old.primaryColor != primaryColor || 
    old.pulseValue != pulseValue ||
    old.isRecording != isRecording;
}

// ── Bottom Panel ──────────────────────────────────────────────────────────────

class _BottomPanel extends StatelessWidget {
  const _BottomPanel({required this.provider, required this.onStartPressed});

  final VerificationProvider provider;
  final VoidCallback onStartPressed;

  @override
  Widget build(BuildContext context) {
    final isBusy = provider.isBusy;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 28),
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.18),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey[300],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 14),

          // Progress bar
          if (isBusy) ...[
            LinearPercentIndicator(
              lineHeight: 5,
              percent: provider.progress.clamp(0.0, 1.0),
              backgroundColor: Colors.grey.shade200,
              progressColor: AppTheme.primary,
              barRadius: const Radius.circular(4),
              padding: EdgeInsets.zero,
            ),
            const SizedBox(height: 12),
          ],

          // Status message
          _StatusLabel(status: provider.status, message: provider.statusMessage),
          const SizedBox(height: 16),

          // Action button
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                elevation: 0,
              ),
              onPressed: isBusy ? null : onStartPressed,
              child: isBusy
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                        const SizedBox(width: 10),
                        Text(
                          provider.status == VerificationStatus.recording
                              ? provider.statusMessage
                              : _busyLabel(provider.status),
                          style: const TextStyle(
                              fontSize: 15, fontWeight: FontWeight.w600),
                        ),
                      ],
                    )
                  : const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.face_retouching_natural, size: 20),
                        SizedBox(width: 8),
                        Text('Start Verification',
                            style: TextStyle(
                                fontSize: 15, fontWeight: FontWeight.w600)),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }

  String _busyLabel(VerificationStatus s) {
    switch (s) {
      case VerificationStatus.recording:
        return 'Recording…';
      case VerificationStatus.uploading:
        return 'Analysing…';
      default:
        return 'Processing…';
    }
  }
}

// ── Status Label ──────────────────────────────────────────────────────────────

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status, required this.message});
  final VerificationStatus status;
  final String message;

  @override
  Widget build(BuildContext context) {
    if (status == VerificationStatus.idle) {
      return const Text(
        'Position your face inside the oval',
        textAlign: TextAlign.center,
        style: TextStyle(color: Color(0xFF9E9E9E), fontSize: 13),
      );
    }

    Color color;
    IconData icon;

    switch (status) {
      case VerificationStatus.recording:
        color = AppTheme.primary;
        icon = Icons.fiber_manual_record;
        break;
      case VerificationStatus.uploading:
      case VerificationStatus.processing:
        color = Colors.amber.shade700;
        icon = Icons.autorenew;
        break;
      case VerificationStatus.requestingPermissions:
        color = Colors.blue;
        icon = Icons.security_outlined;
        break;
      default:
        color = const Color(0xFF9E9E9E);
        icon = Icons.info_outline;
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, color: color, size: 16),
        const SizedBox(width: 6),
        Flexible(
          child: Text(
            message,
            style: TextStyle(
                color: color, fontSize: 13, fontWeight: FontWeight.w500),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}
