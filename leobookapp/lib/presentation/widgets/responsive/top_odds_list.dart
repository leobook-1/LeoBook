import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class TopOddsList extends StatelessWidget {
  const TopOddsList({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _SectionHeader(
              title: "TOP ODDS",
              icon: Icons.local_fire_department_rounded,
              color: Color(0xFFEAB308), // Fire Orange/Yellow
            ),
            Text(
              "VIEW ALL ODDS",
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w900,
                color: AppColors.primary,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        SizedBox(
          height: 180,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: const [
              _OddsCard(
                title: "Man City to Win & Haaland to Score",
                wasOdds: "2.10",
                nowOdds: "2.50",
                badge: "BOOSTED",
                type: "EPL SPECIAL",
                color: AppColors.warning,
              ),
              _OddsCard(
                title: "Lakers to make Western Conf. Finals",
                wasOdds: "3.50",
                nowOdds: "4.20",
                badge: "HOT PICK",
                type: "NBA FUTURES",
                color: Color(0xFFF97316),
              ),
              _OddsCard(
                title: "Alcaraz to Win French Open '24",
                wasOdds: "2.75",
                nowOdds: "3.10",
                badge: "VALUE",
                type: "GRAND SLAM",
                color: Color(0xFFEAB308),
              ),
              _OddsCard(
                title: "Caleb Williams #1 Overall Pick",
                wasOdds: "1.05",
                nowOdds: "1.15",
                badge: "SPECIAL",
                type: "NFL DRAFT",
                color: AppColors.primary,
              ),
            ],
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

class _OddsCard extends StatefulWidget {
  final String title;
  final String wasOdds;
  final String nowOdds;
  final String badge;
  final String type;
  final Color color;

  const _OddsCard({
    required this.title,
    required this.wasOdds,
    required this.nowOdds,
    required this.badge,
    required this.type,
    required this.color,
  });

  @override
  State<_OddsCard> createState() => _OddsCardState();
}

class _OddsCardState extends State<_OddsCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 320,
        margin: const EdgeInsets.only(right: 20),
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.desktopSearchFill.withValues(alpha: 0.5),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: _isHovered
                ? widget.color.withValues(alpha: 0.3)
                : Colors.white.withValues(alpha: 0.05),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: widget.color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      widget.type,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w900,
                        color: AppColors.textGrey,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: widget.color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    widget.badge,
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w900,
                      color: widget.color,
                      letterSpacing: 1,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Text(
                widget.title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                  height: 1.2,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "WAS ${widget.wasOdds}",
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.white.withValues(alpha: 0.3),
                        fontWeight: FontWeight.w700,
                        decoration: TextDecoration.lineThrough,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "ODDS",
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ],
                ),
                Text(
                  widget.nowOdds,
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    color: widget.color,
                    fontStyle: FontStyle.italic,
                    height: 1,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
