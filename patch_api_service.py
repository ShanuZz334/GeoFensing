import re

with open("mobile/lib/core/network/api_service.dart", "r", encoding="utf-8") as f:
    dart = f.read()

# Add getMyLeaves and applyLeave
methods_to_add = '''
  Future<ApiResponse> applyLeave({
    required String startDate,
    required String endDate,
    required bool isHalfDay,
    required String leaveType,
    String? reason,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse(success: false, message: 'No token');

      final response = await http.post(
        Uri.parse('${ApiConstants.baseUrl}/leaves'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({
          'start_date': startDate,
          'end_date': endDate,
          'is_half_day': isHalfDay,
          'leave_type': leaveType,
          if (reason != null && reason.isNotEmpty) 'reason': reason,
        }),
      );

      final data = json.decode(response.body);
      if (response.statusCode == 201 || response.statusCode == 200) {
        return ApiResponse(success: true, message: data['message'] ?? 'Leave applied successfully', data: data);
      } else {
        return ApiResponse(success: false, message: data['error'] ?? 'Failed to apply leave');
      }
    } catch (e) {
      return ApiResponse(success: false, message: 'Network error: $e');
    }
  }

  Future<ApiResponse> getMyLeaves() async {
    try {
      final token = await _getToken();
      if (token == null) return ApiResponse(success: false, message: 'No token');

      final response = await http.get(
        Uri.parse('${ApiConstants.baseUrl}/leaves'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return ApiResponse(success: true, data: data);
      } else {
        return ApiResponse(success: false, message: 'Failed to load leaves');
      }
    } catch (e) {
      return ApiResponse(success: false, message: 'Network error: $e');
    }
  }
'''

# Find the fetchMe function and insert these methods after it
insert_pos = dart.rfind('Future<ApiResponse> fetchMe')
if insert_pos != -1:
    end_of_fetchMe = dart.find('}', insert_pos)
    if end_of_fetchMe != -1:
        # Actually just insert it before the last brace of the class
        last_brace = dart.rfind('}')
        if last_brace != -1:
            dart = dart[:last_brace] + methods_to_add + dart[last_brace:]

with open("mobile/lib/core/network/api_service.dart", "w", encoding="utf-8") as f:
    f.write(dart)
