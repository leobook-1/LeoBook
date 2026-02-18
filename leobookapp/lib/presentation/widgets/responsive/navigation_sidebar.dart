import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/theme/liquid_glass_theme.dart';

class NavigationSideBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onIndexChanged;
  final bool isExpanded;
  final VoidCallback onToggle;

  const NavigationSideBar({
    super.key,
    required this.currentIndex,
    required this.onIndexChanged,
    required this.isExpanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedSize(
      duration: LiquidGlassTheme.tabSwitchDuration,
      curve: LiquidGlassTheme.tabSwitchCurve,
      child: IntrinsicWidth(
        child: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(
              sigmaX: LiquidGlassTheme.blurRadiusMedium,
              sigmaY: LiquidGlassTheme.blurRadiusMedium,
            ),
            child: Container(
              height: double.infinity,
              decoration: BoxDecoration(
                color: AppColors.surfaceDark.withValues(alpha: 0.85),
                border: Border(
                  right: BorderSide(
                    color: LiquidGlassTheme.glassBorderDark,
                  ),
                ),
              ),
              child: SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: MediaQuery.of(context).size.height,
                  ),
                  child: IntrinsicHeight(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _buildLogo(),
                        const SizedBox(height: 32),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              _NavItem(
                                icon: Icons.home_rounded,
                                label: "HOME",
                                isActive: currentIndex == 0,
                                isExpanded: isExpanded,
                                onTap: () => onIndexChanged(0),
                              ),
                              _NavItem(
                                icon: Icons.gavel_rounded,
                                label: "RULES",
                                isActive: currentIndex == 1,
                                isExpanded: isExpanded,
                                onTap: () => onIndexChanged(1),
                              ),
                              _NavItem(
                                icon: Icons.emoji_events_rounded,
                                label: "TOP",
                                isActive: currentIndex == 2,
                                isExpanded: isExpanded,
                                onTap: () => onIndexChanged(2),
                              ),
                              _NavItem(
                                icon: Icons.person_rounded,
                                label: "PROFILE",
                                isActive: currentIndex == 3,
                                isExpanded: isExpanded,
                                onTap: () => onIndexChanged(3),
                              ),
                            ],
                          ),
                        ),
                        const Spacer(),
                        if (isExpanded) _buildProCard(),
                        _buildToggleBtn(),
                        const SizedBox(height: 16),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildToggleBtn() {
    return IconButton(
      onPressed: onToggle,
      icon: AnimatedRotation(
        turns: isExpanded ? 0.0 : 0.5,
        duration: LiquidGlassTheme.tabSwitchDuration,
        child: const Icon(
          Icons.keyboard_double_arrow_left,
          color: Colors.white54,
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: isExpanded ? 16.0 : 4.0,
        vertical: isExpanded ? 24.0 : 12.0,
      ),
      child: FittedBox(
        fit: BoxFit.scaleDown,
        alignment: isExpanded ? Alignment.centerLeft : Alignment.center,
        child: Row(
          mainAxisAlignment:
              isExpanded ? MainAxisAlignment.start : MainAxisAlignment.center,
          mainAxisSize: isExpanded ? MainAxisSize.max : MainAxisSize.min,
          children: [
            Container(
              padding: EdgeInsets.all(isExpanded ? 8 : 6),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.analytics_rounded,
                color: Colors.white,
                size: isExpanded ? 24 : 18,
              ),
            ),
            if (isExpanded) ...[
              const SizedBox(width: 8),
              const Text(
                "LEOBOOK",
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  fontStyle: FontStyle.italic,
                  letterSpacing: -1,
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProCard() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 24.0),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.backgroundDark.withValues(alpha: 0.6),
          borderRadius: BorderRadius.circular(LiquidGlassTheme.borderRadius),
          border: Border.all(color: LiquidGlassTheme.glassBorderDark),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "PREMIUM STATUS",
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppColors.textGrey,
                letterSpacing: 1.5,
              ),
            ),
            const SizedBox(height: 8),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    "PRO MEMBER",
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.successGreen,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(Icons.verified, color: AppColors.warning, size: 16),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final bool isExpanded;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.isExpanded,
    required this.onTap,
  });

  @override
  State<_NavItem> createState() => _NavItemState();
}

class _NavItemState extends State<_NavItem> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: GestureDetector(
          onTap: widget.onTap,
          child: AnimatedContainer(
            duration: LiquidGlassTheme.cardPressDuration,
            curve: LiquidGlassTheme.cardPressCurve,
            padding: EdgeInsets.symmetric(
              horizontal: widget.isExpanded ? 16 : 12,
              vertical: 12,
            ),
            decoration: BoxDecoration(
              color: widget.isActive
                  ? AppColors.primary.withValues(alpha: 0.15)
                  : (_isHovered
                      ? Colors.white.withValues(alpha: 0.05)
                      : Colors.transparent),
              borderRadius: BorderRadius.circular(
                LiquidGlassTheme.borderRadiusSmall,
              ),
              border: Border.all(
                color: widget.isActive
                    ? AppColors.primary.withValues(alpha: 0.5)
                    : (_isHovered
                        ? LiquidGlassTheme.glassBorderDark
                        : Colors.transparent),
              ),
            ),
            child: FittedBox(
              fit: BoxFit.scaleDown,
              alignment:
                  widget.isExpanded ? Alignment.centerLeft : Alignment.center,
              child: Row(
                mainAxisAlignment: widget.isExpanded
                    ? MainAxisAlignment.start
                    : MainAxisAlignment.center,
                children: [
                  Icon(
                    widget.icon,
                    color: widget.isActive ? AppColors.primary : Colors.white54,
                    size: 20,
                  ),
                  if (widget.isExpanded) ...[
                    const SizedBox(width: 12),
                    Text(
                      widget.label,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: widget.isActive ? Colors.white : Colors.white54,
                        letterSpacing: 1.0,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
