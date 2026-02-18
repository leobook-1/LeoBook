import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/theme/liquid_glass_theme.dart';
import '../../../logic/cubit/home_cubit.dart';
import 'leo_date_picker.dart';

class CategoryBar extends StatefulWidget {
  const CategoryBar({super.key});

  @override
  State<CategoryBar> createState() => _CategoryBarState();
}

class _CategoryBarState extends State<CategoryBar> {
  final ScrollController _scrollController = ScrollController();

  // 4 past + TODAY + 4 future = 9 date items + 1 "More Dates" = 10 total
  static const int _pastDays = 4;
  static const int _futureDays = 4;
  static const int _todayIndex = _pastDays; // index 4
  static const int _totalDates = _pastDays + 1 + _futureDays; // 9
  static const int _totalItems = _totalDates + 1; // 10 (includes More Dates)

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToIndex(_todayIndex);
    });
  }

  void _scrollToIndex(int index) {
    if (!_scrollController.hasClients) return;
    final screenWidth = MediaQuery.of(context).size.width;
    const itemExtent = 98.0;
    final offset = (index * itemExtent) - (screenWidth / 2) + (itemExtent / 2);
    _scrollController.animateTo(
      offset.clamp(0.0, _scrollController.position.maxScrollExtent),
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOut,
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<HomeCubit, HomeState>(
      listener: (context, state) {
        if (state is HomeLoaded) {
          final now = DateTime.now();
          final start = DateTime(now.year, now.month, now.day)
              .subtract(Duration(days: _pastDays));
          final diff = DateTime(
            state.selectedDate.year,
            state.selectedDate.month,
            state.selectedDate.day,
          ).difference(start).inDays;
          if (diff >= 0 && diff < _totalDates) {
            _scrollToIndex(diff);
          }
        }
      },
      builder: (context, state) {
        final selectedDate =
            state is HomeLoaded ? state.selectedDate : DateTime.now();
        final now = DateTime.now();

        return Container(
          height: 44,
          margin: const EdgeInsets.symmetric(vertical: 24),
          child: ListView.separated(
            controller: _scrollController,
            scrollDirection: Axis.horizontal,
            itemCount: _totalItems,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              if (index == _totalDates) {
                return _buildMoreDates(context, selectedDate);
              }

              final date = now.add(Duration(days: index - _pastDays));
              final isYesterday =
                  _isSameDay(date, now.subtract(const Duration(days: 1)));
              final isToday = _isSameDay(date, now);
              final isTomorrow =
                  _isSameDay(date, now.add(const Duration(days: 1)));

              String label;
              if (isYesterday) {
                label = "YESTERDAY";
              } else if (isToday) {
                label = "TODAY";
              } else if (isTomorrow) {
                label = "TOMORROW";
              } else {
                label =
                    "${DateFormat('EEE').format(date).toUpperCase()} ${date.day}";
              }

              return _buildChip(
                context,
                label,
                _isSameDay(selectedDate, date),
                () => context.read<HomeCubit>().updateDate(date),
              );
            },
          ),
        );
      },
    );
  }

  bool _isSameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  Widget _buildChip(
      BuildContext context, String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        constraints: const BoxConstraints(minWidth: 90),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.desktopSearchFill,
          borderRadius:
              BorderRadius.circular(LiquidGlassTheme.borderRadiusSmall),
          border: isSelected
              ? null
              : Border.all(color: LiquidGlassTheme.glassBorderDark),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w900,
              color: isSelected ? Colors.white : AppColors.textGrey,
              letterSpacing: 1.2,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMoreDates(BuildContext context, DateTime current) {
    return GestureDetector(
      onTap: () async {
        // Max 7 days future, unlimited past
        final maxDate = DateTime.now().add(const Duration(days: 7));
        final date = await LeoDatePicker.show(
          context,
          current,
          lastDate: maxDate,
        );
        if (date != null && context.mounted) {
          context.read<HomeCubit>().updateDate(date);
        }
      },
      child: Container(
        constraints: const BoxConstraints(minWidth: 90),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: AppColors.desktopSearchFill,
          borderRadius:
              BorderRadius.circular(LiquidGlassTheme.borderRadiusSmall),
          border: Border.all(color: LiquidGlassTheme.glassBorderDark),
        ),
        child: const Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.calendar_today_rounded,
                  color: AppColors.textGrey, size: 14),
              SizedBox(width: 8),
              Text(
                "MORE DATES",
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  color: AppColors.textGrey,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
