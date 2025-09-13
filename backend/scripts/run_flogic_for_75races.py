#!/usr/bin/env python3
"""
F-Logic予想実行スクリプト（8月31日〜9月7日の65レース）
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# パスを追加
sys.path.append('/mnt/e/dev/Cusor/chatbot/uma/backend')
from services.flogic_engine import FLogicEngine

# .envファイルの読み込み
load_dotenv('/mnt/e/dev/Cusor/front/d-logic-ai-frontend/.env.local')

# Supabase設定
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# F-Logicエンジン初期化
flogic_engine = FLogicEngine()

def get_races_with_odds():
    """オッズデータがあるレースを取得"""
    print("📊 オッズデータがあるレースを取得中...")
    
    # 期間内のレースを取得
    races_response = supabase.table('jra_races').select('*').gte('開催日', '2025-08-31').lte('開催日', '2025-09-07').execute()
    races = races_response.data
    
    races_with_odds = []
    
    for race in races:
        # 馬データを取得してオッズの存在確認
        horses_response = supabase.table('jra_horses').select('*').eq('race_id', race['id']).execute()
        horses = horses_response.data
        
        if horses and any(h.get('単勝オッズ') and h['単勝オッズ'] > 0 for h in horses):
            races_with_odds.append({
                'race': race,
                'horses': horses
            })
    
    print(f"✅ {len(races_with_odds)}レースにオッズデータあり")
    return races_with_odds

def get_existing_engine_predictions(race_id: int, engine_name: str) -> Optional[dict]:
    """既存の予想データを取得"""
    response = supabase.table('jra_predictions').select('*').eq('race_id', race_id).eq('エンジン名', engine_name).execute()
    return response.data[0] if response.data else None

def calculate_flogic(race_data: dict) -> List[tuple]:
    """F-Logic計算を実行"""
    race = race_data['race']
    horses = race_data['horses']
    race_id = race['id']
    
    # 他のエンジンの予想を取得
    dlogic_pred = get_existing_engine_predictions(race_id, 'D-Logic')
    ilogic_pred = get_existing_engine_predictions(race_id, 'I-Logic')
    viewlogic_pred = get_existing_engine_predictions(race_id, 'ViewLogic')
    
    if not all([dlogic_pred, ilogic_pred, viewlogic_pred]):
        return None
    
    # 馬名から馬番へのマッピング作成
    name_to_number = {h['馬名']: h['馬番'] for h in horses}
    number_to_name = {h['馬番']: h['馬名'] for h in horses}
    
    # 各エンジンのスコアを馬番ベースで集計
    scores_by_number = {}
    
    # D-Logic
    for i in range(1, 6):
        horse_name = dlogic_pred.get(f'予想{i}位')
        score = dlogic_pred.get(f'予想{i}位スコア', 0)
        if horse_name and horse_name in name_to_number:
            num = name_to_number[horse_name]
            if num not in scores_by_number:
                scores_by_number[num] = {'d': 0, 'i': 0, 'v': 0, 'odds': 99.9}
            scores_by_number[num]['d'] = score or 0
    
    # I-Logic
    for i in range(1, 6):
        horse_name = ilogic_pred.get(f'予想{i}位')
        score = ilogic_pred.get(f'予想{i}位スコア', 0)
        if horse_name and horse_name in name_to_number:
            num = name_to_number[horse_name]
            if num not in scores_by_number:
                scores_by_number[num] = {'d': 0, 'i': 0, 'v': 0, 'odds': 99.9}
            scores_by_number[num]['i'] = score or 0
    
    # ViewLogic
    for i in range(1, 6):
        horse_name = viewlogic_pred.get(f'予想{i}位')
        score = viewlogic_pred.get(f'予想{i}位スコア', 0)
        if horse_name and horse_name in name_to_number:
            num = name_to_number[horse_name]
            if num not in scores_by_number:
                scores_by_number[num] = {'d': 0, 'i': 0, 'v': 0, 'odds': 99.9}
            scores_by_number[num]['v'] = score or 0
    
    # オッズを追加
    for h in horses:
        num = h['馬番']
        if num in scores_by_number:
            scores_by_number[num]['odds'] = h.get('単勝オッズ', 99.9) or 99.9
    
    # F-Logic計算
    flogic_scores = []
    for num, scores in scores_by_number.items():
        # オッズファクター (低オッズほど高評価)
        odds_factor = 100 / (1 + scores['odds'])
        
        # エンジンスコアの平均
        engine_avg = (scores['d'] + scores['i'] + scores['v']) / 3
        
        # F-Logicスコア = エンジン平均 * 0.7 + オッズファクター * 0.3
        flogic_score = engine_avg * 0.7 + odds_factor * 0.3
        
        horse_name = number_to_name.get(num, f'馬番{num}')
        flogic_scores.append((horse_name, flogic_score))
    
    # スコアでソート
    flogic_scores.sort(key=lambda x: x[1], reverse=True)
    
    return flogic_scores[:5]  # 上位5頭

def save_flogic_prediction(race_id: int, predictions: List[tuple]):
    """F-Logic予想をSupabaseに保存"""
    
    # 既存のF-Logic予想があるか確認
    existing = supabase.table('jra_predictions').select('id').eq('race_id', race_id).eq('エンジン名', 'F-Logic').execute()
    
    if existing.data:
        print(f"  ⚠️ 既存のF-Logic予想をスキップ")
        return False
    
    # 予想データを作成
    pred_data = {
        'race_id': race_id,
        'エンジン名': 'F-Logic',
        '予想作成日時': datetime.now().isoformat()
    }
    
    # 上位5頭を設定
    for i, (horse_name, score) in enumerate(predictions, 1):
        pred_data[f'予想{i}位'] = horse_name
        pred_data[f'予想{i}位スコア'] = round(score, 1)
    
    # 保存
    response = supabase.table('jra_predictions').insert(pred_data).execute()
    
    if response.data:
        print(f"  ✅ F-Logic予想を保存")
        return True
    else:
        print(f"  ❌ 保存失敗")
        return False

def main():
    print("=== F-Logic予想実行（8月31日〜9月7日）===\n")
    
    # オッズデータがあるレースを取得
    races_with_odds = get_races_with_odds()
    
    if not races_with_odds:
        print("❌ オッズデータがあるレースが見つかりません")
        return
    
    print(f"\n📈 F-Logic予想を実行中...\n")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, race_data in enumerate(races_with_odds, 1):
        race = race_data['race']
        race_name = f"{race['開催日']} {race['競馬場']}{race['レース番号']}R"
        print(f"[{i}/{len(races_with_odds)}] {race_name}")
        
        try:
            # F-Logic計算
            predictions = calculate_flogic(race_data)
            
            if predictions:
                # 予想結果を表示
                print(f"  予想: ", end="")
                for j, (name, score) in enumerate(predictions[:3], 1):
                    print(f"{j}位:{name}({score:.1f})", end=" ")
                print()
                
                # Supabaseに保存
                if save_flogic_prediction(race['id'], predictions):
                    success_count += 1
                else:
                    skip_count += 1
            else:
                print(f"  ⚠️ 他エンジンの予想が不足")
                skip_count += 1
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            error_count += 1
    
    print("\n========== 実行結果 ==========")
    print(f"✅ 成功: {success_count}レース")
    print(f"⏭️ スキップ: {skip_count}レース")
    print(f"❌ エラー: {error_count}レース")
    print(f"合計: {len(races_with_odds)}レース")

if __name__ == "__main__":
    main()