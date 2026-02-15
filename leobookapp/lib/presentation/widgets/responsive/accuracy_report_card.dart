import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class AccuracyReportCard extends StatelessWidget {
  const AccuracyReportCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _SectionHeader(
              title: "YESTERDAY'S ACCURACY REPORT",
              icon: Icons.check_circle_rounded,
              color: AppColors.successGreen,
            ),
            Text(
              "24 MATCHES ANALYZED",
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppColors.textGrey,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: AppColors.desktopSearchFill.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
          ),
          child: Row(
            children: [
              _buildMainAccuracy(),
              const SizedBox(width: 48),
              Container(width: 1, height: 100, color: Colors.white10),
              const SizedBox(width: 48),
              const Expanded(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _LeagueAccuracy(
                      label: "PREMIER LEAGUE",
                      percentage: 0.92,
                      color: AppColors.primary,
                      icon: Icons.sports_soccer_rounded,
                    ),
                    _LeagueAccuracy(
                      label: "NBA",
                      percentage: 0.85,
                      color: AppColors.warning,
                      icon: Icons.sports_basketball_rounded,
                    ),
                    _LeagueAccuracy(
                      label: "LA LIGA",
                      percentage: 0.80,
                      color: AppColors.successGreen,
                      icon: Icons.sports_soccer_rounded,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMainAccuracy() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "TOTAL ACCURACY",
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w900,
            color: AppColors.textGrey,
            letterSpacing: 1.5,
          ),
        ),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            const Text(
              "88",
              style: TextStyle(
                fontSize: 64,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                fontStyle: FontStyle.italic,
                letterSpacing: -2,
              ),
            ),
            const Text(
              "%",
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: AppColors.successGreen,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: const Icon(
                Icons.trending_up_rounded,
                color: AppColors.successGreen,
                size: 32,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.successGreen.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(6),
          ),
          child: const Text(
            "HIGH PERFORMANCE",
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: AppColors.successGreen,
              letterSpacing: 1,
            ),
          ),
        ),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;

  const _SectionHeader({
    required this.title,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 12),
        Text(
          title,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
            letterSpacing: 2.0,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}

class _LeagueAccuracy extends StatelessWidget {
  final String label;
  final double percentage;
  final Color color;
  final IconData icon;

  const _LeagueAccuracy({
    required this.label,
    required this.percentage,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 180,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.desktopHeaderBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label.split(' ').first, // Just the first word if long
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: AppColors.textGrey,
                  letterSpacing: 1.5,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              Icon(icon, color: color.withValues(alpha: 0.5), size: 16),
            ],
          ),
          const Spacer(),
          Text(
            "${(percentage * 100).toInt()}%",
            style: const TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.w900,
              color: Colors.white,
              fontStyle: FontStyle.italic,
              letterSpacing: -1,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            height: 6,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(10),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: percentage,
              child: Container(
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(10),
                  boxShadow: [
                    BoxShadow(
                      color: color.withValues(alpha: 0.3),
                      blurRadius: 10,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
