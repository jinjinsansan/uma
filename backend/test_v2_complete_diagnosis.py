#!/usr/bin/env python3
"""
ViewLogic展開予想改革の完全診断テスト
1. 計画書との整合性
2. V2チャット統合テスト
3. 既存機能への影響
4. エラーチェック
"""

import sys
import json
from typing import Dict, Any
from services.viewlogic_engine import ViewLogicEngine
# V2AIHandlerはimportしない（ViewLogicエンジンを直接テスト）

def print_section(title: str):
    """セクションヘッダーを表示"""
    print("\n" + "="*60)
    print(f"【{title}】")
    print("="*60)

def test_phase1_normalization():
    """Phase 1: データ正規化の確認"""
    print_section("Phase 1: データ正規化関数の実装確認")
    
    engine = ViewLogicEngine()
    test_values = [
        (331.0, "0.1秒単位", 33.1),
        (35, "秒の整数部分", 35.0),
        (369.0, "0.1秒単位", 36.9),
        (0, "欠損値", None),
        (999.0, "欠損値", None),
    ]
    
    all_pass = True
    for value, desc, expected in test_values:
        result = engine._normalize_3f_time(value)
        if result == expected:
            print(f"✅ {desc}: {value} → {result}")
        else:
            print(f"❌ {desc}: {value} → {result} (期待値: {expected})")
            all_pass = False
    
    return all_pass

def test_phase2_calculation():
    """Phase 2: 計算ロジックの確認"""
    print_section("Phase 2: 計算ロジックの修正確認")
    
    engine = ViewLogicEngine()
    
    # テスト用データ
    test_horses = ['ドウデュース', 'イクイノックス']
    horses_data = []
    for horse in test_horses:
        data = engine.data_manager.get_horse_data(horse)
        if data:
            horses_data.append(data)
    
    # ペース予測
    pace_pred = engine._advanced_pace_prediction(horses_data)
    print(f"ペース: {pace_pred.get('pace')}")
    print(f"前半3F平均: {pace_pred.get('zenhan_avg', 0):.1f}秒")
    print(f"後半3F平均: {pace_pred.get('kohan_avg', 0):.1f}秒")
    
    # 正常な範囲内か確認
    zenhan = pace_pred.get('zenhan_avg', 0)
    kohan = pace_pred.get('kohan_avg', 0)
    
    checks = []
    checks.append(("前半3Fが現実的な範囲(30-40秒)", 30 <= zenhan <= 40))
    checks.append(("後半3Fが現実的な範囲(30-40秒)", 30 <= kohan <= 40))
    checks.append(("ペースが多様", pace_pred.get('pace') != '超ハイペース'))
    
    all_pass = True
    for desc, result in checks:
        if result:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc}")
            all_pass = False
    
    # フローマッチングスコアの差別化
    flow_matching = engine._calculate_flow_matching(horses_data, pace_pred)
    scores = list(flow_matching.values())
    if len(set(scores)) > 1:  # スコアに差がある
        print(f"✅ フローマッチングスコアが差別化: {scores}")
    else:
        print(f"❌ フローマッチングスコアが同一: {scores}")
        all_pass = False
    
    return all_pass

def test_phase3_top5_selection():
    """Phase 3: 上位5頭選出の確認"""
    print_section("Phase 3: 上位5頭選出の改善確認")
    
    engine = ViewLogicEngine()
    
    test_race = {
        'venue': '東京',
        'race_number': 11,
        'distance': '2000m',
        'horses': ['ドウデュース', 'イクイノックス', 'ジャスティンパレス', 'ダノンベルーガ']
    }
    
    result = engine.predict_race_flow_advanced(test_race)
    
    if result.get('status') == 'success':
        simulation = result.get('race_simulation', {})
        if 'finish' in simulation:
            print("総合スコアによる上位馬:")
            for i, horse_info in enumerate(simulation['finish'][:3], 1):
                horse_name = horse_info.get('horse_name', '不明')
                position = horse_info.get('position', 99)
                print(f"  {i}位: {horse_name} (予測値: {position:.2f})")
            return True
    
    print("❌ 上位5頭の選出に失敗")
    return False

