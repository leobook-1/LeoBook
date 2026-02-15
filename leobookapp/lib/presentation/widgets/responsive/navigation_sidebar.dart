import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class NavigationSideBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onIndexChanged;

  const NavigationSideBar({
    super.key,
    required this.currentIndex,
    required this.onIndexChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 256,
      height: double.infinity,
      decoration: const BoxDecoration(
        color: AppColors.surfaceDark,
        border: Border(right: BorderSide(color: Colors.white10)),
      ),
      child: Column(
        children: [
          _buildLogo(),
          const SizedBox(height: 32),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Column(
                children: [
                  _NavItem(
                    icon: Icons.home_rounded,
                    label: "HOME",
                    isActive: currentIndex == 0,
                    onTap: () => onIndexChanged(0),
                  ),
                  _NavItem(
                    icon: Icons.gavel_rounded,
                    label: "RULES",
                    isActive: currentIndex == 1,
                    onTap: () => onIndexChanged(1),
                  ),
                  _NavItem(
                    icon: Icons.emoji_events_rounded,
                    label: "TOP",
                    isActive: currentIndex == 2,
                    onTap: () => onIndexChanged(2),
                  ),
                  _NavItem(
                    icon: Icons.person_rounded,
                    label: "PROFILE",
                    isActive: currentIndex == 3,
                    onTap: () => onIndexChanged(3),
                  ),
                ],
              ),
            ),
          ),
          _buildProCard(),
        ],
      ),
    );
  }

  Widget _buildLogo() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.primary,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.analytics_rounded,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          const Text(
            "LEOBOOK",
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
              color: Colors.white,
              fontStyle: FontStyle.italic,
              letterSpacing: -1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProCard() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.backgroundDark,
          borderRadius: BorderRadius.circular(20),
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
            Row(
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
                Icon(Icons.verified, color: AppColors.warning, size: 16),
              ],
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
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
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
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: widget.isActive
                  ? AppColors.primary.withValues(alpha: 0.12)
                  : _isHovered
                  ? Colors.white.withValues(alpha: 0.04)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                if (widget.isActive)
                  Positioned(
                    left: -16,
                    top: 8,
                    bottom: 8,
                    child: Container(
                      width: 4,
                      decoration: const BoxDecoration(
                        color: AppColors.primary,
                        borderRadius: BorderRadius.horizontal(
                          right: Radius.circular(4),
                        ),
                      ),
                    ),
                  ),
                Row(
                  children: [
                    Icon(
                      widget.icon,
                      color: widget.isActive
                          ? AppColors.primary
                          : AppColors.textGrey,
                      size: 22,
                    ),
                    const SizedBox(width: 16),
                    Text(
                      widget.label,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: widget.isActive
                            ? FontWeight.w900
                            : FontWeight.w600,
                        letterSpacing: 1.2,
                        color: widget.isActive
                            ? Colors.white
                            : AppColors.textGrey,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
