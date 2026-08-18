/// Teacher model matching backend /login response
class UserModel {
  final String teacherId;
  final String fullName;
  final String email;
  final String? regNo;
  final String? department;
  final String? role;
  final String? phoneNo;
  final bool isActive;
  final bool hasFaceEncoding;
  final bool setupComplete;
  final String createdAt;
  final String? profilePic;
  final bool faceReregisterAllowed;
  final String? faceReregisterUntil;

  const UserModel({
    required this.teacherId,
    required this.fullName,
    required this.email,
    this.regNo,
    this.department,
    this.role,
    this.phoneNo,
    required this.isActive,
    required this.hasFaceEncoding,
    required this.setupComplete,
    required this.createdAt,
    this.profilePic,
    this.faceReregisterAllowed = false,
    this.faceReregisterUntil,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      teacherId: json['teacher_id'] as String,
      fullName: json['full_name'] as String,
      email: json['email'] as String,
      regNo: json['reg_no'] as String?,
      department: json['department'] as String?,
      role: json['role'] as String?,
      phoneNo: json['phone_no'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      hasFaceEncoding: json['has_face_encoding'] as bool? ?? false,
      setupComplete: json['setup_complete'] as bool? ?? false,
      createdAt: json['created_at'] as String? ?? '',
      profilePic: json['profile_pic'] as String?,
      faceReregisterAllowed: json['face_reregister_allowed'] as bool? ?? false,
      faceReregisterUntil: json['face_reregister_until'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'teacher_id': teacherId,
        'full_name': fullName,
        'email': email,
        'reg_no': regNo,
        'department': department,
        'role': role,
        'phone_no': phoneNo,
        'is_active': isActive,
        'has_face_encoding': hasFaceEncoding,
        'setup_complete': setupComplete,
        'created_at': createdAt,
        'profile_pic': profilePic,
        'face_reregister_allowed': faceReregisterAllowed,
        'face_reregister_until': faceReregisterUntil,
      };

  String get initials {
    final parts = fullName.trim().split(RegExp(r'\s+'));
    if (parts.length >= 2 && parts[0].isNotEmpty && parts[1].isNotEmpty) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : '?';
  }
}
