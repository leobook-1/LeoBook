import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import 'package:leobookapp/core/constants/app_colors.dart';
import 'package:leobookapp/core/constants/responsive_constants.dart';
import 'package:leobookapp/core/utils/match_sorter.dart';
import 'package:leobookapp/core/animations/liquid_glass_animations.dart';
import '../widgets/match_card.dart';
import '../widgets/featured_carousel.dart';
import '../widgets/news_feed.dart';
import '../widgets/responsive/desktop_home_content.dart';
import '../widgets/responsive/category_bar.dart';
import '../widgets/responsive/top_odds_list.dart';
import '../../logic/cubit/search_cubit.dart';
import 'search_screen.dart';
import '../widgets/responsive/accuracy_report_card.dart';
import '../../core/theme/liquid_glass_theme.dart';
import '../widgets/footnote_section.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isDesktop = Responsive.isDesktop(context);
    final hp = Responsive.horizontalPadding(context);

    return Scaffold(
      backgroundColor: isDesktop ? AppColors.backgroundDark : null,
      body: BlocBuilder<HomeCubit, HomeState>(
        builder: (context, state) {
          if (state is HomeLoading) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is HomeLoaded) {
            if (isDesktop) {
              return DesktopHomeContent(
                state: state,
              );
            }

            return SafeArea(
              bottom: false,
              child: RefreshIndicator(
                onRefresh: () async {
                  context.read<HomeCubit>().loadDashboard();
                },
                child: CustomScrollView(
                  physics: liquidScrollPhysics,
                  slivers: [
                    SliverAppBar(
                      pinned: true,
                      floating: false,
                      elevation: 0,
                      backgroundColor: Colors.transparent,
                      expandedHeight: 0,
                      toolbarHeight: Responsive.sp(context, 32),
                      centerTitle: false,
                      title: Padding(
                        padding: EdgeInsets.symmetric(horizontal: hp),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "LEOBOOK",
                              style: TextStyle(
                                fontSize: Responsive.sp(context, 12),
                                fontWeight: FontWeight.w900,
                                color:
                                    isDark ? Colors.white : AppColors.textDark,
                                letterSpacing: 2.0,
                              ),
                            ),
                            GestureDetector(
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => BlocProvider.value(
                                      value: context.read<SearchCubit>(),
                                      child: const SearchScreen(),
                                    ),
                                  ),
                                );
                              },
                              child: Container(
                                padding:
                                    EdgeInsets.all(Responsive.sp(context, 6)),
                                decoration: BoxDecoration(
                                  color: isDark
                                      ? Colors.white.withValues(alpha: 0.05)
                                      : Colors.black.withValues(alpha: 0.05),
                                  borderRadius: BorderRadius.circular(
                                      Responsive.sp(context, 8)),
                                ),
                                child: Icon(
                                  Icons.search_rounded,
                                  color:
                                      isDark ? Colors.white70 : Colors.black54,
                                  size: Responsive.sp(context, 15),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      bottom: PreferredSize(
                        preferredSize:
                            Size.fromHeight(Responsive.sp(context, 44)),
                        child: const CategoryBar(),
                      ),
                      flexibleSpace: ClipRect(
                        child: BackdropFilter(
                          filter: ImageFilter.blur(
                            sigmaX: LiquidGlassTheme.blurRadiusMedium,
                            sigmaY: LiquidGlassTheme.blurRadiusMedium,
                          ),
                          child: Container(
                            decoration: BoxDecoration(
                              color: (isDark
                                      ? AppColors.backgroundDark
                                      : AppColors.backgroundLight)
                                  .withValues(alpha: 0.35),
                              border: Border(
                                bottom: BorderSide(
                                  color: isDark
                                      ? Colors.white10
                                      : Colors.black.withValues(alpha: 0.04),
                                  width: 1.0,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    SliverPadding(
                      padding: EdgeInsets.symmetric(horizontal: hp),
                      sliver: SliverToBoxAdapter(
                        child: FeaturedCarousel(
                          matches: state.featuredMatches,
                          recommendations: state.filteredRecommendations,
                          allMatches: state.allMatches,
                        ),
                      ),
                    ),
                    SliverPadding(
                      padding: EdgeInsets.symmetric(horizontal: hp),
                      sliver: SliverToBoxAdapter(
                        child: Column(
                          children: [
                            SizedBox(height: Responsive.sp(context, 10)),
                            const TopOddsList(),
                            SizedBox(height: Responsive.sp(context, 12)),
                            const AccuracyReportCard(),
                            SizedBox(height: Responsive.sp(context, 10)),
                          ],
                        ),
                      ),
                    ),
                    SliverToBoxAdapter(child: NewsFeed(news: state.news)),
                    SliverToBoxAdapter(
                        child: SizedBox(height: Responsive.sp(context, 6))),
                    SliverPersistentHeader(
                      pinned: true,
                      delegate: _StickyTabBarDelegate(
                        TabBar(
                          controller: _tabController,
                          indicatorColor: AppColors.primary,
                          indicatorWeight: 2,
                          labelColor: AppColors.primary,
                          unselectedLabelColor:
                              isDark ? Colors.white60 : AppColors.textGrey,
                          labelStyle: TextStyle(
                            fontSize: Responsive.sp(context, 10),
                            fontWeight: FontWeight.w900,
                            letterSpacing: 0.8,
                          ),
                          unselectedLabelStyle: TextStyle(
                            fontSize: Responsive.sp(context, 8),
                            fontWeight: FontWeight.w700,
                          ),
                          dividerColor: Colors.transparent,
                          labelPadding: EdgeInsets.symmetric(
                              horizontal: Responsive.sp(context, 4)),
                          tabs: [
                            Tab(text: "ALL (${state.filteredMatches.length})"),
                            Tab(
                                text:
                                    "LIVE (${state.filteredMatches.where((m) => m.isLive).length})"),
                            Tab(
                                text:
                                    "FINISHED (${state.filteredMatches.where((m) => m.isFinished).length})"),
                            Tab(
                                text:
                                    "SCHEDULED (${state.filteredMatches.where((m) => !m.isLive && !m.isFinished).length})"),
                          ],
                        ),
                        isDark,
                      ),
                    ),
                    SliverFillRemaining(
                      hasScrollBody: true,
                      child: TabBarView(
                        controller: _tabController,
                        physics: const AlwaysScrollableScrollPhysics(),
                        children: [
                          _buildMatchList(
                            state.filteredMatches,
                            MatchTabType.all,
                            isDark,
                          ),
                          _buildMatchList(
                            state.filteredMatches,
                            MatchTabType.live,
                            isDark,
                          ),
                          _buildMatchList(
                            state.filteredMatches,
                            MatchTabType.finished,
                            isDark,
                          ),
                          _buildMatchList(
                            state.filteredMatches,
                            MatchTabType.scheduled,
                            isDark,
                          ),
                        ],
                      ),
                    ),
                    SliverToBoxAdapter(
                      child: SizedBox(height: Responsive.sp(context, 20)),
                    ),
                    const SliverToBoxAdapter(
                      child: FootnoteSection(),
                    ),
                  ],
                ),
              ),
            );
          } else if (state is HomeError) {
            return Center(child: Text(state.message));
          }
          return Container();
        },
      ),
    );
  }

  Widget _buildMatchList(
    List<dynamic> matches,
    MatchTabType type,
    bool isDark,
  ) {
    final sortedItems = MatchSorter.getSortedMatches(matches.cast(), type);
    final guideLine = Responsive.sp(context, 14);

    if (sortedItems.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.sports_soccer_rounded,
              size: Responsive.sp(context, 28),
              color: isDark ? Colors.white24 : Colors.black12,
            ),
            SizedBox(height: Responsive.sp(context, 8)),
            Text(
              "No matches found",
              style: TextStyle(
                fontSize: Responsive.sp(context, 10),
                color: isDark ? Colors.white38 : Colors.black38,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      physics: liquidScrollPhysics,
      itemCount: sortedItems.length,
      itemBuilder: (context, index) {
        return Stack(
          children: [
            Positioned(
              left: guideLine + 1,
              top: 0,
              bottom: 0,
              child: Container(
                width: 0.5,
                color: isDark
                    ? Colors.white.withValues(alpha: 0.08)
                    : Colors.black.withValues(alpha: 0.04),
              ),
            ),
            _buildItem(sortedItems[index], isDark),
          ],
        );
      },
    );
  }

  Widget _buildItem(dynamic item, bool isDark) {
    if (item is MatchGroupHeader) {
      return Padding(
        padding: EdgeInsets.fromLTRB(
          Responsive.sp(context, 14),
          Responsive.sp(context, 12),
          Responsive.sp(context, 14),
          Responsive.sp(context, 4),
        ),
        child: Row(
          children: [
            Container(
              width: Responsive.sp(context, 2.5),
              height: Responsive.sp(context, 8),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(1),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.4),
                    blurRadius: 3,
                    spreadRadius: 0,
                  ),
                ],
              ),
            ),
            SizedBox(width: Responsive.sp(context, 4)),
            Text(
              item.title.toUpperCase(),
              style: TextStyle(
                fontSize: Responsive.sp(context, 9),
                fontWeight: FontWeight.w900,
                color: isDark ? Colors.white70 : AppColors.textDark,
                letterSpacing: 0.8,
              ),
            ),
            const Spacer(),
            Flexible(
              child: Container(
                height: 0.5,
                color: isDark
                    ? Colors.white10
                    : Colors.black.withValues(alpha: 0.04),
              ),
            ),
          ],
        ),
      );
    } else {
      return MatchCard(match: item);
    }
  }
}

class _StickyTabBarDelegate extends SliverPersistentHeaderDelegate {
  final TabBar _tabBar;
  final bool isDark;

  _StickyTabBarDelegate(this._tabBar, this.isDark);

  @override
  double get minExtent => 50.0;
  @override
  double get maxExtent => 50.0;

  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    final hp = Responsive.horizontalPadding(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: hp),
      color: Colors.transparent,
      height: 50.0,
      child: Stack(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(Responsive.sp(context, 16)),
            ),
            child: BackdropFilter(
              filter: ImageFilter.blur(
                sigmaX: LiquidGlassTheme.blurRadiusMedium,
                sigmaY: LiquidGlassTheme.blurRadiusMedium,
              ),
              child: Container(
                height: 50.0,
                decoration: BoxDecoration(
                  color: (isDark
                          ? AppColors.backgroundDark
                          : AppColors.backgroundLight)
                      .withValues(alpha: 0.5),
                  borderRadius: BorderRadius.vertical(
                    top: Radius.circular(Responsive.sp(context, 16)),
                  ),
                  border: Border(
                    top: BorderSide(
                      color: Colors.white.withValues(alpha: 0.1),
                      width: 1.0, // Solid 1px to avoid fractional gaps
                    ),
                    left: BorderSide(
                      color: Colors.white.withValues(alpha: 0.1),
                      width: 1.0,
                    ),
                    right: BorderSide(
                      color: Colors.white.withValues(alpha: 0.1),
                      width: 1.0,
                    ),
                  ),
                ),
                child: _tabBar,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  bool shouldRebuild(_StickyTabBarDelegate oldDelegate) {
    return false;
  }
}
