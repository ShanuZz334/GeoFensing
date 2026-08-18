import 'package:flutter/material.dart';

class UiverseSwitch extends StatelessWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;
  final double width;
  final double height;

  const UiverseSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.width = 56.0,
    this.height = 32.0,
  });

  @override
  Widget build(BuildContext context) {
    final double padding = height * 0.15;
    final double thumbSize = height - (padding * 2);
    final double activeLeft = width - thumbSize - padding;

    return GestureDetector(
      onTap: () {
        if (onChanged != null) {
          onChanged!(!value);
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 400),
        width: width,
        height: height,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(height / 3),
          color: value ? const Color(0xFF21CC4C) : const Color(0xFFB6B6B6),
          boxShadow: [
            if (value)
              BoxShadow(
                color: const Color(0xFF2196F3).withValues(alpha: 0.5),
                blurRadius: 1,
                spreadRadius: 1,
              ),
          ],
        ),
        child: Stack(
          children: [
            AnimatedPositioned(
              duration: const Duration(milliseconds: 400),
              curve: Curves.easeInOut,
              left: value ? activeLeft : padding,
              top: padding,
              child: AnimatedRotation(
                turns: value ? 0 : 0.75,
                duration: const Duration(milliseconds: 400),
                child: Container(
                  width: thumbSize,
                  height: thumbSize,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(thumbSize / 2.5),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
