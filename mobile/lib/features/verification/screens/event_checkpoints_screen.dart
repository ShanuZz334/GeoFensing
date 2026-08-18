import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../auth/providers/auth_provider.dart';
import '../../../core/constants/api_constants.dart';
import 'checkpoint_finder_screen.dart';

class EventCheckpointsScreen extends StatefulWidget {
  const EventCheckpointsScreen({super.key});

  @override
  State<EventCheckpointsScreen> createState() => _EventCheckpointsScreenState();
}

class _EventCheckpointsScreenState extends State<EventCheckpointsScreen> {
  bool _isLoading = true;
  List<dynamic> _checkpoints = [];

  @override
  void initState() {
    super.initState();
    _fetchCheckpoints();
  }

  Future<void> _fetchCheckpoints() async {
    setState(() => _isLoading = true);
    try {
      final token = context.read<AuthProvider>().token;
      final response = await http.get(
        Uri.parse('${ApiConstants.baseUrl}/checkpoints/mine'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _checkpoints = data['checkpoints'] ?? [];
        });
      }
    } catch (e) {
      debugPrint("Error fetching checkpoints: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Event Checkpoints', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _fetchCheckpoints,
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF10B981)))
          : _checkpoints.isEmpty
              ? _buildEmptyState()
              : _buildList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.event_busy_rounded, size: 80, color: Colors.white.withOpacity(0.1)),
          const SizedBox(height: 16),
          const Text(
            'No Active Checkpoints',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(
            'There are no seminars or events\nyou are required to attend right now.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.5)),
          ),
        ],
      ),
    );
  }

  Widget _buildList() {
    return RefreshIndicator(
      onRefresh: _fetchCheckpoints,
      color: const Color(0xFF10B981),
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _checkpoints.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final cp = _checkpoints[index];
          final expiry = DateTime.parse(cp['expires_at']).toLocal();
          final timeStr = DateFormat('MMM d, h:mm a').format(expiry);
          final isCompulsory = cp['is_compulsory'] ?? false;
          
          return GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => CheckpointFinderScreen(
                    checkpointId: cp['id'],
                    name: cp['name'],
                    lat: cp['lat'],
                    lng: cp['lng'],
                    radius: cp['radius'].toDouble(),
                  ),
                ),
              );
            },
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A2E),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: isCompulsory ? Colors.red.withOpacity(0.3) : Colors.white.withOpacity(0.05)),
              ),
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: isCompulsory ? Colors.red.withOpacity(0.15) : const Color(0xFF10B981).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(isCompulsory ? Icons.warning_rounded : Icons.explore_rounded, color: isCompulsory ? Colors.redAccent : const Color(0xFF10B981)),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                cp['name'],
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: isCompulsory ? Colors.red.withOpacity(0.1) : Colors.grey.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                isCompulsory ? 'Compulsory' : 'Optional',
                                style: TextStyle(
                                  color: isCompulsory ? Colors.redAccent : Colors.white54,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Expires: $timeStr',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(Icons.chevron_right_rounded, color: Colors.white.withOpacity(0.3)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
