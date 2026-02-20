import 'package:flutter/material.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import 'package:leobookapp/core/constants/responsive_constants.dart';
import 'package:leobookapp/data/models/match_model.dart';
import 'package:leobookapp/data/models/recommendation_model.dart';
import 'recommendation_card.dart';

class FeaturedCarousel extends StatelessWidget {
  final List<MatchModel> matches;
  final List<RecommendationModel> recommendations;
  final List<MatchModel> allMatches;
  final VoidCallback? onViewAll;

  const FeaturedCarousel({
    super.key,
    required this.matches,
    required this.recommendations,
    required this.allMatches,
    this.onViewAll,
  });

  @override
  Widget build(BuildContext context) {
    if (recommendations.isEmpty) return const SizedBox.shrink();

    final cardWidth =
        Responsive.sp(context, 260); // Wider for RecommendationCard info
    final carouselHeight = Responsive.sp(context, 145);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: EdgeInsets.symmetric(
            horizontal: Responsive.sp(context, 10),
            vertical: Responsive.sp(context, 6),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.auto_awesome,
                    color: AppColors.primary,
                    size: Responsive.sp(context, 14),
                  ),
                  SizedBox(width: Responsive.sp(context, 5)),
                  Text(
                    "TOP PREDICTIONS",
                    style: TextStyle(
                      fontSize: Responsive.sp(context, 10),
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.0,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : AppColors.textDark,
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: onViewAll,
                child: Text(
                  "VIEW ALL",
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: Responsive.sp(context, 8),
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),
        ),
        SizedBox(
          height: carouselHeight,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding:
                EdgeInsets.symmetric(horizontal: Responsive.sp(context, 10)),
            itemCount: recommendations.length,
            itemBuilder: (context, index) {
              final rec = recommendations[index];
              return SizedBox(
                width: cardWidth,
                child: RecommendationCard(recommendation: rec),
              );
            },
          ),
        ),
      ],
    );
  }
}
