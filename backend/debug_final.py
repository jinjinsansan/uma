#!/usr/bin/env python3
"""
最終デバッグ - なぜ3Fタイムがあるのに動作しないのか
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2

def debug_final():
    """最終デバッグ"""
    print("🔍 最終デバッグ開始\n")
    
    # 1. ロードアスタリスクのデータを直接確認
    test_horse = 'ロードアスタリスク'
    print(f"1️⃣ {test_horse}のデータ確認:")
    
    raw_data = local_dlogic_manager_v2.get_horse_raw_data(test_horse)
    if raw_data and raw_data.get('races'):
        print(f"   ✅ データ取得成功: {len(raw_data['races'])}走")
        
        # 最新走のデータ
        latest_race = raw_data['races'][0]
        print("\n   最新走のフィールド確認:")
        
        # 重要フィールドの確認
        important_fields = [
            'KAISAI_NEN', 'KAISAI_GAPPI', 'track_name',
            'RACE_BANGO', 'KAKUTEI_CHAKUJUN', 'SOHA_TIME',
            'ZENHAN_3F_TIME', 'KOHAN_3F_TIME'
        ]
        
        for field in important_fields:
            value = latest_race.get(field, 'キーなし')
            if field in ['ZENHAN_3F_TIME', 'KOHAN_3F_TIME']:
                print(f"      {field}: {value} ← ★3Fタイム")
            else:
                print(f"      {field}: {value}")
        
        # 3Fタイムの値を確認
        print("\n   3Fタイムの実際の値:")
        for i, race in enumerate(raw_data['races'][:3], 1):
            zenhan = race.get('ZENHAN_3F_TIME', '000')
            kohan = race.get('KOHAN_3F_TIME', '000')
            print(f"      第{i}走: 前半3F={zenhan}, 後半3F={kohan}")
    else:
        print(f"   ❌ データなし")
    
    # 2. get_horse_history の動作確認
    print(f"\n2️⃣ get_horse_history メソッドの動作確認:")
    history_result = local_viewlogic_engine_v2.get_horse_history(test_horse, limit=5)
    
    if history_result.get('status') == 'success':
        races = history_result.get('races', [])
        if races:
            first_race = races[0]
            print(f"   ✅ 履歴取得成功: {len(races)}走")
            print(f"   最新走の情報:")
            for key, value in first_race.items():
                print(f"      {key}: {value}")
        else:
            print(f"   ❌ レースデータなし")
    else:
        print(f"   ❌ エラー: {history_result.get('message')}")
    
    # 3. ペース予測のデバッグ
    print(f"\n3️⃣ ペース予測のデバッグ:")
    
    # 小規模なレースデータでテスト
    test_race_data = {
        'venue': '川崎',
        'distance': 1500,
        'horses': [test_horse],
        'horse_numbers': [1]
    }
    
    flow_result = local_viewlogic_engine_v2.predict_race_flow_advanced(test_race_data)
    
    if flow_result.get('status') == 'success':
        pace = flow_result.get('pace_prediction', {})
        print(f"   - 予想ペース: {pace.get('predicted_pace', '不明')}")
        print(f"   - 確信度: {pace.get('confidence', 0)}%")
        
        # デバッグ情報があれば表示
        if 'debug_info' in pace:
            debug = pace['debug_info']
            print(f"   - デバッグ情報:")
            for key, value in debug.items():
                print(f"      {key}: {value}")
    else:
        print(f"   ❌ エラー: {flow_result.get('message')}")
    
    # 4. _advanced_pace_prediction メソッドの存在確認
    print(f"\n4️⃣ ViewLogicエンジンのメソッド確認:")
    
    # メソッドの存在確認
    methods = [
        '_advanced_pace_prediction',
        '_classify_detailed_styles',
        '_calculate_position_stability_all',
        '_calculate_flow_matching',
        '_simulate_race_positions'
    ]
    
    for method_name in methods:
        if hasattr(local_viewlogic_engine_v2, method_name):
            print(f"   ✅ {method_name}: 存在")
        else:
            print(f"   ❌ {method_name}: 存在しない")

if __name__ == "__main__":
    debug_final()