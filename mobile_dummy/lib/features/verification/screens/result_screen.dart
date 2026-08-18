import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../providers/verification_provider.dart';
import '../../../core/theme/app_theme.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.read<VerificationProvider>();
    final result   = provider.result;
    final isSuccess = result?.isSuccess ?? false;
    final isError   = provider.status == VerificationStatus.error;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
          child: Column(
            children: [
              // ── Header ────────────────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Verification Result',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  IconButton(
                    onPressed: () {
                      provider.reset();
                      Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
                    },
                    icon: const Icon(Icons.close_rounded, color: Color(0xFF64748B)),
                  ),
                ],
              ),

              const Spacer(),

              // ── Result Illustration/Icon ──────────────────────────────
              Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 140,
                    height: 140,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: (isSuccess ? AppTheme.primary : AppTheme.error).withValues(alpha: 0.05),
                    ),
                  ).animate().scale(duration: 600.ms, curve: Curves.easeOutBack),
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: (isSuccess ? AppTheme.primary : AppTheme.error).withValues(alpha: 0.12),
                    ),
                    child: Icon(
                      isSuccess ? Icons.check_rounded : Icons.priority_high_rounded,
                      size: 48,
                      color: isSuccess ? AppTheme.primary : AppTheme.error,
                    ),
                  ).animate().scale(delay: 100.ms, duration: 600.ms, curve: Curves.easeOutBack),
                ],
              ),

              const SizedBox(height: 40),

              // ── Reason Box ────────────────────────────────────────────
              Container(
                margin: const EdgeInsets.only(top: 0),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                decoration: BoxDecoration(
                  color: (isSuccess ? AppTheme.primary : AppTheme.error).withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: (isSuccess ? AppTheme.primary : AppTheme.error).withValues(alpha: 0.2),
                  ),
                ),
                child: Text(
                  result?.reason ?? provider.statusMessage,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: isSuccess ? AppTheme.primary : const Color(0xFF991B1B),
                    height: 1.4,
                  ),
                  textAlign: TextAlign.center,
                ),
              ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.1),

              const SizedBox(height: 48),

              // ── Details Section ───────────────────────────────────────
              if (result?.details != null) ...[
                _DetailsCard(details: result!.details!)
                    .animate()
                    .fadeIn(delay: 400.ms)
                    .slideY(begin: 0.1),
              ],

              const Spacer(),

              // ── Footer Buttons ────────────────────────────────────────
              Column(
                children: [
                  if (!isSuccess) ...[
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        minimumSize: const Size.fromHeight(56),
                      ),
                      onPressed: () {
                        provider.reset();
                        Navigator.pushReplacementNamed(context, '/verify');
                      },
                      child: const Text('Retry Verification'),
                    ),
                    const SizedBox(height: 12),
                  ],
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size.fromHeight(56),
                      side: const BorderSide(color: Color(0xFFE2E8F0)),
                      foregroundColor: const Color(0xFF475569),
                    ),
                    onPressed: () {
                      provider.reset();
                      Navigator.pushNamedAndRemoveUntil(context, '/home', (_) => false);
                    },
                    child: const Text('Return to Home'),
                  ),
                ],
              ).animate().fadeIn(delay: 500.ms),
            ],
          ),
        ),
      ),
    );
  }

}

// ── Details card ──────────────────────────────────────────────────────────────

class _DetailsCard extends StatelessWidget {
  const _DetailsCard({required this.details});
  final Map<String, dynamic> details;

  @override
  Widget build(BuildContext context) {
    final rows = [
      ('Face Match',   _pct(details['face_distance'])),
      ('Face Frames',  '${details['face_frames']}/${details['total_frames']}'),
      ('GPS Distance', '${details['gps_distance_m']?.toStringAsFixed(0) ?? '—'} m'),
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF7F7F7),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: rows.map((r) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(r.$1,
                    style: const TextStyle(
                        color: Color(0xFF9E9E9E), fontSize: 13)),
                Text(r.$2,
                    style: const TextStyle(
                        color: Color(0xFF2D2D2D),
                        fontSize: 13,
                        fontWeight: FontWeight.w600)),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  String _pct(dynamic dist) {
    if (dist == null) return '—';
    final d = (dist as num).toDouble();
    final match = ((1 - d) * 100).clamp(0, 100);
    return '${match.toStringAsFixed(0)}%';
  }
}
