import re

with open("mobile/lib/features/profile/screens/profile_screen.dart", "r", encoding="utf-8") as f:
    dart = f.read()

# 1. Import ApplyLeaveScreen
import_statement = "import '../../auth/providers/auth_provider.dart';\nimport '../../verification/providers/verification_provider.dart';\nimport '../../verification/screens/apply_leave_screen.dart';"
dart = re.sub(r"import '../../auth/providers/auth_provider\.dart';\s*import '../../verification/providers/verification_provider\.dart';", import_statement, dart)

# 2. Add Leave Management Section
leave_section = '''                  // ── Leave Management ──────────────────────────────────────────
                  _SectionHeader(title: 'Leave & Attendance', icon: Icons.calendar_month_outlined),
                  const SizedBox(height: 12),
                  _InfoCard(
                    children: [
                      GestureDetector(
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => const ApplyLeaveScreen()));
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Row(
                            children: [
                              Icon(Icons.edit_calendar_outlined, color: AppTheme.primary, size: 22),
                              const SizedBox(width: 14),
                              const Text('Apply for Leave', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                              const Spacer(),
                              Icon(Icons.arrow_forward_ios, color: Colors.white.withOpacity(0.3), size: 14),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ── Change Password ──────────────────────────────────────────'''

change_password_pattern = r"// ── Change Password ──────────────────────────────────────────"
dart = dart.replace(change_password_pattern, leave_section)

with open("mobile/lib/features/profile/screens/profile_screen.dart", "w", encoding="utf-8") as f:
    f.write(dart)
