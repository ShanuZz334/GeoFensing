import 'package:flutter/material.dart';

import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import 'dart:async';

import '../../auth/providers/auth_provider.dart';
import '../../auth/models/user_model.dart';
import '../../auth/widgets/demo_setup_dialog.dart';
import '../../../core/constants/app_config.dart';
import '../providers/verification_provider.dart';
import '../widgets/dynamic_qr_widget.dart';
import 'attendance_stats_screen.dart';
import 'face_scan_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  late PageController _cardPageController;

  @override
  void initState() {
    super.initState();
    _cardPageController = PageController(initialPage: 1000);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<VerificationProvider>();
      provider.reset();
      await provider.fetchSettings();
      await provider.fetchHistory();
    });
  }

  @override
  void dispose() {
    _cardPageController.dispose();
    super.dispose();
  }

  void _onStartPressed() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const FaceScanScreen()),
    ).then((_) {
      // Refresh history when returning from scan screen
      if (mounted) context.read<VerificationProvider>().fetchHistory();
    });
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
                      RichText(
                        text: const TextSpan(
                          text: 'Geo',
                          style: TextStyle(
                            fontFamily: 'Bitcount',
                            fontSize: 28,
                            fontWeight: FontWeight.w200,
                            color: Colors.white70,
                            letterSpacing: -0.5,
                          ),
                          children: [
                            TextSpan(
                              text: 'Face',
                              style: TextStyle(
                                color: Color(0xFF9F00FF),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 4),
                      if (kDemoEnabled)
                        InkWell(
                          onTap: () => showDialog(context: context, builder: (_) => const DemoSetupDialog()),
                          child: const Icon(Icons.play_circle_outline, color: Color(0xFF7C3AED), size: 16),
                        ),
                    ],
                  ),
                ),
              ),

              // 1. Faculty Pass
              _buildUserInfo(context, user, auth),
              const SizedBox(height: 24),

              // 2. Scan Button
              _buildScanButton(verificationProvider),
              const SizedBox(height: 24),

              // 3. Infinite swipeable info cards
              _buildSwipeableCards(verificationProvider),
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
                      Expanded(child: _buildTicketDetail('DEPT', _formatDept(user?.department))),
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
                          if (kDemoEnabled && context.watch<VerificationProvider>().demoMode)
                            Container(
                              margin: const EdgeInsets.only(right: 12, top: 16),
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFF7C3AED).withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.3)),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 6,
                                    height: 6,
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

  Widget _buildScanButton(VerificationProvider provider) {
    final isAbsentLocked = !provider.bypassLimits &&
        provider.isTooLate() &&
        provider.nextAction != 'check_out' &&
        provider.nextAction != 'completed';
    final isCompleted = !provider.bypassLimits && provider.nextAction == 'completed';

    Color btnColor;
    String btnText;
    IconData btnIcon;

    if (isAbsentLocked) {
      btnColor = const Color(0xFFEF4444);
      btnText = 'Absent - Limit Passed';
      btnIcon = Icons.block_rounded;
    } else if (isCompleted) {
      btnColor = const Color(0xFF10B981);
      btnText = 'Completed for Today';
      btnIcon = Icons.check_circle_outline_rounded;
    } else {
      btnColor = const Color(0xFF7C3AED);
      btnText = provider.nextAction == 'check_in'
          ? 'Start Scan (Check In)'
          : 'Start Scan (Check Out)';
      btnIcon = provider.nextAction == 'check_in'
          ? Icons.login_rounded
          : Icons.logout_rounded;
    }

    return ElevatedButton.icon(
      onPressed: (isAbsentLocked || isCompleted) ? null : _onStartPressed,
      icon: Icon(btnIcon, color: Colors.white, size: 20),
      label: Text(btnText,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
      style: ElevatedButton.styleFrom(
        backgroundColor: btnColor,
        disabledBackgroundColor: btnColor.withValues(alpha: 0.35),
        minimumSize: const Size.fromHeight(56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        elevation: 6,
        shadowColor: btnColor.withValues(alpha: 0.4),
      ),
    );
  }

  Widget _buildSwipeableCards(VerificationProvider provider) {
    return SizedBox(
      height: 300,
      child: PageView.builder(
        controller: _cardPageController,
        itemBuilder: (context, index) {
          final page = index % 3;
          if (page == 0) return _buildStatusCard(provider);
          if (page == 1) return _buildHistoryCard(provider);
          return _buildScheduleCard(provider);
        },
      ),
    );
  }

  Widget _buildStatusCard(VerificationProvider provider) {
    final isCompleted = !provider.bypassLimits && provider.nextAction == 'completed';
    final isAbsentLocked = !provider.bypassLimits &&
        provider.isTooLate() &&
        provider.nextAction != 'check_out' &&
        provider.nextAction != 'completed';

    final modeText = isCompleted
        ? 'Completed Today'
        : isAbsentLocked
            ? 'Marked Absent'
            : provider.nextAction == 'check_in'
                ? 'Check In Mode'
                : 'Check Out Mode';
    final modeColor = isCompleted
        ? const Color(0xFF10B981)
        : isAbsentLocked
            ? const Color(0xFFEF4444)
            : provider.nextAction == 'check_in'
                ? const Color(0xFF7C3AED)
                : const Color(0xFFEF4444);

    return _cardShell(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Verification Status',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white)),
              Text('1/3', style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.3))),
            ],
          ),
          const SizedBox(height: 24),
          Icon(
            isCompleted ? Icons.check_circle_outline_rounded
              : isAbsentLocked ? Icons.block_rounded
              : Icons.face_retouching_natural_outlined,
            color: modeColor,
            size: 64,
          ),
          const SizedBox(height: 16),
          Text(modeText,
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: modeColor)),
          const SizedBox(height: 8),
          if (!provider.bypassLimits && !isCompleted)
            Text('Attempt ${provider.currentAttempts + 1}/${provider.maxAttempts}',
                style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.4))),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (i) => Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: i == 0 ? 18 : 6,
              height: 6,
              decoration: BoxDecoration(
                color: i == 0 ? const Color(0xFF7C3AED) : Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(3),
              ),
            )),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryCard(VerificationProvider provider) {
    const maxItems = 4;
    final history = provider.history;
    return _cardShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Attendance History',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white)),
              Row(
                children: [
                  Text('2/3', style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.3))),
                  const SizedBox(width: 8),
                  IconButton(
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    onPressed: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => const AttendanceStatsScreen())),
                    icon: const Icon(Icons.arrow_forward_ios_rounded, color: Color(0xFF7C3AED), size: 16),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: Column(
              children: List.generate(maxItems, (index) {
                if (index < history.length) {
                  final log = history[index];
                  final dateStr = DateFormat('dd MMM, hh:mm a').format(log.timestamp.toLocal());
                  Color statusColor = log.attendanceMark == 'absent'
                      ? const Color(0xFFEF4444)
                      : log.attendanceMark == 'half_day'
                          ? const Color(0xFFF59E0B)
                          : log.isSuccess ? const Color(0xFF10B981) : const Color(0xFFEF4444);
                  return Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(dateStr, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500)),
                            Text(log.statusDisplay, style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.w900)),
                          ],
                        ),
                        if (index < maxItems - 1)
                          Divider(height: 1, color: Colors.white.withValues(alpha: 0.08)),
                      ],
                    ),
                  );
                }
                return Expanded(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('No data', style: TextStyle(color: Colors.white.withValues(alpha: 0.2), fontSize: 12)),
                      Text('--', style: TextStyle(color: Colors.white.withValues(alpha: 0.2), fontSize: 12)),
                    ],
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (i) => Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: i == 1 ? 18 : 6, height: 6,
              decoration: BoxDecoration(
                color: i == 1 ? const Color(0xFF7C3AED) : Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(3),
              ),
            )),
          ),
        ],
      ),
    );
  }

  Widget _buildScheduleCard(VerificationProvider provider) {
    final rules = provider.settings['attendance_rules'] as Map<String, dynamic>?;
    String fmt(String? t) {
      if (t == null || t.isEmpty) return '--';
      try {
        final p = t.split(':'); int h = int.parse(p[0]); final m = p[1];
        final period = h >= 12 ? 'PM' : 'AM';
        if (h > 12) h -= 12; if (h == 0) h = 12;
        return '$h:$m $period';
      } catch (_) { return t; }
    }
    final halfDay     = fmt(rules?['half_day_limit'] as String?);
    final absentLimit = fmt(rules?['absent_limit'] as String?);
    final halfCheckout= fmt(rules?['half_day_checkout_limit'] as String?);
    final anytime     = rules?['anytime_checkout_full_day'] == true;

    return _cardShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(children: [
                const Icon(Icons.schedule_rounded, color: Color(0xFF7C3AED), size: 15),
                const SizedBox(width: 6),
                const Text('Attendance Schedule', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white)),
              ]),
              Text('3/3', style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.3))),
            ],
          ),
          const SizedBox(height: 14),
          _buildScheduleRow(Icons.check_circle_outline, 'Full Day', 'Check in before $halfDay', const Color(0xFF10B981)),
          _buildScheduleRow(Icons.timelapse_rounded, 'Half Day', 'Check in $halfDay – $absentLimit', const Color(0xFFF59E0B)),
          _buildScheduleRow(Icons.block_rounded, 'Absent', 'Check in after $absentLimit', const Color(0xFFEF4444)),
          _buildScheduleRow(Icons.logout_rounded,
            anytime ? 'Checkout' : 'Early Exit',
            anytime ? 'Any time counts as full day' : 'Before $halfCheckout = half day',
            const Color(0xFF7C3AED)),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (i) => Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: i == 2 ? 18 : 6, height: 6,
              decoration: BoxDecoration(
                color: i == 2 ? const Color(0xFF7C3AED) : Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(3),
              ),
            )),
          ),
        ],
      ),
    );
  }

  Widget _cardShell({required Widget child}) {
    return Container(
      margin: EdgeInsets.zero,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
      ),
      child: child,
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

  String _formatDept(String? deptStr) {
    if (deptStr == null || deptStr.isEmpty) return '-';
    
    final deptNicknames = {
      "Computer Science": "CSE",
      "Electronics & Electrical": "EEE/ECE",
      "Civil Engineering": "CE",
      "Mechanical Engineering": "ME",
      "Mittal School of Business": "MSB",
      "School of Law": "LAW",
      "Hotel Management & Tourism": "HM",
      "Architecture & Design": "ARCH",
      "Agriculture": "AGRI",
      "Pharmacy": "PHARMA",
      "Bioengineering & Biosciences": "BIO",
      "Physical Education": "PE",
      "Fashion Design": "FD",
      "Media & Communication": "MEDIA",
      "Allied Medical Sciences": "PHYSIO",
      "Computer Applications": "IT"
    };

    for (var entry in deptNicknames.entries) {
      if (deptStr.contains(entry.key)) return entry.value;
    }
    
    final match = RegExp(r'\((.*?)\)').firstMatch(deptStr);
    if (match != null) return match.group(1)!;
    
    return deptStr;
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
