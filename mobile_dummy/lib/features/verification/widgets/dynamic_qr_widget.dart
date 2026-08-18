import 'dart:async';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

class DynamicQrWidget extends StatefulWidget {
  final String facultyId;
  final double size;
  final bool isDark;

  const DynamicQrWidget({
    super.key,
    required this.facultyId,
    this.size = 100,
    this.isDark = false,
  });

  @override
  State<DynamicQrWidget> createState() => _DynamicQrWidgetState();
}

class _DynamicQrWidgetState extends State<DynamicQrWidget> {
  late Timer _timer;
  late String _qrData;

  @override
  void initState() {
    super.initState();
    _updateQrData();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        final newTimestamp = DateTime.now().millisecondsSinceEpoch ~/ 10000;
        final currentTimestamp = int.tryParse(_qrData.split('|').last) ?? 0;
        if (newTimestamp != currentTimestamp) {
          setState(() {
            _updateQrData();
          });
        }
      }
    });
  }

  void _updateQrData() {
    final timestamp = DateTime.now().millisecondsSinceEpoch ~/ 10000;
    _qrData = '${widget.facultyId}|$timestamp';
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isDark) {
      return QrImageView(
        data: _qrData,
        version: QrVersions.auto,
        size: widget.size,
        gapless: false,
        backgroundColor: Colors.transparent,
        eyeStyle: const QrEyeStyle(
          eyeShape: QrEyeShape.square,
          color: Colors.white,
        ),
        dataModuleStyle: const QrDataModuleStyle(
          dataModuleShape: QrDataModuleShape.square,
          color: Colors.white,
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: QrImageView(
        data: _qrData,
        version: QrVersions.auto,
        size: widget.size,
        gapless: false,
        eyeStyle: const QrEyeStyle(
          eyeShape: QrEyeShape.square,
          color: Colors.black,
        ),
        dataModuleStyle: const QrDataModuleStyle(
          dataModuleShape: QrDataModuleShape.square,
          color: Colors.black,
        ),
      ),
    );
  }
}
