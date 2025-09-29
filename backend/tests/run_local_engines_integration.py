#!/usr/bin/env python3
"""簡易統合テスト: 地方競馬用ローカルエンジン群を一巡させる"""

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def load_race_fixture() -> dict:
    from tests.fixtures.local_race_sample import RACE_DATA

    # defensive copy to avoid accidental mutation between engines
    return {k: (v.copy() if isinstance(v, list) else v) for k, v in RACE_DATA.items()}


def main() -> int:
    race_data = load_race_fixture()
    failures = []

    # IMLogic
    try:
        from services.local_imlogic_engine_v2 import local_imlogic_engine_v2

        imlogic_result = local_imlogic_engine_v2.analyze_race(race_data)
        if imlogic_result.get("status") != "success":
            failures.append("IMLogic: status != success")
        elif not (imlogic_result.get("results") or imlogic_result.get("scores")):
            failures.append("IMLogic: no results")
    except Exception as exc:  # pragma: no cover - diagnostic output
        failures.append(f"IMLogic exception: {exc}")

    # MetaLogic
    try:
        from services.local_metalogic_engine_v2 import local_metalogic_engine_v2

        metalogic_result = local_metalogic_engine_v2.analyze_race(race_data)
        if metalogic_result.get("status") != "success":
            failures.append("MetaLogic: status != success")
        elif not metalogic_result.get("rankings"):
            failures.append("MetaLogic: no rankings")
    except Exception as exc:  # pragma: no cover
        failures.append(f"MetaLogic exception: {exc}")

    # ViewLogic (コース傾向)
    try:
        from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2

        trend_result = local_viewlogic_engine_v2.analyze_course_trend(race_data)
        if trend_result.get("status") != "success":
            failures.append("ViewLogic trend: status != success")
        elif not (trend_result.get("trends") or trend_result.get("insights")):
            failures.append("ViewLogic trend: empty payload")
    except Exception as exc:  # pragma: no cover
        failures.append(f"ViewLogic exception: {exc}")

    # F-Logic（市場オッズ連携）
    try:
        from services.local_flogic_engine_v2 import local_flogic_engine_v2

        market_odds = {
            horse: odds
            for horse, odds in zip(race_data.get("horses", []), race_data.get("odds", []))
            if odds and odds > 0
        }
        flogic_result = local_flogic_engine_v2.analyze_race(race_data, market_odds)
        if flogic_result.get("status") != "success":
            failures.append("F-Logic: status != success")
        elif not flogic_result.get("rankings"):
            failures.append("F-Logic: no rankings")
    except Exception as exc:  # pragma: no cover
        failures.append(f"F-Logic exception: {exc}")

    if failures:
        print("❌ ローカル統合テストに失敗しました:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("✅ ローカル統合テスト完了 (IMLogic / MetaLogic / ViewLogic / F-Logic)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
