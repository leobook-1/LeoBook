import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/responsive_constants.dart';
import '../../screens/top_odds_screen.dart';

class TopOddsList extends StatelessWidget {
  const TopOddsList({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(Icons.local_fire_department_rounded,
                    color: const Color(0xFFEAB308),
                    size: Responsive.sp(context, 14)),
                SizedBox(width: Responsive.sp(context, 6)),
                Text(
                  "TOP ODDS",
                  style: TextStyle(
                    fontSize: Responsive.sp(context, 10),
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.5,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
            GestureDetector(
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const TopOddsScreen()),
                );
              },
              child: Text(
                "VIEW ALL ODDS",
                style: TextStyle(
                  fontSize: Responsive.sp(context, 7),
                  fontWeight: FontWeight.w900,
                  color: AppColors.primary,
                  letterSpacing: 1.0,
                ),
              ),
            ),
          ],
        ),
        SizedBox(height: Responsive.sp(context, 10)),
        ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: Responsive.sp(context, 140),
            maxHeight: Responsive.sp(context, 180),
          ),
          child: ListView(
            scrollDirection: Axis.horizontal,
            clipBehavior: Clip.none,
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
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minWidth: Responsive.sp(context, 160),
          maxWidth: Responsive.sp(context, 240),
        ),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: EdgeInsets.only(right: Responsive.sp(context, 10)),
          padding: EdgeInsets.all(Responsive.sp(context, 12)),
          decoration: BoxDecoration(
            color: AppColors.desktopSearchFill.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(Responsive.sp(context, 14)),
            border: Border.all(
              color: _isHovered
                  ? widget.color.withValues(alpha: 0.3)
                  : Colors.white.withValues(alpha: 0.05),
              width: 0.5,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Flexible(
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: Responsive.sp(context, 5),
                          height: Responsive.sp(context, 5),
                          decoration: BoxDecoration(
                            color: widget.color,
                            shape: BoxShape.circle,
                          ),
                        ),
                        SizedBox(width: Responsive.sp(context, 4)),
                        Flexible(
                          child: Text(
                            widget.type,
                            style: TextStyle(
                              fontSize: Responsive.sp(context, 7),
                              fontWeight: FontWeight.w900,
                              color: AppColors.textGrey,
                              letterSpacing: 1.0,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: Responsive.sp(context, 5),
                      vertical: Responsive.sp(context, 2),
                    ),
                    decoration: BoxDecoration(
                      color: widget.color.withValues(alpha: 0.1),
                      borderRadius:
                          BorderRadius.circular(Responsive.sp(context, 4)),
                    ),
                    child: Text(
                      widget.badge,
                      style: TextStyle(
                        fontSize: Responsive.sp(context, 6),
                        fontWeight: FontWeight.w900,
                        color: widget.color,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: Responsive.sp(context, 8)),
              Expanded(
                child: Text(
                  widget.title,
                  style: TextStyle(
                    fontSize: Responsive.sp(context, 11),
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    height: 1.2,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              SizedBox(height: Responsive.sp(context, 6)),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "WAS ${widget.wasOdds}",
                          style: TextStyle(
                            fontSize: Responsive.sp(context, 7),
                            color: Colors.white.withValues(alpha: 0.3),
                            fontWeight: FontWeight.w700,
                            decoration: TextDecoration.lineThrough,
                          ),
                        ),
                        SizedBox(height: Responsive.sp(context, 2)),
                        Text(
                          "ODDS",
                          style: TextStyle(
                            fontSize: Responsive.sp(context, 8),
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                            letterSpacing: 1.0,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    widget.nowOdds,
                    style: TextStyle(
                      fontSize: Responsive.sp(context, 18),
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
      ),
    );
  }
}
