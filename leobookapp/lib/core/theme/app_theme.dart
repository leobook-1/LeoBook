import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';

class AppTheme {
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.backgroundDark,
      primaryColor: AppColors.primary,
      cardColor: AppColors.glassDark,

      textTheme: GoogleFonts.lexendTextTheme().copyWith(
        displayLarge: GoogleFonts.lexend(
          fontSize: 32,
          fontWeight: FontWeight.w700,
          color: Colors.white,
          letterSpacing: -1.5,
        ),
        titleLarge: GoogleFonts.lexend(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
          letterSpacing: -0.5,
        ),
        titleMedium: GoogleFonts.lexend(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: AppColors.textLight,
        ),
        bodyLarge: GoogleFonts.lexend(
          fontSize: 16,
          fontWeight: FontWeight.w400,
          color: AppColors.textLight,
          height: 1.5,
        ),
        bodyMedium: GoogleFonts.lexend(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: AppColors.textGrey,
          height: 1.6,
        ),
        bodySmall: GoogleFonts.lexend(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          color: AppColors.textGrey,
        ),
        labelLarge: GoogleFonts.lexend(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: AppColors.textGrey,
          letterSpacing: 1.0,
        ),
      ),

      colorScheme: const ColorScheme.dark(
        primary: AppColors.primary,
        surface: AppColors.surfaceDark,
        onSurface: AppColors.textLight,
        error: AppColors.liveRed,
        secondary: AppColors.successGreen,
        surfaceContainerHighest: AppColors.surfaceDark,
      ),

      // Glass-aware AppBar
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.backgroundDark.withValues(alpha: 0.8),
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.lexend(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.5,
        ),
      ),

      // Glass-aware Card theme
      cardTheme: CardThemeData(
        color: AppColors.glassDark,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
        ),
      ),

      // Input Decoration
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.desktopSearchFill,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        hintStyle: const TextStyle(
          color: Colors.white24,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),

      // Smooth bottom sheet
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
      ),

      // Animated snackbar
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.cardDark,
        contentTextStyle: GoogleFonts.lexend(color: Colors.white, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),

      // Floating action button
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),

      // Divider
      dividerColor: Colors.white10,
      dividerTheme: const DividerThemeData(
        color: Colors.white10,
        thickness: 0.5,
      ),
    );
  }
}
