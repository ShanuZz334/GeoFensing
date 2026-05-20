import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class CustomLoader extends StatefulWidget {
  final Color? color;
  const CustomLoader({super.key, this.color});

  @override
  State<CustomLoader> createState() => _CustomLoaderState();
}

class _CustomLoaderState extends State<CustomLoader> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _buildBar(double height, double delay) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        double t = (_controller.value - delay) % 1.0;
        if (t < 0) t += 1.0;

        double scaleY = 1.0;
        double opacity = 0.5;

        if (t <= 0.2) {
          double progress = t / 0.2;
          scaleY = 1.0 + (0.5 * progress);
          opacity = 0.5 + (0.5 * progress);
        } else if (t <= 0.4) {
          double progress = (t - 0.2) / 0.2;
          scaleY = 1.5 - (0.5 * progress);
          opacity = 1.0 - (0.5 * progress);
        }

        final color = widget.color ?? AppTheme.primary;

        return Transform.scale(
          scaleY: scaleY,
          child: Container(
            width: 3,
            height: height,
            decoration: BoxDecoration(
              color: color.withOpacity(opacity),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        _buildBar(20, 0.0),
        const SizedBox(width: 5),
        _buildBar(35, 0.25),
        const SizedBox(width: 5),
        _buildBar(20, 0.5),
      ],
    );
  }
}
