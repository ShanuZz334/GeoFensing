import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/custom_loader.dart';
import '../../auth/providers/auth_provider.dart';
import '../../verification/providers/verification_provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _isUploadingPic = false;
  bool _isChangingPassword = false;
  final _oldPasswordCtrl = TextEditingController();
  final _newPasswordCtrl = TextEditingController();
  final _confirmPasswordCtrl = TextEditingController();
  bool _obscureOld = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  String? _pwError;
  String? _pwSuccess;

  @override
  void dispose() {
    _oldPasswordCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmPasswordCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickAndUpdateProfilePic(ImageSource source) async {
    try {
      final picker = ImagePicker();
      final picked = await picker.pickImage(
        source: source,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 85,
      );
      if (picked == null) return;

      setState(() => _isUploadingPic = true);
      final bytes = await picked.readAsBytes();
      final b64 = base64Encode(bytes);

      if (!mounted) return;
      final auth = context.read<AuthProvider>();
      final success = await auth.updateProfile(profilePicBase64: b64);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(success
              ? 'Profile picture updated successfully!'
              : auth.errorMessage ?? 'Update failed'),
          backgroundColor: success ? AppTheme.success : AppTheme.error,
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: AppTheme.error,
        ));
      }
    } finally {
      if (mounted) setState(() => _isUploadingPic = false);
    }
  }

  void _showImagePickerSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.slateLight,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Update Profile Picture',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                '⚠️ This updates your display picture only. Your face registration for attendance verification remains unchanged.',
                style: TextStyle(
                  color: Colors.amber.shade300,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 20),
              _PickerOption(
                icon: Icons.camera_alt_outlined,
                label: 'Take Photo',
                onTap: () {
                  Navigator.pop(context);
                  _pickAndUpdateProfilePic(ImageSource.camera);
                },
              ),
              const SizedBox(height: 12),
              _PickerOption(
                icon: Icons.photo_library_outlined,
                label: 'Choose from Gallery',
                onTap: () {
                  Navigator.pop(context);
                  _pickAndUpdateProfilePic(ImageSource.gallery);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _changePassword() async {
    setState(() {
      _pwError = null;
      _pwSuccess = null;
    });

    final oldPw = _oldPasswordCtrl.text;
    final newPw = _newPasswordCtrl.text;
    final confirmPw = _confirmPasswordCtrl.text;

    if (oldPw.isEmpty || newPw.isEmpty || confirmPw.isEmpty) {
      setState(() => _pwError = 'All password fields are required.');
      return;
    }
    if (newPw.length < 8) {
      setState(() => _pwError = 'New password must be at least 8 characters.');
      return;
    }
    if (newPw != confirmPw) {
      setState(() => _pwError = 'New passwords do not match.');
      return;
    }

    setState(() => _isChangingPassword = true);

    final auth = context.read<AuthProvider>();
    final success = await auth.updateProfile(password: newPw);

    if (mounted) {
      setState(() => _isChangingPassword = false);
      if (success) {
        _oldPasswordCtrl.clear();
        _newPasswordCtrl.clear();
        _confirmPasswordCtrl.clear();
        setState(() => _pwSuccess = 'Password changed successfully!');
      } else {
        setState(() => _pwError = auth.errorMessage ?? 'Failed to update password.');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().currentUser;
    final supportContact = context.watch<VerificationProvider>().supportContact;

    return Scaffold(
      backgroundColor: AppTheme.slate,
      appBar: AppBar(
        title: const Text('My Profile', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        systemOverlayStyle: SystemUiOverlayStyle.light,
      ),
      body: user == null
          ? const Center(child: CustomLoader(color: AppTheme.primary))
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Profile Picture ─────────────────────────────────────────
                  Center(
                    child: Stack(
                      children: [
                        _isUploadingPic
                            ? Container(
                                width: 110,
                                height: 110,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: AppTheme.slateLight,
                                  border: Border.all(color: AppTheme.primary, width: 3),
                                ),
                                child: const Center(child: CustomLoader(color: AppTheme.primary)),
                              )
                            : GestureDetector(
                                onTap: _showImagePickerSheet,
                                child: Container(
                                  width: 110,
                                  height: 110,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(color: AppTheme.primary, width: 3),
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppTheme.primary.withValues(alpha: 0.3),
                                        blurRadius: 20,
                                        spreadRadius: 2,
                                      ),
                                    ],
                                    image: user.profilePic != null
                                        ? DecorationImage(
                                            image: MemoryImage(base64Decode(user.profilePic!)),
                                            fit: BoxFit.cover,
                                          )
                                        : null,
                                    color: AppTheme.slateLight,
                                  ),
                                  child: user.profilePic == null
                                      ? Center(
                                          child: Text(
                                            user.initials,
                                            style: const TextStyle(
                                              fontSize: 38,
                                              fontWeight: FontWeight.bold,
                                              color: Colors.white,
                                            ),
                                          ),
                                        )
                                      : null,
                                ),
                              ),
                        Positioned(
                          bottom: 0,
                          right: 0,
                          child: GestureDetector(
                            onTap: _showImagePickerSheet,
                            child: Container(
                              width: 32,
                              height: 32,
                              decoration: BoxDecoration(
                                color: AppTheme.primary,
                                shape: BoxShape.circle,
                                border: Border.all(color: AppTheme.slate, width: 2),
                              ),
                              child: const Icon(Icons.camera_alt, color: Colors.white, size: 16),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Center(
                    child: Text(
                      user.fullName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (user.role != null && user.role!.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [AppTheme.primary.withValues(alpha: 0.3), AppTheme.primaryDark.withValues(alpha: 0.3)],
                          ),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppTheme.primary.withValues(alpha: 0.5)),
                        ),
                        child: Text(
                          user.role!,
                          style: TextStyle(
                            color: AppTheme.primary,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 28),

                  // ── Details Card ─────────────────────────────────────────────
                  _SectionHeader(title: 'Personal Information', icon: Icons.person_outline),
                  const SizedBox(height: 12),
                  _InfoCard(
                    children: [
                      _InfoRow(icon: Icons.badge_outlined, label: 'Reg Number', value: user.regNo ?? 'N/A'),
                      _Divider(),
                      _InfoRow(icon: Icons.email_outlined, label: 'Email', value: user.email),
                      _Divider(),
                      _InfoRow(icon: Icons.phone_outlined, label: 'Phone', value: user.phoneNo?.isNotEmpty == true ? user.phoneNo! : 'Not set'),
                      _Divider(),
                      _InfoRow(icon: Icons.school_outlined, label: 'Department', value: user.department ?? 'N/A'),
                      _Divider(),
                      _InfoRow(icon: Icons.work_outline, label: 'Role', value: user.role?.isNotEmpty == true ? user.role! : 'N/A'),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ── Change Password ──────────────────────────────────────────
                  _SectionHeader(title: 'Change Password', icon: Icons.lock_outline),
                  const SizedBox(height: 12),
                  _InfoCard(
                    children: [
                      if (_pwError != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _StatusBanner(message: _pwError!, isError: true),
                        ),
                      if (_pwSuccess != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _StatusBanner(message: _pwSuccess!, isError: false),
                        ),
                      _PasswordField(
                        controller: _oldPasswordCtrl,
                        label: 'Current Password',
                        obscure: _obscureOld,
                        onToggle: () => setState(() => _obscureOld = !_obscureOld),
                      ),
                      const SizedBox(height: 12),
                      _PasswordField(
                        controller: _newPasswordCtrl,
                        label: 'New Password',
                        obscure: _obscureNew,
                        onToggle: () => setState(() => _obscureNew = !_obscureNew),
                      ),
                      const SizedBox(height: 12),
                      _PasswordField(
                        controller: _confirmPasswordCtrl,
                        label: 'Confirm New Password',
                        obscure: _obscureConfirm,
                        onToggle: () => setState(() => _obscureConfirm = !_obscureConfirm),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isChangingPassword ? null : _changePassword,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primary,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          child: _isChangingPassword
                              ? const SizedBox(height: 20, child: CustomLoader(color: Colors.white))
                              : const Text('Update Password', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ── Security Notice ───────────────────────────────────────────
                  _InfoCard(
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: Colors.amber.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.shield_outlined, color: Colors.amber, size: 22),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Face Recognition Security',
                                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Your registered face scan for attendance verification cannot be changed here. Contact your admin for face re-registration.',
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.55), fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ── Support ───────────────────────────────────────────────────
                  _SectionHeader(title: 'Support', icon: Icons.help_outline),
                  const SizedBox(height: 12),
                  _InfoCard(
                    children: [
                      _InfoRow(
                        icon: Icons.mail_outline,
                        label: 'Contact Email',
                        value: supportContact?['email']?.toString() ?? 'support@geoface.local',
                      ),
                      _Divider(),
                      _InfoRow(
                        icon: Icons.phone_outlined,
                        label: 'Contact Phone',
                        value: supportContact?['phone']?.toString() ?? '—',
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
    );
  }
}

// ── Helper widgets ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  const _SectionHeader({required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: AppTheme.primary, size: 18),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }
}

class _InfoCard extends StatelessWidget {
  final List<Widget> children;
  const _InfoCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.slateLight,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _InfoRow({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: AppTheme.primary, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 11)),
                const SizedBox(height: 2),
                Text(value, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Divider(color: Colors.white.withValues(alpha: 0.07), height: 1);
  }
}

class _PasswordField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final bool obscure;
  final VoidCallback onToggle;
  const _PasswordField({
    required this.controller,
    required this.label,
    required this.obscure,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 13),
        filled: true,
        fillColor: Colors.white.withValues(alpha: 0.05),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        suffixIcon: IconButton(
          icon: Icon(
            obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
            color: Colors.white.withValues(alpha: 0.4),
            size: 18,
          ),
          onPressed: onToggle,
        ),
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  final String message;
  final bool isError;
  const _StatusBanner({required this.message, required this.isError});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (isError ? AppTheme.error : AppTheme.success).withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: (isError ? AppTheme.error : AppTheme.success).withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(isError ? Icons.error_outline : Icons.check_circle_outline,
              color: isError ? AppTheme.error : AppTheme.success, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message,
                style: TextStyle(color: isError ? AppTheme.error : AppTheme.success, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _PickerOption extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _PickerOption({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.primary, size: 22),
            const SizedBox(width: 14),
            Text(label, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
            const Spacer(),
            Icon(Icons.arrow_forward_ios, color: Colors.white.withValues(alpha: 0.3), size: 14),
          ],
        ),
      ),
    );
  }
}
