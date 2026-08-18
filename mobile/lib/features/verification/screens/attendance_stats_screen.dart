import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';

import '../providers/verification_provider.dart';
import '../models/attendance_log_model.dart';
import '../../../shared/widgets/custom_loader.dart';
import '../../../core/theme/app_theme.dart';

class AttendanceStatsScreen extends StatefulWidget {
  const AttendanceStatsScreen({super.key});

  @override
  State<AttendanceStatsScreen> createState() => _AttendanceStatsScreenState();
}

class _AttendanceStatsScreenState extends State<AttendanceStatsScreen> {
  bool _isSemester = false; // false = monthly, true = semester

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VerificationProvider>().fetchStats();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<VerificationProvider>();
    final stats = provider.stats;
    final isLoading = provider.isLoadingStats;

    final currentData = _isSemester 
        ? (stats != null ? stats['semester'] as Map<String, dynamic>? : null) 
        : (stats != null ? stats['monthly'] as Map<String, dynamic>? : null);
    final double attended = (currentData?['attended'] ?? 0).toDouble();
    final double absent = (currentData?['absent'] ?? 0).toDouble();
    final double approvedFullLeaves = (currentData?['approved_full_leaves'] ?? 0).toDouble();
    final double approvedHalfLeaves = (currentData?['approved_half_leaves'] ?? 0).toDouble();
    final double unapprovedAbsences = (currentData?['unapproved_absences'] ?? 0).toDouble();
    final double unapprovedHalfDays = (currentData?['unapproved_half_days'] ?? 0).toDouble();
    final double deductionPct = (currentData?['deduction_pct'] ?? 0).toDouble();
    final double effectiveAttended = attended + approvedFullLeaves + (approvedHalfLeaves * 0.5);
    final double totalUnapproved = unapprovedAbsences + (unapprovedHalfDays * 0.5);
    final double total = effectiveAttended + totalUnapproved;
    
    // Effective attended includes approved leaves
    final double totalApprovedLeaves = approvedFullLeaves + (approvedHalfLeaves * 0.5);
    
    final Map<String, dynamic>? eventsData = stats != null ? stats['events'] as Map<String, dynamic>? : null;
    
    final List<dynamic> rawLogs = currentData?['logs'] ?? [];
    
    // 1. Filter out intermediate failures (only show successes or final results)
    List<AttendanceLogModel> logs = rawLogs
        .map((e) => AttendanceLogModel.fromJson(e as Map<String, dynamic>))
        .where((log) {
          if (log.isSuccess) return true;
          if (log.attendanceMark == 'absent') return true;
          return false;
        }).toList();

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Attendance Insights',
          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
        body: isLoading && stats == null
            ? const Center(child: CustomLoader(color: AppTheme.primary))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 1. Stats Card (Header)
                  _buildStatsHeader(attended, approvedFullLeaves, approvedHalfLeaves, totalUnapproved, deductionPct, effectiveAttended, total),
                  
                  if (!_isSemester && eventsData != null) ...[
                    const SizedBox(height: 16),
                    _buildEventsStats(eventsData),
                  ],
                  
                  const SizedBox(height: 32),

                  // 2. Range Toggle
                  _buildToggle(),
                  const SizedBox(height: 24),

