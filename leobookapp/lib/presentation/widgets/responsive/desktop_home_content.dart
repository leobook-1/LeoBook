import 'package:flutter/material.dart';
import 'top_predictions_grid.dart';
import 'category_bar.dart';
import 'accuracy_report_card.dart';
import 'top_odds_list.dart';
import '../../../logic/cubit/home_cubit.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/match_sorter.dart';
import '../match_card.dart';

class DesktopHomeContent extends StatefulWidget {
  final HomeLoaded state;

  const DesktopHomeContent({super.key, required this.state});

  @override
  State<DesktopHomeContent> createState() => _DesktopHomeContentState();
}

class _DesktopHomeContentState extends State<DesktopHomeContent>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CategoryBar(),
          const SizedBox(height: 8),
          const TopPredictionsGrid(),
          const SizedBox(height: 48),
          const AccuracyReportCard(),
          const SizedBox(height: 48),
          const TopOddsList(),
          const SizedBox(height: 48),
          _buildTabsSection(),
        ],
      ),
    );
  }

  Widget _buildTabsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TabBar(
          controller: _tabController,
          isScrollable: true,
          labelPadding: const EdgeInsets.only(right: 32),
          indicatorColor: AppColors.primary,
          indicatorWeight: 4,
          dividerColor: Colors.white10,
          labelColor: Colors.white,
          unselectedLabelColor: AppColors.textGrey,
          labelStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.5,
          ),
          tabs: const [
            Tab(text: "ALL PREDICTIONS"),
            Tab(text: "FINISHED"),
            Tab(text: "SCHEDULED"),
          ],
        ),
        const SizedBox(height: 24),
        SizedBox(
          height: 600, // Large enough for the list
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildMatchGrid(MatchTabType.all),
              _buildMatchGrid(MatchTabType.finished),
              _buildMatchGrid(MatchTabType.scheduled),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMatchGrid(MatchTabType type) {
    final matches = MatchSorter.getSortedMatches(
      widget.state.filteredMatches.cast(),
      type,
    );

    if (matches.isEmpty) {
      return const Center(
        child: Text(
          "No matches found for this category",
          style: TextStyle(color: AppColors.textGrey),
        ),
      );
    }

    // On desktop, we can use a grid for the "All Predictions" section too if we want,
    // but the screenshot shows a list-like structure with specific leagues.
    // I'll use a responsive grid that shows 1 column on smaller desktop and 2 on wide.
    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: MediaQuery.of(context).size.width > 1600 ? 3 : 2,
        crossAxisSpacing: 20,
        mainAxisSpacing: 20,
        childAspectRatio: 2.2,
      ),
      itemCount: matches.length,
      itemBuilder: (context, index) {
        final item = matches[index];
        if (item is MatchGroupHeader) {
          return Center(
            child: Text(
              item.title.toUpperCase(),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w900,
                color: AppColors.textGrey,
                letterSpacing: 1.5,
              ),
            ),
          );
        }
        return MatchCard(match: item);
      },
    );
  }
}
