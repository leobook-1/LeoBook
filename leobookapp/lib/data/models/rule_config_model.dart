// rule_config_model.dart: Data model for custom prediction rule engines.
// Part of LeoBook App — Data Models
//
// Classes: RuleEngineAccuracy, RuleEngineScope, RuleConfigModel

/// Accuracy stats for a rule engine.
class RuleEngineAccuracy {
  final int totalPredictions;
  final int correct;
  final double winRate;
  final String? lastBacktested;
  final String? backtestPeriod;

  const RuleEngineAccuracy({
    this.totalPredictions = 0,
    this.correct = 0,
    this.winRate = 0.0,
    this.lastBacktested,
    this.backtestPeriod,
  });

  factory RuleEngineAccuracy.fromJson(Map<String, dynamic> json) {
    return RuleEngineAccuracy(
      totalPredictions: json['total_predictions'] ?? 0,
      correct: json['correct'] ?? 0,
      winRate: (json['win_rate'] ?? 0.0).toDouble(),
      lastBacktested: json['last_backtested'],
      backtestPeriod: json['backtest_period'],
    );
  }

  Map<String, dynamic> toJson() => {
        'total_predictions': totalPredictions,
        'correct': correct,
        'win_rate': winRate,
        'last_backtested': lastBacktested,
        'backtest_period': backtestPeriod,
      };
}

/// Scope definition for a rule engine.
class RuleEngineScope {
  final String type; // "global" | "league" | "team"
  final List<String> leagues;
  final List<String> teams;

  const RuleEngineScope({
    this.type = 'global',
    this.leagues = const [],
    this.teams = const [],
  });

  factory RuleEngineScope.fromJson(Map<String, dynamic> json) {
    return RuleEngineScope(
      type: json['type'] ?? 'global',
      leagues: List<String>.from(json['leagues'] ?? []),
      teams: List<String>.from(json['teams'] ?? []),
    );
  }

  Map<String, dynamic> toJson() => {
        'type': type,
        'leagues': leagues,
        'teams': teams,
      };

  String get displayLabel {
    if (type == 'league' && leagues.isNotEmpty) {
      return leagues.length == 1 ? leagues.first : '${leagues.length} leagues';
    }
    if (type == 'team' && teams.isNotEmpty) {
      return teams.length == 1 ? teams.first : '${teams.length} teams';
    }
    return 'Global';
  }
}

/// Full rule engine model matching the backend `rule_engines.json` schema.
class RuleConfigModel {
  String id;
  String name;
  String description;
  String? createdAt;
  bool isDefault;
  RuleEngineScope scope;
  RuleEngineAccuracy accuracy;

  // Weights (0-10 scale)
  double xgAdvantage;
  double xgDraw;
  double h2hHomeWin;
  double h2hAwayWin;
  double h2hDraw;
  double h2hOver25;
  double standingsTopBottom;
  double standingsTableAdv;
  double standingsGdStrong;
  double standingsGdWeak;
  double formScore2plus;
  double formScore3plus;
  double formConcede2plus;
  double formNoScore;
  double formCleanSheet;
  double formVsTopWin;

  // Parameters
  int h2hLookbackDays;
  int minFormMatches;
  String riskPreference;

