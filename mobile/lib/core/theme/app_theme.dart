import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  AppTheme._();

  // ── Professional Color Palette ──────────────────────────────────────────────
  static const primary      = Color(0xFF7C3AED); // Vibrant Blue from design
  static const primaryDark  = Color(0xFF1A26D9);
  static const slate        = Color(0xFF050505); // Deep Dark background
  static const slateLight   = Color(0xFF121212); // Card surface
  static const textDark     = Colors.white;
  static const textMedium   = Color(0xFF94A3B8);
  static const borderColor  = Color(0xFF7C3AED);
  static const surface      = Color(0xFF121212);

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

  // ── Dark Theme (Professional) ─────────────────────────────────────────────
  static ThemeData get lightTheme => darkTheme; // Force dark mode

  static ThemeData get darkTheme {
    const colorScheme = ColorScheme.dark(
      primary:     primary,
      secondary:   primaryDark,
      error:       Color(0xFFEF4444),
      surface:     surface,
      onPrimary:   Colors.white,
      onSecondary: Colors.white,
      onSurface:   textDark,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: slate,
      textTheme: _buildTextTheme(textDark, textMedium),
      appBarTheme: AppBarTheme(
        backgroundColor: slate,
        elevation: 0,
        scrolledUnderElevation: 1,
        iconTheme: const IconThemeData(color: textDark),
        titleTextStyle: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w600, color: textDark),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 15,
        shadowColor: Colors.white.withValues(alpha: 0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          elevation: 5,
          shadowColor: primary.withValues(alpha: 0.5),
          textStyle: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: slateLight,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
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
}
