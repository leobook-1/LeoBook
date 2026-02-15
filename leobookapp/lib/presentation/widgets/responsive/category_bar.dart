import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../logic/cubit/home_cubit.dart';
import 'leo_date_picker.dart';

class CategoryBar extends StatelessWidget {
  const CategoryBar({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<HomeCubit, HomeState>(
      builder: (context, state) {
        final selectedDate = state is HomeLoaded ? state.selectedDate : DateTime.now();
        
        return Container(
          height: 44,
          margin: const EdgeInsets.symmetric(vertical: 24),
          child: Row(
            children: [
              Expanded(
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _buildChip(context, "TODAY", _isSameDay(selectedDate, DateTime.now()), () {
                      context.read<HomeCubit>().updateDate(DateTime.now());
                    }),
                    const SizedBox(width: 12),
                    _buildChip(context, "TOMORROW", _isSameDay(selectedDate, DateTime.now().add(const Duration(days: 1))), () {
                      context.read<HomeCubit>().updateDate(DateTime.now().add(const Duration(days: 1)));
                    }),
                    const SizedBox(width: 12),
                    ...List.generate(5, (index) {
                      final date = DateTime.now().add(Duration(days: index + 2));
                      final label = "${DateFormat('EEE').format(date).toUpperCase()} ${date.day}";
                      final isSelected = _isSameDay(selectedDate, date);
                      
                      return Padding(
                        padding: const EdgeInsets.only(right: 12),
                        child: _buildChip(context, label, isSelected, () {
                          context.read<HomeCubit>().updateDate(date);
                        }),
                      );
                    }),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              _buildMoreDates(context, selectedDate),
            ],
          ),
        );
      },
    );
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  Widget _buildChip(BuildContext context, String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 24),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.desktopSearchFill,
          borderRadius: BorderRadius.circular(10),
          border: isSelected ? null : Border.all(color: Colors.white.withValues(alpha: 0.05)),
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
        final date = await LeoDatePicker.show(context, current);
        if (date != null && context.mounted) {
          context.read<HomeCubit>().updateDate(date);
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: AppColors.desktopSearchFill,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
        ),
        child: const Row(
          children: [
            Icon(Icons.calendar_today_rounded, color: AppColors.textGrey, size: 14),
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
    );
  }
}
