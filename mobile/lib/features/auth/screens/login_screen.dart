import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../providers/auth_provider.dart';
import 'teacher_register_details_screen.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/custom_loader.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  late AnimationController _flipController;
  late Animation<double> _flipAnimation;

  // Front Form (Login)
  final _loginFormKey = GlobalKey<FormState>();
  final _loginRegNoController = TextEditingController();
  final _loginPasswordController = TextEditingController();

  // Back Form (Sign Up / Setup)
  final _signupFormKey = GlobalKey<FormState>();
  final _signupRegNoController = TextEditingController();
  final _signupPasswordController = TextEditingController();

  bool _isLoginObscured = true;
  bool _isSignupObscured = true;

  String? _errorText;
  bool _isLoading = false;
  bool _showForgotPassword = false;

  @override
  void initState() {
    super.initState();
    _flipController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _flipAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _flipController, curve: Curves.easeInOutBack),
    );
  }

  @override
  void dispose() {
    _flipController.dispose();
    _loginRegNoController.dispose();
    _loginPasswordController.dispose();
    _signupRegNoController.dispose();
    _signupPasswordController.dispose();
    super.dispose();
  }

  void _toggleFlip() {
    setState(() {
      _errorText = null;
      _showForgotPassword = false;
    });
    if (_flipController.isCompleted) {
      _flipController.reverse();
    } else {
      _flipController.forward();
    }
  }

  Future<void> _submitLogin() async {
    if (!_loginFormKey.currentState!.validate()) return;
    
    setState(() {
      _isLoading = true;
      _errorText = null;
      _showForgotPassword = false;
    });

    final auth = context.read<AuthProvider>();
    final success = await auth.login(
      _loginRegNoController.text.trim(),
      _loginPasswordController.text,
    );

    if (success && mounted) {
      if (auth.currentUser?.department == 'Pending' || auth.currentUser?.email.endsWith('@geoface.local') == true) {
        // They used the normal login card, but they are pending!
        await auth.logout();
        setState(() {
          _isLoading = false;
          _errorText = 'Account registration is pending. Please use the "Register Here" button below to activate your account.';
        });
      } else {
        Navigator.pushReplacementNamed(context, '/home');
      }
    } else if (mounted) {
      setState(() {
        _isLoading = false;
        _errorText = auth.errorMessage ?? 'Login failed. Please check your credentials.';
        _showForgotPassword = true;
      });
    }
  }

  Future<void> _submitSignup() async {
    if (!_signupFormKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorText = null;
    });

    try {
      final auth = context.read<AuthProvider>();
      await auth.login(
        _signupRegNoController.text.trim(),
        _signupPasswordController.text,
      );

      if (auth.status == AuthStatus.authenticated && auth.currentUser != null) {
        final email = auth.currentUser!.email;
        if (email.endsWith('@geoface.local') || auth.currentUser!.department == 'Pending') {
          if (!mounted) return;
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const TeacherRegisterDetailsScreen()),
          );
        } else {
          await auth.logout();
          setState(() {
            _errorText = 'Account is already fully registered. Please login normally.';
          });
        }
      } else {
        setState(() => _errorText = auth.errorMessage ?? 'Invalid temporary credentials');
      }
    } catch (e) {
      setState(() => _errorText = e.toString());
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showPasswordResetTerminal() {
    final totpController = TextEditingController();
    final newPasswordController = TextEditingController();
    final confirmController = TextEditingController();
    bool isResetLoading = false;
    String? resetError;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: const BoxDecoration(
                  color: Color(0xFF1E1E1E),
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Reset Password',
                      style: TextStyle(
                        fontSize: 25,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Provide the 6-digit Admin TOTP and your new password.',
                      style: TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                    const SizedBox(height: 30),
                    if (resetError != null) ...[
                      Text(resetError!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
                      const SizedBox(height: 12),
                    ],
                    _buildNeuInput(
                      child: TextField(
                        controller: totpController,
                        style: const TextStyle(color: Colors.white),
                        keyboardType: TextInputType.number,
                        decoration: _neuInputDecoration('Admin TOTP (6 digits)', null),
                      ),
                    ),
                    const SizedBox(height: 20),
                    _buildNeuInput(
                      child: TextField(
                        controller: newPasswordController,
                        obscureText: true,
                        style: const TextStyle(color: Colors.white),
                        decoration: _neuInputDecoration('New Password', null),
                      ),
                    ),
                    const SizedBox(height: 20),
                    _buildNeuInput(
                      child: TextField(
                        controller: confirmController,
                        obscureText: true,
                        style: const TextStyle(color: Colors.white),
                        decoration: _neuInputDecoration('Confirm Password', null),
                      ),
                    ),
                    const SizedBox(height: 30),
                    _buildNeuButton(
                      text: 'Execute Reset',
                      isLoadingOverride: isResetLoading,
                      onPressed: () async {
                        final totp = totpController.text.trim();
                        final pass = newPasswordController.text;
                        final conf = confirmController.text;
                        
                        if (totp.isEmpty || pass.isEmpty || conf.isEmpty) {
                          setModalState(() => resetError = 'All fields are required.');
                          return;
                        }
                        if (pass != conf) {
                          setModalState(() => resetError = 'Passwords do not match.');
                          return;
                        }
                        if (pass.length < 8) {
                          setModalState(() => resetError = 'Password must be at least 8 characters.');
                          return;
                        }

                        setModalState(() {
                          isResetLoading = true;
                          resetError = null;
                        });

                        final auth = context.read<AuthProvider>();
                        final success = await auth.resetPassword(_loginRegNoController.text, totp, pass);

                        if (success && mounted) {
                          Navigator.pop(context); // Close sheet
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Password Reset Successfully!'), backgroundColor: Colors.green),
                          );
                          setState(() {
                            _showForgotPassword = false;
                            _loginPasswordController.clear();
                          });
                        } else {
                          setModalState(() {
                            isResetLoading = false;
                            resetError = auth.errorMessage ?? 'Reset failed.';
                          });
                        }
                      },
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  // Neumorphic Input Decoration
  InputDecoration _neuInputDecoration(String hint, Widget? suffixIcon) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF999999)),
      filled: false,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      suffixIcon: suffixIcon,
      border: InputBorder.none,
      enabledBorder: InputBorder.none,
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppTheme.primary, width: 2),
      ),
    );
  }

  // Neumorphic Input Wrapper
  Widget _buildNeuInput({required Widget child}) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF212121),
        borderRadius: BorderRadius.circular(6),
        boxShadow: const [
          BoxShadow(
            color: Colors.black,
            offset: Offset(6, 6),
            blurRadius: 10,
          ),
          BoxShadow(
            color: Color(0x26FFFFFF), // ~15% white to simulate rgba(255,255,255,0.6) loosely on dark mode
            offset: Offset(1, 1),
            blurRadius: 10,
          ),
        ],
      ),
      child: child,
    );
  }

  // Neumorphic Button
  Widget _buildNeuButton({required String text, required VoidCallback onPressed, bool? isLoadingOverride}) {
    final isLoading = isLoadingOverride ?? _isLoading;
    return GestureDetector(
      onTap: isLoading ? null : onPressed,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: const Color(0xFF212121),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xFF212121), width: 2),
          boxShadow: const [
            BoxShadow(
              color: Colors.black,
              offset: Offset(6, 6),
              blurRadius: 10,
            ),
            BoxShadow(
              color: Color(0x26FFFFFF),
              offset: Offset(1, 1),
              blurRadius: 10,
            ),
          ],
        ),
        child: Center(
          child: isLoading 
            ? const SizedBox(height: 20, child: CustomLoader(color: AppTheme.primary))
            : Text(
                text,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
        ),
      ),
    );
  }

  Widget _buildFrontCard() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 48),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E), // Slightly lighter than background to match CSS form
        borderRadius: BorderRadius.circular(15),
        boxShadow: const [
          BoxShadow(color: Colors.black, offset: Offset(2, 2), blurRadius: 10),
          BoxShadow(color: Color(0x1AFFFFFF), offset: Offset(-1, -1), blurRadius: 5),
        ],
      ),
      child: Form(
        key: _loginFormKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Login',
              style: TextStyle(
                fontSize: 25,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 30),
            _buildNeuInput(
              child: TextFormField(
                controller: _loginRegNoController,
                style: const TextStyle(color: Colors.white),
                decoration: _neuInputDecoration('Registration Number', null),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
            ),
            const SizedBox(height: 20),
            _buildNeuInput(
              child: TextFormField(
                controller: _loginPasswordController,
                obscureText: _isLoginObscured,
                onChanged: (_) {
                  if (_showForgotPassword) setState(() => _showForgotPassword = false);
                },
                style: const TextStyle(color: Colors.white),
                decoration: _neuInputDecoration(
                  'Password',
                  IconButton(
                    icon: Icon(
                      _isLoginObscured ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      color: Colors.white54,
                      size: 20,
                    ),
                    onPressed: () => setState(() => _isLoginObscured = !_isLoginObscured),
                  ),
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
            ),
            if (_showForgotPassword)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Align(
                  alignment: Alignment.centerRight,
                  child: GestureDetector(
                    onTap: _showPasswordResetTerminal,
                    child: const Text(
                      'Forgot Password?',
                      style: TextStyle(
                        color: AppTheme.primary,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ).animate().fadeIn(duration: 300.ms),
                  ),
                ),
              ),
            SizedBox(height: _showForgotPassword ? 20 : 30),
            _buildNeuButton(text: 'Login', onPressed: _submitLogin),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  "New Teacher? ",
                  style: TextStyle(color: Colors.white, fontSize: 13),
                ),
                GestureDetector(
                  onTap: _toggleFlip,
                  child: const Text(
                    "Register Here",
                    style: TextStyle(
                      color: AppTheme.primary,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBackCard() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 48),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E),
        borderRadius: BorderRadius.circular(15),
        boxShadow: const [
          BoxShadow(color: Colors.black, offset: Offset(2, 2), blurRadius: 10),
          BoxShadow(color: Color(0x1AFFFFFF), offset: Offset(-1, -1), blurRadius: 5),
        ],
      ),
      child: Form(
        key: _signupFormKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Activate Account',
              style: TextStyle(
                fontSize: 25,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 30),
            _buildNeuInput(
              child: TextFormField(
                controller: _signupRegNoController,
                style: const TextStyle(color: Colors.white),
                decoration: _neuInputDecoration('Registration Number', null),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
            ),
            const SizedBox(height: 20),
            _buildNeuInput(
              child: TextFormField(
                controller: _signupPasswordController,
                obscureText: _isSignupObscured,
                style: const TextStyle(color: Colors.white),
                decoration: _neuInputDecoration(
                  'Temporary Password',
                  IconButton(
                    icon: Icon(
                      _isSignupObscured ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      color: Colors.white54,
                      size: 20,
                    ),
                    onPressed: () => setState(() => _isSignupObscured = !_isSignupObscured),
                  ),
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
            ),
            const SizedBox(height: 30),
            _buildNeuButton(text: 'Setup Account', onPressed: _submitSignup),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  "Already have an account? ",
                  style: TextStyle(color: Colors.white, fontSize: 13),
                ),
                GestureDetector(
                  onTap: _toggleFlip,
                  child: const Text(
                    "Sign In",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      decoration: TextDecoration.underline,
                      decorationColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // The CSS uses a dark background context
      backgroundColor: const Color(0xFF121212),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 40),
              
              // ── Logo Section ──────────────────────────────────────────
              Center(
                child: Column(
                  children: [
                    Image.asset(
                      'assets/images/logo.png',
                      width: 100,
                      height: 100,
                      fit: BoxFit.contain,
                    ).animate().scale(duration: 600.ms, curve: Curves.easeOutBack),
                    const SizedBox(height: 16),
                    RichText(
                      text: const TextSpan(
                        text: 'Geo',
                        style: TextStyle(
                          fontFamily: 'Bitcount',
                          fontSize: 32,
                          fontWeight: FontWeight.w200,
                          letterSpacing: 1.2,
                          color: Colors.white70,
                        ),
                        children: [
                          TextSpan(
                            text: 'Face',
                            style: TextStyle(
                              color: Color(0xFF9F00FF),
                            ),
                          ),
                        ],
                      ),
                    ).animate().fadeIn(delay: 200.ms),
                  ],
                ),
              ),

              const SizedBox(height: 30),

              // Error Toast
              if (_errorText != null) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.redAccent.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Colors.redAccent, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _errorText!,
                          style: const TextStyle(color: Colors.redAccent, fontSize: 13, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                ).animate().fadeIn(duration: 300.ms),
                const SizedBox(height: 16),
              ],

              // ── 3D Flip Card Container ───────────────────────────────
              Center(
                child: AnimatedBuilder(
                  animation: _flipAnimation,
                  builder: (context, child) {
                    final value = _flipAnimation.value;
                    final angle = value * pi;
                    final isFront = value < 0.5;

                    return Transform(
                      transform: Matrix4.identity()
                        ..setEntry(3, 2, 0.001) // perspective
                        ..rotateY(angle),
                      alignment: Alignment.center,
                      child: isFront
                          ? _buildFrontCard()
                          : Transform(
                              // Reverse the rotation so the back content isn't mirrored
                              transform: Matrix4.identity()..rotateY(pi),
                              alignment: Alignment.center,
                              child: _buildBackCard(),
                            ),
                    );
                  },
                ),
              ),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}
