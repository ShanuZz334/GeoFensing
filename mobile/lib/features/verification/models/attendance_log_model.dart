/// Model for verification history logs
class AttendanceLogModel {
  final String id;
  final String teacherId;
  final String? teacherName;
  final DateTime timestamp;
  final double? latitude;
  final double? longitude;
  final String status;
  final String reason;
  final int? framesCount;
  final String? failureStage;

  const AttendanceLogModel({
    required this.id,
    required this.teacherId,
    this.teacherName,
    required this.timestamp,
    this.latitude,
    this.longitude,
    required this.status,
    required this.reason,
    this.framesCount,
    this.failureStage,
  });

  bool get isSuccess => status == 'success';

  factory AttendanceLogModel.fromJson(Map<String, dynamic> json) {
    return AttendanceLogModel(
      id: json['id'] as String? ?? '',
      teacherId: json['teacher_id'] as String? ?? '',
      teacherName: json['teacher_name'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String? ?? DateTime.now().toIso8601String()).toLocal(),
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'failure',
      reason: json['reason'] as String? ?? 'Unknown error',
      framesCount: json['frames_count'] as int?,
      failureStage: json['failure_stage'] as String?,
    );
  }
}
