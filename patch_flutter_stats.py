import re

with open("mobile/lib/features/verification/screens/attendance_stats_screen.dart", "r", encoding="utf-8") as f:
    dart = f.read()

# 1. Update the variables parsing section
vars_pattern = r"final double attended = .*?final List<dynamic> rawLogs = currentData\?\['logs'\] \?\? \[\];"
new_vars = '''final double attended = (currentData?['attended'] ?? 0).toDouble();
    final double absent = (currentData?['absent'] ?? 0).toDouble();
    final double approvedFullLeaves = (currentData?['approved_full_leaves'] ?? 0).toDouble();
    final double approvedHalfLeaves = (currentData?['approved_half_leaves'] ?? 0).toDouble();
    final double unapprovedAbsences = (currentData?['unapproved_absences'] ?? 0).toDouble();
    final double unapprovedHalfDays = (currentData?['unapproved_half_days'] ?? 0).toDouble();
    final double deductionPct = (currentData?['deduction_pct'] ?? 0).toDouble();
    final double total = (currentData?['total'] ?? (attended + absent)).toDouble();
    
    // Effective attended includes approved leaves
    final double effectiveAttended = attended + approvedFullLeaves + (approvedHalfLeaves * 0.5);
    final double totalApprovedLeaves = approvedFullLeaves + (approvedHalfLeaves * 0.5);
    final double totalUnapproved = unapprovedAbsences + (unapprovedHalfDays * 0.5);
    
    final List<dynamic> rawLogs = currentData?['logs'] ?? [];'''
dart = re.sub(vars_pattern, new_vars, dart, flags=re.DOTALL)

# 2. Update _buildStatsHeader parameter list and invocation
header_call_pattern = r"_buildStatsHeader\(attended, displayAbsent, total, takenFullLeaves, approvedFullLeaves, allottedFullLeaves, halfLeavesQuotaUsed, allottedHalfLeaves, leavesQuotaUsed, leavesCoveredAbsent, effectiveAttended\)"
dart = dart.replace(header_call_pattern, "_buildStatsHeader(attended, totalApprovedLeaves, totalUnapproved, deductionPct, effectiveAttended, total)")

header_def_pattern = r"Widget _buildStatsHeader\(double attended, double absent, double total, double takenFullLeaves, double approvedFullLeaves, int allottedFullLeaves, double halfLeavesQuotaUsed, int allottedHalfLeaves, double leavesQuotaUsed, double leavesCoveredAbsent, double effectiveAttended\) \{.*?return Container\("
new_header_def = '''Widget _buildStatsHeader(double attended, double totalApprovedLeaves, double totalUnapproved, double deductionPct, double effectiveAttended, double total) {
    return Container('''
dart = re.sub(header_def_pattern, new_header_def, dart, flags=re.DOTALL)

# 3. Update Pie Chart sections
pie_sections_pattern = r"sections: \[.*?\]"
new_pie_sections = '''sections: [
                      PieChartSectionData(
                        color: const Color(0xFF7C3AED),
                        value: attended,
                        title: '',
                        radius: 20,
                      ),
                      PieChartSectionData(
                        color: const Color(0xFF00D1FF),
                        value: totalApprovedLeaves,
                        title: '',
                        radius: 20,
                      ),
                      PieChartSectionData(
                        color: const Color(0xFFEF4444),
                        value: totalUnapproved == 0 && attended == 0 && totalApprovedLeaves == 0 ? 1 : totalUnapproved,
                        title: '',
                        radius: 20,
                      ),
                    ]'''
dart = re.sub(pie_sections_pattern, new_pie_sections, dart, flags=re.DOTALL)

# 4. Update the bottom 4 stats rows
stats_row_pattern = r"Row\(\s*mainAxisAlignment: MainAxisAlignment.spaceAround,\s*children: \[\s*_buildStatInfo\('Attended', attended.toStringAsFixed\(attended == attended.toInt\(\) \? 0 : 1\), const Color\(0xFF7C3AED\)\),.*?\]\s*\),"
new_stats_row = '''Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatInfo('Attended', attended.toStringAsFixed(attended == attended.toInt() ? 0 : 1), const Color(0xFF7C3AED)),
              _buildStatInfo('Appr. Leaves', totalApprovedLeaves.toStringAsFixed(totalApprovedLeaves == totalApprovedLeaves.toInt() ? 0 : 1), const Color(0xFF00D1FF)),
              _buildStatInfo('Unapproved', totalUnapproved.toStringAsFixed(totalUnapproved == totalUnapproved.toInt() ? 0 : 1), const Color(0xFFEF4444)),
              _buildStatInfo('Deduction', '${deductionPct.toStringAsFixed(1)}%', deductionPct > 0 ? const Color(0xFFEF4444) : const Color(0xFF10B981)),
            ],
          ),'''
dart = re.sub(stats_row_pattern, new_stats_row, dart, flags=re.DOTALL)

with open("mobile/lib/features/verification/screens/attendance_stats_screen.dart", "w", encoding="utf-8") as f:
    f.write(dart)
