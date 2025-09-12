#!/usr/bin/env python3
"""
F-Logic対応版エンジン実行スクリプト
D-Logic, I-Logic, ViewLogicを実行後、その結果を使ってF-Logicを計算
"""

import os
import sys
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

# パスを追加
sys.path.append('/mnt/e/dev/Cusor/chatbot/uma/backend')
from services.flogic_engine import FLogicEngine

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# API設定
API_URL = 'https://uma-i30n.onrender.com'

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# F-Logicエンジン初期化
flogic_engine = FLogicEngine()

class EnginePredictor:
    """各エンジンで予想を実行するクラス"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_dlogic(self, horses: List[str]) -> Dict[str, float]:
        """D-Logic分析を実行（既存のコードと同じ）"""
        # ... 既存の実装 ...
        
    async def run_ilogic(self, horses: List[str]) -> Dict[str, float]:
        """I-Logic分析を実行（既存のコードと同じ）"""
        # ... 既存の実装 ...
        
    async def run_viewlogic(self, horses: List[str], jockeys: List[str], posts: List[int]) -> Dict[str, float]:
        """ViewLogic分析を実行（既存のコードと同じ）"""
        # ... 既存の実装 ...

async def process_race_with_flogic(race: dict):
    """1レースを処理（F-Logic対応版）"""
    race_id = race['id']
    race_date = race['開催日']
    venue = race['競馬場']
    race_num = race['レース番号']
    race_name = race.get('レース名', '')
    
    print(f"\n処理中: {race_date} {venue} {race_num}R {race_name}")
    
    # 馬情報を取得
    horses_data = await get_horses_for_race(race_id)
    if not horses_data:
        print(f"  馬情報なし、スキップ")
        return
    
    # データ準備
    horses = [h['馬名'] for h in horses_data]
    jockeys = [h.get('騎手', '不明') for h in horses_data]
    posts = [h.get('枠番号', 0) for h in horses_data]
    odds = [h.get('オッズ', 99.9) for h in horses_data]
    popularities = [h.get('人気', i+1) for i, h in enumerate(horses_data)]
    
    async with EnginePredictor() as predictor:
        # ========== 第1段階: 3エンジン並列実行 ==========
        print("  [第1段階] D-Logic/I-Logic/ViewLogic実行中...")
        
        # 3つのエンジンを並列実行
        results = await asyncio.gather(
            predictor.run_dlogic(horses),
            predictor.run_ilogic(horses),
            predictor.run_viewlogic(horses, jockeys, posts)
        )
        
        dlogic_scores = results[0]
        ilogic_scores = results[1]
        viewlogic_scores = results[2]
        
        # 各エンジンの結果を保存
        if dlogic_scores:
            sorted_dlogic = sorted(dlogic_scores.items(), key=lambda x: x[1], reverse=True)
            await save_predictions(race_id, 'D-Logic', sorted_dlogic)
            
        if ilogic_scores:
            sorted_ilogic = sorted(ilogic_scores.items(), key=lambda x: x[1], reverse=True)
            await save_predictions(race_id, 'I-Logic', sorted_ilogic)
            
        if viewlogic_scores:
            sorted_viewlogic = sorted(viewlogic_scores.items(), key=lambda x: x[1], reverse=True)
            await save_predictions(race_id, 'ViewLogic', sorted_viewlogic)
        
        # ========== 第2段階: F-Logic実行 ==========
        print("  [第2段階] F-Logic実行中...")
        
        # F-Logic用のデータを準備
        race_data_for_flogic = {
            'horses': horses,
            'odds': odds,
            'popularities': popularities,
            'jockeys': jockeys,
            'trainers': [h.get('調教師', '不明') for h in horses_data],
            'predictions': {
                'D-Logic': dlogic_scores,
                'I-Logic': ilogic_scores,
                'ViewLogic': viewlogic_scores
            }
        }
        
        # F-Logic実行
        flogic_result = await flogic_engine.analyze(race_data_for_flogic)
        
        if flogic_result and 'scores' in flogic_result:
            flogic_scores = flogic_result['scores']
            sorted_flogic = sorted(flogic_scores.items(), key=lambda x: x[1], reverse=True)
            await save_predictions(race_id, 'F-Logic', sorted_flogic)
            
            # 投資価値のある馬を表示
            value_bets = flogic_result.get('value_bets', [])
            if value_bets:
                print(f"  💰 投資推奨馬:")
                for bet in value_bets[:2]:
                    print(f"    - {bet['horse']} (期待値: {bet['expected_value']:.1f}%)")

async def save_predictions(race_id: int, engine_name: str, predictions: List[Tuple[str, float]]):
    """予想結果をSupabaseに保存（4エンジン対応）"""
    try:
        # 既存の予想を削除
        supabase.table('jra_predictions').delete().eq('race_id', race_id).eq('エンジン名', engine_name).execute()
        
        # 上位5頭を1レコードで保存
        if len(predictions) >= 5:
            data = {
                'race_id': race_id,
                'エンジン名': engine_name,
                '予想1位': predictions[0][0],
                '予想1位スコア': predictions[0][1],
                '予想2位': predictions[1][0],
                '予想2位スコア': predictions[1][1],
                '予想3位': predictions[2][0],
                '予想3位スコア': predictions[2][1],
                '予想4位': predictions[3][0],
                '予想4位スコア': predictions[3][1],
                '予想5位': predictions[4][0],
                '予想5位スコア': predictions[4][1],
                '予想作成日時': datetime.now().isoformat()
            }
            supabase.table('jra_predictions').insert(data).execute()
            
        print(f"    ✅ {engine_name}: 上位5頭を保存完了")
        
    except Exception as e:
        print(f"    ❌ {engine_name} 保存エラー: {e}")

async def get_horses_for_race(race_id: int):
    """特定レースの馬情報を取得"""
    try:
        result = supabase.table('jra_horses').select('*').eq('race_id', race_id).execute()
        return result.data
    except Exception as e:
        print(f"馬情報取得エラー: {e}")
        return []

async def main():
    """メイン処理"""
    print("=" * 60)
    print("4エンジン体制（D-Logic/I-Logic/ViewLogic/F-Logic）実行開始")
    print("=" * 60)
    
    # テスト用: 最初の3レースのみ
    races = await get_races_from_supabase()
    test_races = races[:3]
    
    print(f"\n処理対象: {len(test_races)}レース")
    
    for race in test_races:
        await process_race_with_flogic(race)
        await asyncio.sleep(2)  # API負荷対策
    
    print("\n" + "=" * 60)
    print("4エンジン処理完了！")
    
    # 結果サマリー表示
    result = supabase.table('jra_predictions').select('エンジン名').execute()
    from collections import Counter
    engine_counts = Counter([d['エンジン名'] for d in result.data])
    
    print("\n【処理結果サマリー】")
    for engine, count in engine_counts.items():
        print(f"  {engine}: {count}レース")

async def get_races_from_supabase():
    """Supabaseから全レース情報を取得"""
    try:
        result = supabase.table('jra_races').select('*').execute()
        return result.data
    except Exception as e:
        print(f"レース取得エラー: {e}")
        return []

if __name__ == '__main__':
    asyncio.run(main())