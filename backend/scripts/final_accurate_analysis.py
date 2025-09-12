#!/usr/bin/env python3
"""
最終正確分析システム
Supabaseの馬番データを使用した完全正確な的中率分析
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict
import json

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class FinalAccurateAnalyzer:
    """最終正確分析クラス"""
    
    def __init__(self):
        self.races = []
        self.predictions = []
        self.payouts = []
        self.horses = []
        self.horse_mapping = {}  # race_id -> {horse_name: horse_number}
        self.analysis_results = defaultdict(dict)
        
    def load_all_data(self):
        """全データ読み込み"""
        print("🚀 最終正確分析システム")
        print("=" * 80)
        print("📊 データ読み込み開始")
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
        
        # 出走馬データ（馬番付き）取得
        horses_response = supabase.table('jra_horses').select('*').execute()
        self.horses = horses_response.data
        print(f"✅ 出走馬データ: {len(self.horses)}件")
        
        # データ整理
        self.race_dict = {r['id']: r for r in self.races}
        self.payout_dict = {p['race_id']: p for p in self.payouts}
        
        # 予測データをエンジン別に整理
        self.predictions_by_engine = defaultdict(dict)
        for pred in self.predictions:
            race_id = pred['race_id']
            engine = pred['エンジン名'].lower().replace('-', '')
            self.predictions_by_engine[engine][race_id] = pred
        
        print(f"✅ データ整理完了")
        
        # エンジン別件数表示
        for engine in ['dlogic', 'ilogic', 'viewlogic']:
            count = len(self.predictions_by_engine.get(engine, {}))
            print(f"  {engine.upper()}: {count}件")
    
    def create_accurate_horse_mapping(self):
        """正確な馬名→馬番マッピングを作成"""
        print("\n🔍 正確な馬名→馬番マッピング作成")
        
        mapped_count = 0
        
        for horse in self.horses:
            race_id = horse['race_id']
            horse_name = horse['馬名']
            horse_number = horse.get('馬番')
            
            if horse_number is not None:
                if race_id not in self.horse_mapping:
                    self.horse_mapping[race_id] = {}
                
                self.horse_mapping[race_id][horse_name] = horse_number
                mapped_count += 1
        
        print(f"✅ 正確マッピング完了: {len(self.horse_mapping)}レース、{mapped_count}頭")
        
        # サンプル表示
        sample_race_ids = list(self.horse_mapping.keys())[:3]
        for race_id in sample_race_ids:
            race = self.race_dict.get(race_id, {})
            mapping = self.horse_mapping[race_id]
            race_info = f"{race.get('開催日', '')} {race.get('競馬場', '')} {race.get('レース番号', '')}R"
            print(f"  {race_info}: {len(mapping)}頭")
            for horse_name, number in list(mapping.items())[:3]:
                print(f"    {horse_name} → {number}番")
    
    def calculate_final_tansho_accuracy(self):
        """最終単勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎯 最終単勝的中率分析（完全正確版）")
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
                
                # 正確な馬番マッピングから取得
                predicted_horse_num = mapping.get(predicted_horse_name)
                
                if predicted_horse_num is None:
                    continue
                
                total += 1
                actual_num = int(actual_winner_num)
                
                # 的中判定
                if predicted_horse_num == actual_num:
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
            profit = total_return - (total * 100)
            roi = (profit / (total * 100) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['単勝'] = {
                '的中数': hits,
                '総レース数': total,
                '的中率': accuracy,
                '回収率': recovery_rate,
                '総払戻': total_return,
                '総投資': total * 100,
                '損益': profit,
                'ROI': roi,
                '的中詳細': hit_details
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  📊 分析対象: {total}レース")
            print(f"  🎯 的中: {hits}/{total} ({accuracy:.1f}%)")
            print(f"  💰 回収率: {recovery_rate:.1f}%")
            print(f"  💵 ROI: {roi:+.1f}%")
            print(f"  📈 総投資: {total * 100:,}円 → 総払戻: {total_return:,}円")
            print(f"  💸 損益: {profit:+,}円")
            
            if roi > 0:
                print(f"  🎉 利益確定！")
            
            if hit_details:
                print(f"  🏆 的中例（最新3件）:")
                for detail in hit_details[-3:]:
                    print(f"    • {detail['race']} {detail['race_name']}")
                    print(f"      {detail['horse_name']}({detail['horse_num']}番) {detail['payout']}円")
    
    def calculate_final_fukusho_accuracy(self):
        """最終複勝的中率計算"""
        print("\n" + "=" * 80)
        print("🎪 最終複勝的中率分析（上位5頭完全版）")
        print("=" * 80)
        
        engines = ['dlogic', 'ilogic', 'viewlogic']
        
        for engine in engines:
            hits_by_rank = [0, 0, 0, 0, 0]  # 1-5位予想
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
                for rank in range(1, 6):
                    predicted_horse_name = prediction.get(f'予想{rank}位')
                    if predicted_horse_name:
                        predicted_horse_num = mapping.get(predicted_horse_name)
                        if predicted_horse_num and predicted_horse_num in actual_top3:
                            hits_by_rank[rank - 1] += 1
            
            total_hits = sum(hits_by_rank)
            overall_accuracy = (total_hits / (total * 5) * 100) if total > 0 else 0
            
            self.analysis_results[engine]['複勝'] = {
                '1位予想的中': hits_by_rank[0],
                '2位予想的中': hits_by_rank[1],
                '3位予想的中': hits_by_rank[2],
                '4位予想的中': hits_by_rank[3],
                '5位予想的中': hits_by_rank[4],
                '総的中数': total_hits,
                '総レース数': total,
                '総合的中率': overall_accuracy
            }
            
            print(f"\n【{engine.upper()}】")
            print(f"  📊 分析対象: {total}レース")
            for rank in range(5):
                rate = (hits_by_rank[rank] / total * 100) if total > 0 else 0
                print(f"  {rank+1}位予想→3着内: {hits_by_rank[rank]}/{total} ({rate:.1f}%)")
            
            print(f"  🎪 総合的中率: {overall_accuracy:.1f}%")
            
            # TOP3的中率（体験ページとの比較用）
            top3_hits = sum(hits_by_rank[:3])
            top3_accuracy = (top3_hits / (total * 3) * 100) if total > 0 else 0
            print(f"  🥇 TOP3複勝的中率: {top3_accuracy:.1f}% (体験ページ比較用)")
    
    def generate_final_championship_report(self):
        """最終チャンピオンシップレポート"""
        print("\n" + "=" * 80)
        print("👑 最終チャンピオンシップレポート（完全正確版）")
        print("=" * 80)
        
        # エンジン別総合評価
        engine_scores = {}
        
        for engine in ['dlogic', 'ilogic', 'viewlogic']:
            tansho = self.analysis_results[engine].get('単勝', {})
            fukusho = self.analysis_results[engine].get('複勝', {})
            
            # 総合スコア計算（重み付け）
            tansho_score = tansho.get('的中率', 0) * 3        # 単勝3倍
            fukusho_score = fukusho.get('総合的中率', 0) * 2   # 複勝2倍  
            recovery_score = min(tansho.get('回収率', 0), 200) * 1.5  # 回収率1.5倍（上限200%）
            
            total_score = (tansho_score + fukusho_score + recovery_score) / 6.5
            
            engine_scores[engine] = {
                'engine_name': engine.upper(),
                'total_score': total_score,
                'tansho_hits': tansho.get('的中数', 0),
                'tansho_rate': tansho.get('的中率', 0),
                'tansho_recovery': tansho.get('回収率', 0),
                'fukusho_rate': fukusho.get('総合的中率', 0),
                'top3_fukusho_rate': (sum([
                    fukusho.get('1位予想的中', 0),
                    fukusho.get('2位予想的中', 0),
                    fukusho.get('3位予想的中', 0)
                ]) / (fukusho.get('総レース数', 1) * 3) * 100),
                'total_races': tansho.get('総レース数', 0),
                'profit': tansho.get('損益', 0),
                'roi': tansho.get('ROI', 0)
            }
        
        # 最終チャンピオン決定
        print("\n🏆 最終エンジンチャンピオンシップ")
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for rank, (engine, scores) in enumerate(sorted_engines, 1):
            if rank == 1:
                print(f"\n🥇 チャンピオン: {scores['engine_name']}")
            elif rank == 2:
                print(f"\n🥈 準チャンピオン: {scores['engine_name']}")
            else:
                print(f"\n🥉 第3位: {scores['engine_name']}")
            
            print(f"  📊 総合スコア: {scores['total_score']:.2f}点")
            print(f"  🎯 対象レース: {scores['total_races']}レース")
            print(f"  🏁 単勝: {scores['tansho_hits']}的中 / {scores['tansho_rate']:.1f}%")
            print(f"  💰 回収率: {scores['tansho_recovery']:.1f}%")
            print(f"  🎪 複勝的中率: {scores['fukusho_rate']:.1f}%")
            print(f"  🥇 TOP3複勝的中率: {scores['top3_fukusho_rate']:.1f}%")
            print(f"  💵 ROI: {scores['roi']:+.1f}%")
            print(f"  📈 損益: {scores['profit']:+,}円")
            
            if scores['roi'] > 0:
                print(f"  🎉 利益確定エンジン！")
        
        # 最終結論
        champion = sorted_engines[0]
        print(f"\n🎯 最終結論")
        print(f"チャンピオンエンジン: {champion[1]['engine_name']}")
        print(f"- 総合力でNo.1の実力を実証")
        print(f"- {champion[1]['total_races']}レース完全分析済み")
        print(f"- ROI {champion[1]['roi']:+.1f}%の実績")
        
        return engine_scores

def main():
    """最終メイン処理"""
    analyzer = FinalAccurateAnalyzer()
    
    # データ読み込み・整理
    analyzer.load_all_data()
    analyzer.create_accurate_horse_mapping()
    
    # 最終分析実行
    analyzer.calculate_final_tansho_accuracy()
    analyzer.calculate_final_fukusho_accuracy()
    
    # 最終レポート
    performance = analyzer.generate_final_championship_report()
    
    # 最終結果保存
    with open('/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/final_championship_result.json', 'w', encoding='utf-8') as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 最終チャンピオンシップレポート保存: final_championship_result.json")
    print("=" * 80)
    print("🎉 完全正確分析完了！これが真の結果です！")
    print("=" * 80)

if __name__ == '__main__':
    main()