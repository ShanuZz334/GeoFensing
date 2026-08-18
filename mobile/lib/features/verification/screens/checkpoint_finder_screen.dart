import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_compass/flutter_compass.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';

import '../../auth/providers/auth_provider.dart';
import '../../../core/constants/api_constants.dart';
import 'verification_screen.dart';

class CheckpointFinderScreen extends StatefulWidget {
  final String checkpointId;
  final String name;
  final double lat;
  final double lng;
  final double radius;

  const CheckpointFinderScreen({
    super.key,
    required this.checkpointId,
    required this.name,
    required this.lat,
    required this.lng,
    required this.radius,
  });

  @override
  State<CheckpointFinderScreen> createState() => _CheckpointFinderScreenState();
}

class _CheckpointFinderScreenState extends State<CheckpointFinderScreen> {
  StreamSubscription<Position>? _positionStream;
  StreamSubscription<CompassEvent>? _compassStream;
  Position? _currentPosition;
  double _distance = -1;
  double _bearing = 0; // The absolute angle towards the destination
  double _deviceHeading = 0;
  double _turns = 0; // Accumulated turns for smooth animation

  bool _isAttending = false;
  bool _attended = false;

  void _updateTurns() {
    double currentFinalBearing = _bearing - _deviceHeading;
    double currentTurns = currentFinalBearing / 360;
    
    // Normalize against _turns to prevent 360-degree snapback
    double diff = currentTurns - _turns;
    while (diff > 0.5) diff -= 1.0;
    while (diff < -0.5) diff += 1.0;
    
    _turns += diff;
  }

  @override
  void initState() {
    super.initState();
    _initTracking();
  }

  Future<void> _initTracking() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return;

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }
    
    // Start compass stream
    _compassStream = FlutterCompass.events?.listen((CompassEvent event) {
      if (mounted) {
        setState(() {
          _deviceHeading = event.heading ?? 0;
          _updateTurns();
        });
      }
    });

    // Start streaming location
    _positionStream = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.bestForNavigation,
        distanceFilter: 0,
      ),
    ).listen((Position position) {
      if (mounted) {
        setState(() {
          _currentPosition = position;
          _distance = Geolocator.distanceBetween(
            position.latitude,
            position.longitude,
            widget.lat,
            widget.lng,
          );
          
          // Calculate bearing towards destination relative to North
          _bearing = Geolocator.bearingBetween(
            position.latitude,
            position.longitude,
            widget.lat,
            widget.lng,
          );
          
          _updateTurns();
        });
      }
    });
  }

  @override
  void dispose() {
    _compassStream?.cancel();
    _positionStream?.cancel();
    super.dispose();
  }

  void _markAttended() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VerificationScreen(
          checkpointId: widget.checkpointId,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Is the user within the checkpoint radius (plus 20m GPS buffer)?
    bool isCloseEnough = _distance != -1 && _distance <= (widget.radius + 20);

    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(widget.name, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 16)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: _attended
          ? _buildSuccess()
          : Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Spacer(),
                
                // AirTag-like Arrow
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  height: 300,
                  width: 300,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isCloseEnough ? const Color(0xFF10B981).withOpacity(0.1) : Colors.white.withOpacity(0.05),
                    border: Border.all(
                      color: isCloseEnough ? const Color(0xFF10B981) : Colors.white.withOpacity(0.1),
                      width: 2,
                    ),
                  ),
                  child: Center(
                    child: _distance == -1
                        ? const CircularProgressIndicator(color: Colors.white54)
                        : AnimatedRotation(
                            turns: _turns,
                            duration: const Duration(milliseconds: 200),
                            child: Icon(
                              Icons.navigation_rounded,
                              size: 150,
                              color: isCloseEnough ? const Color(0xFF10B981) : Colors.white,
                            ),
                          ),
                  ),
                ),
                
                const SizedBox(height: 48),
                
                // Distance Text
                Text(
                  _distance == -1 ? 'Finding signal...' : '${_distance.toStringAsFixed(1)} m',
                  style: TextStyle(
                    color: isCloseEnough ? const Color(0xFF10B981) : Colors.white,
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    letterSpacing: -1,
                  ),
                ),
                Text(
                  isCloseEnough ? 'You have arrived!' : 'Walk towards the checkpoint',
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16),
                ),
                
                const Spacer(),
                
                // Mark Attended Button
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
                  child: ElevatedButton(
                    onPressed: (isCloseEnough && !_isAttending) ? _markAttended : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      disabledBackgroundColor: const Color(0xFF10B981).withOpacity(0.3),
                      minimumSize: const Size.fromHeight(56),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: _isAttending
                        ? const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Text(
                            'Mark Attended',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildSuccess() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF10B981).withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check_circle_rounded, color: Color(0xFF10B981), size: 100),
          ),
          const SizedBox(height: 24),
          const Text(
            'Attendance Marked!',
            style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Text(
            'You can now safely close this screen.',
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16),
          ),
          const SizedBox(height: 48),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Back to Home', style: TextStyle(color: Color(0xFF10B981), fontSize: 16)),
          )
        ],
      ),
    );
  }
}
