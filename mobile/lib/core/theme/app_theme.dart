import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  AppTheme._();

  // ── Professional Color Palette ──────────────────────────────────────────────
  static const primary      = Color(0xFF2563EB); // Modern Blue
  static const primaryDark  = Color(0xFF1E40AF);
  static const slate        = Color(0xFF0F172A); // Deep Slate
  static const slateLight   = Color(0xFFF8FAFC);
  static const textDark     = Color(0xFF1E293B);
  static const textMedium   = Color(0xFF64748B);
  static const borderColor  = Color(0xFFE2E8F0);
  static const surface      = Colors.white;

  // Semantic aliases
  static const Color success        = Color(0xFF10B981);
  static const Color error          = Color(0xFFEF4444);
  static const Color warning        = Color(0xFFF59E0B);
  static const Color primaryBlue    = primary;
  static const Color primaryBlueDark = primaryDark;

  // ── Text Theme ────────────────────────────────────────────────────────────
  static TextTheme _buildTextTheme(Color primary, Color secondary) {
    return GoogleFonts.interTextTheme().copyWith(
      displayLarge:  GoogleFonts.inter(fontSize: 32, fontWeight: FontWeight.w700, color: primary, height: 1.2),
      displayMedium: GoogleFonts.inter(fontSize: 26, fontWeight: FontWeight.w600, color: primary, height: 1.3),
      headlineLarge: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w600, color: primary),
      headlineMedium:GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w600, color: primary),
      titleLarge:    GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600, color: primary),
      titleMedium:   GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w500, color: primary),
      bodyLarge:     GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w400, color: primary),
      bodyMedium:    GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w400, color: secondary),
      bodySmall:     GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w400, color: secondary),
      labelLarge:    GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.5),
    );
  }

  // ── Light Theme (Professional) ────────────────────────────────────────────
  static ThemeData get lightTheme {
    const colorScheme = ColorScheme.light(
      primary:     primary,
      secondary:   primaryDark,
      error:       Color(0xFFEF4444),
      surface:     Colors.white,
      onPrimary:   Colors.white,
      onSecondary: Colors.white,
      onSurface:   textDark,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: slateLight,
      textTheme: _buildTextTheme(textDark, textMedium),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 1,
        iconTheme: const IconThemeData(color: textDark),
        titleTextStyle: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w600, color: textDark),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: borderColor),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          elevation: 0,
          textStyle: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFEF4444)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        hintStyle: GoogleFonts.inter(color: textMedium.withValues(alpha: 0.5), fontSize: 14),
      ),
    );
  }

  // ── Dark Theme (kept for compatibility but same structure) ─────────────────
  static ThemeData get darkTheme => lightTheme;
}
