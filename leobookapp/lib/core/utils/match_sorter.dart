import 'package:leobookapp/data/models/match_model.dart';

enum MatchTabType { all, finished, scheduled }

class MatchSorter {
  static List<dynamic> getSortedMatches(
    List<MatchModel> matches,
    MatchTabType type,
  ) {
    switch (type) {
      case MatchTabType.all:
        return _groupAllMatches(matches);
      case MatchTabType.finished:
        return _sortFinishedMatches(matches);
      case MatchTabType.scheduled:
        return _sortScheduledMatches(matches);
    }
  }

  static List<dynamic> _groupAllMatches(List<MatchModel> matches) {
    if (matches.isEmpty) return [];

    // Group by Region/League
    final Map<String, List<MatchModel>> groups = {};
    for (var match in matches) {
      final key = match.league?.trim() ?? "Other";
      if (!groups.containsKey(key)) {
        groups[key] = [];
      }
      groups[key]!.add(match);
    }

    // Sort Keys Alphabetically
    final sortedKeys = groups.keys.toList()..sort();

    final List<dynamic> result = [];
    for (var key in sortedKeys) {
      // Sort matches within group: Time -> Alphabetical (Home Team)
      final groupMatches = groups[key]!;
      groupMatches.sort((a, b) {
        int timeComp = a.time.compareTo(b.time);
        if (timeComp != 0) return timeComp;
        return a.homeTeam.compareTo(b.homeTeam);
      });

      result.add(MatchGroupHeader(title: key));
      result.addAll(groupMatches);
    }
    return result;
  }

  static List<MatchModel> _sortFinishedMatches(List<MatchModel> matches) {
    return matches
        .where(
          (m) =>
              m.status.toLowerCase().contains('finish') ||
              m.status.toLowerCase().contains('ft') ||
              m.status.toLowerCase().contains('full time'),
        )
        .toList()
      ..sort((a, b) {
        // Latest first -> Date DESC -> Time DESC
        int dateComp = b.date.compareTo(a.date);
        if (dateComp != 0) return dateComp;
        return b.time.compareTo(a.time);
      });
  }

  static List<MatchModel> _sortScheduledMatches(List<MatchModel> matches) {
    return matches
        .where(
          (m) =>
              !m.isLive &&
              !m.status.toLowerCase().contains('finish') &&
              !m.status.toLowerCase().contains('ft'),
        )
        .toList()
      ..sort((a, b) {
        // Earliest first -> Date ASC -> Time ASC
        int dateComp = a.date.compareTo(b.date);
        if (dateComp != 0) return dateComp;
        return a.time.compareTo(b.time);
      });
  }
}

class MatchGroupHeader {
  final String title;
  MatchGroupHeader({required this.title});
}
