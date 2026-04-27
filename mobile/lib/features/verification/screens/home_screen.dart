import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import 'package:camera/camera.dart';

import '../../auth/providers/auth_provider.dart';
import '../../auth/models/user_model.dart';
import '../providers/verification_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  bool _cameraReady = false;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VerificationProvider>().fetchHistory();
      _initCamera();
    });
  }

  Future<void> _initCamera() async {
    final provider = context.read<VerificationProvider>();
    await provider.initCamera();
    if (mounted) setState(() => _cameraReady = true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    context.read<VerificationProvider>().disposeCamera();
    super.dispose();
  }

  Future<void> _onStartPressed() async {
    final provider = context.read<VerificationProvider>();
    await provider.startVerification();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.statusMessage),
          backgroundColor: provider.status == VerificationStatus.success ? Colors.green : Colors.redAccent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final verificationProvider = context.watch<VerificationProvider>();
    final user = auth.currentUser;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
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
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: const Color(0xFFEFF6FF),
            backgroundImage: (user?.profilePic != null && user!.profilePic!.isNotEmpty)
                ? MemoryImage(base64Decode(user.profilePic!))
                : null,
            child: (user?.profilePic == null || user!.profilePic!.isEmpty)
                ? const Icon(Icons.person_rounded, color: Color(0xFF2563EB), size: 30)
                : null,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  user?.fullName ?? 'Faculty Member',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Color(0xFF0F172A)),
                ),
                const SizedBox(height: 4),
                Text(
                  user?.email ?? 'faculty@geoface.io',
                  style: const TextStyle(fontSize: 13, color: Color(0xFF64748B)),
                ),
              ],
            ),
          ),
          if (context.watch<VerificationProvider>().demoMode)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Container(
                width: 12,
                height: 12,
                decoration: const BoxDecoration(
                  color: Colors.greenAccent,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.greenAccent,
                      blurRadius: 6,
                      spreadRadius: 2,
                    ),
                  ],
                ),
              ),
            ),
          IconButton(
            onPressed: () async {
              await auth.logout();
              if (context.mounted) {
                Navigator.pushReplacementNamed(context, '/login');
              }
            },
            icon: const Icon(Icons.logout_rounded, color: Color(0xFFEF4444)),
            tooltip: 'Sign Out',
          ),
        ],
      ),
    );
  }

  Widget _buildAttendanceHistory(VerificationProvider provider) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Attendance History',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
          ),
          const SizedBox(height: 16),
          provider.history.isEmpty
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Text('No previous records found', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 14)),
                  ),
                )
              : ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: provider.history.length > 4 ? 4 : provider.history.length,
                  separatorBuilder: (_, __) => const Divider(height: 20, color: Color(0xFFF1F5F9)),
                  itemBuilder: (context, index) {
                    final log = provider.history[index];
                    final dateStr = DateFormat('EEE, MMM d, yyyy').format(log.timestamp);
                    final isPresent = log.status.toLowerCase() == 'success';

                    return Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(dateStr, style: const TextStyle(color: Color(0xFF334155), fontWeight: FontWeight.w500)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: isPresent ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            isPresent ? 'Present' : 'Absent',
                            style: TextStyle(
                              color: isPresent ? const Color(0xFF15803D) : const Color(0xFFB91C1C),
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
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
    Color statusColor = const Color(0xFF2563EB);

    if (isRecording) {
      statusText = provider.statusMessage.isNotEmpty ? provider.statusMessage : 'Scanning...';
      statusIcon = Icons.face_retouching_natural_outlined;
    } else if (isUploading) {
      statusText = 'Processing...';
      statusIcon = Icons.cloud_upload_outlined;
    } else if (isSuccess) {
      statusText = 'Ready to scan';
      statusIcon = Icons.camera_alt_outlined;
      statusColor = const Color(0xFF2563EB);
    } else if (isFailure) {
      statusText = 'Failed ❌';
      statusIcon = Icons.error_outline_rounded;
      statusColor = const Color(0xFFEF4444);
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Face Verification',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
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
                    child: _cameraReady &&
                            provider.cameraController != null &&
                            provider.cameraController!.value.isInitialized
                        ? AspectRatio(
                            aspectRatio: 1.0,
                            child: CameraPreview(provider.cameraController!),
                          )
                        : Container(
                            color: const Color(0xFFF1F5F9),
                            child: const Icon(Icons.videocam_off_outlined, color: Color(0xFF94A3B8), size: 40),
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
                backgroundColor: Color(0xFFF1F5F9),
                color: Color(0xFF2563EB),
                minHeight: 4,
              ),
            ),
          ],
          const SizedBox(height: 20),

          ElevatedButton(
            onPressed: (isRecording || isUploading) ? null : _onStartPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2563EB),
              disabledBackgroundColor: const Color(0xFF94A3B8),
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 0,
            ),
            child: Text(
              isSuccess ? 'Scan Again' : 'Start Scan',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Instructions',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
          ),
          const SizedBox(height: 16),
          _buildInstructionItem('Ensure proper lighting'),
          _buildInstructionItem('Keep face centered'),
          _buildInstructionItem('Remove obstructions (mask, glasses if required)'),
          _buildInstructionItem('Turn left, look straight, then turn right when prompted'),
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
          const Text('• ', style: TextStyle(fontSize: 16, color: Color(0xFF2563EB), fontWeight: FontWeight.bold)),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 14, color: Color(0xFF475569), height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}
