import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/network/api_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/custom_loader.dart';

class ApplyLeaveScreen extends StatefulWidget {
  const ApplyLeaveScreen({super.key});

  @override
  State<ApplyLeaveScreen> createState() => _ApplyLeaveScreenState();
}

class _ApplyLeaveScreenState extends State<ApplyLeaveScreen> {
  final _apiService = ApiService.instance;
  bool _isLoading = false;
  bool _isLoadingHistory = false;
  
  DateTime? _startDate;
  DateTime? _endDate;
  bool _isHalfDay = false;
  String _leaveType = 'normal'; // 'normal' or 'emergency'
  final _reasonController = TextEditingController();
  
  List<dynamic> _leaveHistory = [];

  @override
  void initState() {
    super.initState();
    _loadLeaveHistory();
  }
  
  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  Future<void> _loadLeaveHistory() async {
    setState(() => _isLoadingHistory = true);
    final res = await _apiService.getMyLeaves();
    if (mounted) {
      setState(() {
        _isLoadingHistory = false;
        if (res.success) {
          _leaveHistory = res.data?['leaves'] ?? [];
        }
      });
    }
  }

  Future<void> _deleteLeave(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text('Delete Leave', style: TextStyle(color: Colors.white)),
        content: const Text('Are you sure you want to delete this leave request?', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
    if (confirm != true) return;

    setState(() => _isLoadingHistory = true);
    final res = await _apiService.deleteLeaveRequest(id);
    if (mounted) {
      if (res.success) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res.errorMessage ?? 'Deleted successfully')));
        _loadLeaveHistory();
      } else {
        setState(() => _isLoadingHistory = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res.errorMessage ?? 'Failed to delete')));
      }
    }
  }

  Future<void> _selectDate(BuildContext context, bool isStart) async {
    final initialDate = isStart 
        ? (_startDate ?? DateTime.now()) 
        : (_endDate ?? _startDate ?? DateTime.now());
        
    final firstDate = DateTime.now();
    final lastDate = DateTime.now().add(const Duration(days: 365));

    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: firstDate,
      lastDate: lastDate,
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppTheme.primary,
              onPrimary: Colors.white,
              surface: Color(0xFF1E1E1E),
              onSurface: Colors.white,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
          if (_endDate != null && _endDate!.isBefore(_startDate!)) {
            _endDate = _startDate;
          }
        } else {
          _endDate = picked;
          if (_startDate != null && _startDate!.isAfter(_endDate!)) {
            _startDate = _endDate;
          }
        }
      });
    }
  }

  Future<void> _submitLeave() async {
    if (_startDate == null || _endDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select both start and end dates', style: TextStyle(color: Colors.white)), backgroundColor: Colors.red),
      );
      return;
    }
    
    if (_leaveType == 'emergency' && _reasonController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reason is required for emergency leaves', style: TextStyle(color: Colors.white)), backgroundColor: Colors.red),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    final DateFormat formatter = DateFormat('yyyy-MM-dd');
    final String startStr = formatter.format(_startDate!);
    final String endStr = formatter.format(_endDate!);

    final res = await _apiService.applyLeave(
      startDate: startStr,
      endDate: endStr,
      isHalfDay: _isHalfDay,
      leaveType: _leaveType,
      reason: _reasonController.text.trim(),
    );

    if (mounted) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.errorMessage ?? (res.success ? 'Success' : 'Error'), style: const TextStyle(color: Colors.white)),
          backgroundColor: res.success ? Colors.green : Colors.red,
        ),
      );
      if (res.success) {
        setState(() {
          _startDate = null;
          _endDate = null;
          _isHalfDay = false;
          _leaveType = 'normal';
          _reasonController.clear();
        });
        _loadLeaveHistory();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Leave Management',
          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Leave Form Card
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF121212),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Apply for Leave', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 24),
                  
                  // Leave Type Toggle
                  Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setState(() => _leaveType = 'normal'),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: _leaveType == 'normal' ? AppTheme.primary.withOpacity(0.2) : Colors.transparent,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: _leaveType == 'normal' ? AppTheme.primary : Colors.white24),
                            ),
                            alignment: Alignment.center,
                            child: Text('Normal', style: TextStyle(color: _leaveType == 'normal' ? AppTheme.primary : Colors.white54, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setState(() => _leaveType = 'emergency'),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: _leaveType == 'emergency' ? Colors.red.withOpacity(0.2) : Colors.transparent,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: _leaveType == 'emergency' ? Colors.red : Colors.white24),
                            ),
                            alignment: Alignment.center,
                            child: Text('Emergency', style: TextStyle(color: _leaveType == 'emergency' ? Colors.red : Colors.white54, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (_leaveType == 'normal')
                    const Padding(
                      padding: EdgeInsets.only(top: 8.0),
                      child: Text('Requires 16hrs advance notice', style: TextStyle(color: Colors.white54, fontSize: 12)),
                    ),

                  const SizedBox(height: 20),

                  // Dates
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Start Date', style: TextStyle(color: Colors.white54, fontSize: 13)),
                            const SizedBox(height: 8),
                            GestureDetector(
                              onTap: () => _selectDate(context, true),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.05),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _startDate != null ? DateFormat('dd MMM yyyy').format(_startDate!) : 'Select Date',
                                  style: TextStyle(color: _startDate != null ? Colors.white : Colors.white38),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('End Date', style: TextStyle(color: Colors.white54, fontSize: 13)),
                            const SizedBox(height: 8),
                            GestureDetector(
                              onTap: () => _selectDate(context, false),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.05),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _endDate != null ? DateFormat('dd MMM yyyy').format(_endDate!) : 'Select Date',
                                  style: TextStyle(color: _endDate != null ? Colors.white : Colors.white38),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  
                  // Half Day switch
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Half Day Leave', style: TextStyle(color: Colors.white, fontSize: 15)),
                      Switch(
                        value: _isHalfDay,
                        onChanged: (val) => setState(() => _isHalfDay = val),
                        activeColor: AppTheme.primary,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Reason
                  Text(_leaveType == 'emergency' ? 'Reason (Required)' : 'Reason (Optional)', style: const TextStyle(color: Colors.white54, fontSize: 13)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _reasonController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.05),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      hintText: 'Enter reason...',
                      hintStyle: const TextStyle(color: Colors.white38),
                    ),
                    maxLines: 2,
                  ),
                  const SizedBox(height: 24),

                  // Submit
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _submitLeave,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: _isLoading 
                          ? Transform.scale(scale: 0.6, child: CustomLoader(color: Colors.white))
                          : const Text('Submit Application', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Recent Applications', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                IconButton(
                  icon: const Icon(Icons.refresh, color: AppTheme.primary, size: 20),
                  onPressed: () => _loadLeaveHistory(),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  splashRadius: 20,
                  tooltip: 'Refresh',
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            if (_isLoadingHistory)
              const Center(child: Padding(padding: EdgeInsets.all(20), child: CustomLoader(color: AppTheme.primary)))
            else if (_leaveHistory.isEmpty)
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 30),
                  child: Text('No recent leave requests', style: TextStyle(color: Colors.white.withOpacity(0.5))),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _leaveHistory.length,
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final leave = _leaveHistory[index];
                  final status = leave['status'];
                  
                  Color statusColor = Colors.orange;
                  if (status == 'approved') statusColor = Colors.green;
                  if (status == 'rejected') statusColor = Colors.red;

                  final start = DateFormat('dd MMM').format(DateTime.parse(leave['start_date']));
                  final end = DateFormat('dd MMM').format(DateTime.parse(leave['end_date']));
                  final dateStr = start == end ? start : '$start - $end';

                  final bool showDelete = !DateTime.parse(leave['start_date']).isBefore(DateTime(DateTime.now().year, DateTime.now().month, DateTime.now().day));
                  
                  return Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.05)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Top Row: Date and Status
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(dateStr, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: statusColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                status.toUpperCase(),
                                style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        
                        // Middle Row: Applied Date
                        Text('Applied: ${DateFormat('dd MMM hh:mm a').format(DateTime.parse(leave['applied_at']).toLocal())}', 
                          style: const TextStyle(color: Colors.white54, fontSize: 12)),
                        
                        // Bottom Row: Pills & Actions
                        if (leave['is_half_day'] || leave['leave_type'] == 'emergency' || showDelete) ...[
                          const SizedBox(height: 12),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Row(
                                children: [
                                  if (leave['is_half_day'])
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(color: Colors.orange.withOpacity(0.2), borderRadius: BorderRadius.circular(6)),
                                      child: const Text('Half Day', style: TextStyle(color: Colors.orange, fontSize: 11, fontWeight: FontWeight.bold)),
                                    ),
                                  if (leave['is_half_day'] && leave['leave_type'] == 'emergency')
                                    const SizedBox(width: 8),
                                  if (leave['leave_type'] == 'emergency')
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(color: Colors.red.withOpacity(0.2), borderRadius: BorderRadius.circular(6)),
                                      child: const Text('Emergency', style: TextStyle(color: Colors.redAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                                    ),
                                ],
                              ),
                              if (showDelete)
                                InkWell(
                                  onTap: () => _deleteLeave(leave['id'].toString()),
                                  borderRadius: BorderRadius.circular(6),
                                  child: Container(
                                    padding: const EdgeInsets.all(6),
                                    decoration: BoxDecoration(
                                      color: Colors.red.withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(6)
                                    ),
                                    child: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 18),
                                  ),
                                ),
                            ],
                          ),
                        ]
                      ],
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
