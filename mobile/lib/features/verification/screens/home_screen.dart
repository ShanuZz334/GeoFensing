import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import 'package:camera/camera.dart';
import 'dart:async';

import '../../auth/providers/auth_provider.dart';
import '../../auth/models/user_model.dart';
import '../../auth/widgets/demo_setup_dialog.dart';
import '../providers/verification_provider.dart';
import '../widgets/dynamic_qr_widget.dart';
import 'attendance_stats_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _scanLineController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    
    _scanLineController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<VerificationProvider>();
      // Always reset stale result/status from previous session on every home entry
      provider.reset();
      await provider.fetchSettings();
      await provider.fetchHistory();
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _scanLineController.dispose();
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
                      Text(
                        'GeoFace',
                        style: TextStyle(
                          fontFamily: 'Bitcount',
                          fontSize: 28,
                          fontWeight: FontWeight.w200,
                          color: const Color(0xFF7C3AED),
                          letterSpacing: -0.5,
                        ),
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
                      _buildPassportPhoto(user),
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
                          GestureDetector(
                            onTap: () => _showLargeQR(context),
                            child: DynamicQrWidget(
                              facultyId: user?.teacherId ?? '00000000',
                              size: 40,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(barcodeId, style: TextStyle(fontFamily: 'monospace', fontSize: 10, color: Colors.white.withValues(alpha: 0.5), letterSpacing: 2)),
                        ],
                      ),
                      Row(
                        children: [
                          if (context.watch<VerificationProvider>().demoMode)
                            Container(
                              margin: const EdgeInsets.only(right: 12, top: 16),
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFF7C3AED).withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: const Color(0xFF7C3AED).withValues(alpha: 0.6),
                                  width: 1.5,
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    width: 5,
                                    height: 5,
                                    decoration: const BoxDecoration(
                                      color: Color(0xFF7C3AED),
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 4),
                                  const Text(
                                    'DEMO',
                                    style: TextStyle(
                                      color: Color(0xFF7C3AED),
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 0.8,
                                    ),
                                  ),
                                ],
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

  Widget _buildPassportPhoto(UserModel? user) {
    final hasPhoto = user?.profilePic != null && user!.profilePic!.isNotEmpty;
    
    return Container(
      width: 50,
      height: 64,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.white.withValues(alpha: 0.6), width: 1.0),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.4),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(2),
        child: hasPhoto
            ? _buildImage(user.profilePic!, user)
            : _buildPlaceholderPhoto(user),
      ),
    );
  }

  Widget _buildImage(String profilePic, UserModel user) {
    // Clean the string: remove whitespace and newlines which can break Base64 decoding
    final cleanProfilePic = profilePic.trim().replaceAll(RegExp(r'\s+'), '');
    
    // Detect if this is likely a Base64 string vs a URL
    // JPEG Base64 often starts with '/9j/' which can be mistaken for a relative URL path
    bool isLikelyBase64 = cleanProfilePic.startsWith('data:image') || 
                         (cleanProfilePic.length > 100 && !cleanProfilePic.startsWith('http'));

    if (isLikelyBase64) {
      try {
        final base64String = cleanProfilePic.contains(',') ? cleanProfilePic.split(',').last : cleanProfilePic;
        return Image.memory(
          base64Decode(base64String),
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) => _buildPlaceholderPhoto(user),
        );
      } catch (e) {
        // Fall through to network if decode fails and it looks like a path
        if (!cleanProfilePic.startsWith('/')) return _buildPlaceholderPhoto(user);
      }
    }
    
    // Otherwise treat as URL (relative or absolute)
    return Image.network(
      profilePic,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) => _buildPlaceholderPhoto(user),
    );
  }

  Widget _buildPlaceholderPhoto(UserModel? user) {
    return Container(
      color: const Color(0xFF7C3AED).withValues(alpha: 0.2),
      child: Center(
        child: Text(
          user?.initials ?? '?',
          style: const TextStyle(
            color: Color(0xFF7C3AED),
            fontWeight: FontWeight.w900,
            fontSize: 16,
          ),
        ),
      ),
    );
  }

  Widget _buildAttendanceHistory(VerificationProvider provider) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: _darkBoxDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Attendance History',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              IconButton(
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const AttendanceStatsScreen()),
                ),
                icon: const Icon(Icons.arrow_forward_ios_rounded, color: Color(0xFF7C3AED), size: 20),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildHistoryList(provider),
        ],
      ),
    );
  }

  Widget _buildHistoryList(VerificationProvider provider) {
    const int maxItems = 4;
    final history = provider.history;
    
    return Column(
      children: List.generate(maxItems, (index) {
        if (index < history.length) {
          final log = history[index];
          final dateStr = DateFormat('dd MMM yyyy, hh:mm a').format(log.timestamp.toLocal());
          final isPresent = log.isSuccess;
          final isAbsentMark = log.attendanceMark == 'absent';
          final isHalfDay = log.attendanceMark == 'half_day';

          String statusLabel = log.statusDisplay;
          Color statusColor = const Color(0xFF10B981);
          
          if (isAbsentMark) {
            statusColor = const Color(0xFFEF4444);
          } else if (isHalfDay) {
            statusColor = const Color(0xFFF59E0B);
          } else if (!isPresent) {
            statusColor = const Color(0xFFEF4444);
          }

          return Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(dateStr, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 13)),
                  Text(
                    statusLabel,
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
              if (index < maxItems - 1) Divider(height: 24, color: Colors.white.withValues(alpha: 0.1)),
            ],
          );
        } else {
          // Placeholder for empty slot
          return Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('No data', style: TextStyle(color: Colors.white.withValues(alpha: 0.2), fontSize: 13)),
                  Text('--', style: TextStyle(color: Colors.white.withValues(alpha: 0.2), fontSize: 13)),
                ],
              ),
              if (index < maxItems - 1) Divider(height: 24, color: Colors.white.withValues(alpha: 0.1)),
            ],
          );
        }
      }),
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
      statusText = provider.statusMessage.contains('Absent') ? 'Marked Absent' : 'Failed ❌';
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
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    (!provider.bypassLimits && provider.nextAction == 'completed') 
                      ? 'Completed Today' 
                      : (provider.nextAction == 'check_in' ? 'Check In Mode' : 'Check Out Mode'),
                    style: TextStyle(
                      color: (!provider.bypassLimits && provider.nextAction == 'completed') 
                        ? const Color(0xFF10B981) 
                        : (provider.nextAction == 'check_in' ? const Color(0xFF7C3AED) : const Color(0xFFEF4444)),
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (!provider.bypassLimits && provider.nextAction != 'completed')
                    Text(
                      'Attempt ${provider.currentAttempts + 1}/${provider.maxAttempts}',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.5),
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                ],
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
                    child: Stack(
                      children: [
                        provider.cameraController != null &&
                                provider.cameraController!.value.isInitialized
                            ? Builder(
                                builder: (ctx) {
                                  double ratio = provider.cameraController!.value.aspectRatio;
                                  if (MediaQuery.of(ctx).size.height > MediaQuery.of(ctx).size.width && ratio > 1.0) {
                                    ratio = 1.0 / ratio;
                                  }
                                  return SizedBox.expand(
                                    child: FittedBox(
                                      fit: BoxFit.cover,
                                      child: SizedBox(
                                        width: 100 * ratio,
                                        height: 100,
                                        child: CameraPreview(provider.cameraController!),
                                      ),
                                    ),
                                  );
                                },
                              )
                            : Center(
                                child: isSuccess
                                    ? const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 80)
                                    : isFailure
                                        ? const Icon(Icons.cancel, color: Color(0xFFEF4444), size: 80)
                                        : const Icon(Icons.videocam_off_outlined, color: Colors.white38, size: 60),
                              ),
                        if (isRecording)
                          AnimatedBuilder(
                            animation: _scanLineController,
                            builder: (context, child) {
                              return Positioned(
                                top: _scanLineController.value * 200,
                                left: 0,
                                right: 0,
                                child: Container(
                                  height: 3,
                                  decoration: BoxDecoration(
                                    boxShadow: [
                                      BoxShadow(
                                        color: const Color(0xFF7C3AED).withValues(alpha: 0.6),
                                        blurRadius: 15,
                                        spreadRadius: 2,
                                      ),
                                    ],
                                    gradient: LinearGradient(
                                      colors: [
                                        const Color(0xFF7C3AED).withValues(alpha: 0.1),
                                        const Color(0xFF7C3AED),
                                        const Color(0xFF7C3AED).withValues(alpha: 0.1),
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 24),

          // Status & Progress
          if (!isSuccess && !isFailure)
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
            onPressed: (isRecording || isUploading || (!provider.bypassLimits && (provider.isTooLate() || provider.nextAction == 'completed'))) ? null : _onStartPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: (!provider.bypassLimits && provider.isTooLate()) ? Colors.redAccent : const Color(0xFF7C3AED),
              disabledBackgroundColor: Colors.white24,
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 5,
              shadowColor: const Color(0xFF7C3AED).withValues(alpha: 0.5),
            ),
            child: Text(
              (!provider.bypassLimits && provider.isTooLate())
                  ? 'Marked Absent (Too Late)' 
                  : ((!provider.bypassLimits && provider.nextAction == 'completed')
                      ? 'Completed for Today' 
                      : (isSuccess 
                          ? 'Scan Again' 
                          : (provider.nextAction == 'check_in' ? 'Start Scan (Check In)' : 'Start Scan (Check Out)'))),
              style: const TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    final provider = context.watch<VerificationProvider>();
    final rules = provider.settings['attendance_rules'] as Map<String, dynamic>?;

    // Format "09:00" → "9:00 AM"
    String fmt(String? t) {
      if (t == null || t.isEmpty) return '--';
      try {
        final parts = t.split(':');
        int h = int.parse(parts[0]);
        final m = parts[1];
        final period = h >= 12 ? 'PM' : 'AM';
        if (h > 12) h -= 12;
        if (h == 0) h = 12;
        return '$h:$m $period';
      } catch (_) { return t; }
    }

    final classStart   = fmt(rules?['class_start']  as String?);
    final classEnd     = fmt(rules?['class_end']     as String?);
    final halfDay      = fmt(rules?['half_day_limit'] as String?);
    final absentLimit  = fmt(rules?['absent_limit']  as String?);
    final halfCheckout = fmt(rules?['half_day_checkout_limit'] as String?);
    final anytime      = rules?['anytime_checkout_full_day'] == true;

    return SizedBox(
      height: 320,
      child: PageView(
        physics: const ClampingScrollPhysics(),
        children: [
          // ── Page 1: Scan Tips ──────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(20),
            decoration: _darkBoxDecoration(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Text('Instructions', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                    const Spacer(),
                    Text('Swipe for schedule →', style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.35))),
                  ],
                ),
                const SizedBox(height: 14),
                _buildInstructionItem('Ensure proper lighting on your face'),
                _buildInstructionItem('Keep your face centered in the circle'),
                _buildInstructionItem('Remove obstructions (mask, glasses if required)'),
                const SizedBox(height: 16),
                Center(
                  child: TextButton.icon(
                    onPressed: () {
                      final p = context.read<VerificationProvider>();
                      if (p.supportContact != null) {
                        _showSupportDialog(p.supportContact!);
                      } else {
                        _showSupportDialog({"phone": "8089602280", "email": "shanifshaz546@gmail.com"});
                      }
                    },
                    icon: const Icon(Icons.help_outline, color: Color(0xFF7C3AED), size: 18),
                    label: const Text('Need Help? Contact Support', style: TextStyle(color: Color(0xFF7C3AED))),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                        side: BorderSide(color: const Color(0xFF7C3AED).withValues(alpha: 0.3)),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // ── Page 2: Live Schedule from Settings ────────────────────────
          Container(
            padding: const EdgeInsets.all(20),
            decoration: _darkBoxDecoration(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  children: [
                    const Icon(Icons.schedule_rounded, color: Color(0xFF7C3AED), size: 16),
                    const SizedBox(width: 8),
                    const Text('Attendance Schedule', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                    const Spacer(),
                    Text('← Swipe back', style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.35))),
                  ],
                ),
                const SizedBox(height: 16),
                _buildScheduleRow(Icons.check_circle_outline,    'Full Day',   'Check in before $halfDay',                    const Color(0xFF10B981)),
                _buildScheduleRow(Icons.timelapse_rounded,       'Half Day',   'Check in $halfDay – $absentLimit',            const Color(0xFFF59E0B)),
                _buildScheduleRow(Icons.block_rounded,           'Absent',     'Check in after $absentLimit',                 const Color(0xFFEF4444)),
                _buildScheduleRow(Icons.logout_rounded,          anytime ? 'Checkout' : 'Early Exit',
                                                                  anytime ? 'Any time checkout counts as full day' : 'Before $halfCheckout counts as half day', const Color(0xFF7C3AED)),
                if (classEnd != '--')
                  _buildScheduleRow(Icons.access_time_filled_rounded, 'Class Hours', '$classStart – $classEnd', const Color(0xFF9CA3AF)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScheduleRow(IconData icon, String label, String desc, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 14),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label, 
                  style: const TextStyle(
                    fontSize: 13, 
                    fontWeight: FontWeight.w700, 
                    color: Colors.white,
                    letterSpacing: 0.3,
                  )
                ),
                const SizedBox(height: 2),
                Text(
                  desc, 
                  style: TextStyle(
                    fontSize: 12, 
                    color: Colors.white.withValues(alpha: 0.5),
                    height: 1.2,
                  )
                ),
              ],
            ),
          ),
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

  void _showLargeQR(BuildContext context) {
    final user = context.read<AuthProvider>().currentUser;
    int secondsLeft = 10 - ((DateTime.now().millisecondsSinceEpoch ~/ 1000) % 10);
    Timer? countdownTimer;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          countdownTimer ??= Timer.periodic(const Duration(seconds: 1), (timer) {
            if (context.mounted) {
              setState(() {
                secondsLeft = 10 - ((DateTime.now().millisecondsSinceEpoch ~/ 1000) % 10);
              });
            } else {
              timer.cancel();
            }
          });

          return Dialog(
            backgroundColor: Colors.transparent,
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Faculty QR Code',
                    style: TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Scannable for $secondsLeft second${secondsLeft == 1 ? '' : 's'}',
                    style: const TextStyle(color: Colors.black54, fontSize: 12),
                  ),
                  const SizedBox(height: 24),
                  DynamicQrWidget(
                    facultyId: user?.teacherId ?? '00000000',
                    size: 260,
                  ),
                  const SizedBox(height: 24),
                  TextButton(
                    onPressed: () {
                      countdownTimer?.cancel();
                      Navigator.pop(context);
                    },
                    child: const Text('Close', style: TextStyle(color: Color(0xFF7C3AED), fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    ).then((_) => countdownTimer?.cancel());
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
