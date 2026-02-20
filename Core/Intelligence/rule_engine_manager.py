# rule_engine_manager.py: Central manager for custom rule engine CRUD + storage.
# Part of LeoBook Core — Intelligence (AI Engine)
#
# Classes: RuleEngineManager
# Called by: Leo.py (--rule-engine), fs_offline.py, Flutter UI

"""
Rule Engine Manager
Central registry for user-defined prediction rule engines.
Each engine has its own weights, scope, learning history, and accuracy stats.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .rule_config import RuleConfig

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENGINES_FILE = PROJECT_ROOT / "Data" / "Store" / "rule_engines.json"

# Default engine weights (mirrors RuleConfig defaults)
DEFAULT_WEIGHTS = {
    "xg_advantage": 3.0,
    "xg_draw": 2.0,
    "h2h_home_win": 3.0,
    "h2h_away_win": 3.0,
    "h2h_draw": 4.0,
    "h2h_over25": 3.0,
    "standings_top_vs_bottom": 6.0,
    "standings_table_advantage": 3.0,
    "standings_gd_strong": 2.0,
    "standings_gd_weak": 2.0,
    "form_score_2plus": 4.0,
    "form_score_3plus": 2.0,
    "form_concede_2plus": 4.0,
    "form_no_score": 5.0,
    "form_clean_sheet": 5.0,
    "form_vs_top_win": 3.0,
}

DEFAULT_PARAMETERS = {
    "h2h_lookback_days": 540,
    "min_form_matches": 3,
    "risk_preference": "conservative",
    "confidence_calibration": {
        "Very High": 0.70,
        "High": 0.60,
        "Medium": 0.50,
        "Low": 0.40,
    },
}


def _make_id(name: str) -> str:
    """Generate a slug-style ID from a name."""
    slug = name.lower().replace(" ", "_").replace("'", "")
    return f"{slug}_{uuid.uuid4().hex[:6]}"


class RuleEngineManager:
    """Central registry for user-defined prediction rule engines."""

    @staticmethod
    def _load_all() -> List[Dict[str, Any]]:
        """Load all engines from disk."""
        if not ENGINES_FILE.exists():
            return []
        try:
            with open(ENGINES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _save_all(engines: List[Dict[str, Any]]) -> None:
        """Save all engines to disk."""
        os.makedirs(ENGINES_FILE.parent, exist_ok=True)
        with open(ENGINES_FILE, "w", encoding="utf-8") as f:
            json.dump(engines, f, indent=2)

    @staticmethod
    def _ensure_default_exists() -> List[Dict[str, Any]]:
        """Ensure at least a 'Default' engine exists."""
        engines = RuleEngineManager._load_all()
        if not engines:
            default_engine = {
                "id": "default",
                "name": "Default",
                "description": "Standard LeoBook prediction logic",
                "created_at": datetime.utcnow().isoformat(),
                "is_default": True,
                "scope": {"type": "global", "leagues": [], "teams": []},
                "weights": DEFAULT_WEIGHTS.copy(),
                "parameters": DEFAULT_PARAMETERS.copy(),
                "accuracy": {
                    "total_predictions": 0,
                    "correct": 0,
                    "win_rate": 0.0,
                    "last_backtested": None,
                    "backtest_period": None,
                },
            }
            engines = [default_engine]
            RuleEngineManager._save_all(engines)
        return engines

    # ── CRUD ──────────────────────────────────────────────

    @staticmethod
    def list_engines() -> List[Dict[str, Any]]:
        """List all saved rule engines."""
        return RuleEngineManager._ensure_default_exists()

    @staticmethod
    def get_engine(engine_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific engine by ID."""
        engines = RuleEngineManager._ensure_default_exists()
        for e in engines:
            if e["id"] == engine_id:
                return e
        return None

    @staticmethod
    def get_default() -> Dict[str, Any]:
        """Get the current default engine."""
        engines = RuleEngineManager._ensure_default_exists()
        for e in engines:
            if e.get("is_default"):
                return e
        # Fallback: first engine
        return engines[0]

    @staticmethod
    def set_default(engine_id: str) -> bool:
        """Mark an engine as the default (unmarks all others)."""
        engines = RuleEngineManager._ensure_default_exists()
        found = False
        for e in engines:
            if e["id"] == engine_id:
                e["is_default"] = True
                found = True
            else:
                e["is_default"] = False
        if found:
            RuleEngineManager._save_all(engines)
        return found

    @staticmethod
    def create_engine(
        name: str,
        description: str = "",
        weights: Optional[Dict[str, float]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new rule engine and save to disk."""
        engines = RuleEngineManager._ensure_default_exists()

        engine = {
            "id": _make_id(name),
            "name": name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "is_default": False,
            "scope": scope or {"type": "global", "leagues": [], "teams": []},
            "weights": {**DEFAULT_WEIGHTS, **(weights or {})},
            "parameters": {**DEFAULT_PARAMETERS, **(parameters or {})},
            "accuracy": {
                "total_predictions": 0,
                "correct": 0,
                "win_rate": 0.0,
                "last_backtested": None,
                "backtest_period": None,
            },
        }
        engines.append(engine)
        RuleEngineManager._save_all(engines)
        return engine

    @staticmethod
    def update_engine(engine_id: str, updates: Dict[str, Any]) -> bool:
        """Update fields on an existing engine."""
        engines = RuleEngineManager._ensure_default_exists()
        for e in engines:
            if e["id"] == engine_id:
                for key, val in updates.items():
                    if key == "weights" and isinstance(val, dict):
                        e.setdefault("weights", {}).update(val)
                    elif key == "parameters" and isinstance(val, dict):
                        e.setdefault("parameters", {}).update(val)
                    elif key == "accuracy" and isinstance(val, dict):
                        e.setdefault("accuracy", {}).update(val)
                    elif key == "scope" and isinstance(val, dict):
                        e["scope"] = val
                    else:
                        e[key] = val
                RuleEngineManager._save_all(engines)
                return True
        return False

    @staticmethod
    def delete_engine(engine_id: str) -> bool:
        """Delete an engine. Cannot delete the last remaining engine."""
        engines = RuleEngineManager._ensure_default_exists()
        if len(engines) <= 1:
            return False
        original_len = len(engines)
        engines = [e for e in engines if e["id"] != engine_id]
        if len(engines) == original_len:
            return False
        # If we deleted the default, make the first remaining engine default
        if not any(e.get("is_default") for e in engines):
            engines[0]["is_default"] = True
        RuleEngineManager._save_all(engines)
        return True

    # ── Conversion ────────────────────────────────────────

    @staticmethod
    def to_rule_config(engine: Dict[str, Any]) -> RuleConfig:
        """Convert a stored engine dict to a RuleConfig for the prediction engine."""
        weights = engine.get("weights", {})
        params = engine.get("parameters", {})
        scope = engine.get("scope", {})

        return RuleConfig(
            id=engine.get("id", "default"),
            name=engine.get("name", "Default"),
            description=engine.get("description", ""),
            # Weights
            xg_advantage=weights.get("xg_advantage", 3.0),
            xg_draw=weights.get("xg_draw", 2.0),
            h2h_home_win=weights.get("h2h_home_win", 3.0),
            h2h_away_win=weights.get("h2h_away_win", 3.0),
            h2h_draw=weights.get("h2h_draw", 4.0),
            h2h_over25=weights.get("h2h_over25", 3.0),
            standings_top_vs_bottom=weights.get("standings_top_vs_bottom", 6.0),
            standings_table_advantage=weights.get("standings_table_advantage", 3.0),
            standings_gd_strong=weights.get("standings_gd_strong", 2.0),
            standings_gd_weak=weights.get("standings_gd_weak", 2.0),
            form_score_2plus=weights.get("form_score_2plus", 4.0),
            form_score_3plus=weights.get("form_score_3plus", 2.0),
            form_concede_2plus=weights.get("form_concede_2plus", 4.0),
            form_no_score=weights.get("form_no_score", 5.0),
            form_clean_sheet=weights.get("form_clean_sheet", 5.0),
            form_vs_top_win=weights.get("form_vs_top_win", 3.0),
            # Parameters
            h2h_lookback_days=params.get("h2h_lookback_days", 540),
            min_form_matches=params.get("min_form_matches", 3),
            risk_preference=params.get("risk_preference", "conservative"),
            # Scope
            scope_type=scope.get("type", "global"),
            scope_leagues=scope.get("leagues", []),
            scope_teams=scope.get("teams", []),
        )

    # ── Display ───────────────────────────────────────────

    @staticmethod
    def print_engine(engine: Dict[str, Any]) -> None:
        """Pretty-print a single engine to console."""
        acc = engine.get("accuracy", {})
        win_rate = acc.get("win_rate", 0)
        total = acc.get("total_predictions", 0)
        correct = acc.get("correct", 0)
        scope = engine.get("scope", {})
        scope_type = scope.get("type", "global")
        is_default = "⭐ DEFAULT" if engine.get("is_default") else ""

        print(f"\n   {'─' * 50}")
        print(f"   📋 {engine['name']}  {is_default}")
        print(f"   ID: {engine['id']}")
        if engine.get("description"):
            print(f"   Description: {engine['description']}")
        print(f"   Scope: {scope_type.upper()}", end="")
        if scope.get("leagues"):
            print(f" | Leagues: {', '.join(scope['leagues'][:5])}", end="")
        if scope.get("teams"):
            print(f" | Teams: {', '.join(scope['teams'][:5])}", end="")
        print()
        print(f"   Accuracy: {win_rate:.1f}% ({correct}/{total} predictions)")
        last_bt = acc.get("last_backtested")
        if last_bt:
            print(f"   Last Backtested: {last_bt}")
        print(f"   Risk: {engine.get('parameters', {}).get('risk_preference', 'conservative')}")
        print(f"   {'─' * 50}")

    @staticmethod
    def print_engine_list() -> None:
        """Print all engines in a table format."""
        engines = RuleEngineManager.list_engines()
        print(f"\n   {'─' * 60}")
        print(f"   {'Name':<25} {'Accuracy':<12} {'Scope':<10} {'Default':<8}")
        print(f"   {'─' * 60}")
        for e in engines:
            acc = e.get("accuracy", {})
            win_rate = acc.get("win_rate", 0)
            total = acc.get("total_predictions", 0)
            scope_type = e.get("scope", {}).get("type", "global")
            default_flag = "⭐" if e.get("is_default") else ""
            acc_str = f"{win_rate:.1f}% ({total})" if total > 0 else "—"
            print(f"   {e['name']:<25} {acc_str:<12} {scope_type:<10} {default_flag:<8}")
        print(f"   {'─' * 60}")
        print(f"   Total: {len(engines)} engine(s)\n")
