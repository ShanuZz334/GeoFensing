import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/theme/app_theme.dart';
import '../../features/verification/providers/verification_provider.dart';

/// Animated status indicator shown during and after verification.
/// Displays a pulsing ring + icon based on the current [VerificationStatus].
class StatusIndicator extends StatelessWidget {
  const StatusIndicator({
    super.key,
    required this.status,
    this.size = 96.0,
  });

  final VerificationStatus status;
  final double size;

  @override
  Widget build(BuildContext context) {
    final config = _configFromStatus(status);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer pulsing ring
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: config.color.withValues(alpha: 0.12),
              border: Border.all(color: config.color.withValues(alpha: 0.3), width: 2),
            ),
          )
              .animate(onPlay: (c) => c.repeat())
              .scale(
                begin: const Offset(0.9, 0.9),
                end: const Offset(1.05, 1.05),
                duration: 900.ms,
                curve: Curves.easeInOut,
              )
              .then()
              .scale(
                begin: const Offset(1.05, 1.05),
                end: const Offset(0.9, 0.9),
                duration: 900.ms,
                curve: Curves.easeInOut,
              ),

          // Inner circle + icon
          Container(
            width: size * 0.65,
            height: size * 0.65,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: config.color.withValues(alpha: 0.18),
            ),
            child: Icon(config.icon, color: config.color, size: size * 0.35),
          ),
        ],
      ),
    );
  }

  _StatusConfig _configFromStatus(VerificationStatus status) {
    switch (status) {
      case VerificationStatus.recording:
        return _StatusConfig(
          color: Colors.red,
          icon: Icons.fiber_manual_record,
        );
      case VerificationStatus.processing:
      case VerificationStatus.uploading:
        return _StatusConfig(
          color: Colors.orange,
          icon: Icons.autorenew,
        );
      case VerificationStatus.success:
        return _StatusConfig(
          color: AppTheme.success,
          icon: Icons.check_circle_outline,
        );
      case VerificationStatus.failure:
        return _StatusConfig(
          color: AppTheme.error,
          icon: Icons.cancel_outlined,
        );
      case VerificationStatus.error:
        return _StatusConfig(
          color: AppTheme.warning,
          icon: Icons.warning_amber_outlined,
        );
      default:
        return _StatusConfig(
          color: Colors.grey,
          icon: Icons.face_outlined,
        );
    }
  }
}

class _StatusConfig {
  final Color color;
  final IconData icon;
  const _StatusConfig({required this.color, required this.icon});
}
