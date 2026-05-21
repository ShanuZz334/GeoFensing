import 'dart:async';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:flutter/foundation.dart';

import '../providers/verification_provider.dart';
import '../services/face_scan_service.dart';

class FaceScanScreen extends StatefulWidget {
  const FaceScanScreen({super.key});

  @override
  State<FaceScanScreen> createState() => _FaceScanScreenState();
}

class _FaceScanScreenState extends State<FaceScanScreen>
    with TickerProviderStateMixin {
  late AnimationController _scanLineController;
  late AnimationController _pulseController;
  late AnimationController _checkController;

  final FaceScanService _faceService = FaceScanService();
  FaceScanStatus _scanStatus = const FaceScanStatus();
  Timer? _analysisTimer;

  bool _cameraReady = false;
  bool _hasShownResult = false;
  bool _isAnalyzing = false;

  @override
  void initState() {
    super.initState();
    _scanLineController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    _checkController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        final provider = context.read<VerificationProvider>();
        provider.reset();
        if (provider.history.isEmpty) {
          provider.fetchHistory();
        }
        _checkController.forward();
      }
    });
  }

  @override
  void dispose() {
    _analysisTimer?.cancel();
    _scanLineController.dispose();
    _pulseController.dispose();
    _checkController.dispose();
    _faceService.dispose();
    context.read<VerificationProvider>().disposeCamera();
    super.dispose();
  }

  void _startRealTimeAnalysis() {
    final provider = context.read<VerificationProvider>();
    final cam = provider.cameraController;
    if (cam == null || !cam.value.isInitialized) return;

    _faceService.init();
    _faceService.reset();

    _analysisTimer = Timer.periodic(const Duration(milliseconds: 400), (_) async {
      if (!mounted || provider.isBusy) return;

      if (kIsWeb) {
        // Web simulation since startImageStream is natively unsupported on browsers
        if (mounted) {
          setState(() => _scanStatus = const FaceScanStatus(
              faceDetected: true, goodLighting: true, faceCentered: true));
          if (_isAnalyzing && !provider.isBusy) {
            setState(() => _isAnalyzing = false);
            _beginCapture(provider);
          }
        }
        return;
      }

      if (cam.value.isStreamingImages) return;
      try {
        await cam.startImageStream((image) async {
          await cam.stopImageStream();
          if (!mounted) return;
          final desc = provider.cameraDescription;
          if (desc == null) return;
          final status = await _faceService.analyze(image, desc);
          if (mounted) {
            setState(() => _scanStatus = status);

            if (status.allGood && _isAnalyzing && !provider.isBusy) {
              _faceService.reset(); // clear stability counter for next scan
              setState(() => _isAnalyzing = false);
              _beginCapture(provider);
            }
          }
        });
      } catch (_) {}
    });
  }

  void _stopRealTimeAnalysis() {
    _analysisTimer?.cancel();
    _analysisTimer = null;
    final cam = context.read<VerificationProvider>().cameraController;
    try {
      if (cam != null && cam.value.isStreamingImages) {
        cam.stopImageStream();
      }
    } catch (_) {}
    if (mounted) setState(() => _scanStatus = const FaceScanStatus());
  }

  Future<void> _onStartScan() async {
    if (_hasShownResult) return;
    final provider = context.read<VerificationProvider>();

    if (provider.isTooLate()) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text("You are too late. You have been marked as Absent."),
        backgroundColor: Colors.redAccent,
      ));
      return;
    }

    if (provider.isTooEarly()) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text("Too early to check in. Please wait until 20 mins before class."),
        backgroundColor: Colors.redAccent,
      ));
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _scanStatus = const FaceScanStatus();
    });

    await provider.initCamera();
    if (!mounted) return;
    setState(() => _cameraReady = true);
    
    _startRealTimeAnalysis();
  }

  Future<void> _beginCapture(VerificationProvider provider) async {
    _scanLineController.repeat(reverse: true);
    _pulseController.repeat(reverse: true);

    await provider.startVerification();
    if (!mounted) return;

    _stopRealTimeAnalysis();
    await provider.disposeCamera();
    _scanLineController.stop();
    _pulseController.stop();
    if (mounted) setState(() => _cameraReady = false);

    if (provider.result?.contactSupport != null) {
      _hasShownResult = true;
      if (!mounted) return;
      _showSupportDialog(provider.result!.contactSupport!,
          message: 'You have exceeded the maximum attempts. Please reach out to our team:');
    } else {
      if (!mounted) return;
      final isSuccess = provider.status == VerificationStatus.success;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(provider.statusMessage),
        backgroundColor: isSuccess ? Colors.green : Colors.redAccent,
      ));
      if (isSuccess && mounted) {
        await Future.delayed(const Duration(seconds: 2));
        if (mounted) Navigator.pop(context);
      }
    }
  }

  void _showSupportDialog(Map<String, dynamic> contact, {String? message}) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF121212),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        ),
        title: const Row(children: [
          Icon(Icons.contact_support_outlined, color: Color(0xFF7C3AED)),
          SizedBox(width: 10),
          Text('Contact Support',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
        ]),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message ?? 'Please reach out to our team for assistance:',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.7))),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(children: [
                ListTile(
                  leading: const Icon(Icons.phone, color: Color(0xFF7C3AED)),
                  title: Text(contact['phone'] ?? '8089602280',
                      style: const TextStyle(color: Colors.white)),
                  dense: true,
                ),
                ListTile(
                  leading: const Icon(Icons.email, color: Color(0xFF7C3AED)),
                  title: Text(contact['email'] ?? 'shanifshaz546@gmail.com',
                      style: const TextStyle(color: Colors.white)),
                  dense: true,
                ),
              ]),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close', style: TextStyle(color: Color(0xFF7C3AED))),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<VerificationProvider>();
    final isRecording = provider.status == VerificationStatus.recording;
    final isUploading = provider.status == VerificationStatus.uploading;
    final isSuccess = provider.status == VerificationStatus.success;
    final isCompleted = !provider.bypassLimits && provider.nextAction == 'completed';
    final isAbsentLocked = !provider.bypassLimits &&
        provider.isTooLate() &&
        provider.nextAction != 'check_out' &&
        provider.nextAction != 'completed';
    final isEarlyLocked = !provider.bypassLimits &&
        provider.isTooEarly() &&
        provider.nextAction != 'check_out' &&
        provider.nextAction != 'completed';

    final modeLabel = isCompleted
        ? 'Completed Today'
        : isEarlyLocked 
            ? 'Check In Locked' 
            : (provider.nextAction == 'check_in' ? 'Check In Mode' : 'Check Out Mode');
    final modeColor = isCompleted
        ? const Color(0xFF10B981)
        : isEarlyLocked
            ? const Color(0xFF9CA3AF)
            : (provider.nextAction == 'check_in'
                ? const Color(0xFF7C3AED)
                : const Color(0xFFEF4444));

    final lastScan = provider.history.isNotEmpty
        ? 'Today, ' + DateFormat('hh:mm a').format(provider.history.first.timestamp.toLocal())
        : 'No scans today';

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D14),
      body: SafeArea(
        child: Column(
          children: [
            // ── Header ─────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Align(
                    alignment: Alignment.centerLeft,
                    child: GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                        ),
                        child: const Icon(Icons.arrow_back_ios_new_rounded,
                            color: Colors.white70, size: 16),
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: modeColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: modeColor.withValues(alpha: 0.4), width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (isCompleted) Icon(Icons.check_circle, color: modeColor, size: 14),
                        if (isCompleted) const SizedBox(width: 6),
                        Text(modeLabel,
                            style: TextStyle(
                                color: modeColor,
                                fontSize: 13,
                                fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            Expanded(
              child: Column(
                children: [
                  _buildScannerCircle(provider, isRecording, isSuccess),
                  const SizedBox(height: 18),
                  _buildStatusPill(provider, isRecording, isUploading, isSuccess),
                  const SizedBox(height: 16),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: _buildChecklist(isRecording || _isAnalyzing),
                  ),
                  const Spacer(),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: _buildScanButton(
                        provider, isRecording, isUploading, isAbsentLocked, isEarlyLocked, isCompleted),
                  ),
                  const SizedBox(height: 14),
                  _buildFooter(lastScan),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Scanner Circle (280px) ────────────────────────────────────────────────
  Widget _buildScannerCircle(VerificationProvider provider,
      bool isRecording, bool isSuccess) {
    final isFailure = provider.status == VerificationStatus.failure;
    return SizedBox(
      width: 280, height: 280,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (isRecording)
            AnimatedBuilder(
              animation: _pulseController,
              builder: (ctx, _) => Container(
                width: 280, height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7C3AED)
                          .withValues(alpha: 0.25 * _pulseController.value),
                      blurRadius: 35 + 15 * _pulseController.value,
                      spreadRadius: 5 + 4 * _pulseController.value,
                    ),
                  ],
                ),
              ),
            ),
          Container(
                width: 260, height: 260,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isSuccess
                        ? const Color(0xFF7C3AED)
                        : isFailure
                            ? const Color(0xFFEF4444)
                            : const Color(0xFF7C3AED),
                    width: 3,
                  ),
                ),
                child: ClipOval(
                  child: Stack(
                    children: [
                      if (_cameraReady &&
                          provider.cameraController != null &&
                          provider.cameraController!.value.isInitialized)
                        Builder(builder: (ctx) {
                          double ratio = provider.cameraController!.value.aspectRatio;
                          if (MediaQuery.of(ctx).size.height >
                                  MediaQuery.of(ctx).size.width && ratio > 1.0) {
                            ratio = 1.0 / ratio;
                          }
                          return SizedBox.expand(
                            child: FittedBox(
                              fit: BoxFit.cover,
                              child: SizedBox(
                                width: 100 * ratio, height: 100,
                                child: CameraPreview(provider.cameraController!),
                              ),
                            ),
                          );
                        })
                      else if (isSuccess)
                        const ColoredBox(color: Color(0xFF190F2E),
                          child: Center(child: Icon(Icons.check_circle,
                              color: Color(0xFF7C3AED), size: 100)))
                      else if (isFailure)
                        const ColoredBox(color: Color(0xFF2D0D0D),
                          child: Center(child: Icon(Icons.cancel,
                              color: Color(0xFFEF4444), size: 100)))
                      else
                        ColoredBox(
                          color: Colors.black,
                          child: SizedBox.expand(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Image.asset(
                                  'assets/images/geoface_logo.png',
                                  width: 140,
                                  height: 140,
                                  fit: BoxFit.contain,
                                ),
                                const SizedBox(height: 12),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.05),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                                  ),
                                  child: Text(
                                    'Attempt ${provider.currentAttempts}/${provider.maxAttempts}',
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.6),
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),

                      ..._buildCorners(),

                      if (isRecording && _cameraReady)
                        AnimatedBuilder(
                          animation: _scanLineController,
                          builder: (ctx, _) => Positioned(
                            top: _scanLineController.value * 255,
                            left: 0, right: 0,
                            child: Container(
                              height: 2,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(colors: [
                                  const Color(0xFF7C3AED).withValues(alpha: 0.0),
                                  const Color(0xFF7C3AED),
                                  const Color(0xFFA855F7),
                                  const Color(0xFF7C3AED),
                                  const Color(0xFF7C3AED).withValues(alpha: 0.0),
                                ]),
                                boxShadow: [BoxShadow(
                                  color: const Color(0xFF7C3AED).withValues(alpha: 0.8),
                                  blurRadius: 10, spreadRadius: 1,
                                )],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
  }

  List<Widget> _buildCorners() {
    const color = Color(0xFF7C3AED);
    const sz = 28.0, st = 3.0, off = 20.0;
    return [
      Positioned(top: off, left: off,
          child: CustomPaint(painter: _CornerPainter(color, sz, st, CornerPos.topLeft))),
      Positioned(top: off, right: off,
          child: CustomPaint(painter: _CornerPainter(color, sz, st, CornerPos.topRight))),
      Positioned(bottom: off, left: off,
          child: CustomPaint(painter: _CornerPainter(color, sz, st, CornerPos.bottomLeft))),
      Positioned(bottom: off, right: off,
          child: CustomPaint(painter: _CornerPainter(color, sz, st, CornerPos.bottomRight))),
    ];
  }

  // ── Status Pill ───────────────────────────────────────────────────────────
  Widget _buildStatusPill(VerificationProvider provider, bool isRecording,
      bool isUploading, bool isSuccess) {
    final isFailure = provider.status == VerificationStatus.failure;
    String text; IconData icon; Color color;
    if (isRecording) {
      text = 'Scanning...'; icon = Icons.graphic_eq_rounded;
      color = const Color(0xFF7C3AED);
    } else if (isUploading) {
      text = 'Processing...'; icon = Icons.cloud_upload_outlined;
      color = const Color(0xFF7C3AED);
    } else if (isSuccess) {
      text = 'Verified ✓'; icon = Icons.check_circle_outline;
      color = const Color(0xFF7C3AED);
    } else if (isFailure) {
      text = 'Scan Failed'; icon = Icons.error_outline;
      color = const Color(0xFFEF4444);
    } else {
      text = 'Tap Start to scan'; icon = Icons.center_focus_strong_rounded;
      color = Colors.white54;
    }

    return AnimatedBuilder(
      animation: _pulseController,
      builder: (context, _) {
        final p = isRecording ? _pulseController.value : 0.0;
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.10 + 0.06 * p),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: color.withValues(alpha: 0.25 + 0.2 * p)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 8),
            Text(text, style: TextStyle(fontSize: 14,
                fontWeight: FontWeight.w600, color: color)),
          ]),
        );
      },
    );
  }

  // ── Checklist (real-time status) ──────────────────────────────────────────
  Widget _buildChecklist(bool isScanning) {
    // Show a stability progress hint when all individual checks pass but
    // the 3-frame gate hasn't accumulated yet.
    final stable = _faceService.consecutivePassing;
    final showStabilityHint = isScanning &&
        _scanStatus.faceDetected &&
        _scanStatus.goodLighting &&
        _scanStatus.faceCentered == false &&
        stable > 0;

    return Column(
      children: [
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
          ),
          child: Column(
            children: [
              _buildCheckRow(
                icon: Icons.face_retouching_natural_outlined,
                label: 'Face detected',
                sublabel: _scanStatus.hint ?? 'Position your full face in the circle',
                ok: isScanning ? _scanStatus.faceDetected : null,
                index: 0,
                isLast: false,
              ),
              _buildCheckRow(
                icon: Icons.wb_sunny_outlined,
                label: 'Good lighting',
                sublabel: 'Move to a brighter, evenly-lit area',
                ok: isScanning ? _scanStatus.goodLighting : null,
                index: 1,
                isLast: false,
              ),
              _buildCheckRow(
                icon: Icons.person_outline_rounded,
                label: 'Face centered',
                sublabel: 'Keep your face centred and upright',
                ok: isScanning ? _scanStatus.faceCentered : null,
                index: 2,
                isLast: true,
              ),
            ],
          ),
        ),
        if (showStabilityHint)
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFF59E0B).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                    color: const Color(0xFFF59E0B).withValues(alpha: 0.35)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.timer_outlined,
                      color: Color(0xFFF59E0B), size: 14),
                  const SizedBox(width: 6),
                  Text(
                    'Hold steady… ($stable/${FaceScanService.stabilityRequired})',
                    style: const TextStyle(
                        color: Color(0xFFF59E0B),
                        fontSize: 12,
                        fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildCheckRow({
    required IconData icon,
    required String label,
    required String sublabel,
    required bool? ok, // null = idle, true = good, false = warning
    required int index,
    required bool isLast,
  }) {
    Color iconBg, iconColor, statusColor;
    IconData statusIcon;

    if (ok == null) {
      // Idle state
      iconBg = const Color(0xFF7C3AED).withValues(alpha: 0.12);
      iconColor = const Color(0xFF7C3AED).withValues(alpha: 0.6);
      statusColor = Colors.white24;
      statusIcon = Icons.radio_button_unchecked_rounded;
    } else if (ok) {
      iconBg = const Color(0xFF7C3AED).withValues(alpha: 0.12);
      iconColor = const Color(0xFF7C3AED);
      statusColor = const Color(0xFF7C3AED);
      statusIcon = Icons.check_circle_rounded;
    } else {
      iconBg = const Color(0xFFF59E0B).withValues(alpha: 0.12);
      iconColor = const Color(0xFFF59E0B);
      statusColor = const Color(0xFFF59E0B);
      statusIcon = Icons.warning_amber_rounded;
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              // Icon box
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: iconColor, size: 20),
              ),
              const SizedBox(width: 12),
              // Labels
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w600,
                            color: Colors.white)),
                    if (ok == false)
                      Text(sublabel,
                          style: TextStyle(fontSize: 11,
                              color: const Color(0xFFF59E0B).withValues(alpha: 0.8))),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              // Status indicator
              if (ok != null)
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: Container(
                    key: ValueKey(ok),
                    width: 32, height: 32,
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                      border: Border.all(
                          color: statusColor.withValues(alpha: 0.3)),
                    ),
                    child: Icon(statusIcon, color: statusColor, size: 18),
                  ),
                ),
            ],
          ),
        ),
        if (!isLast)
          Divider(height: 1, color: Colors.white.withValues(alpha: 0.05),
              indent: 14, endIndent: 14),
      ],
    );
  }

  // ── Scan Button ───────────────────────────────────────────────────────────
  Widget _buildScanButton(VerificationProvider provider, bool isRecording,
      bool isUploading, bool isAbsentLocked, bool isEarlyLocked, bool isCompleted) {
    final canTap = !isRecording && !isUploading && !isAbsentLocked && !isEarlyLocked && !isCompleted && !_isAnalyzing;
    Color btnColor; String btnText; IconData btnIcon;

    if (isAbsentLocked) {
      btnColor = const Color(0xFFEF4444);
      btnText = 'Absent - Limit Passed';
      btnIcon = Icons.block_rounded;
    } else if (isEarlyLocked) {
      btnColor = const Color(0xFF6B7280);
      btnText = 'Too Early to Scan';
      btnIcon = Icons.lock_clock;
    } else if (isCompleted) {
      btnColor = const Color(0xFF10B981);
      btnText = 'Completed for Today';
      btnIcon = Icons.check_circle_outline_rounded;
    } else if (_isAnalyzing) {
      btnColor = const Color(0xFFF59E0B);
      btnText = 'Position your face...';
      btnIcon = Icons.face_retouching_natural;
    } else if (isRecording || isUploading) {
      btnColor = const Color(0xFF7C3AED);
      btnText = isRecording ? 'Scanning...' : 'Processing...';
      btnIcon = Icons.hourglass_top_rounded;
    } else {
      btnColor = const Color(0xFF7C3AED);
      btnText = 'Start Scan';
      btnIcon = Icons.camera_alt_rounded;
    }

    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: canTap ? _onStartScan : null,
        icon: Icon(btnIcon, color: Colors.white, size: 20),
        label: Text(btnText,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold,
                color: Colors.white)),
        style: ElevatedButton.styleFrom(
          backgroundColor: canTap ? btnColor : btnColor.withValues(alpha: 0.4),
          disabledBackgroundColor: btnColor.withValues(alpha: 0.3),
          minimumSize: const Size.fromHeight(56),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          elevation: canTap ? 6 : 0,
          shadowColor: const Color(0xFF7C3AED).withValues(alpha: 0.5),
        ),
      ),
    );
  }

  // ── Footer ────────────────────────────────────────────────────────────────
  Widget _buildFooter(String lastScan) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(children: [
        Expanded(child: _footerTile(
          Icons.shield_outlined, const Color(0xFF7C3AED),
          'Secure & Encrypted', 'Your data is protected',
        )),
        const SizedBox(width: 10),
        Expanded(child: _footerTile(
          Icons.access_time_rounded, const Color(0xFF7C3AED),
          'Last Scan', lastScan,
        )),
      ]),
    );
  }

  Widget _footerTile(IconData icon, Color color, String title, String sub) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
      ),
      child: Row(children: [
        Icon(icon, color: color.withValues(alpha: 0.7), size: 16),
        const SizedBox(width: 8),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 11,
              fontWeight: FontWeight.w600, color: Colors.white70)),
          Text(sub, style: TextStyle(fontSize: 10,
              color: Colors.white.withValues(alpha: 0.4))),
        ]),
      ]),
    );
  }
}

// ─── Painters ─────────────────────────────────────────────────────────────────
enum CornerPos { topLeft, topRight, bottomLeft, bottomRight }

class _CornerPainter extends CustomPainter {
  final Color color; final double size, stroke; final CornerPos pos;
  _CornerPainter(this.color, this.size, this.stroke, this.pos);

  @override
  void paint(Canvas canvas, Size canvasSize) {
    final paint = Paint()
      ..color = color ..strokeWidth = stroke
      ..style = PaintingStyle.stroke ..strokeCap = StrokeCap.round;
    final path = Path();
    switch (pos) {
      case CornerPos.topLeft:
        path.moveTo(size, 0); path.lineTo(0, 0); path.lineTo(0, size);
        break;
      case CornerPos.topRight:
        path.moveTo(0, 0); path.lineTo(size, 0); path.lineTo(size, size);
        break;
      case CornerPos.bottomLeft:
        path.moveTo(0, 0); path.lineTo(0, size); path.lineTo(size, size);
        break;
      case CornerPos.bottomRight:
        path.moveTo(0, size); path.lineTo(size, size); path.lineTo(size, 0);
        break;
    }
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}
