#!/usr/bin/env python3
"""
正確な予測精度分析システム
jra_horsesテーブルを使用した馬名→馬番変換
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from collections import defaultdict
import json

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class AccurateAnalyzer:
    """正確な予測精度分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.horses = []
        self.horse_mapping = {}  # race_id -> {horse_name: number}
        self.analysis_results = defaultdict(dict)
        
    def load_data(self):
        """データ読み込み"""
        print("=" * 80)
        print("📊 正確なデータ読み込み開始")
        print("=" * 80)
        
        # レース情報取得
        races_response = supabase.table('jra_races').select('*').order('id').execute()
        self.races = races_response.data
        print(f"✅ レース情報: {len(self.races)}件")
        
        # 予測データ取得
        predictions_response = supabase.table('jra_predictions').select('*').execute()
        self.predictions = predictions_response.data
        print(f"✅ 予測データ: {len(self.predictions)}件")
        
        # 払い戻しデータ取得
        payouts_response = supabase.table('jra_payouts').select('*').execute()
        self.payouts = payouts_response.data
        print(f"✅ 払い戻しデータ: {len(self.payouts)}件")
        
        # 出走馬データ取得
        horses_response = supabase.table('jra_horses').select('*').execute()
        self.horses = horses_response.data
        print(f"✅ 出走馬データ: {len(self.horses)}件")
        
        # データを辞書形式で整理
        self.race_dict = {r['id']: r for r in self.races}
        self.payout_dict = {p['race_id']: p for p in self.payouts}
        
        # 予測データをエンジン別に整理
        self.predictions_by_engine = defaultdict(dict)
        for pred in self.predictions:
            race_id = pred['race_id']
            engine = pred['エンジン名'].lower().replace('-', '')
            self.predictions_by_engine[engine][race_id] = pred
        
        # 出走馬データから馬名→馬番マッピングを作成
        self.create_horse_mapping()
        
        print(f"✅ データ整理完了")
    
    def create_horse_mapping(self):
        """出走馬データから馬名→馬番マッピングを作成"""
        print("\n🔍 馬名→馬番マッピング作成")
        
        for horse in self.horses:
            race_id = horse['race_id']
            horse_name = horse['馬名']
            horse_number = horse['馬番']
            
            if race_id not in self.horse_mapping:
                self.horse_mapping[race_id] = {}
            
            self.horse_mapping[race_id][horse_name] = horse_number
        
        # マッピング状況を確認
        mapped_races = len(self.horse_mapping)
        print(f"  マッピング完了: {mapped_races}レース")
        
        # サンプル表示
        for i, (race_id, mapping) in enumerate(list(self.horse_mapping.items())[:3]):
            print(f"  Race {race_id}: {len(mapping)}頭")
            for horse_name, num in list(mapping.items())[:3]:
                print(f"    {horse_name} → {num}番")
    
    def calculate_exact_tansho_accuracy(self):
        """正確な単勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 正確な単勝的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits = 0
            total = 0
            total_return = 0
            hit_details = []
            
            engine_predictions = self.predictions_by_engine.get(engine, {})
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in engine_predictions or race_id not in self.horse_mapping:
                    continue
                
                prediction = engine_predictions[race_id]
                mapping = self.horse_mapping[race_id]
                race = self.race_dict.get(race_id, {})
                
                # 予想1位の馬名
                predicted_horse_name = prediction.get('予想1位')
                # 実際の1着馬番
                actual_winner_num = payout.get('単勝_馬番')
                
                if not predicted_horse_name or not actual_winner_num:
                    continue
                
                # 予想馬名を馬番に変換
                predicted_horse_num = mapping.get(predicted_horse_name)
                
                if predicted_horse_num is None:
                    continue  # マッピングなし
                
                total += 1
                actual_num = int(actual_winner_num)
                
                # 的中判定
                if int(predicted_horse_num) == actual_num:
                    hits += 1
                    payout_amount = payout.get('単勝_払戻', 0)
                    total_return += payout_amount
                    
                    hit_details.append({
                        'race': f"{race.get('開催日', '')} {race.get('競馬場', '')} {race.get('レース番号', '')}R",
                        'race_name': race.get('レース名', ''),
                        'horse_name': predicted_horse_name,
                        'horse_num': actual_winner_num,
                        'payout': payout_amount
                    })
            
            accuracy = (hits / total * 100) if total > 0 else 0
            recovery_rate = (total_return / (total * 100) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['単勝'] = {
                '的中数': hits,
                '総レース数': total,
                '的中率': accuracy,
                '回収率': recovery_rate,
                '総払戻': total_return,
                '的中詳細': hit_details
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  的中: {hits}/{total} ({accuracy:.1f}%)")
            print(f"  回収率: {recovery_rate:.1f}%")
            print(f"  総投資: {total * 100:,}円 → 総払戻: {total_return:,}円")
            print(f"  損益: {total_return - (total * 100):+,}円")
            
            if hit_details:
                print(f"  的中例（最新3件）:")
                for detail in hit_details[-3:]:
                    print(f"    • {detail['race']} {detail['horse_name']}({detail['horse_num']}番) {detail['payout']}円")
    
    def calculate_exact_fukusho_accuracy(self):
        """正確な複勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 正確な複勝的中率分析")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits_by_rank = [0, 0, 0]  # 1位予想、2位予想、3位予想
            total = 0
            
            engine_predictions = self.predictions_by_engine.get(engine, {})
            
            for race_id, payout in self.payout_dict.items():
                if race_id not in engine_predictions or race_id not in self.horse_mapping:
                    continue
                
                prediction = engine_predictions[race_id]
                mapping = self.horse_mapping[race_id]
                
                # 実際の3着以内の馬番
                actual_top3 = []
                for i in range(1, 4):
                    horse_num = payout.get(f'複勝_馬番_{i}')
                    if horse_num:
                        try:
                            actual_top3.append(int(horse_num))
                        except:
                            pass
                
                if not actual_top3:
                    continue
                
                total += 1
                
                # 各順位の予想をチェック
                for rank in range(1, 4):
                    predicted_horse_name = prediction.get(f'予想{rank}位')
                    if predicted_horse_name:
                        predicted_horse_num = mapping.get(predicted_horse_name)
                        if predicted_horse_num and int(predicted_horse_num) in actual_top3:
                            hits_by_rank[rank - 1] += 1
            
            total_hits = sum(hits_by_rank)
            avg_accuracy = (total_hits / (total * 3) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['複勝'] = {
                '1位予想的中': hits_by_rank[0],
                '2位予想的中': hits_by_rank[1], 
                '3位予想的中': hits_by_rank[2],
                '総的中数': total_hits,
                '総レース数': total,
                '平均的中率': avg_accuracy
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  1位予想→3着内: {hits_by_rank[0]}/{total} ({hits_by_rank[0]/total*100:.1f}%)")
            print(f"  2位予想→3着内: {hits_by_rank[1]}/{total} ({hits_by_rank[1]/total*100:.1f}%)")
            print(f"  3位予想→3着内: {hits_by_rank[2]}/{total} ({hits_by_rank[2]/total*100:.1f}%)")
            print(f"  総合的中率: {avg_accuracy:.1f}%")
    
    def generate_final_report(self):
        """最終レポート生成"""
        print("\n" + "=" * 80)
        print("📈 最終分析レポート")
        print("=" * 80)
        
        # エンジン別総合評価
        engine_scores = {}
        
        for engine in ['dlogic', 'ilogic', 'viewlogic']:
            tansho = self.analysis_results[engine].get('単勝', {})
            fukusho = self.analysis_results[engine].get('複勝', {})
            
            # 総合スコア計算
            tansho_score = tansho.get('的中率', 0) * 3
            fukusho_score = fukusho.get('平均的中率', 0) * 2
            recovery_score = tansho.get('回収率', 0) * 1.5
            
            total_score = (tansho_score + fukusho_score + recovery_score) / 6.5
            
            engine_scores[engine] = {
                'engine_name': engine.upper(),
                'total_score': total_score,
                'tansho_hits': tansho.get('的中数', 0),
                'tansho_rate': tansho.get('的中率', 0),
                'tansho_recovery': tansho.get('回収率', 0),
                'fukusho_rate': fukusho.get('平均的中率', 0),
                'total_races': tansho.get('総レース数', 0),
                'profit': tansho.get('総払戻', 0) - (tansho.get('総レース数', 0) * 100)
            }
        
        # ランキング表示
        print("\n🏆 エンジン最終ランキング（実測値）")
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for rank, (engine, scores) in enumerate(sorted_engines, 1):
            print(f"\n第{rank}位: {scores['engine_name']}")
            print(f"  総合スコア: {scores['total_score']:.2f}点")
            print(f"  対象レース: {scores['total_races']}レース")
            print(f"  単勝: {scores['tansho_hits']}的中 / 的中率{scores['tansho_rate']:.1f}% / 回収率{scores['tansho_recovery']:.1f}%")
            print(f"  複勝的中率: {scores['fukusho_rate']:.1f}%")
            print(f"  損益: {scores['profit']:+,}円")
        
        # 投資シミュレーション
        print(f"\n💰 実績ベース投資シミュレーション")
        print(f"（過去{sorted_engines[0][1]['total_races']}レース実績）")
        
        for engine, perf in sorted_engines:
            investment = perf['total_races'] * 100
            returns = perf['profit'] + investment
            roi = (perf['profit'] / investment * 100) if investment > 0 else 0
            
            print(f"{perf['engine_name']}: {investment:,}円投資 → {returns:,}円回収")
            print(f"  実損益: {perf['profit']:+,}円 (ROI: {roi:+.1f}%)")
        
        return engine_scores

def main():
    """メイン処理"""
    print("🚀 正確な競馬AI予測分析システム")
    print("=" * 80)
    
    analyzer = AccurateAnalyzer()
    
    # データ読み込み・整理
    analyzer.load_data()
    
    # 正確な分析実行
    analyzer.calculate_exact_tansho_accuracy()
    analyzer.calculate_exact_fukusho_accuracy()
    
    # 最終レポート
    performance = analyzer.generate_final_report()
    
    # 結果保存
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/accurate_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 正確な分析レポートを保存: accurate_analysis_result.json")
    print("=" * 80)
    print("🎉 正確な分析完了")
    print("=" * 80)

if __name__ == '__main__':
    main()