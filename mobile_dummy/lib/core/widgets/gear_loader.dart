import 'dart:math';
import 'package:flutter/material.dart';

class GearLoader extends StatefulWidget {
  final double size;
  final Color? color;

  const GearLoader({
    super.key,
    this.size = 40.0, // Default height. Width will be 1.5x
    this.color,
  });

  @override
  State<GearLoader> createState() => _GearLoaderState();
}

class _GearLoaderState extends State<GearLoader> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3), // Speed of large gear
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Color gearColor = widget.color ?? const Color(0xFF9F00FF);
    final double width = widget.size * 1.5;
    final double height = widget.size;

    return SizedBox(
      width: width,
      height: height,
      child: Stack(
        children: [
          // Large Gear
          Positioned(
            left: 0,
            top: 0,
            width: height * 0.9,
            height: height * 0.9,
            child: AnimatedBuilder(
              animation: _controller,
              child: RepaintBoundary(
                child: CustomPaint(
                  painter: _GearPainter(color: gearColor, teethCount: 8, centerHoleRatio: 0.44),
                ),
              ),
              builder: (_, child) {
                return Transform.rotate(
                  angle: -_controller.value * 2 * pi, // Rotate counter-clockwise
                  child: child,
                );
              },
            ),
          ),
          // Small Gear
          Positioned(
            left: width * 0.58,
            top: height * 0.375,
            width: height * 0.6,
            height: height * 0.6,
            child: AnimatedBuilder(
              animation: _controller,
              child: RepaintBoundary(
                child: CustomPaint(
                  painter: _GearPainter(color: gearColor, teethCount: 8, centerHoleRatio: 0.41),
                ),
              ),
              builder: (_, child) {
                return Transform.rotate(
                  angle: (_controller.value * 2 * pi) * (3 / 4), // Rotate clockwise
                  child: child,
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _GearPainter extends CustomPainter {
  final Color color;
  final int teethCount;
  final double centerHoleRatio;

  _GearPainter({
    required this.color,
    required this.teethCount,
    required this.centerHoleRatio,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // We draw a solid circle, then we subtract small circles from its edge
    // to simulate the exact CSS cutout look.
    final Path gearPath = Path()..addOval(Rect.fromCircle(center: center, radius: radius));

    Path cutoutsPath = Path();
    
    // Center hole
    cutoutsPath.addOval(Rect.fromCircle(center: center, radius: radius * centerHoleRatio));

    // Edge cutouts (teeth gaps)
    // CSS cutout circles have radius of about 22% of the gear size
    final cutoutRadius = radius * 0.22;
    for (int i = 0; i < teethCount; i++) {
      final angle = (i * 2 * pi) / teethCount;
      // Position the cutouts exactly on the edge
      final cx = center.dx + radius * cos(angle);
      final cy = center.dy + radius * sin(angle);
      cutoutsPath.addOval(Rect.fromCircle(center: Offset(cx, cy), radius: cutoutRadius));
    }

    // Combine paths (Solid Circle - Cutouts)
    final Path finalPath = Path.combine(PathOperation.difference, gearPath, cutoutsPath);

    canvas.drawPath(finalPath, paint);
  }

  @override
  bool shouldRepaint(covariant _GearPainter oldDelegate) {
    return color != oldDelegate.color;
  }
}
