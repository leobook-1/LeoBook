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
import '../widgets/footnote_section.dart';
import '../widgets/responsive/desktop_home_content.dart';
import '../widgets/responsive/category_bar.dart';
import '../widgets/responsive/top_predictions_grid.dart';
import '../../logic/cubit/search_cubit.dart';
import 'search_screen.dart';
import '../../core/theme/liquid_glass_theme.dart';

class HomeScreen extends StatefulWidget {
  final bool isSidebarExpanded;
  const HomeScreen({super.key, this.isSidebarExpanded = true});

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
                isSidebarExpanded: widget.isSidebarExpanded,
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
                    SliverPersistentHeader(
                      pinned: true,
                      delegate: _CategoryHeaderDelegate(
                        child: Row(
                          children: [
                            const Expanded(child: CategoryBar()),
                            SizedBox(width: Responsive.sp(context, 6)),
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
                                    EdgeInsets.all(Responsive.sp(context, 7)),
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
                                  size: Responsive.sp(context, 16),
                                ),
                              ),
                            ),
                          ],
                        ),
                        hp: hp,
                        isDark: isDark,
                      ),
                    ),
                    SliverPadding(
                      padding: EdgeInsets.symmetric(horizontal: hp),
                      sliver: const SliverToBoxAdapter(
                        child: TopPredictionsGrid(),
                      ),
                    ),
                    SliverToBoxAdapter(
                        child: SizedBox(height: Responsive.sp(context, 10))),
                    SliverToBoxAdapter(
                      child: FeaturedCarousel(
                        matches: state.featuredMatches,
                        recommendations: state.filteredRecommendations,
                        allMatches: state.allMatches,
                      ),
                    ),
                    SliverToBoxAdapter(
                        child: SizedBox(height: Responsive.sp(context, 6))),
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
                            fontSize: Responsive.sp(context, 9),
                            fontWeight: FontWeight.w900,
                            letterSpacing: 0.8,
                          ),
                          unselectedLabelStyle: TextStyle(
                            fontSize: Responsive.sp(context, 8),
                            fontWeight: FontWeight.w700,
                          ),
                          labelPadding: EdgeInsets.symmetric(
                              horizontal: Responsive.sp(context, 4)),
                          tabs: const [
                            Tab(text: "ALL"),
                            Tab(text: "LIVE"),
                            Tab(text: "FINISHED"),
                            Tab(text: "SCHEDULED"),
                          ],
                        ),
                        isDark,
                      ),
                    ),
                    SliverFillRemaining(
                      child: TabBarView(
                        controller: _tabController,
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
      itemCount: sortedItems.length + 1,
      itemBuilder: (context, index) {
        final isFooter = index == sortedItems.length;

        return Stack(
          children: [
            if (!isFooter)
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
            if (isFooter)
              const FootnoteSection()
            else
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
  double get minExtent => _tabBar.preferredSize.height + 1;
  @override
  double get maxExtent => _tabBar.preferredSize.height + 1;

  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    final guideLine = Responsive.sp(context, 14);
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
        ClipRect(
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
                    width: 0.5,
                  ),
                ),
              ),
              child: _tabBar,
            ),
          ),
        ),
      ],
    );
  }

  @override
  bool shouldRebuild(_StickyTabBarDelegate oldDelegate) {
    return false;
  }
}

class _CategoryHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double hp;
  final bool isDark;

  _CategoryHeaderDelegate({
    required this.child,
    required this.hp,
    required this.isDark,
  });

  @override
  double get minExtent => 48; // Fixed height optimized for compact UI
  @override
  double get maxExtent => 48;

  // We rewrite to use context in the builder
  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(
          sigmaX: LiquidGlassTheme.blurRadiusMedium,
          sigmaY: LiquidGlassTheme.blurRadiusMedium,
        ),
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: hp,
            vertical: Responsive.sp(context, 4),
          ),
          decoration: BoxDecoration(
            color:
                (isDark ? AppColors.backgroundDark : AppColors.backgroundLight)
                    .withValues(alpha: 0.35),
            border: Border(
              bottom: BorderSide(
                color: isDark
                    ? Colors.white10
                    : Colors.black.withValues(alpha: 0.04),
                width: 0.5,
              ),
            ),
          ),
          child: child,
        ),
      ),
    );
  }

  @override
  bool shouldRebuild(_CategoryHeaderDelegate oldDelegate) {
    return isDark != oldDelegate.isDark || hp != oldDelegate.hp;
  }
}