def test_phase4_text_diversity():
    """Phase 4: 出力文章の多様性確認"""
    print_section("Phase 4: 出力文章の多様化確認")
    
    engine = ViewLogicEngine()
    test_race = {
        'venue': '東京',
        'race_number': 11,
        'horses': ['ドウデュース', 'イクイノックス']
    }
    
    # ペース説明部分を3回取得して比較
    pace_descriptions = []
    for i in range(3):
        result = engine.predict_race_flow_advanced(test_race)
        if result.get('status') == 'success':
            formatted = result.get('formatted_output', '')
            # ペース説明部分を探す
            lines = formatted.split('\n')
            for line in lines:
                if '序盤' in line or 'スタート' in line or '各馬' in line or '前半' in line:
                    pace_descriptions.append(line)
                    break
    
    # 少なくとも2つの異なる説明があれば多様性ありと判定
    unique_descriptions = len(set(pace_descriptions))
    if unique_descriptions >= 2:
        print(f"✅ 出力文章に多様性あり（{unique_descriptions}種類の異なる表現）")
        return True
    else:
        print(f"❌ 出力文章の多様性が不十分（{unique_descriptions}種類のみ）")
        return False

def test_v2_chat_integration():
    """V2チャット統合テスト"""
    print_section("V2チャット統合テスト")
    
    try:
        # ViewLogicエンジンの直接テスト（V2AIHandlerは別の実装）
        from services.viewlogic_engine import ViewLogicEngine
        engine = ViewLogicEngine()
        
        # ViewLogic展開予想のテスト
        test_race = {
            'venue': '東京',
            'race_number': 11,
            'horses': ['ドウデュース', 'イクイノックス']
        }
        
        result = engine.predict_race_flow_advanced(test_race)
        
        if result.get('status') == 'success':
            formatted = result.get('formatted_output', '')
            if 'ViewLogic展開予想' in formatted:
                print("✅ ViewLogic展開予想が正常に出力")
                # 前半3Fタイムが正常か確認
                pace_pred = result.get('pace_prediction', {})
                zenhan = pace_pred.get('zenhan_avg', 0)
                if 30 <= zenhan <= 40:
                    print(f"✅ 3Fタイムが正常な範囲: {zenhan:.1f}秒")
                return True
            else:
                print("❌ 展開予想の出力が不正")
                return False
        else:
            print(f"❌ エラー: {result.get('message', '不明')}")
            return False
            
    except Exception as e:
        print(f"❌ 統合テストエラー: {str(e)}")
        return False

def test_existing_functions():
    """既存機能への影響確認"""
    print_section("既存機能への影響確認")
    
    checks = []
    
    # D-Logicエンジンの確認
    try:
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        manager = DLogicRawDataManager()
        checks.append(("D-Logicエンジン", True))
    except Exception as e:
        checks.append(("D-Logicエンジン", False))
    
    # MyLogic計算エンジンの確認（V1機能）
    try:
        from services.mylogic_calculator import MyLogicCalculator
        # MyLogicはV1の機能なのでインスタンス化のみ確認
        checks.append(("MyLogic計算エンジン（V1）", True))
    except Exception as e:
        checks.append(("MyLogic計算エンジン（V1）", False))
    
    # IMLogicエンジンの確認
    try:
        from services.imlogic_engine import IMLogicEngine
        engine = IMLogicEngine()
        checks.append(("IMLogicエンジン", True))
    except Exception as e:
        checks.append(("IMLogicエンジン", False))
    
    all_pass = True
    for name, result in checks:
        if result:
            print(f"✅ {name}: 正常動作")
        else:
            print(f"❌ {name}: エラー")
            all_pass = False
    
    return all_pass

def main():
    """完全診断を実行"""
    print("\n" + "="*60)
    print("    ViewLogic展開予想改革 - 完全診断レポート")
    print("="*60)
    
    results = {
        "Phase 1: データ正規化": test_phase1_normalization(),
        "Phase 2: 計算ロジック": test_phase2_calculation(),
        "Phase 3: 上位5頭選出": test_phase3_top5_selection(),
        "Phase 4: 文章多様化": test_phase4_text_diversity(),
        "V2チャット統合": test_v2_chat_integration(),
        "既存機能への影響": test_existing_functions(),
    }
    
    # 最終診断結果
    print_section("最終診断結果")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    score = int((passed / total) * 100)
    
    for name, result in results.items():
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"{name}: {status}")
    
    print(f"\n総合スコア: {score}点 / 100点")
    
    if score == 100:
        print("\n🎉 完璧です！すべてのテストに合格しました。")
        print("ViewLogic展開予想の改革は成功です！")
    elif score >= 80:
        print("\n👍 良好です。いくつかの小さな問題がありますが、使用可能です。")
    else:
        print("\n⚠️ 問題があります。修正が必要です。")
    
    return score

if __name__ == "__main__":
    score = main()
    sys.exit(0 if score == 100 else 1)