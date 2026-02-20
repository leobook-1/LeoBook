// leo_service.dart: File I/O service for rule engine management.
// Part of LeoBook App — Services
//
// Classes: LeoService

import 'dart:convert';
import 'dart:io';
import '../models/rule_config_model.dart';

class LeoService {
  static const String _storePath =
      r'C:\Users\Admin\Desktop\ProProjection\LeoBook\Data\Store';
  static const String _enginesFile = '$_storePath\\rule_engines.json';

  // ── Rule Engine CRUD ─────────────────────────────

  /// Load all rule engines from rule_engines.json.
  Future<List<RuleConfigModel>> loadAllEngines() async {
    final file = File(_enginesFile);
    if (!await file.exists()) {
      // Create default engine if file doesn't exist
      final defaultEngine = RuleConfigModel(
        id: 'default',
        name: 'Default',
        description: 'Standard LeoBook prediction logic',
        isDefault: true,
      );
      await saveAllEngines([defaultEngine]);
      return [defaultEngine];
    }
    final jsonString = await file.readAsString();
    final List<dynamic> list = jsonDecode(jsonString);
    return list.map((e) => RuleConfigModel.fromJson(e)).toList();
  }

  /// Save all engines to rule_engines.json.
  Future<void> saveAllEngines(List<RuleConfigModel> engines) async {
    final file = File(_enginesFile);
    await file.writeAsString(
      jsonEncode(engines.map((e) => e.toJson()).toList()),
    );
  }

  /// Get the current default engine.
  Future<RuleConfigModel> getDefaultEngine() async {
    final engines = await loadAllEngines();
    return engines.firstWhere(
      (e) => e.isDefault,
      orElse: () => engines.first,
    );
  }

  /// Save a single engine (creates or updates).
  Future<void> saveEngine(RuleConfigModel engine) async {
    final engines = await loadAllEngines();
    final idx = engines.indexWhere((e) => e.id == engine.id);
    if (idx >= 0) {
      engines[idx] = engine;
    } else {
      engines.add(engine);
    }
    await saveAllEngines(engines);
  }

  /// Set an engine as default (unmarks all others).
  Future<void> setDefaultEngine(String engineId) async {
    final engines = await loadAllEngines();
    for (final e in engines) {
      e.isDefault = e.id == engineId;
    }
    await saveAllEngines(engines);
  }

  /// Delete an engine by ID. Cannot delete the last one.
  Future<bool> deleteEngine(String engineId) async {
    final engines = await loadAllEngines();
    if (engines.length <= 1) return false;
    engines.removeWhere((e) => e.id == engineId);
    // Ensure one is default
    if (!engines.any((e) => e.isDefault)) {
      engines.first.isDefault = true;
    }
    await saveAllEngines(engines);
    return true;
  }

  // ── Legacy compatibility ─────────────────────────

  Future<void> saveRuleConfig(RuleConfigModel config) async {
    await saveEngine(config);
  }

  Future<RuleConfigModel> loadRuleConfig() async {
    return getDefaultEngine();
  }

  Future<void> triggerBacktest(RuleConfigModel config) async {
    await saveEngine(config);
    final triggerFile = File('$_storePath\\trigger_backtest.json');
    await triggerFile.writeAsString(
      jsonEncode({
        'timestamp': DateTime.now().toIso8601String(),
        'config_name': config.name,
        'engine_id': config.id,
      }),
    );
  }

  Future<List<Map<String, dynamic>>> getBacktestResults(
    String configName,
  ) async {
    // Try new format first (backtest_{id}.csv), then legacy
    for (final prefix in ['backtest_', 'predictions_custom_']) {
      final file = File('$_storePath\\$prefix$configName.csv');
      if (await file.exists()) return _parseCsv(file);
    }
    return [];
  }

  Future<List<Map<String, dynamic>>> _parseCsv(File file) async {
    final lines = await file.readAsLines();
    if (lines.isEmpty) return [];
    final headers = lines.first.split(',');
    return [
      for (var i = 1; i < lines.length; i++)
        {
          for (var j = 0; j < headers.length; j++)
            headers[j]:
                j < lines[i].split(',').length ? lines[i].split(',')[j] : '',
        },
    ];
  }
}