  RuleConfigModel({
    this.id = 'default',
    this.name = 'Default',
    this.description = 'Standard LeoBook prediction logic',
    this.createdAt,
    this.isDefault = false,
    this.scope = const RuleEngineScope(),
    this.accuracy = const RuleEngineAccuracy(),
    this.xgAdvantage = 3.0,
    this.xgDraw = 2.0,
    this.h2hHomeWin = 3.0,
    this.h2hAwayWin = 3.0,
    this.h2hDraw = 4.0,
    this.h2hOver25 = 3.0,
    this.standingsTopBottom = 6.0,
    this.standingsTableAdv = 3.0,
    this.standingsGdStrong = 2.0,
    this.standingsGdWeak = 2.0,
    this.formScore2plus = 4.0,
    this.formScore3plus = 2.0,
    this.formConcede2plus = 4.0,
    this.formNoScore = 5.0,
    this.formCleanSheet = 5.0,
    this.formVsTopWin = 3.0,
    this.h2hLookbackDays = 540,
    this.minFormMatches = 3,
    this.riskPreference = 'conservative',
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_at': createdAt,
      'is_default': isDefault,
      'scope': scope.toJson(),
      'weights': {
        'xg_advantage': xgAdvantage,
        'xg_draw': xgDraw,
        'h2h_home_win': h2hHomeWin,
        'h2h_away_win': h2hAwayWin,
        'h2h_draw': h2hDraw,
        'h2h_over25': h2hOver25,
        'standings_top_vs_bottom': standingsTopBottom,
        'standings_table_advantage': standingsTableAdv,
        'standings_gd_strong': standingsGdStrong,
        'standings_gd_weak': standingsGdWeak,
        'form_score_2plus': formScore2plus,
        'form_score_3plus': formScore3plus,
        'form_concede_2plus': formConcede2plus,
        'form_no_score': formNoScore,
        'form_clean_sheet': formCleanSheet,
        'form_vs_top_win': formVsTopWin,
      },
      'parameters': {
        'h2h_lookback_days': h2hLookbackDays,
        'min_form_matches': minFormMatches,
        'risk_preference': riskPreference,
      },
      'accuracy': accuracy.toJson(),
    };
  }

  factory RuleConfigModel.fromJson(Map<String, dynamic> json) {
    final weights = json['weights'] as Map<String, dynamic>? ??
        json['logic'] as Map<String, dynamic>? ??
        {};
    final params = json['parameters'] as Map<String, dynamic>? ?? {};

    return RuleConfigModel(
      id: json['id'] ?? 'default',
      name: json['name'] ?? 'Custom Rule',
      description: json['description'] ?? '',
      createdAt: json['created_at'],
      isDefault: json['is_default'] ?? false,
      scope: RuleEngineScope.fromJson(json['scope'] ?? {}),
      accuracy: RuleEngineAccuracy.fromJson(json['accuracy'] ?? {}),
      xgAdvantage: (weights['xg_advantage'] ?? 3.0).toDouble(),
      xgDraw: (weights['xg_draw'] ?? 2.0).toDouble(),
      h2hHomeWin: (weights['h2h_home_win'] ?? 3.0).toDouble(),
      h2hAwayWin: (weights['h2h_away_win'] ?? 3.0).toDouble(),
      h2hDraw: (weights['h2h_draw'] ?? 4.0).toDouble(),
      h2hOver25: (weights['h2h_over25'] ?? 3.0).toDouble(),
      standingsTopBottom:
          (weights['standings_top_vs_bottom'] ?? 6.0).toDouble(),
      standingsTableAdv:
          (weights['standings_table_advantage'] ?? 3.0).toDouble(),
      standingsGdStrong: (weights['standings_gd_strong'] ?? 2.0).toDouble(),
      standingsGdWeak: (weights['standings_gd_weak'] ?? 2.0).toDouble(),
      formScore2plus: (weights['form_score_2plus'] ?? 4.0).toDouble(),
      formScore3plus: (weights['form_score_3plus'] ?? 2.0).toDouble(),
      formConcede2plus: (weights['form_concede_2plus'] ?? 4.0).toDouble(),
      formNoScore: (weights['form_no_score'] ?? 5.0).toDouble(),
      formCleanSheet: (weights['form_clean_sheet'] ?? 5.0).toDouble(),
      formVsTopWin: (weights['form_vs_top_win'] ?? 3.0).toDouble(),
      h2hLookbackDays: params['h2h_lookback_days'] ?? 540,
      minFormMatches: params['min_form_matches'] ?? 3,
      riskPreference: params['risk_preference'] ?? 'conservative',
    );
  }

  /// Copy with modifications.
  RuleConfigModel copyWith({
    String? id,
    String? name,
    String? description,
    bool? isDefault,
    RuleEngineScope? scope,
    String? riskPreference,
  }) {
    final copy = RuleConfigModel.fromJson(toJson());
    if (id != null) copy.id = id;
    if (name != null) copy.name = name;
    if (description != null) copy.description = description;
    if (isDefault != null) copy.isDefault = isDefault;
    if (scope != null) copy.scope = scope;
    if (riskPreference != null) copy.riskPreference = riskPreference;
    return copy;
  }
}
