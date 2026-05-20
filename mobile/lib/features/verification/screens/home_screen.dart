import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../auth/providers/auth_provider.dart';
import '../../auth/models/user_model.dart';
import '../../auth/widgets/demo_setup_dialog.dart';
import '../../profile/screens/profile_screen.dart';
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

  late final VerificationProvider _provider;

  @override
  void initState() {
    super.initState();
    _provider = context.read<VerificationProvider>();
    _cardPageController = PageController(initialPage: 999);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      _provider.reset();
      await _provider.fetchSettings();
      await _provider.fetchHistory();
      _provider.fetchStats();
      _provider.startPolling();
    });
  }

  @override
  void dispose() {
    _cardPageController.dispose();
    _provider.stopPolling();
    super.dispose();
  }

  void _onStartPressed() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const FaceScanScreen()),
    ).then((_) {
      if (mounted) {
        final provider = context.read<VerificationProvider>();
        provider.fetchHistory();
        provider.fetchStats(); // Update stats after a new scan
      }
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
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Header ──────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.only(bottom: 24),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Row(
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
                                style: TextStyle(color: Color(0xFF9F00FF)),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 4),
                        if (kDemoEnabled)
                          InkWell(
                            onTap: () => showDialog(
                                context: context,
                                builder: (_) => const DemoSetupDialog()),
                            child: const Icon(Icons.play_circle_outline,
                                color: Color(0xFF7C3AED), size: 16),
                          ),
                      ],
                    ),
                    Align(
                      alignment: Alignment.centerRight,
                      child: GestureDetector(
                        onTap: () => Navigator.push(context,
                            MaterialPageRoute(
                                builder: (_) => const ProfileScreen())),
                        child: const Icon(Icons.person_outline,
                            color: Colors.white70, size: 26),
                      ),
                    ),
                  ],
                ),
              ),

              // 1. Faculty Pass Card (flippable)
              _FacultyPassCard(user: user, auth: auth),
              const SizedBox(height: 24),

              // 2. Scan Button
              _buildScanButton(verificationProvider),
              const SizedBox(height: 24),

              // 3. Swipeable info cards
              _buildSwipeableCards(verificationProvider),
            ],
          ),
        ),
      ),
    );
  }

  // ── Scan Button ──────────────────────────────────────────────────────────
  Widget _buildScanButton(VerificationProvider provider) {
    final isAbsentLocked = !provider.bypassLimits &&
        provider.isTooLate() &&
        provider.nextAction != 'check_out' &&
        provider.nextAction != 'completed';
    final isCompleted =
        !provider.bypassLimits && provider.nextAction == 'completed';

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
      btnColor = const Color(0xFF44388F);
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
          style: const TextStyle(
              fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
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

  // ── Swipeable Cards ──────────────────────────────────────────────────────
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
    final isCompleted =
        !provider.bypassLimits && provider.nextAction == 'completed';
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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(children: [
                const Icon(Icons.verified_user_outlined,
                    color: Color(0xFF7C3AED), size: 15),
                const SizedBox(width: 6),
                const Text('Verification Status',
                    style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
              ]),
              Text('1/3',
                  style: TextStyle(
                      fontSize: 11,
                      color: Colors.white.withValues(alpha: 0.3))),
            ],
          ),
          const SizedBox(height: 14),
          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isCompleted
                        ? Icons.check_circle_outline_rounded
                        : isAbsentLocked
                            ? Icons.block_rounded
                            : Icons.face_retouching_natural_outlined,
                    color: modeColor,
                    size: 64,
                  ),
                  const SizedBox(height: 16),
                  Text(modeText,
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: modeColor)),
                  const SizedBox(height: 8),
                  if (!provider.bypassLimits && !isCompleted)
                    Text(
                        'Attempt ${provider.currentAttempts + 1}/${provider.maxAttempts}',
                        style: TextStyle(
                            fontSize: 12,
                            color: Colors.white.withValues(alpha: 0.4))),
                ],
              ),
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
                3,
                (i) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: i == 0 ? 18 : 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: i == 0
                            ? const Color(0xFF7C3AED)
                            : Colors.white.withValues(alpha: 0.2),
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
              Row(children: [
                const Icon(Icons.history_rounded,
                    color: Color(0xFF7C3AED), size: 15),
                const SizedBox(width: 6),
                const Text('Attendance History',
                    style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
              ]),
              Row(
                children: [
                  Text('2/3',
                      style: TextStyle(
                          fontSize: 11,
                          color: Colors.white.withValues(alpha: 0.3))),
                  const SizedBox(width: 8),
                  IconButton(
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => const AttendanceStatsScreen())),
                    icon: const Icon(Icons.arrow_forward_ios_rounded,
                        color: Color(0xFF7C3AED), size: 14),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Expanded(
            child: history.isEmpty
                ? Center(
                    child: Text('No recent logs',
                        style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.4),
                            fontSize: 13)))
                : SingleChildScrollView(
                    physics: const NeverScrollableScrollPhysics(),
                    child: Column(
                      children: List.generate(
                        history.length > maxItems ? maxItems : history.length,
                        (index) {
                          final log = history[index];
                          final dateStr = DateFormat('dd MMM, hh:mm a')
                              .format(log.timestamp.toLocal());
                          Color statusColor = log.attendanceMark == 'absent'
                              ? const Color(0xFFEF4444)
                              : log.attendanceMark == 'half_day'
                                  ? const Color(0xFFF59E0B)
                                  : log.isSuccess
                                      ? const Color(0xFF10B981)
                                      : const Color(0xFFEF4444);
                          IconData statusIcon = log.attendanceMark == 'absent'
                              ? Icons.block_rounded
                              : log.attendanceMark == 'half_day'
                                  ? Icons.timelapse_rounded
                                  : log.isSuccess
                                      ? Icons.check_circle_outline
                                      : Icons.error_outline_rounded;
                          return _buildHistoryRow(
                              statusIcon, dateStr, log.statusDisplay, statusColor);
                        },
                      ),
                    ),
                  ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
                3,
                (i) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: i == 1 ? 18 : 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: i == 1
                            ? const Color(0xFF7C3AED)
                            : Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    )),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryRow(
      IconData icon, String dateStr, String statusDisplay, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
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
            child: Text(dateStr,
                style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                    letterSpacing: 0.3)),
          ),
          Text(statusDisplay,
              style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w900, color: color)),
        ],
      ),
    );
  }

  Widget _buildScheduleCard(VerificationProvider provider) {
    final rules =
        provider.settings['attendance_rules'] as Map<String, dynamic>?;
    String fmt(String? t) {
      if (t == null || t.isEmpty) return '--';
      try {
        final p = t.split(':');
        int h = int.parse(p[0]);
        final m = p[1];
        final period = h >= 12 ? 'PM' : 'AM';
        if (h > 12) h -= 12;
        if (h == 0) h = 12;
        return '$h:$m $period';
      } catch (_) {
        return t;
      }
    }

    final halfDay = fmt(rules?['half_day_limit'] as String?);
    final absentLimit = fmt(rules?['absent_limit'] as String?);
    final halfCheckout = fmt(rules?['half_day_checkout_limit'] as String?);
    final anytime = rules?['anytime_checkout_full_day'] == true;

    return _cardShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(children: [
                const Icon(Icons.schedule_rounded,
                    color: Color(0xFF7C3AED), size: 15),
                const SizedBox(width: 6),
                const Text('Attendance Schedule',
                    style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
              ]),
              Text('3/3',
                  style: TextStyle(
                      fontSize: 11,
                      color: Colors.white.withValues(alpha: 0.3))),
            ],
          ),
          const SizedBox(height: 14),
          Expanded(
            child: SingleChildScrollView(
              physics: const NeverScrollableScrollPhysics(),
              child: Column(
                children: [
                  _buildScheduleRow(Icons.check_circle_outline, 'Full Day',
                      'Arrival by $halfDay', const Color(0xFF10B981)),
                  _buildScheduleRow(Icons.timelapse_rounded, 'Half Day',
                      'Arrival between $halfDay – $absentLimit',
                      const Color(0xFFF59E0B)),
                  _buildScheduleRow(Icons.block_rounded, 'Absent',
                      'Arrival after $absentLimit', const Color(0xFFEF4444)),
                  _buildScheduleRow(
                      Icons.logout_rounded,
                      anytime ? 'Flexible Checkout' : 'Early Exit',
                      anytime
                          ? 'Departure at any time is permitted'
                          : 'Departure before $halfCheckout counts as half day',
                      const Color(0xFF7C3AED)),
                ],
              ),
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
                3,
                (i) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: i == 2 ? 18 : 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: i == 2
                            ? const Color(0xFF7C3AED)
                            : Colors.white.withValues(alpha: 0.2),
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

  Widget _buildScheduleRow(
      IconData icon, String label, String desc, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
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
                Text(label,
                    style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                        letterSpacing: 0.3)),
                const SizedBox(height: 2),
                Text(desc,
                    style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withValues(alpha: 0.5),
                        height: 1.2)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Faculty Pass Card — Flippable (Front: ID card, Back: QR)
// ═══════════════════════════════════════════════════════════════════════════

class _FacultyPassCard extends StatefulWidget {
  final UserModel? user;
  final AuthProvider auth;

  const _FacultyPassCard({required this.user, required this.auth});

  @override
  State<_FacultyPassCard> createState() => _FacultyPassCardState();
}

class _FacultyPassCardState extends State<_FacultyPassCard>
    with TickerProviderStateMixin {
  late AnimationController _flipController;
  late Animation<double> _flipAnimation;
  bool _isFlipped = false;

  // Smooth countdown — runs continuously at 60fps, no 1s jumps
  late AnimationController _countdownController;

  // Cached decoded image bytes — decoded once to prevent blink on setState
  Uint8List? _cachedImageBytes;

  @override
  void initState() {
    super.initState();
    _flipController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _flipAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _flipController, curve: Curves.easeInOutBack),
    );

    // Sync countdown to the current 10s epoch window for continuity
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    final elapsedInCycle = (nowMs % 10000) / 10000.0; // 0.0..1.0 elapsed
    _countdownController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
      value: elapsedInCycle, // start mid-cycle so it's already in sync
    )..repeat();

    _decodeProfileImage(widget.user?.profilePic);
  }

  @override
  void didUpdateWidget(_FacultyPassCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.user?.profilePic != widget.user?.profilePic) {
      _decodeProfileImage(widget.user?.profilePic);
    }
  }

  void _decodeProfileImage(String? profilePic) {
    if (profilePic == null || profilePic.isEmpty) {
      _cachedImageBytes = null;
      return;
    }
    try {
      final clean = profilePic.trim().replaceAll(RegExp(r'\s+'), '');
      final isBase64 = clean.startsWith('data:image') ||
          (clean.length > 100 && !clean.startsWith('http'));
      if (isBase64) {
        final b64 = clean.contains(',') ? clean.split(',').last : clean;
        _cachedImageBytes = base64Decode(b64);
      } else {
        _cachedImageBytes = null;
      }
    } catch (_) {
      _cachedImageBytes = null;
    }
  }


  void _toggleFlip() {
    if (_isFlipped) {
      _flipController.reverse();
    } else {
      _flipController.forward();
    }
    setState(() => _isFlipped = !_isFlipped);
  }

  @override
  void dispose() {
    _flipController.dispose();
    _countdownController.dispose();
    super.dispose();
  }

  String get _passId {
    final id = widget.user?.teacherId ?? '00000000';
    final clean = id.replaceAll('-', '').toUpperCase();
    return 'GF-${clean.substring(0, min(8, clean.length))}';
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _flipAnimation,
      builder: (context, _) {
        final value = _flipAnimation.value;
        final angle = value * pi;
        final isFront = value < 0.5;

        return Transform(
          transform: Matrix4.identity()
            ..setEntry(3, 2, 0.001)
            ..rotateY(angle),
          alignment: Alignment.center,
          child: isFront
              ? _buildFront()
              : Transform(
                  transform: Matrix4.identity()..rotateY(pi),
                  alignment: Alignment.center,
                  child: _buildBack(),
                ),
        );
      },
    );
  }

  // ── Front of the Card ──────────────────────────────────────────────────
  Widget _buildFront() {
    final user = widget.user;
    return AspectRatio(
      aspectRatio: 1.50,
      child: Container(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1F2444), Color(0xFF0C0D11)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF7C3AED).withValues(alpha: 0.18),
              blurRadius: 28,
              offset: const Offset(0, 10),
            ),
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.5),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          children: [
            // ── Main body (landscape row layout) ──────────────────
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Left: badge, photo
                    Expanded(
                      flex: 4,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // FACULTY PASS badge — top left
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                  color: const Color(0xFFA5B4FC),
                                  width: 1.2),
                            ),
                            child: const Text(
                              'FACULTY PASS',
                              style: TextStyle(
                                fontSize: 8,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFFA5B4FC),
                                letterSpacing: 1.5,
                              ),
                            ),
                          ),
                          const Spacer(flex: 1),
                          // Passport photo
                          Expanded(
                            flex: 12,
                            child: _buildPassportPhoto(user),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 14),
                    // Right: name, info rows
                    Expanded(
                      flex: 6,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Spacer(flex: 1),
                          // Name
                          Text(
                            user?.fullName.toUpperCase() ?? 'FACULTY MEMBER',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                              color: Colors.white,
                              letterSpacing: 0.3,
                              height: 1.1,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const Spacer(flex: 2),
                          // Info rows — compact for ATM size
                          _buildInfoRow(Icons.badge_outlined, 'REG NO',
                              user?.regNo ?? '-'),
                          const SizedBox(height: 3),
                          _buildInfoRow(Icons.apartment_outlined, 'DEPT',
                              _formatDept(user?.department)),
                          const SizedBox(height: 3),
                          _buildInfoRow(Icons.person_outline_rounded, 'ROLE',
                              _formatRole(user?.role)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // ── Dashed separator ──────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: CustomPaint(
                painter: _DashedLinePainter(),
                size: const Size(double.infinity, 1),
              ),
            ),
            // ── Bottom stub ───────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 8, 10, 8),
              child: Row(
                children: [
                // QR — tap to flip
                GestureDetector(
                  onTap: _toggleFlip,
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: const Color(0xFF0A0C14),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF23253A)),
                    ),
                    child: const Icon(Icons.qr_code_scanner_rounded,
                        color: Color(0xFF6D64BA), size: 18),
                  ),
                ),
                const SizedBox(width: 10),
                // Pass ID
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'PASS ID',
                      style: TextStyle(
                        fontSize: 7,
                        color: Colors.white.withValues(alpha: 0.35),
                        letterSpacing: 1.8,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _passId,
                      style: const TextStyle(
                        fontSize: 10,
                        fontFamily: 'monospace',
                        color: Color(0xFFB89DF8),
                        letterSpacing: 1.8,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                  ),
                  const Spacer(),
                  // Logout
                  IconButton(
                    onPressed: () async {
                      await widget.auth.logout();
                      if (context.mounted) {
                        Navigator.pushReplacementNamed(context, '/login');
                      }
                    },
                    icon: const Icon(Icons.logout_rounded,
                        color: Color(0xFFE05B5B), size: 22),
                    tooltip: 'Sign Out',
                    padding: const EdgeInsets.all(6),
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Back of the Card (ATM landscape — QR right, info left) ────────────
  Widget _buildBack() {
    final user = widget.user;
    // _countdownController goes 0→1 repeatedly; remaining = 1 - value
    // No local `progress` needed — we read it inside AnimatedBuilder

    return AspectRatio(
      aspectRatio: 1.50,
      child: Container(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1F2444), Color(0xFF0C0D11)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border:
              Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.45)),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF7C3AED).withValues(alpha: 0.2),
              blurRadius: 28,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Column(
          children: [
            // ── Main body ─────────────────────────────────────────
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 14, 14, 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Left: info + countdown + hint
                    Expanded(
                      flex: 5,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Title
                          Row(children: [
                            Container(
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                color: const Color(0xFF7C3AED)
                                    .withValues(alpha: 0.15),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.qr_code_2_rounded,
                                  color: Color(0xFF7C3AED), size: 16),
                            ),
                            const SizedBox(width: 7),
                            const Expanded(
                              child: Text(
                                'FACULTY QR PASS',
                                style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                    letterSpacing: 1),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ]),
                          const Spacer(),
                          // Countdown ring — smooth 60fps animation
                          AnimatedBuilder(
                            animation: _countdownController,
                            builder: (context, _) {
                              // remaining fraction: counts DOWN from 1→0 each cycle
                              final remaining = 1.0 - _countdownController.value;
                              final secsLeft = (remaining * 10).ceil().clamp(1, 10);
                              return Stack(
                                alignment: Alignment.center,
                                children: [
                                  SizedBox(
                                    width: 42,
                                    height: 42,
                                    child: CircularProgressIndicator(
                                      value: remaining,
                                      strokeWidth: 2.5,
                                      backgroundColor: const Color(0xFF7C3AED)
                                          .withValues(alpha: 0.15),
                                      valueColor:
                                          const AlwaysStoppedAnimation<Color>(
                                              Color(0xFF7C3AED)),
                                    ),
                                  ),
                                  Text(
                                    '${secsLeft}s',
                                    style: const TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.bold,
                                        color: Color(0xFF7C3AED)),
                                  ),
                                ],
                              );
                            },
                          ),
                          const SizedBox(height: 8),
                          // Faculty name
                          Text(
                            user?.fullName.toUpperCase() ?? '',
                            style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                                letterSpacing: 0.5),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _passId,
                            style: TextStyle(
                                fontSize: 8,
                                fontFamily: 'monospace',
                                color: Colors.white.withValues(alpha: 0.35),
                                letterSpacing: 1.5),
                          ),
                          const Spacer(),
                          // Flip back hint
                          GestureDetector(
                            onTap: _toggleFlip,
                            child: Row(children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: BoxDecoration(
                                  color: const Color(0xFF7C3AED)
                                      .withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(7),
                                  border: Border.all(
                                      color: const Color(0xFF7C3AED)
                                          .withValues(alpha: 0.3)),
                                ),
                                child: const Icon(Icons.qr_code_scanner_rounded,
                                    color: Color(0xFF7C3AED), size: 16),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Tap to flip back',
                                style: TextStyle(
                                    fontSize: 10,
                                    color: Colors.white.withValues(alpha: 0.3)),
                              ),
                            ]),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    // Right: QR code panel
                    Expanded(
                      flex: 6,
                      child: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0C0C14),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                              color: const Color(0xFF7C3AED)
                                  .withValues(alpha: 0.2)),
                        ),
                        child: Center(
                          child: LayoutBuilder(
                            builder: (context, constraints) {
                              final qrSize =
                                  constraints.maxWidth.clamp(80.0, 160.0);
                              return DynamicQrWidget(
                                facultyId:
                                    user?.teacherId ?? '00000000',
                                size: qrSize,
                                isDark: true,
                              );
                            },
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
      ),
    );
  }

  // ── Helpers ────────────────────────────────────────────────────────────
  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Container(
          width: 26,
          height: 26,
          decoration: BoxDecoration(
            color: const Color(0xFF0A0C14),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: const Color(0xFF23253A)),
          ),
          child: Icon(icon, color: const Color(0xFF6D64BA), size: 14),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 42,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 9,
              color: Colors.white.withValues(alpha: 0.4),
              letterSpacing: 1.0,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Text(
          ':',
          style: TextStyle(
              color: Colors.white.withValues(alpha: 0.25),
              fontSize: 10,
              fontWeight: FontWeight.bold),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Colors.white,
              letterSpacing: 0.3,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildPassportPhoto(UserModel? user) {
    final hasPhoto =
        user?.profilePic != null && user!.profilePic!.isNotEmpty;
    return Align(
      alignment: Alignment.bottomLeft,
      child: AspectRatio(
        aspectRatio: 0.75,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: Colors.white.withValues(alpha: 0.5), width: 1.5),
            boxShadow: [
              BoxShadow(
                  color: Colors.black.withValues(alpha: 0.5),
                  blurRadius: 8,
                  offset: const Offset(0, 3)),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: hasPhoto
                ? _buildImageWidget(user!.profilePic!, user)
                : _buildPlaceholderPhoto(user),
          ),
        ),
      ),
    );
  }

  Widget _buildImageWidget(String profilePic, UserModel user) {
    // Use cached bytes — never re-decode on timer setState
    if (_cachedImageBytes != null) {
      return Image.memory(
        _cachedImageBytes!,
        fit: BoxFit.cover,
        gaplessPlayback: true,
        errorBuilder: (_, __, ___) => _buildPlaceholderPhoto(user),
      );
    }
    // Fallback: network URL
    final clean = profilePic.trim().replaceAll(RegExp(r'\s+'), '');
    if (!clean.startsWith('http')) return _buildPlaceholderPhoto(user);
    return Image.network(
      profilePic,
      fit: BoxFit.cover,
      gaplessPlayback: true,
      errorBuilder: (_, __, ___) => _buildPlaceholderPhoto(user),
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
              fontSize: 20),
        ),
      ),
    );
  }

  String _formatDept(String? dept) {
    if (dept == null || dept.isEmpty) return '-';
    final map = {
      'Computer Science': 'CSE',
      'Electronics': 'EEE/ECE',
      'Mittal School of Business': 'MSB',
      'School of Law': 'LAW',
      'Hotel Management': 'HM',
      'Architecture': 'ARCH',
      'Agriculture': 'AGRI',
      'Pharmacy': 'PHARMA',
      'Allied Medical': 'PHYSIO',
      'Computer Applications': 'IT',
      'Media': 'MEDIA',
      'Physical Education': 'PE',
      'Humanities': 'HSS',
      'Sciences': 'SCI',
    };
    for (final e in map.entries) {
      if (dept.contains(e.key)) return e.value;
    }
    final match = RegExp(r'\((.*?)\)').firstMatch(dept);
    if (match != null) return match.group(1)!;
    return dept.length > 8 ? '${dept.substring(0, 8)}…' : dept;
  }

  String _formatRole(String? role) {
    if (role == null || role.isEmpty) return 'FACULTY';
    if (role.contains('(')) return role.split('(')[0].trim().toUpperCase();
    return role.toUpperCase();
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Painters
// ═══════════════════════════════════════════════════════════════════════════

class _DashedLinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.12)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    const dashW = 8.0;
    const dashSpace = 6.0;
    double x = 0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, 0), Offset(x + dashW, 0), paint);
      x += dashW + dashSpace;
    }
  }

  @override
  bool shouldRepaint(CustomPainter _) => false;
}
