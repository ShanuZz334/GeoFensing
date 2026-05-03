/// Verification result model
class VerificationModel {
  final String status;
  final String reason;
  final String timestamp;
  final Map<String, dynamic>? details;
  final Map<String, dynamic>? contactSupport;

  const VerificationModel({
    required this.status,
    required this.reason,
    required this.timestamp,
    this.details,
    this.contactSupport,
  });

  bool get isSuccess => status == 'success';

  factory VerificationModel.fromJson(Map<String, dynamic> json) {
    return VerificationModel(
      status: json['status'] as String? ?? 'failure',
      reason: json['reason'] as String? ?? 'Unknown error',
      timestamp: json['timestamp'] as String? ?? '',
      details: json['details'] as Map<String, dynamic>?,
      contactSupport: json['contact_support'] as Map<String, dynamic>?,
    );
  }
}
