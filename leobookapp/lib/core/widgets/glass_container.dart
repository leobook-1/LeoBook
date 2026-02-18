import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_colors.dart';
import '../theme/liquid_glass_theme.dart';
import '../theme/glass_settings.dart';

/// Premium frosted-glass container with Liquid Glass aesthetics.
///
/// Features:
/// - Configurable backdrop blur (respects performance settings)
/// - Inner glow gradient for depth / refraction illusion
/// - Hover (scale up) and press (scale down) micro-animations
/// - Optional radial refraction shimmer via ShaderMask
class GlassContainer extends StatefulWidget {
  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double blurSigma;
  final Color? color;
  final Color? borderColor;
  final double borderWidth;
  final VoidCallback? onTap;
  final bool interactive;
  final bool enableRefraction;

  const GlassContainer({
    super.key,
    required this.child,
    this.borderRadius = 20,
    this.padding,
    this.margin,
    this.blurSigma = 24,
    this.color,
    this.borderColor,
    this.borderWidth = 1.0,
    this.onTap,
    this.interactive = true,
    this.enableRefraction = false,
  });

  @override
  State<GlassContainer> createState() => _GlassContainerState();
}

class _GlassContainerState extends State<GlassContainer> {
  bool _isHovered = false;
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Calculate base colors
    Color fillColor =
        widget.color ?? (isDark ? AppColors.glassDark : AppColors.glassLight);
    Color border = widget.borderColor ??
        (isDark
            ? AppColors.liquidGlassBorderDark
            : AppColors.liquidGlassBorderLight);

    // Adjust for states if interactive
    double scale = 1.0;
    if (widget.interactive && widget.onTap != null) {
      if (_isPressed) {
        scale = 0.98;
        fillColor = fillColor.withValues(
          alpha: (fillColor.a * 1.2).clamp(0.0, 1.0),
        );
      } else if (_isHovered) {
        scale = 1.02;
        fillColor = fillColor.withValues(
          alpha: (fillColor.a * 1.1).clamp(0.0, 1.0),
        );
      }
    }

    final glassDecoration = BoxDecoration(
      color: fillColor,
      borderRadius: BorderRadius.circular(widget.borderRadius),
      border: Border.all(
        color: _isHovered ? AppColors.primary.withValues(alpha: 0.3) : border,
        width: widget.borderWidth,
      ),
      boxShadow: [
        // Inner glow for depth
        BoxShadow(
          color: LiquidGlassTheme.innerGlow(Theme.of(context).brightness),
          blurRadius: 1,
          spreadRadius: 0,
          offset: const Offset(0, 1),
        ),
        // Outer subtle shadow
        if (_isHovered)
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.1),
            blurRadius: 15,
            spreadRadius: 2,
          ),
      ],
    );

    Widget glassChild = AnimatedContainer(
      duration: LiquidGlassTheme.cardPressDuration,
      padding: widget.padding,
      decoration: glassDecoration,
      child: widget.child,
    );

    // Refraction shimmer — subtle radial gradient overlay
    if (widget.enableRefraction) {
      glassChild = ShaderMask(
        shaderCallback: (bounds) => RadialGradient(
          center: const Alignment(-0.8, -0.8),
          radius: 1.5,
          colors: [
            Colors.white.withValues(alpha: 0.06),
            Colors.transparent,
            Colors.white.withValues(alpha: 0.03),
          ],
          stops: const [0.0, 0.5, 1.0],
        ).createShader(bounds),
        blendMode: BlendMode.srcOver,
        child: glassChild,
      );
    }

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTapDown: (_) => setState(() => _isPressed = true),
        onTapUp: (_) => setState(() => _isPressed = false),
        onTapCancel: () => setState(() => _isPressed = false),
        onTap: () {
          if (widget.onTap != null) {
            HapticFeedback.lightImpact();
            widget.onTap!();
          }
        },
        child: AnimatedScale(
          scale: scale,
          duration: LiquidGlassTheme.cardPressDuration,
          curve: LiquidGlassTheme.cardPressCurve,
          child: Container(
            margin: widget.margin,
            child: Builder(
              builder: (context) {
                final sigma =
                    GlassSettings.isBlurEnabled ? GlassSettings.blurSigma : 0.0;
                final inner = ClipRRect(
                  borderRadius: BorderRadius.circular(widget.borderRadius),
                  child: sigma > 0
                      ? BackdropFilter(
                          filter: ImageFilter.blur(
                            sigmaX: sigma,
                            sigmaY: sigma,
                          ),
                          child: glassChild,
                        )
                      : glassChild,
                );
                return inner;
              },
            ),
          ),
        ),
      ),
    );
  }
}