                  // 3. Attendance Log
                  const Text(
                    'Detailed Records',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 16),
                  logs.isEmpty
                      ? _buildEmptyState()
                      : ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: logs.length,
                          separatorBuilder: (_, __) => Divider(height: 24, color: Colors.white.withValues(alpha: 0.1)),
                          itemBuilder: (context, index) => _buildLogItem(logs[index]),
                        ),
                ],
              ),
            ),
    );
  }

    Widget _buildStatsHeader(double attended, double approvedFullLeaves, double approvedHalfLeaves, double totalUnapproved, double deductionPct, double effectiveAttended, double total) {
    return Stack(
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: const Color(0xFF121212),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          ),
          child: Column(
            children: [
              SizedBox(
                height: 200,
                child: Stack(
                  children: [
                    PieChart(
                      PieChartData(
                        sectionsSpace: 4,
                        centerSpaceRadius: 60,
                        startDegreeOffset: -90,
                        sections: [
                          PieChartSectionData(
                            color: const Color(0xFF7C3AED),
                            value: attended == 0 ? 0.01 : attended,
                            title: '',
                            radius: 20,
                          ),
                          PieChartSectionData(
                            color: const Color(0xFF00D1FF),
                            value: (approvedFullLeaves + approvedHalfLeaves * 0.5) == 0 ? 0.01 : (approvedFullLeaves + approvedHalfLeaves * 0.5),
                            title: '',
                            radius: 20,
                          ),
                          PieChartSectionData(
                            color: const Color(0xFFEF4444),
                            value: totalUnapproved == 0 ? 0.01 : totalUnapproved,
                            title: '',
                            radius: 20,
                          ),
                        ],
                      ),
                    ),
                    Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${effectiveAttended.toStringAsFixed(effectiveAttended == effectiveAttended.toInt() ? 0 : 1)} / ${total.toStringAsFixed(total == total.toInt() ? 0 : 1)}',
                            style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                          ),
                          const Text(
                            'ATTENDED',
                            style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildStatInfo('Attended', attended.toStringAsFixed(attended == attended.toInt() ? 0 : 1), const Color(0xFF7C3AED)),
                  _buildStatInfo('Full Leave', approvedFullLeaves.toStringAsFixed(approvedFullLeaves == approvedFullLeaves.toInt() ? 0 : 1), const Color(0xFF00D1FF)),
                  _buildStatInfo('Half Leave', approvedHalfLeaves.toStringAsFixed(approvedHalfLeaves == approvedHalfLeaves.toInt() ? 0 : 1), const Color(0xFFF59E0B)),
                  _buildStatInfo('Absent', totalUnapproved.toStringAsFixed(totalUnapproved == totalUnapproved.toInt() ? 0 : 1), const Color(0xFFEF4444)),
                ],
              ),
            ],
          ),
        ),
        if (deductionPct > 0)
          Positioned(
            top: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '-${deductionPct.toStringAsFixed(1)}% SALARY',
                style: const TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildEventsStats(Map<String, dynamic> events) {
    final int total = events['total_mandatory'] ?? 0;
    if (total == 0) return const SizedBox();

    final int attended = events['attended'] ?? 0;
    final int missed = events['missed'] ?? 0;
    final double deduction = (events['deduction_pct'] ?? 0).toDouble();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF10B981).withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.event_available_rounded, color: Color(0xFF10B981), size: 20),
              const SizedBox(width: 8),
              const Text(
                'Mandatory Events',
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              if (deduction > 0)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '-${deduction.toStringAsFixed(1)}% PENALTY',
                    style: const TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatInfo('Total', total.toString(), Colors.white70),
              _buildStatInfo('Attended', attended.toString(), const Color(0xFF10B981)),
              _buildStatInfo('Missed', missed.toString(), Colors.redAccent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatInfo(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildToggle() {
    return Container(
      height: 48,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF121212),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(child: _buildToggleButton('Monthly History', !_isSemester, () => setState(() => _isSemester = false))),
          Expanded(child: _buildToggleButton('Semester Summary', _isSemester, () => setState(() => _isSemester = true))),
        ],
      ),
    );
  }

  Widget _buildToggleButton(String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF7C3AED).withValues(alpha: 0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: isSelected ? Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.5)) : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? const Color(0xFF7C3AED) : Colors.white38,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            fontSize: 13,
          ),
        ),
      ),
    );
  }

  Widget _buildLogItem(AttendanceLogModel log) {
    final dateStr = DateFormat('dd MMM, yyyy').format(log.timestamp);
    final isSuccess = log.isSuccess;
    final isAbsent = log.attendanceMark == 'absent';
    final isHalfDay = log.attendanceMark == 'half_day';
    
    String statusLabel = log.statusDisplay;
    Color statusColor = const Color(0xFF10B981);
    
    if (isAbsent) {
      statusColor = const Color(0xFFEF4444);
    } else if (isHalfDay) {
      statusColor = const Color(0xFFF59E0B); // Orange/Amber
    } else if (!isSuccess) {
      statusColor = const Color(0xFFEF4444);
    }

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Left: Date & Time
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                dateStr,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
              ),
              const SizedBox(height: 2),
              Text(
                isAbsent ? 'No scan record' : DateFormat('hh:mm a').format(log.timestamp),
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ],
          ),
          
          // Right: Standardized Status (Text only)
          Text(
            statusLabel.toUpperCase(),
            style: TextStyle(
              color: statusColor,
              fontWeight: FontWeight.w900,
              fontSize: 11,
              letterSpacing: 0.8,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40),
      alignment: Alignment.center,
      child: Column(
        children: [
          Icon(Icons.history_toggle_off_rounded, color: Colors.white.withValues(alpha: 0.1), size: 64),
          const SizedBox(height: 16),
          const Text('No records found for this period', style: TextStyle(color: Colors.white38, fontSize: 14)),
        ],
      ),
    );
  }
}
