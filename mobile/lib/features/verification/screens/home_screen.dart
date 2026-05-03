import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import 'package:camera/camera.dart';

import '../../auth/providers/auth_provider.dart';
import '../../auth/models/user_model.dart';
import '../../auth/widgets/demo_setup_dialog.dart';
import '../providers/verification_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<VerificationProvider>();
      await provider.fetchSettings();
      await provider.fetchHistory();
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    context.read<VerificationProvider>().disposeCamera();
    super.dispose();
  }

  Future<void> _onStartPressed() async {
    final provider = context.read<VerificationProvider>();
    
    if (provider.isTooLate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("You are too late. You have been marked as Absent."),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    await provider.startVerification();
    if (!mounted) return;

    if (provider.result?.contactSupport != null) {
      _showSupportDialog(provider.result!.contactSupport!);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.statusMessage),
          backgroundColor: provider.status == VerificationStatus.success ? Colors.green : Colors.redAccent,
        ),
      );
    }
  }

  void _showSupportDialog(Map<String, dynamic> contact) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF121212),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        ),
        title: const Row(
          children: [
            Icon(Icons.contact_support_outlined, color: Color(0xFF7C3AED)),
            SizedBox(width: 10),
            Text('Contact Support', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('You have exceeded the maximum attempts. Please reach out to our team:', style: TextStyle(color: Colors.white.withValues(alpha: 0.7))),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.phone, color: Color(0xFF7C3AED)),
                    title: Text(contact['phone'] ?? '8089602280', style: const TextStyle(color: Colors.white)),
                    dense: true,
                  ),
                  ListTile(
                    leading: const Icon(Icons.email, color: Color(0xFF7C3AED)),
                    title: Text(contact['email'] ?? 'shanifshaz546@gmail.com', style: const TextStyle(color: Colors.white)),
                    dense: true,
                  ),
                ],
              ),
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

  BoxDecoration _darkBoxDecoration() {
    return BoxDecoration(
      color: const Color(0xFF121212),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      boxShadow: [
        BoxShadow(
          color: Colors.white.withValues(alpha: 0.1),
          blurRadius: 15,
          offset: const Offset(0, 0),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final verificationProvider = context.watch<VerificationProvider>();
    final user = auth.currentUser;

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // GeoFace Logo Header
              Center(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 24),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'GeoFace',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF7C3AED), letterSpacing: -0.5),
                      ),
                      const SizedBox(width: 4),
                      InkWell(
                        onTap: () => showDialog(context: context, builder: (_) => const DemoSetupDialog()),
                        child: const Icon(Icons.play_circle_outline, color: Color(0xFF7C3AED), size: 16),
                      ),
                    ],
                  ),
                ),
              ),

              // 1. User Info Section
              _buildUserInfo(context, user, auth),
              const SizedBox(height: 24),

              // 2. Attendance History
              _buildAttendanceHistory(verificationProvider),
              const SizedBox(height: 24),

              // 3. Face Scanner
              _buildFaceScanner(verificationProvider),
              const SizedBox(height: 24),

              // 4. Instructions
              _buildInstructions(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUserInfo(BuildContext context, UserModel? user, AuthProvider auth) {
    final barcodeId = 'GF-${user?.teacherId.substring(0, 8).toUpperCase() ?? '00000000'}';

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.6),
            blurRadius: 30,
            offset: const Offset(0, 15),
          ),
        ],
      ),
      child: ClipPath(
        clipper: TicketClipper(topHeight: 220),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Top Section (t-main)
            Container(
              height: 220,
              padding: const EdgeInsets.all(24),
              color: const Color(0xFF1E1E24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.security, color: Color(0xFF7C3AED), size: 20),
                          SizedBox(width: 8),
                          Text('LPU', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1, color: Colors.white)),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          border: Border.all(color: const Color(0xFF7C3AED)),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Text('FACULTY PASS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF7C3AED), letterSpacing: 1.5)),
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Name
                  Text(
                    user?.fullName.toUpperCase() ?? 'FACULTY MEMBER',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                      height: 1.1,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const Spacer(),
                  // Details Grid
                  Row(
                    children: [
                      Expanded(child: _buildTicketDetail('REG NO', user?.regNo ?? '-')),
                      Expanded(child: _buildTicketDetail('DEPT', user?.department ?? '-')),
                    ],
                  ),
                ],
              ),
            ),
            
            // Bottom Section (t-stub)
            Container(
              color: const Color(0xFF2B2B36),
              height: 100,
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  // Dashed Line (positioned at the top)
                  Positioned(
                    top: 0,
                    left: 0,
                    right: 0,
                    child: CustomPaint(
                      painter: DashedLinePainter(),
                      size: const Size(double.infinity, 2),
                    ),
                  ),
                  // Content
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.9), borderRadius: BorderRadius.circular(4)),
                            child: const Icon(Icons.qr_code_2, size: 40, color: Colors.black),
                          ),
                          const SizedBox(height: 6),
                          Text(barcodeId, style: TextStyle(fontFamily: 'monospace', fontSize: 10, color: Colors.white.withValues(alpha: 0.5), letterSpacing: 2)),
                        ],
                      ),
                      Row(
                        children: [
                          if (context.watch<VerificationProvider>().demoMode)
                            Container(
                              margin: const EdgeInsets.only(right: 16, top: 16),
                              width: 12,
                              height: 12,
                              decoration: const BoxDecoration(
                                color: Colors.greenAccent,
                                shape: BoxShape.circle,
                                boxShadow: [BoxShadow(color: Colors.greenAccent, blurRadius: 6, spreadRadius: 2)],
                              ),
                            ),
                          Padding(
                            padding: const EdgeInsets.only(top: 16.0),
                            child: IconButton(
                              onPressed: () async {
                                await auth.logout();
                                if (context.mounted) {
                                  Navigator.pushReplacementNamed(context, '/login');
                                }
                              },
                              icon: const Icon(Icons.logout_rounded, color: Color(0xFFEF4444), size: 28),
                              tooltip: 'Sign Out',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTicketDetail(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 10, color: Colors.white.withValues(alpha: 0.5), letterSpacing: 1)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white), maxLines: 1, overflow: TextOverflow.ellipsis),
      ],
    );
  }

  Widget _buildAttendanceHistory(VerificationProvider provider) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _darkBoxDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Attendance History',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          provider.history.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 20),
                    child: Text('No previous records found', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 14)),
                  ),
                )
              : ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: provider.history.length > 4 ? 4 : provider.history.length,
                  separatorBuilder: (_, __) => Divider(height: 20, color: Colors.white.withValues(alpha: 0.1)),
                  itemBuilder: (context, index) {
                    final log = provider.history[index];
                    final dateStr = DateFormat('dd MMM yyyy, hh:mm a').format(log.timestamp.toLocal());
                    final isPresent = log.status.toLowerCase() == 'success';
                    final isAbsentMark = log.attendanceMark == 'absent';
                    final isHalfDay = log.attendanceMark == 'half_day';

                    String statusText;
                    if (isPresent) {
                       statusText = log.actionType == 'check_in' ? 'Checked in' : 'Checked out';
                       if (isHalfDay) statusText += ' (Half Day)';
                    } else {
                       statusText = isAbsentMark ? 'Marked Absent' : 'Failed ${log.actionType == 'check_in' ? "Check In" : "Check Out"}';
                    }

                    return Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(dateStr, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                        Text(
                          statusText,
                          style: TextStyle(
                            color: isPresent ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    );
                  },
                ),
        ],
      ),
    );
  }

  Widget _buildFaceScanner(VerificationProvider provider) {
    final isRecording = provider.status == VerificationStatus.recording;
    final isUploading = provider.status == VerificationStatus.uploading;
    final isSuccess = provider.status == VerificationStatus.success;
    final isFailure = provider.status == VerificationStatus.failure;

    String statusText = 'Ready to scan';
    IconData statusIcon = Icons.camera_alt_outlined;
    Color statusColor = const Color(0xFF7C3AED);

    if (isRecording) {
      statusText = provider.statusMessage.isNotEmpty ? provider.statusMessage : 'Scanning...';
      statusIcon = Icons.face_retouching_natural_outlined;
    } else if (isUploading) {
      statusText = 'Processing...';
      statusIcon = Icons.cloud_upload_outlined;
    } else if (isSuccess) {
      statusText = 'Ready to scan';
      statusIcon = Icons.camera_alt_outlined;
      statusColor = const Color(0xFF7C3AED);
    } else if (isFailure) {
      statusText = 'Failed ❌';
      statusIcon = Icons.error_outline_rounded;
      statusColor = const Color(0xFFEF4444);
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _darkBoxDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Face Verification',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              Text(
                provider.nextAction == 'check_in' ? 'Check In Mode' : 'Check Out Mode',
                style: TextStyle(
                  color: provider.nextAction == 'check_in' ? const Color(0xFF7C3AED) : const Color(0xFFEF4444),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          
          // Camera Preview Area
          Center(
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (context, child) {
                return Container(
                  width: 200,
                  height: 200,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: statusColor, width: 3),
                    boxShadow: [
                      if (isRecording)
                        BoxShadow(
                          color: statusColor.withValues(alpha: 0.3 * _pulseController.value),
                          blurRadius: 10 + 10 * _pulseController.value,
                          spreadRadius: 2 + 3 * _pulseController.value,
                        ),
                    ],
                  ),
                  child: ClipOval(
                    child: provider.cameraController != null &&
                            provider.cameraController!.value.isInitialized
                        ? AspectRatio(
                            aspectRatio: 1.0,
                            child: CameraPreview(provider.cameraController!),
                          )
                        : Container(
                            color: Colors.white.withValues(alpha: 0.05),
                            child: isSuccess
                                ? const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 80)
                                : isFailure
                                    ? const Icon(Icons.cancel, color: Color(0xFFEF4444), size: 80)
                                    : const Icon(Icons.videocam_off_outlined, color: Colors.white38, size: 40),
                          ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 24),

          // Status & Progress
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(statusIcon, color: statusColor, size: 20),
              const SizedBox(width: 8),
              Text(
                statusText,
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: statusColor),
              ),
            ],
          ),
          if (isUploading) ...[
            const SizedBox(height: 12),
            const SizedBox(
              width: 140,
              child: LinearProgressIndicator(
                backgroundColor: Colors.white12,
                color: Color(0xFF7C3AED),
                minHeight: 4,
              ),
            ),
          ],
          const SizedBox(height: 20),

          ElevatedButton(
            onPressed: (isRecording || isUploading || provider.isTooLate()) ? null : _onStartPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: provider.isTooLate() ? Colors.redAccent : const Color(0xFF7C3AED),
              disabledBackgroundColor: Colors.white24,
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 5,
              shadowColor: const Color(0xFF7C3AED).withValues(alpha: 0.5),
            ),
            child: Text(
              provider.isTooLate() ? 'Marked Absent (Too Late)' : (isSuccess ? 'Scan Again' : (provider.nextAction == 'check_in' ? 'Start Scan (Check In)' : 'Start Scan (Check Out)')),
              style: const TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _darkBoxDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Instructions',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          _buildInstructionItem('Ensure proper lighting'),
          _buildInstructionItem('Keep face centered'),
          _buildInstructionItem('Remove obstructions (mask, glasses if required)'),
        ],
      ),
    );
  }

  Widget _buildInstructionItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ', style: TextStyle(fontSize: 16, color: Color(0xFF7C3AED), fontWeight: FontWeight.bold)),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.7), height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class TicketClipper extends CustomClipper<Path> {
  final double holeRadius;
  final double topHeight;

  TicketClipper({this.holeRadius = 12, required this.topHeight});

  @override
  Path getClip(Size size) {
    final path = Path();
    path.moveTo(0, 0);
    path.lineTo(0, topHeight - holeRadius);
    path.arcToPoint(
      Offset(0, topHeight + holeRadius),
      radius: Radius.circular(holeRadius),
      clockwise: true,
    );
    path.lineTo(0, size.height);
    path.lineTo(size.width, size.height);
    path.lineTo(size.width, topHeight + holeRadius);
    path.arcToPoint(
      Offset(size.width, topHeight - holeRadius),
      radius: Radius.circular(holeRadius),
      clockwise: true,
    );
    path.lineTo(size.width, 0);
    path.close();
    return path;
  }

  @override
  bool shouldReclip(TicketClipper oldClipper) => true;
}

class DashedLinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    var paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.2)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
      
    var dashWidth = 8.0;
    var dashSpace = 6.0;
    var startX = 0.0;
    
    while (startX < size.width) {
      canvas.drawLine(Offset(startX, 0), Offset(startX + dashWidth, 0), paint);
      startX += dashWidth + dashSpace;
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
